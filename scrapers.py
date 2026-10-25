"""Price readers, one per retailer family.

Each reader returns a dict: price, rrp (original price, may equal price), in_stock, promo.
Retailers behind bot protection (Boots, Sephora UK, Merit's own store) are deliberately
not scraped; they are tracked as manual links.
"""
import json
import re
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}

# hostname -> reader name; anything else is a manual link
RETAILERS = {
    "www.lookfantastic.com": ("LookFantastic", "thg"),
    "www.cultbeauty.co.uk": ("Cult Beauty", "thg"),
    "www.spacenk.com": ("Space NK", "spacenk"),
    "www.boots.com": ("Boots", None),
    "www.sephora.co.uk": ("Sephora UK", None),
    "www.meritbeauty.com": ("Merit", None),
}

_session = requests.Session()


def retailer_for(url):
    host = urlparse(url).netloc.lower()
    return RETAILERS.get(host, (host.replace("www.", ""), None))


def _get(url):
    r = _session.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text


def _json_after(text, marker):
    i = text.find(marker)
    if i < 0:
        return None
    obj, _ = json.JSONDecoder().raw_decode(text[i + len(marker):].lstrip())
    return obj


def _money(v):
    try:
        return float(re.sub(r"[^\d.]", "", str(v)))
    except ValueError:
        return None


def _pct_promo(text):
    """'Save 22% | Use Code: FLASH22' -> ('Save 22% | Use Code: FLASH22', 22.0)"""
    m = re.search(r"(\d{1,2})\s*%", text or "")
    return (text, float(m.group(1))) if m and re.search(r"code", text, re.I) else (None, None)


def read_thg(url):
    """LookFantastic and Cult Beauty (same platform)."""
    html = _get(url)
    soup = BeautifulSoup(html, "lxml")
    want = parse_qs(urlparse(url).query).get("variation", [None])[0]
    variants = _json_after(html, "const variants = ") or []
    default = _json_after(html, "const defaultVariant = ")
    v = None
    if want:
        v = next((x for x in variants if str(x.get("sku")) == want), None)
    v = v or default
    if not v:
        raise ValueError("no product data found on page")
    p = v["price"]
    price = _money(p["price"]["amount"])
    rrp = _money((p.get("rrp") or {}).get("amount")) or price
    promo = None
    for el in soup.select("[data-track-push]"):
        text, pct = _pct_promo(el.get("data-track-push"))
        if text:
            promo = {"text": text, "pct": pct}
            break
    return {"price": price, "rrp": rrp, "in_stock": bool(v.get("inStock", True)), "promo": promo,
            "title": v.get("title")}


def read_spacenk(url):
    _get("https://www.spacenk.com/uk/search?q=x")  # establish a session cookie first
    html = _get(url)
    soup = BeautifulSoup(html, "lxml")
    offer = None
    title = None
    for sc in soup.find_all("script", type="application/ld+json"):
        t = sc.string or ""
        if "ProductGroup" in t or '"Product"' in t:
            d = json.loads(t)
            title = d.get("name")
            variants = d.get("hasVariant") or [d]
            offer = (variants[0].get("offers") or {})
            break
    if not offer:
        raise ValueError("no product data found on page")
    price = _money(offer.get("price"))
    # when discounted the pricing block shows both the old and new price
    block = soup.select_one(".product-name__pricing")
    nums = [_money(m) for m in re.findall(r"£\s*[\d.]+", block.get_text(" ")) if block] if block else []
    rrp = max([n for n in nums if n] + [price])
    return {"price": price, "rrp": rrp, "in_stock": "InStock" in str(offer.get("availability")),
            "promo": None, "title": title}


READERS = {"thg": read_thg, "spacenk": read_spacenk}


def read_price(url):
    name, reader = retailer_for(url)
    if not reader:
        raise ValueError("manual link (retailer blocks automated checks)")
    return READERS[reader](url)
