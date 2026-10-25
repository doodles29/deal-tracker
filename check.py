"""Check every automatic listing, record the price, and alert on good changes.
Run by hand or on a schedule."""
import time

import db
import notify
import scrapers


def _alerts(name, retailer, prev, now):
    """Compare this check with the previous good one; return alert lines."""
    out = []
    price, rrp, promo = now["price"], now["rrp"], now.get("promo") or {}
    on_sale = rrp and rrp > price
    if prev is None:
        # first reading: only worth shouting about if it's already discounted
        if on_sale:
            out.append(f"{name} at {retailer}: £{price:.2f} (was £{rrp:.2f})")
        if promo.get("text"):
            out.append(f"{name} at {retailer}: code offer, {promo['text']}")
        return out
    if price < prev["price"]:
        out.append(f"{name} at {retailer}: dropped to £{price:.2f} (from £{prev['price']:.2f})")
    elif on_sale and not (prev["rrp"] and prev["rrp"] > prev["price"]):
        out.append(f"{name} at {retailer}: now on sale, £{price:.2f} (was £{rrp:.2f})")
    if promo.get("text") and promo["text"] != prev["promo_text"]:
        out.append(f"{name} at {retailer}: new code offer, {promo['text']}")
    if now["in_stock"] and prev["in_stock"] == 0:
        out.append(f"{name} at {retailer}: back in stock at £{price:.2f}")
    return out


def check_listing(con, listing):
    """Returns (status line, alert lines)."""
    prev = con.execute(
        "SELECT * FROM prices WHERE listing_id=? AND price IS NOT NULL ORDER BY id DESC LIMIT 1", (listing["id"],)
    ).fetchone()
    try:
        r = scrapers.read_price(listing["url"])
    except Exception as e:  # keep going; one broken page shouldn't stop the rest
        con.execute("INSERT INTO prices (listing_id, error) VALUES (?,?)", (listing["id"], str(e)[:200]))
        return f"{listing['retailer']}: ERROR {e}", []
    promo = r.get("promo") or {}
    con.execute(
        "INSERT INTO prices (listing_id, price, rrp, in_stock, promo_text, promo_pct) VALUES (?,?,?,?,?,?)",
        (listing["id"], r["price"], r["rrp"], int(r["in_stock"]), promo.get("text"), promo.get("pct")),
    )
    line = f"{listing['retailer']}: £{r['price']:.2f} (was £{r['rrp']:.2f})" + (f" + {promo['text']}" if promo else "")
    return line, _alerts(listing["name"], listing["retailer"], prev, r)


def run(product_id=None, notify_on=True):
    out, alerts = [], []
    with db.connect() as con:
        q = "SELECT l.*, p.name FROM listings l JOIN products p ON p.id = l.product_id WHERE l.auto = 1"
        args = ()
        if product_id:
            q += " AND l.product_id = ?"
            args = (product_id,)
        for l in con.execute(q, args).fetchall():
            line, a = check_listing(con, l)
            out.append(f"{l['name']} @ {line}")
            alerts += a
            con.commit()
            time.sleep(2)  # be polite to the retailers
    if notify_on and alerts:
        notify.send("Deal alert", alerts)
    return out, alerts


if __name__ == "__main__":
    db.init()
    lines, alerts = run()
    print("\n".join(lines))
    print(f"\n{len(alerts)} alert(s)" + (":\n" + "\n".join(alerts) if alerts else ""))
