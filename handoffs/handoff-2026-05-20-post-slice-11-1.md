# Handoff — Mithril Veil — Post Slice 11.1 — 2026-05-20

> **Supersedes for future context:** [handoff-2026-05-20.md](handoff-2026-05-20.md) (archive, ends at `7d58a65`) and [handoff-2026-05-20-post-slice-8-1.md](handoff-2026-05-20-post-slice-8-1.md) (ends at `56b7538`). Those files are **not deleted**; use **this document** as the current baseline.

---

## 1. Project identity

| Field | Value |
|-------|-------|
| **Project** | Mithril Veil |
| **Repository** | https://github.com/Kirill-Murashev/mithril-veil |
| **License** | Apache License 2.0 |
| **Version** | 0.1.0 |
| **Branch** | `main` |

**What it is:** An open-source, self-hosted **Russian PII anonymization/sanitization** service for safer LLM workflows. **Local-first** preprocessing: detect and anonymize sensitive data in Russian **text and documents** before content is sent to cloud LLMs.

**Tagline:** *Mithril Veil: a self-hosted Russian PII anonymization gateway for safer AI workflows.*

**Primary language/domain focus:** Russian-language texts and documents (identifiers, legal/banking patterns, Cyrillic NER).

**Target users:** Lawyers, appraisers, consultants, accountants, forensic experts, and small companies that need auditable, self-hosted sanitization instead of sending raw client material to third-party APIs.

---

## 2. Current confirmed baseline

Verified at handoff time (local `main`, synced with `origin/main`):

| Item | Status |
|------|--------|
| **HEAD / origin/main** | `a99f62a` — Harden RTF text ingestion |
| **Version** | `0.1.0` (`app/__init__.py`, `pyproject.toml`) |
| **Tests** | **218 passed**, 1 deselected (`pytest -m 'not integration'`) |
| **ruff check** | Passed |
| **ruff format --check** | Passed |
| **python -m compileall app** | Passed |
| **pytest** | Passed |
| **make check** | Passed |
| **python -m build** | Passed (at last code slice) |
| **Working tree** | Clean |

**Recent commit chain:**

```text
a99f62a Harden RTF text ingestion
f49c05a Add safe RTF text ingestion
395f540 Harden CLI batch directory processing
dcbf0cc Add CLI batch directory anonymization
19be3dd Add handoff for 2026-05-20
56b7538 Add threat model documentation
e973d5a Add post-slice 8.1 project handoff
5a5b1fd Harden encrypted pseudonymization mapping
```

---

## 3. Implemented slices (chronological)

| Slice | Commit (representative) | Summary |
|-------|-------------------------|---------|
| **1 — Scaffold** | `6371e66` | FastAPI app, `/health`, `/api/v1/anonymize`, regex detection, `replace`/`redact`, Apache 2.0 |
| **2 — Deterministic core** | `b69865c` | `DetectedEntity`, span merger, INN/SNILS checksums, expanded regex types, detection summary, safe API metadata |
| **3 — CLI + text I/O** | `3ed5a3d` | `mithril-veil` CLI, `.txt`/`.md`, safe JSON reports, overwrite guards |
| **4A — DOCX/PDF** | `6fcf84a` | `python-docx`, `pypdf`, 10 MB / 50-page limits, no OCR |
| **4B — Natasha NER** | `479a54b` | Optional `PER`/`ORG`/`LOC` → PERSON/ORGANIZATION/LOCATION |
| **5 — GLiNER** | `36b08f7` | Optional zero-shot detector, `[gliner]` extra, integration tests deselected in default CI |
| **6 — Presets** | `37fa090` | Five YAML presets, entity filtering, `GET /api/v1/presets`, `list-presets` |
| **7 — CI / release** | `7d58a65` | GitHub Actions, Makefile, CHANGELOG, release/security checklists |
| **8 — Reversible mapping** | `c70d23a`, `9e4e38b` | `pseudonymize` mode, encrypted CLI mapping (`.json.enc`), `cryptography` dependency |
| **8.1 — Mapping hardening** | `5a5b1fd` | Removed unused `app/security/mapping_io.py`, path-distinct checks, security regression tests |
| **8.1 handoff** | `e973d5a` | Post–Slice 8.1 project handoff document |
| **9 — Threat model** | `56b7538` | `docs/threat_model.md`, security checklist updates |
| **Superseded handoff archive** | `19be3dd` | Committed `handoff-2026-05-20.md` as historical archive |
| **10 — Batch directory** | `dcbf0cc` | `anonymize-dir`, aggregate safe batch report, replace/redact only |
| **10.1 — Batch hardening** | `395f540` | Symlinks, hidden paths, collisions, report safety, deterministic reports, exit codes |
| **11 — RTF ingestion** | `f49c05a` | `.rtf` via `striprtf`, single-file and batch support |
| **11.1 — RTF hardening** | `a99f62a` | Encoding paths, malformed RTF, binary artifact filter, safe errors |

