#!/usr/bin/env python3
"""D5: BBC News RSS — 1-year text-only window.

Fetches BBC News RSS feeds and stages text-only articles.
License: BBC RSS (non-commercial, attribution required).
Source: https://feeds.bbci.co.uk/news/rss.xml

Usage:
  bbc_news.py [--category world|uk|business|tech|science]

Text-only: title, description, pubDate, link. No images/bodies.
Idempotent by RSS guid. 1-year window.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

FEEDS = {
    "world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "uk": "https://feeds.bbci.co.uk/news/uk/rss.xml",
    "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "tech": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "tsx-news/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_rss(xml_text: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        desc = (item.findtext("description") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        pub = (item.findtext("pubDate") or "").strip()
        if not title:
            continue
        items.append({
            "title": title[:200],
            "desc": desc[:500],
            "link": link,
            "guid": guid,
            "pub": pub,
        })
    return items


def main() -> int:
    category = "world"
    if "--category" in sys.argv:
        idx = sys.argv.index("--category")
        if idx + 1 < len(sys.argv):
            category = sys.argv[idx + 1]

    url = FEEDS.get(category)
    if not url:
        print(f"unknown category {category}; use one of {list(FEEDS)}", file=sys.stderr)
        return 2

    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / "news.bbc.jsonl"
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=365)

    xml_text = fetch(url)
    items = parse_rss(xml_text)

    n = 0
    skipped = 0
    with out.open("a", encoding="utf-8") as fh:
        for item in items:
            # 1-year window filter
            try:
                from email.utils import parsedate_to_datetime
                pub_dt = parsedate_to_datetime(item["pub"])
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    skipped += 1
                    continue
                ts = pub_dt.isoformat()
            except (ValueError, TypeError):
                ts = now.isoformat()

            # text-only: strip HTML tags from description
            desc_clean = re.sub(r"<[^>]+>", "", item["desc"])

            ev = {
                "stream_id": "news.bbc",
                "nat_key": item["guid"][:200],
                "ts_utc": ts,
                "value": 1.0,
                "unit": "article",
                "title": item["title"],
                "place": category,
                "url": item["link"],
                "attrib": "BBC News (feeds.bbci.co.uk)",
                "text": desc_clean[:500],
            }
            fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
            n += 1

    print(json.dumps({
        "stream": "news.bbc",
        "category": category,
        "staged": n,
        "skipped": skipped,
        "file": str(out),
        "at": now.isoformat(),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
