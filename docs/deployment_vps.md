# VPS deployment (minimal)

## Requirements

- Python 3.12+ or Docker
- Reverse proxy (nginx, Caddy) with TLS recommended

## Local verification before deploy

From a development checkout, run `make check` after `pip install -e ".[dev]"` to match CI (ruff, format check, compileall, pytest).

## Docker

```bash
docker compose up -d --build
curl http://127.0.0.1:8000/health
```

## Systemd + venv (outline)

1. Clone repo to `/opt/mithril-veil`
2. `python3 -m venv .venv && .venv/bin/pip install .`
3. Run `uvicorn app.main:app --host 127.0.0.1 --port 8000` behind nginx

Do not expose the service to the public internet without authentication in production.

## CLI on a VPS

After `pip install .` in the project venv:

```bash
mithril-veil anonymize-file --input ./examples/synthetic_input.txt --output /tmp/out.txt --mode replace

# DOCX/PDF input → text output (text-based PDF only; no OCR)
mithril-veil anonymize-file --input ./document.docx --output /tmp/out.txt --mode replace
```

Process files only on the server you control. Do not upload real private documents to shared CI or public issue trackers.
