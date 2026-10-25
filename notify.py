"""Phone alerts via ntfy.sh. Does nothing unless a topic is configured.

Topic comes from the NTFY_TOPIC env var or an ntfy_topic.txt file next to this script.
Anyone who knows the topic name can read the alerts, so keep it random.
"""
import os

import requests

_HERE = os.path.dirname(__file__)


def topic():
    t = os.environ.get("NTFY_TOPIC", "").strip()
    if not t:
        try:
            t = open(os.path.join(_HERE, "ntfy_topic.txt")).read().strip()
        except OSError:
            t = ""
    return t


def send(title, lines, click_url=None):
    t = topic()
    if not t or not lines:
        return False
    headers = {"Title": title.encode("ascii", "ignore").decode(), "Tags": "shopping_bags"}
    if click_url:
        headers["Click"] = click_url
    r = requests.post(f"https://ntfy.sh/{t}", data="\n".join(lines).encode("utf-8"), headers=headers, timeout=15)
    return r.ok
