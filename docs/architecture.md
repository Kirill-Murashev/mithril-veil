# Architecture

Mithril Veil is a local-first HTTP service that detects Russian PII in text and returns anonymized output suitable for LLM workflows.

## Components

- **API** (`app/api/`): FastAPI routes for health and anonymization
- **Entities** (`app/core/entities.py`): Internal `DetectedEntity` model with priority, confidence, metadata
- **Validators** (`app/detectors/validators.py`): INN/SNILS checksums and digit normalization
- **Pipeline** (`app/core/pipeline.py`): Detection → merge → anonymize → summary
- **Detectors** (`app/detectors/`): Regex recognizers (deterministic, no ML in this layer)
- **Span merger** (`app/core/span_merger.py`): Priority / length / confidence overlap resolution
- **Presets** (`app/presets/`): YAML entity-type profiles (not yet wired)
- **Security** (`app/security/`): Retention and audit policy hooks

## Deterministic detection pipeline

```
POST /api/v1/anonymize
  → regex detectors (per entity type)
  → checksum / context gates (INN, SNILS)
  → merge_entities (priority, length, confidence)
  → anonymizer (replace | redact)
  → API mapping (strip internal text; mask value_preview)
  → detection summary (counts by type and detector)
```

Internal `DetectedEntity.text` is used only inside the process. It must not be logged or returned in JSON responses.

## Deployment

Run with Uvicorn behind your reverse proxy on a VPS or locally. See [deployment_vps.md](deployment_vps.md).