---

## 4. Current architecture

```text
Input (text / stdin / file / directory)
  → Document I/O layer (format detection, size limits, extraction)
  → Detection configuration / preset resolution
  → Detectors:
       • deterministic regex/checksum detectors (always)
       • optional Natasha NER
       • optional GLiNER zero-shot detector
  → Priority span merger
  → Preset entity filtering
  → Anonymizer (replace | redact | pseudonymize)
  → Safe output / safe API response / safe JSON report
  → optional CLI-only encrypted mapping file (pseudonymize + --mapping-output only)
  → optional batch aggregate safe report (anonymize-dir)
```

**Batch:** Uses the **same pipeline per file**. Supports **`replace` and `redact` only**. Rejects `pseudonymize` and `--mapping-output`. The **API does not write or return mappings**.

**Key modules:**

| Area | Path |
|------|------|
| API routes | `app/api/` |
| CLI | `app/cli/main.py`, `app/cli/batch_cmd.py` |
| Pipeline | `app/core/pipeline.py` |
| Anonymizer | `app/core/anonymizer.py` |
| Batch report | `app/core/batch_report.py` |
| Mapping (in-memory) | `app/core/mapping.py`, `app/core/placeholders.py` |
| Encryption (on disk) | `app/security/encrypted_mapping.py` |
| Presets | `app/presets/*.yml`, `app/core/presets.py` |
| Document I/O | `app/document_io/` (txt, md, docx, pdf, rtf, batch) |
| Detectors | `app/detectors/` |

---

## 5. Public interfaces

### FastAPI

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Service health + version |
| GET | `/api/v1/presets` | List policy presets (safe metadata) |
| POST | `/api/v1/anonymize` | Anonymize text (`replace`, `redact`, `pseudonymize`) |

**Note:** There is **no file-upload API endpoint**. Document ingestion is **CLI-only** (and batch directory).

**Anonymize request highlights:** `text`, `mode`, optional `preset`, `use_ner`, `use_gliner`, GLiNER tuning fields. Response: anonymized `text`, masked `entities`, `summary`, `warnings` — **never** raw detected values or mapping payloads.

### CLI (`mithril-veil`)

| Command | Purpose |
|---------|---------|
| `version` | Print package version |
| `list-presets` | List preset ids and names |
| `anonymize-text` | Inline `--text` |
| `anonymize-stdin` | Read from stdin |
| `anonymize-file` | File in → sanitized text out + optional `--report` |
| `anonymize-dir` | Recursive batch directory → `*.anonymized.txt` + optional aggregate `--report` |

**Common flags:** `--mode`, `--preset`, `--use-ner` / `--no-use-ner`, `--use-gliner` / `--no-use-gliner`, GLiNER flags, `--mapping-output`, `--mapping-passphrase-env`, `--force`.

**Batch-only flags:** `--output-dir`, `--include-hidden`, `--fail-fast`, `--max-files`.

---

## 6. Supported inputs and outputs

### Supported input

- Direct text (`anonymize-text`)
- Stdin (`anonymize-stdin`)
- Files: `.txt`, `.md`, `.markdown`, `.docx`, `.rtf`, text-based `.pdf`
- Batch directory: same extensions (case-insensitive), recursive by default

### RTF specifics (Slice 11 / 11.1)

| Topic | Behavior |
|-------|----------|
| Extraction | Plain text only via **`striprtf`** (`striprtf>=0.0.26`, normal dependency) |
| Encoding | UTF-8 (with BOM) first; **cp1251** if `\ansicpg1251` and bytes are not valid UTF-8; else **latin-1** byte-preserving fallback |
| Malformed RTF | **Best-effort** extraction when striprtf recovers text |
| Unrecoverable parse | Safe **`MithrilVeilError`** — message must **not** include raw document content |
| Empty / format-only | **`EmptyExtractedText`** (consistent with empty DOCX) |
| Embedded content | **No** image/object extraction; `\pict`/`\object`/`\bin` groups not emitted as payloads |
| Post-filter | Control characters removed; long hex runs from `\bin` artifacts stripped |
| Output | Always sanitized **plain text** (`.anonymized.txt` in batch) |

### Unsupported

