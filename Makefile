# tsx — tests + ops helpers (no deploy)
PY ?= python3

test:
	$(PY) tests/test_wx_math.py
	$(PY) tests/test_nws_fetch.py
	$(PY) tests/test_archive_streams.py

health:
	bash tools/wx_health.sh

.PHONY: test health
