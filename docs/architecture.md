# Architecture

Mithril Veil is a local-first service that detects Russian PII in text and returns anonymized output suitable for LLM workflows. Security boundaries and residual risks are documented in [threat_model.md](threat_model.md).

## Layers

| Layer | Location | Role |
|-------|----------|------|
| **API** | `app/api/` | FastAPI HTTP endpoints |
| **CLI** | `app/cli/` | `mithril-veil` commands for text, stdin, files, and batch directories |
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

Deterministic checksum validation (Slice 13): **OGRN** and **OGRNIP** require valid control digits; **BANK_ACCOUNT** and **CORRESPONDENT_ACCOUNT** use Central Bank weighted checksums when a **BIK** appears in the same local text window (~120 characters), otherwise bank accounts still require settlement-account keywords and correspondent accounts remain regex-detected without BIK linkage.

GLiNER loads model weights lazily from Hugging Face on first use unless already cached (local inference afterward; no cloud LLM calls).

Internal `DetectedEntity.text` is used only in-process. It must not be logged, printed, or written to reports.

## Document ingestion (Slice 4A)

| Format | Reader | Notes |
|--------|--------|-------|
| `.txt`, `.md` | UTF-8 | Direct read |
| `.docx` | `python-docx` | Paragraphs + table cells → plain text |
| `.odt` | `zipfile` + stdlib XML | `content.xml` only; ZipInfo size/ratio checks (8 MB cap, 100:1 max ratio); paragraphs/headings/tables → plain text; draw/image/object subtrees skipped; errors never echo file content |
| `.pdf` | `pypdf` | Text extraction only; no OCR |
| `.rtf` | `striprtf` | Best-effort plain text; UTF-8 then cp1251/latin-1; `\\bin` hex stripped; no objects/images; errors never echo file content |
| Encrypted PDF | — | Rejected |
| Image-only PDF | — | Rejected (no extractable text) |

Limits: `MAX_INPUT_FILE_BYTES` (10 MB), `MAX_PDF_PAGES` (50), ODT `content.xml` uncompressed cap 8 MB (see `app/document_io/odt.py`).

DOCX/PDF input produces **text output** only; layout is not preserved.

## Reversible pseudonymization (mapping)

Canonical encryption module: **`app/security/encrypted_mapping.py`** (PBKDF2 + Fernet envelope, `.json.enc` only). In-memory mapping lives in **`app/core/mapping.py`**. There is no alternate production write path.

| Surface | Mapping in memory | Mapping on disk | Report |
|---------|-------------------|-----------------|--------|
| API `pseudonymize` | Yes (per request) | No | N/A |
| CLI `replace` / `redact` | No | No | No mapping block |
| CLI `pseudonymize` | Yes | Only with `--mapping-output` (`.json.enc`) | `mapping.written` / `mapping.encrypted` only |

Passphrase for encrypted mapping files comes from an environment variable (default `MITHRIL_VEIL_MAPPING_PASSPHRASE`, override `--mapping-passphrase-env`). Mapping output path must differ from input, anonymized output, and report paths. Original span text never appears in stdout, stderr, API JSON, or report JSON. **`pseudonymize` is reversible** when a mapping file exists; the API does not write or return mappings.

**Restore / de-anonymization:** Not implemented. A security-first design for a possible future CLI-only restore workflow is in [restore_workflow_design.md](restore_workflow_design.md) (Slice 14, design only). No restore command, API endpoint, or batch restore exists in 0.1.x.

No OCR, image-only PDF, or encrypted PDF ingestion.

## CLI batch flow (Slice 10 / 10.1)

```
mithril-veil anonymize-dir INPUT_DIR --output-dir OUTPUT_DIR
  → validate resolved input/output directories (no nesting; no .. bypass)
  → walk without following symlinks; skip symlinked files; skip hidden paths unless --include-hidden
  → collect supported files (.txt, .md, .markdown, .docx, .odt, .pdf, .rtf; case-insensitive extensions)
  → preflight duplicate output targets and output writability
  → skip unsupported extensions with safe warnings
  → per file: read_document_file → run_anonymization (replace/redact only)
  → write OUTPUT_DIR/<stem>.anonymized.txt (colliding stems such as a.txt + a.md are rejected)
  → optional aggregate batch JSON report (deterministic ordering; safe counts/statuses only)
```

Batch mode does **not** support `pseudonymize` or encrypted mapping output (by design). Exit code `0` when no failures; `1` if any file failed; `2` for unsafe directory/report/output conflicts. Per-file failures after preflight may leave earlier outputs on disk; collision and preflight errors write nothing.

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
