# Architecture

Mithril Veil is a local-first service that detects Russian PII in text and returns anonymized output suitable for LLM workflows.

## Layers

| Layer | Location | Role |
|-------|----------|------|
| **API** | `app/api/` | FastAPI HTTP endpoints |
| **CLI** | `app/cli/` | `mithril-veil` commands for text, stdin, and files |
| **Document I/O** | `app/document_io/` | UTF-8 text, DOCX (`python-docx`), text-based PDF (`pypdf`) |
| **Presets** | `app/presets/`, `app/core/presets.py` | YAML policy profiles (entity types, detector defaults) |
| **Pipeline** | `app/core/pipeline.py` | Shared detection → merge → filter → anonymize flow |
| **Detectors** | `app/detectors/` | Regex/checksum, optional Natasha NER, optional GLiNER |
| **Security** | `app/security/` | Retention and audit policy hooks |

## No-storage-by-default

By default the service does not persist original documents or detected values. The CLI writes only explicit `--output` and `--report` paths. Policy defaults forbid logging raw text or entity values.

## Detection pipeline

```
Input (HTTP body | CLI text | extracted document text)
  1. Deterministic regex/checksum recognizers (always)
  2. Optional local Natasha NER when use_ner=true
  3. Optional local GLiNER zero-shot detector when use_gliner=true
  4. merge_entities (priority, length, confidence)
  5. filter by preset enabled_entities (when a preset is selected)
  6. anonymizer (replace | redact | pseudonymize)
  7. safe response mapping (strip internal text; mask value_preview)
  8. summary / optional JSON report with safe source and policy metadata
  9. optional encrypted mapping file (CLI only, explicit path; never in API or report body)
```

## Policy presets

Presets are **policy/profile configuration**, not new detectors. Each YAML file under `app/presets/` defines:

- `enabled_entities` — which entity types may appear in output
- `detectors.natasha` / `detectors.gliner` — default `use_ner` / `use_gliner`
- optional GLiNER label defaults for when GLiNER is enabled explicitly

API and CLI accept `preset` plus optional overrides. Explicit `use_ner`, `use_gliner`, and GLiNER parameters win over preset defaults. With no preset, behavior matches earlier releases (`use_ner=false`, `use_gliner=false`, no entity filtering).

Natasha and GLiNER are **disabled by default** (and in all bundled presets unless overridden). Structured identifiers (INN, SNILS, passport, bank account, cadastral, court case, etc.) keep higher merge priority than NER/GLiNER spans.

GLiNER loads model weights lazily from Hugging Face on first use unless already cached (local inference afterward; no cloud LLM calls).

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

## Reversible pseudonymization (mapping)

| Surface | Mapping in memory | Mapping on disk | Report |
|---------|-------------------|-----------------|--------|
| API `pseudonymize` | Yes (per request) | No | N/A |
| CLI `replace` / `redact` | No | No | No mapping block |
| CLI `pseudonymize` | Yes | Only with `--mapping-output` (`.json.enc`) | `mapping.written` / `mapping.encrypted` only |

Passphrase for encrypted mapping files comes from an environment variable (default `MITHRIL_VEIL_MAPPING_PASSPHRASE`). Original span text never appears in stdout, stderr, API JSON, or report JSON.

## CLI file flow

```
mithril-veil anonymize-file
  → validate paths and output extension
  → check file size
  → read_document_file (format-specific extraction)
  → run_anonymization (same as API; pseudonymize keeps session mapping in memory)
  → write_text_file (anonymized plain text)
  → optional write_encrypted_mapping_file (--mapping-output, pseudonymize only)
  → optional write_anonymization_report (safe JSON + source + mapping flags)
```

## Deployment

Run the API with Uvicorn behind a reverse proxy, or use the CLI locally/on a VPS. See [deployment_vps.md](deployment_vps.md).
