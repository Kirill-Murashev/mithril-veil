# Architecture

Mithril Veil is a local-first service that detects Russian PII in text and returns anonymized output suitable for LLM workflows.

## Layers

| Layer | Location | Role |
|-------|----------|------|
| **API** | `app/api/` | FastAPI HTTP endpoints |
| **CLI** | `app/cli/` | `mithril-veil` commands for text, stdin, and files |
| **Document I/O** | `app/document_io/` | UTF-8 text, DOCX (`python-docx`), text-based PDF (`pypdf`) |
| **Pipeline** | `app/core/pipeline.py` | Shared detection → merge → anonymize flow |
| **Detectors** | `app/detectors/` | Deterministic regex recognizers (no ML in this slice) |
| **Security** | `app/security/` | Retention and audit policy hooks |

## No-storage-by-default

By default the service does not persist original documents or detected values. The CLI writes only explicit `--output` and `--report` paths. Policy defaults forbid logging raw text or entity values.

## Deterministic detection pipeline

```
Input (HTTP body | CLI text | extracted document text)
  → regex detectors (per entity type)
  → checksum / context gates (INN, SNILS)
  → merge_entities (priority, length, confidence)
  → anonymizer (replace | redact)
  → safe response mapping (strip internal text; mask value_preview)
  → summary / optional JSON report with safe source metadata
```

Internal `DetectedEntity.text` is used only in-process. It must not be logged, printed, or written to reports.

## Document ingestion (Slice 4A)

| Format | Reader | Notes |
|--------|--------|-------|
| `.txt`, `.md` | UTF-8 | Direct read |
| `.docx` | `python-docx` | Paragraphs + table cells → plain text |
| `.pdf` | `pypdf` | Text extraction only; no OCR |
| `.rtf` | — | Unsupported |
| Encrypted PDF | — | Rejected |
| Image-only PDF | — | Rejected (no extractable text) |

Limits: `MAX_INPUT_FILE_BYTES` (10 MB), `MAX_PDF_PAGES` (50).

DOCX/PDF input produces **text output** only; layout is not preserved.

## CLI file flow

```
mithril-veil anonymize-file
  → validate paths and output extension
  → check file size
  → read_document_file (format-specific extraction)
  → run_anonymization (same as API)
  → write_text_file (anonymized plain text)
  → optional write_anonymization_report (safe JSON + source metadata)
```

## Deployment

Run the API with Uvicorn behind a reverse proxy, or use the CLI locally/on a VPS. See [deployment_vps.md](deployment_vps.md).
