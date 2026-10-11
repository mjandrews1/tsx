#!/usr/bin/env python3
"""Headline-only news acquire — BBC + NPR only.

IP policy (private research streams):
  Store **title + date + URL + source** only. Never body/description/media.
  AP and Google News removed (2026-10-12) per IP/license policy.

Timestamps (all UTC ISO-8601):
  ts_utc           — event/pub date from the feed (when known)
  ts_reported_utc  — same as pub date when feed has no separate event time
  ts_ingested_utc  — when we wrote the row
"""
from __future__ import annotations

import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEEDS = {
    "bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "npr": "https://feeds.npr.org/1004/rss.xml",
}
ALLOWED = set(FEEDS)  # no ap, no google


def parse_feed(xml_bytes: bytes, src: str):
    root = ET.fromstring(xml_bytes)
    items = []
    for el in root.iter():
        if el.tag.split("}")[-1].lower() not in ("item", "entry"):
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


def iso_from(raw: str) -> str:
    if not raw:
        return ""
    try:
        dt = parsedate_to_datetime(raw)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return raw


def main() -> int:
    feed = sys.argv[1] if len(sys.argv) > 1 else "bbc"
    if feed not in ALLOWED:
        print(f"allowed feeds: {sorted(ALLOWED)}", file=sys.stderr)
        return 2
    out = Path(sys.argv[2] if len(sys.argv) > 2 else f"news.{feed}.jsonl")
    req = urllib.request.Request(FEEDS[feed], headers={"User-Agent": "tsx-news/0.2 (title+link+date)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    now = datetime.now(timezone.utc).isoformat()
    n = 0
    with out.open("a", encoding="utf-8") as fh:
        for it in parse_feed(body, feed):
            ts = iso_from(it["date"])
            ev = {
                "stream_id": f"news.{feed}",
                "nat_key": it["url"],
                "ts_utc": ts or now,
                "ts_event_utc": ts,          # feed pub date (event/report)
                "ts_reported_utc": ts,
                "ts_ingested_utc": now,
                "value": None,
                "unit": "headline",
                "title": it["title"],
                "url": it["url"],
                "place": it.get("src"),
            }
            fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
            n += 1
    print(json.dumps({"feed": feed, "headlines": n, "file": str(out), "policy": "title+url+date only"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
