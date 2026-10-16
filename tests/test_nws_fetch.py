#!/usr/bin/env python3
"""tsx#18 offline: retry decision + backoff schedule."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "acquire"))
from nws_fetch import BACKOFF_S, should_retry  # noqa: E402


def main() -> int:
    assert should_retry(429)
    assert should_retry(503)
    assert not should_retry(400)
    assert not should_retry(200)
    assert len(BACKOFF_S) == 3 and BACKOFF_S[0] > 0
    print("TEST nws_fetch OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
