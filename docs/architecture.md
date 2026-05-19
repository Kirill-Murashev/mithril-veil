# Architecture

Mithril Veil is a local-first service that detects Russian PII in text and returns anonymized output suitable for LLM workflows.

## Layers

| Layer | Location | Role |
|-------|----------|------|
| **API** | `app/api/` | FastAPI HTTP endpoints |
| **CLI** | `app/cli/` | `mithril-veil` commands for text, stdin, and files |
| **Document I/O** | `app/document_io/` | Safe UTF-8 read/write for `.txt` / `.md` (stubs for DOCX/PDF) |
| **Pipeline** | `app/core/pipeline.py` | Shared detection → merge → anonymize flow |
| **Detectors** | `app/detectors/` | Deterministic regex recognizers (no ML in this slice) |
| **Security** | `app/security/` | Retention and audit policy hooks |

## No-storage-by-default

By default the service does not persist original documents or detected values. The CLI writes only what you explicitly request (`--output`, `--report`). Policy defaults in `app/core/policies.py` forbid logging raw text or entity values.

## Deterministic detection pipeline

```
Input (HTTP body | CLI text | file contents)
  → regex detectors (per entity type)
  → checksum / context gates (INN, SNILS)
  → merge_entities (priority, length, confidence)
  → anonymizer (replace | redact)
  → safe response mapping (strip internal text; mask value_preview)
  → summary / optional JSON report
```

Internal `DetectedEntity.text` is used only in-process. It must not be logged, printed, or written to API/CLI reports.

## CLI file flow

```
mithril-veil anonymize-file
  → validate paths (no input overwrite; --force for existing outputs)
  → read_text_file (.txt | .md | .markdown)
  → run_anonymization (same as API)
  → write_text_file (anonymized output)
  → optional write_anonymization_report (safe JSON)
```

## Deployment

Run the API with Uvicorn behind a reverse proxy, or use the CLI locally/on a VPS. See [deployment_vps.md](deployment_vps.md).
