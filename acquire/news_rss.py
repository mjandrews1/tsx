#!/usr/bin/env python3
"""Acquire headline-only news metadata from RSS/Atom.

**IP policy:** store date/time, title, source name, and URL only.
Never store article body, snippets, or full text. URL points to the
publisher; tsx is an index, not a content host.

Feeds (examples):
  google: https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en
  bbc:    https://feeds.bbci.co.uk/news/world/rss.xml
  npr:    https://feeds.npr.org/1004/rss.xml

Usage:
  news_rss.py [google|bbc|npr] [out.jsonl]
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

FEEDS = {
    "google": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en",
    "bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "npr": "https://feeds.npr.org/1004/rss.xml",
}

# title/url/pubDate only — drop description/content
DATE_TAGS = ("pubDate", "published", "updated", "date")


def parse_feed(xml_bytes: bytes, src: str):
    root = ET.fromstring(xml_bytes)
    # RSS 2.0 item or Atom entry
    items = []
    for el in root.iter():
        tag = el.tag.split("}")[-1].lower()
        if tag not in ("item", "entry"):
            continue
        title = link = date = ""
        for c in el:
            t = c.tag.split("}")[-1].lower()
            if t == "title" and not title:
                title = (c.text or "").strip()
            elif t == "link":
                href = c.attrib.get("href") or (c.text or "")
                if href and not link:
                    link = href.strip()
            elif t in ("pubdate", "published", "updated", "date") and not date:
                date = (c.text or "").strip()
        if title and link:
            items.append({"title": title[:300], "url": link, "date": date, "src": src})
    return items


def to_event(item, stream_id: str) -> dict:
    # ISO-ish ts if possible
    raw = item.get("date") or ""
    ts = raw
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(raw)
        ts = dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    nat = item["url"]
    return {
        "nat_key": nat,
        "ts_utc": ts,
        "value": None,
        "unit": "headline",
        "title": item["title"],
        "url": item["url"],
        "place": item.get("src"),
        "stream_id": stream_id,
    }


def main() -> int:
    feed = sys.argv[1] if len(sys.argv) > 1 else "google"
    if feed not in FEEDS:
        print(f"usage: news_rss.py {{{'|'.join(FEEDS)}}} [out.jsonl]", file=sys.stderr)
        return 2
    out = Path(sys.argv[2] if len(sys.argv) > 2 else f"news.{feed}.jsonl")
    req = urllib.request.Request(FEEDS[feed], headers={"User-Agent": "tsx-news/0.1 (metadata-only)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    items = parse_feed(body, feed)
    n = 0
    with out.open("a", encoding="utf-8") as fh:
        for it in items:
            ev = to_event(it, f"news.{feed}")
            fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
            n += 1
    print(json.dumps({"feed": feed, "headlines": n, "file": str(out), "policy": "title+url+date only"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
