"""Shared NWS (api.weather.gov) HTTP helper (tsx#18).

Retry/backoff for 429/5xx; single User-Agent + timeout.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

UA = "tsx-geodata/0.1 (+tsx research; contact: mark@local)"
TIMEOUT = 60
MAX_TRIES = 3
BACKOFF_S = (1.0, 3.0, 8.0)


def should_retry(code: int) -> bool:
    return code == 429 or code >= 500


def fetch_json(url: str, tries: int = MAX_TRIES, sleep=time.sleep) -> dict:
    last = None
    for i in range(tries):
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "application/geo+json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            last = e
            if i + 1 < tries and should_retry(e.code):
                sleep(BACKOFF_S[min(i, len(BACKOFF_S) - 1)])
                continue
            raise
        except Exception as e:
            last = e
            if i + 1 < tries:
                sleep(BACKOFF_S[min(i, len(BACKOFF_S) - 1)])
                continue
            raise
    raise last if last else RuntimeError("nws_fetch failed")