- OCR
- Image-only PDF
- Encrypted PDF
- **ODT** (not implemented; **recommended next** — see §14)
- Format-preserving DOCX/PDF/RTF output
- Embedded RTF object/image extraction as product feature
- Batch `pseudonymize` / batch mapping
- Web UI
- De-anonymization / restore workflow (no CLI/API)
- Server-side mapping persistence (API cannot write mapping files)

### Output

- Sanitized plain text (stdout or `--output`: `.txt`, `.md`, `.markdown`)
- Safe JSON reports (`--report`): entities, summary, policy, optional `source`, optional `mapping.written` / `mapping.encrypted` only
- Optional **CLI-only** encrypted mapping file for `pseudonymize` + `--mapping-output` (`.json.enc`) in single text/file flows
- Batch: mirrored `*.anonymized.txt` under `--output-dir`
- Batch: optional aggregate safe JSON report (`report_type: batch`)

**Limits:** `MAX_INPUT_FILE_BYTES` (10 MB); `MAX_PDF_PAGES` (50).

---

## 7. Entity types

### Deterministic (regex/checksum)

`EMAIL`, `PHONE`, `INN`, `SNILS`, `PASSPORT_RU`, `OGRN`, `OGRNIP`, `KPP`, `BIK`, `BANK_ACCOUNT`, `CORRESPONDENT_ACCOUNT`, `CARD_NUMBER`, `CADASTRAL_NUMBER`, `COURT_CASE_NUMBER`, `CONTRACT_NUMBER`, `IP_ADDRESS`, `URL`, `TELEGRAM_HANDLE`.

Structured identifiers keep priority over probabilistic detectors in the span merger.

### Optional NER-derived

`PERSON`, `ORGANIZATION`, `LOCATION` (Natasha and/or GLiNER when enabled).

---

## 8. Policy presets

Bundled presets (`app/presets/`):

| Id | Typical use |
|----|-------------|
| `general_ru` | General Russian text |
| `legal_ru` | Legal workflows (NER often on by default) |
| `valuation_ru` | Valuation reports |
| `banking_ru` | Banking identifiers |
| `court_case_ru` | Court case numbers and related types |

**Behavior:**

- YAML loader + validation in `app/core/presets.py`
- Filtering runs **after** merge, **before** anonymization
- Explicit CLI/API flags override preset defaults
- **GLiNER remains disabled** in all bundled presets unless the user explicitly enables it

---

## 9. Pseudonymization and encrypted mapping

### Modes

| Mode | Output text | Reversible mapping |
|------|-------------|-------------------|
| `replace` | Typed placeholders `[TYPE_N]` | No |
| `redact` | `[REDACTED]` | No |
| `pseudonymize` | Same placeholders as `replace` | In-memory during run; optional encrypted file on CLI |

### Mapping lifecycle

1. **In-memory:** `PseudonymizationSession` / `ReversibleMapping` in `app/core/mapping.py` — placeholder → original span text **only inside the process**.
2. **On disk (CLI only):** Written **only** if the user passes `--mapping-output path.json.enc`.
3. **Encryption:** `app/security/encrypted_mapping.py` — PBKDF2-HMAC-SHA256 + Fernet; envelope `mithril-veil-mapping-v1`.
4. **Passphrase:** `MITHRIL_VEIL_MAPPING_PASSPHRASE` (default), overridable via `--mapping-passphrase-env`.
5. **Overwrite:** Refused unless `--force`.
6. **Path rules:** `.json.enc` suffix required; mapping path must differ from `--input`, `--output`, and `--report` when applicable.

### Safe report metadata (only when mapping file was written)

```json
{
  "mapping": {
    "written": true,
    "encrypted": true
  }
}
```

No placeholder→original entries in reports, API JSON, stdout, stderr, or error messages.

### API boundary

- `POST /api/v1/anonymize` with `mode=pseudonymize` returns pseudonymized text and masked entities only.
- No mapping fields in API responses.
- API **cannot** write mapping files.

### Batch boundary

- `anonymize-dir` **rejects** `pseudonymize` and `--mapping-output`.
- No batch mapping support by design.

### Canonical code paths

| Role | Module |
|------|--------|
| In-memory mapping | `app/core/mapping.py`, `app/core/placeholders.py` |
| Encrypted file I/O | `app/security/encrypted_mapping.py` |

**Removed in Slice 8.1:** `app/security/mapping_io.py` — unused competing abstraction; not part of the production path.

**Runtime dependency:** `cryptography>=43.0.0` (normal dependency).

---

## 10. Batch model (`anonymize-dir`)

**Command:**

