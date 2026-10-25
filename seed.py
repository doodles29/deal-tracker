"""Load products.json into the database. Safe to re-run; existing rows are kept.

products.json is the source of truth for the hosted version: edit it (e.g. on
github.com from your phone) and the next run picks up new products and links.
"""
import json
import os

import db
import scrapers

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "products.json")


def add_listing(con, product_id, url):
    name, reader = scrapers.retailer_for(url)
    con.execute("INSERT OR IGNORE INTO listings (product_id, retailer, url, auto) VALUES (?,?,?,?)",
                (product_id, name, url, 1 if reader else 0))


def run():
    db.init()
    with open(PRODUCTS_FILE, encoding="utf-8") as f:
        products = json.load(f)
    with db.connect() as con:
        for p in products:
            row = con.execute("SELECT id FROM products WHERE brand=? AND name=?", (p["brand"], p["name"])).fetchone()
            pid = row["id"] if row else con.execute(
                "INSERT INTO products (brand, name) VALUES (?,?)", (p["brand"], p["name"])).lastrowid
            for u in p["links"]:
                add_listing(con, pid, u)


if __name__ == "__main__":
    run()
    print("seeded")
