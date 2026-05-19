# Architecture

Mithril Veil is a local-first HTTP service that detects Russian PII in text and returns anonymized output suitable for LLM workflows.

## Components

- **API** (`app/api/`): FastAPI routes for health and anonymization
- **Pipeline** (`app/core/pipeline.py`): Orchestrates detection, span merging, and replacement
- **Detectors** (`app/detectors/`): Pluggable detectors (MVP: regex)
- **Presets** (`app/presets/`): YAML entity-type profiles (not yet wired)
- **Security** (`app/security/`): Retention and audit policy hooks

## Request flow

```
POST /api/v1/anonymize
  → detectors (regex)
  → span merger (overlap resolution)
  → anonymizer (replace | redact)
  → JSON response (no original values)
```

## Deployment

Run with Uvicorn behind your reverse proxy on a VPS or locally. See [deployment_vps.md](deployment_vps.md).