```bash
mithril-veil anonymize-dir INPUT_DIR --output-dir OUTPUT_DIR
```

| Topic | Behavior |
|-------|----------|
| Traversal | Recursive; **does not follow** symlinked directories |
| Extensions | Case-insensitive: `.txt`, `.md`, `.markdown`, `.docx`, `.pdf`, `.rtf` |
| Output naming | Source stem + `.anonymized.txt`; relative path tree preserved |
| Hidden paths | Skipped unless `--include-hidden` (any path segment starting with `.`) |
| Symlinks | Symlinked **files** skipped (`skipped_symlink`); symlinked **dirs** not descended |
| Collisions | Duplicate output targets (e.g. `a.txt` + `a.md` → `a.anonymized.txt`) **preflight-rejected** — no writes |
| Directory safety | `input_dir == output_dir` rejected; `output_dir` inside `input_dir` rejected (resolved paths) |
| Report safety | Report must not be inside input dir or equal a planned output path; overwrite requires `--force` |
| Modes | `replace` / `redact` only |
| Exit codes | `0` no failures; `1` one or more files failed; `2` unsafe path/report/preflight conflicts |
| Partial writes | Preflight/collision errors write **nothing**; per-file failures after preflight may leave earlier outputs on disk |
| Reports | Deterministic ordering; per-status counts; **no raw values** in aggregate report / stdout / stderr / errors |

**Useful flags:** `--report`, `--force`, `--fail-fast`, `--max-files`, `--include-hidden`, `--preset`, NER/GLiNER overrides.

---

## 11. Security model / hard invariants

These rules are **non-negotiable** for all future slices:

| Rule | Detail |
|------|--------|
| No real PII in repo | Tests, fixtures, docs, examples — **synthetic only** |
| No real documents in repo | No client files, contracts, court PDFs, etc. |
| No raw input logging | Do not log submitted text |
| No raw values in API | `value_preview` always `***` |
| No raw values in CLI reports | JSON reports are safe summaries only |
| No raw values in stdout/stderr/errors | Including RTF parser and mapping passphrase errors |
| Mapping files are sensitive | Even when encrypted; treat like key material |
| Never commit mappings | `mapping*.json`, `mapping*.json.enc` gitignored |
| Never commit passphrases | Keep `MITHRIL_VEIL_MAPPING_PASSPHRASE` outside the repo |
| No mapping in issues/logs | Do not attach `.json.enc` files or passphrases to tickets |
| GLiNER optional | Default CI must **not** download model weights |
| Integration tests | `@pytest.mark.integration`; excluded from default `pytest` |
| Batch reports | Aggregate/safe only — no raw text or detected values |
| RTF errors | Must **never** include raw document content |
| New document formats | Plain-text extraction only unless separately designed and threat-modeled |

**Regression coverage:** `tests/test_mapping_hardening.py`, `tests/test_encrypted_mapping.py`, `tests/test_cli_batch.py`, `tests/test_rtf_hardening.py`, `tests/test_batch_io.py`, API/CLI anonymizer tests.

**Threat model:** `docs/threat_model.md` — read before security-sensitive slices.

---

## 12. Threat model / residual risks (summary)

- Sanitized output may still contain **undetected** sensitive data.
- NER is **probabilistic** (miss / over-detect).
- Regex-only mode may miss names, addresses, dates of birth, and free-form facts.
- **Encrypted mapping is reversible by design** — mapping file + passphrase leak enables recovery.
- Pseudonymized text can still leak context or quasi-identifiers.
- Batch aggregate reports reveal **file structure** and **entity counts** (not raw values).
- **RTF extraction is best-effort** — may miss or distort text; malformed RTF may partially extract.
- Self-hosted deployment security depends on host configuration.
- No formal privacy guarantee (k-anonymity, differential privacy, etc.).

Full detail: `docs/threat_model.md`.

---

## 13. Current known limitations

- No OCR
- No image-only or encrypted PDF support
- **No ODT support yet** (recommended next)
- No format-preserving DOCX/PDF/RTF output
- No batch mapping / batch pseudonymize
- No web UI
- No de-anonymization / restore CLI or API
- No server-side mapping persistence
- No formal privacy proof
- Person names often need Natasha/GLiNER or a suitable preset; regex-only may miss names
- No dedicated `ADDRESS` or `DATE_OF_BIRTH` regex detectors (backlog)
- OGRN/bank extended checksum validation still backlog
- Bundled presets only (no user-supplied custom preset paths)
- First GLiNER use may download Hugging Face weights (manual `[gliner]` workflow; not default CI)

---

## 14. Recommended next slices (ranked)

