"""Render the dashboard to docs/index.html so it can be hosted as a static page (GitHub Pages)."""
import os
from datetime import datetime, timezone

from flask import render_template

import app as webapp

OUT = os.path.join(os.path.dirname(__file__), "docs")


def build():
    os.makedirs(OUT, exist_ok=True)
    with webapp.app.test_request_context():
        html = render_template(
            "index.html",
            products=webapp.load_products(),
            static_mode=True,
            built=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        )
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        f.write(open(os.path.join(os.path.dirname(__file__), "static", "manifest.json"), encoding="utf-8").read())


if __name__ == "__main__":
    build()
    print("built docs/index.html")
