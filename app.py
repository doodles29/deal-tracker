import os

from flask import Flask, redirect, render_template, request, url_for

import check
import db
import seed

app = Flask(__name__)


def effective(price, pct):
    return round(price * (1 - pct / 100), 2) if price is not None and pct else None


def load_products():
    with db.connect() as con:
        products = []
        for p in con.execute("SELECT * FROM products ORDER BY brand, name"):
            listings = []
            for l in con.execute("SELECT * FROM listings WHERE product_id=? ORDER BY auto DESC, retailer", (p["id"],)):
                rows = con.execute("SELECT * FROM prices WHERE listing_id=? ORDER BY id DESC LIMIT 30", (l["id"],)).fetchall()
                good = [r for r in rows if r["price"] is not None]
                last = rows[0] if rows else None
                cur = good[0] if good else None
                low = min((r["price"] for r in good), default=None)
                item = {"l": l, "last": last, "cur": cur, "low": low, "history": [r["price"] for r in reversed(good)]}
                if cur:
                    item["with_code"] = effective(cur["price"], cur["promo_pct"])
                    item["best"] = item["with_code"] or cur["price"]
                    item["off_pct"] = round((1 - cur["price"] / cur["rrp"]) * 100) if cur["rrp"] and cur["rrp"] > cur["price"] else 0
                listings.append(item)
            priced = [x for x in listings if x.get("best") is not None and x["cur"]["in_stock"]]
            best = min(priced, key=lambda x: x["best"]) if priced else None
            products.append({"p": p, "listings": listings, "best": best})
        return products


@app.route("/")
def index():
    return render_template("index.html", products=load_products())


@app.post("/check")
def run_check():
    check.run(request.form.get("product_id", type=int))
    return redirect(url_for("index"))


@app.post("/add")
def add():
    brand, name, link = (request.form.get(k, "").strip() for k in ("brand", "name", "url"))
    if brand and name:
        with db.connect() as con:
            row = con.execute("SELECT id FROM products WHERE brand=? AND name=?", (brand, name)).fetchone()
            pid = row["id"] if row else con.execute("INSERT INTO products (brand, name) VALUES (?,?)", (brand, name)).lastrowid
            if link.startswith("http"):
                seed.add_listing(con, pid, link)
    return redirect(url_for("index"))


@app.post("/listing")
def add_listing():
    link = request.form.get("url", "").strip()
    pid = request.form.get("product_id", type=int)
    if pid and link.startswith("http"):
        with db.connect() as con:
            seed.add_listing(con, pid, link)
    return redirect(url_for("index"))


@app.post("/delete-listing/<int:lid>")
def delete_listing(lid):
    with db.connect() as con:
        con.execute("DELETE FROM listings WHERE id=?", (lid,))
    return redirect(url_for("index"))


if __name__ == "__main__":
    seed.run()
    # 0.0.0.0 lets your phone reach it over the same wifi; set HOST=127.0.0.1 to keep it laptop-only
    app.run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", 5000)))