Small, reviewable slices — **no broad rewrites**. **Do not implement ODT in this handoff slice.**

### A. Slice 12 — ODT text ingestion (**recommended next**)

**Rationale:** ODT is common in Russian public-sector, municipal, educational, and budgetary organizations (LibreOffice/OpenOffice workflows), and in legal, administrative, expert, and appraisal document flows.

**Scope:**

- Add `.odt` as plain-text extraction input (ZIP + `content.xml`, stdlib XML where feasible).
- No formatting preservation; no macro execution; no LibreOffice/pandoc/external binaries.
- Extract text from common paragraphs/spans/tables; ignore embedded objects/images.
- Apply existing file size limits.
- Single-file (`anonymize-file`) and batch (`anonymize-dir`) support.
- Synthetic fixtures only; no real ODT documents.
- **No API endpoint changes.**
- Batch remains replace/redact only.

### B. Slice 12.1 — ODT hardening

- Malformed ZIP, missing `content.xml`, zip-bomb / compressed-size sanity
- XML parser safety, embedded object ignoring
- Safe errors (no raw leakage), batch consistency

### C. Slice 13 — De-anonymization design document only

- Design restore workflow **without** implementation
- Mapping possession, passphrase handling, accidental re-identification, audit/logging risks
- CLI-only vs API considerations

### D. Slice 14 — Release candidate hygiene for v0.1.0

- README, CLI examples, package metadata
- Release checklist, security checklist, known limitations
- CI confirmation

### E. Optional later (design-only unless user overrides)

- Web UI design only
- Format-preserving output design only
- OCR design only — **strong warning:** OCR is out-of-scope for current security model

**Architectural note:** Do **not** implement restore/de-anonymize, web UI, or OCR without explicit user approval and updated threat model.

---

## 15. Development commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# Optional GLiNER: pip install -e ".[dev,gliner]"

make check          # lint + format check + compileall + pytest
make run-api        # uvicorn app.main:app --reload
python -m build     # sdist + wheel

mithril-veil version
mithril-veil list-presets
mithril-veil anonymize-text --text "Контакт: test@example.local" --mode replace
```

**Batch (replace/redact only):**

```bash
mithril-veil anonymize-dir ./documents --output-dir ./sanitized \
  --mode replace --report ./batch-report.json
```

**Pseudonymize + mapping (CLI single-file only):**

```bash
export MITHRIL_VEIL_MAPPING_PASSPHRASE="your-local-secret"
mithril-veil anonymize-file \
  --input in.txt --output out.txt \
  --mode pseudonymize \
  --mapping-output mapping.json.enc \
  --report report.json
```

---

## 16. New-chat prompt (copy-paste for ChatGPT / architect)

```text
You are the architect and technical lead for Mithril Veil (open-source, self-hosted Russian PII anonymization).

Repository: https://github.com/Kirill-Murashev/mithril-veil

Before any implementation:
1. Read the latest handoff: handoffs/handoff-2026-05-20-post-slice-11-1.md
2. Verify GitHub main when current status matters (expected HEAD: a99f62a or later)
3. Confirm hard security invariants (no real PII, no raw values in API/reports/logs, mapping CLI-only and encrypted, batch replace/redact only)

Current baseline: version 0.1.0; 218 tests (1 deselected); supported inputs include .txt/.md/.docx/.rtf/.pdf and batch anonymize-dir; RTF via striprtf with Slice 11.1 hardening; canonical mapping in app/core/mapping.py + app/security/encrypted_mapping.py; threat model in docs/threat_model.md.

Recommended next slice: Slice 12 — ODT text ingestion (plain-text extraction, synthetic fixtures only). NOT web UI, NOT de-anonymization implementation, NOT OCR.

Your task: write the next Cursor Composer prompt for exactly ONE small slice. Keep privacy/security-first constraints. Do not request broad architecture rewrites. Include quality gates, synthetic-data-only rules, and a final report template.
```

---

## 17. Handoff file lineage

| File | Status |
|------|--------|
| `handoffs/handoff-2026-05-20.md` | **Superseded archive** — ends at `7d58a65` |
| `handoffs/handoff-2026-05-20-post-slice-8-1.md` | **Superseded** — ends at `56b7538` |
| `handoffs/handoff-2026-05-20-post-slice-11-1.md` | **Current** — this document |

---

## 18. When to create the next handoff

Create a new handoff after:

- Slice 12+ product slice ships or threat model changes materially;
- Web UI, OCR, or de-anonymization implementation begins;
- Security model or mapping format changes materially;
- Chat context reaches ~70%.
