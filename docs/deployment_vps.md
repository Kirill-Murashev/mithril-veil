# VPS deployment (minimal)

## Requirements

- Python 3.12+ or Docker
- Reverse proxy (nginx, Caddy) with TLS recommended

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
