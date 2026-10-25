import os
import sqlite3

DB_PATH = os.environ.get("DEALS_DB", os.path.join(os.path.dirname(__file__), "deals.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, brand TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    retailer TEXT NOT NULL, url TEXT NOT NULL, auto INTEGER NOT NULL DEFAULT 1,
    UNIQUE(product_id, url)
);
CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY, listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    checked_at TEXT NOT NULL DEFAULT (datetime('now')),
    price REAL, rrp REAL, in_stock INTEGER, promo_text TEXT, promo_pct REAL, error TEXT
);
"""


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init():
    with connect() as con:
        con.executescript(SCHEMA)
