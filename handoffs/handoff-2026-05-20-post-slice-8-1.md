# Handoff — Mithril Veil — Post Slice 8 / 8.1 — 2026-05-20

## 1. Project identity

| Field | Value |
|-------|-------|
| **Project** | Mithril Veil |
| **Repository** | https://github.com/Kirill-Murashev/mithril-veil |
| **License** | Apache License 2.0 |
| **Version** | 0.1.0 |
| **Branch** | `main` |
| **Latest confirmed commit** | `56b7538` — Add threat model documentation |

**What it is:** An open-source, self-hosted Russian PII anonymization/sanitization service for safer LLM workflows. Local-first preprocessing: detect and anonymize sensitive data in Russian text and documents **before** content is sent to cloud LLMs.

**Tagline:** *Mithril Veil: a self-hosted Russian PII anonymization gateway for safer AI workflows.*

**Target users:** Lawyers, appraisers, consultants, accountants, forensic experts, and small companies that need auditable, self-hosted sanitization instead of sending raw client material to third-party APIs.

---

## 2. Current confirmed baseline

Verified at handoff time (local `main`, synced with `origin/main`):

| Item | Status |
|------|--------|
| **HEAD / origin/main** | `56b75386619c2beb23513be41160f5fc77c7d8c5` |
| **Version** | `0.1.0` (`app/__init__.py`, `pyproject.toml`) |
| **Tests** | **158 passed**, 1 deselected (`pytest -m 'not integration'`) |
| **ruff check** | Passed |
| **ruff format --check** | Passed |
| **compileall** | Passed |
| **make check** | Passed |
| **Working tree** | Clean except optional untracked drafts under `handoffs/` |

**Recent commit chain:**

```text
56b7538 Add threat model documentation
e973d5a Add post-slice 8.1 project handoff
5a5b1fd Harden encrypted pseudonymization mapping
9e4e38b Add encrypted reversible pseudonymization mapping
c70d23a Add pseudonymize mode and encrypted local mapping
7d58a65 Add CI and release hygiene
```

---

## 3. Implemented slices (history)

| Slice | Commit (representative) | Summary |
|-------|-------------------------|---------|
| **1 — Scaffold** | `6371e66` | FastAPI app, `/health`, `/api/v1/anonymize`, regex detection, `replace`/`redact`, Apache 2.0, Docker skeleton |
| **2 — Deterministic core** | `b69865c` | `DetectedEntity`, span merger, INN/SNILS checksums, expanded regex types, detection summary, safe API metadata |
| **3 — CLI + text I/O** | `3ed5a3d` | `mithril-veil` CLI, `.txt`/`.md`, safe JSON reports, overwrite guards |
| **4A — DOCX/PDF** | `6fcf84a` | `python-docx`, `pypdf`, 10 MB / 50-page limits, no OCR |
| **4B — Natasha NER** | `479a54b` | Optional `PER`/`ORG`/`LOC` → PERSON/ORGANIZATION/LOCATION |
| **5 — GLiNER** | `36b08f7` | Optional zero-shot detector, `[gliner]` extra, integration tests deselected in default CI |
| **6 — Presets** | `37fa090` | Five YAML presets, entity filtering, `GET /api/v1/presets`, `list-presets` |
| **7 — CI / release** | `7d58a65` | GitHub Actions, Makefile, CHANGELOG, release/security checklists |
| **8 — Reversible mapping** | `c70d23a`, `9e4e38b` | `pseudonymize` mode, encrypted CLI mapping (`.json.enc`), `cryptography` dependency |
| **8.1 — Hardening** | `5a5b1fd` | Removed unused `mapping_io.py`, path-distinct checks, security regression tests |
| **9 — Threat model docs** | `56b7538` | `docs/threat_model.md`, security checklist, doc cross-links (no code changes) |

---

## 4. Current architecture

```text
Input (text / stdin / file)
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
```

**Key modules:**

| Area | Path |
|------|------|
| API routes | `app/api/` |
| CLI | `app/cli/main.py` |
| Pipeline | `app/core/pipeline.py` |
| Anonymizer | `app/core/anonymizer.py` |
| Mapping (in-memory) | `app/core/mapping.py`, `app/core/placeholders.py` |
| Encryption (on disk) | `app/security/encrypted_mapping.py` |
| Presets | `app/presets/*.yml`, `app/core/presets.py` |
| Document I/O | `app/document_io/` |
| Detectors | `app/detectors/` |

---

## 5. Public interfaces

### FastAPI

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Service health + version |
| GET | `/api/v1/presets` | List policy presets (safe metadata) |
| POST | `/api/v1/anonymize` | Anonymize text (`replace`, `redact`, `pseudonymize`) |

**Anonymize request highlights:** `text`, `mode`, optional `preset`, `use_ner`, `use_gliner`, GLiNER tuning fields. Response: anonymized `text`, masked `entities`, `summary`, `warnings` — **never** raw detected values or mapping payloads.

### CLI (`mithril-veil`)

| Command | Purpose |
|---------|---------|
| `version` | Print package version |
| `list-presets` | List preset ids and names |
| `anonymize-text` | Inline `--text` |
| `anonymize-stdin` | Read from stdin |
| `anonymize-file` | File in → text out + optional `--report` |

**Common flags:** `--mode`, `--preset`, `--use-ner` / `--no-use-ner`, `--use-gliner` / `--no-use-gliner`, GLiNER flags, `--mapping-output`, `--mapping-passphrase-env`, `--force` (file command also uses `--input`, `--output`, `--report`).

---

## 6. Supported inputs and outputs

### Supported input

- Direct text (`anonymize-text`)
- Stdin (`anonymize-stdin`)
- Files: `.txt`, `.md`, `.markdown`, `.docx`, text-based `.pdf`

### Not supported

- OCR, image-only PDF, encrypted PDF, RTF
- Format-preserving DOCX/PDF output
- Batch directory processing
- Web UI
- De-anonymization / restore workflow (no CLI/API yet)
- Server-side mapping file persistence (API cannot write mapping files)

### Output

- Plain sanitized text (stdout or `--output` file: `.txt`, `.md`, `.markdown` only)
- Safe JSON reports (`--report`): entities, summary, policy, optional `source`, optional `mapping.written` / `mapping.encrypted` flags only
- Optional **CLI-only** encrypted mapping file for `pseudonymize` + `--mapping-output` (`.json.enc`)

**Limits:** 10 MB max input; 50 PDF pages max.

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

1. **In-memory:** `PseudonymizationSession` / `ReversibleMapping` in `app/core/mapping.py` records placeholder → original span text **only inside the process**.
2. **On disk (CLI only):** Written **only** if the user passes `--mapping-output path.json.enc`.
3. **Encryption:** `app/security/encrypted_mapping.py` — PBKDF2-HMAC-SHA256 (600k iterations) + Fernet; envelope `mithril-veil-mapping-v1`.
4. **Passphrase:** Environment variable (default `MITHRIL_VEIL_MAPPING_PASSPHRASE`), overridable via `--mapping-passphrase-env`.
5. **Overwrite:** Refused unless `--force`.
6. **Path rules:** `.json.enc` suffix required; mapping path must differ from `--input`, `--output`, and `--report` when applicable (`ensure_mapping_path_distinct`).

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
- No `mapping`, `mapping_metadata`, `placeholder_to_original`, or `original_to_placeholder` fields.
- API **cannot** write mapping files.

### Canonical code paths (post–Slice 8.1)

| Role | Module |
|------|--------|
| In-memory mapping | `app/core/mapping.py`, `app/core/placeholders.py` |
| Encrypted file I/O | `app/security/encrypted_mapping.py` |

**Removed in 8.1:** `app/security/mapping_io.py` — unused protocol layer that duplicated `write_encrypted_mapping_file` and was not used by the CLI production path. Tests now target `encrypted_mapping.py` and `tests/test_mapping_hardening.py`.

**Runtime dependency:** `cryptography>=43.0.0` (normal dependency, not optional).

---

## 10. Security model / hard invariants

These rules are **non-negotiable** for all future slices:

| Rule | Detail |
|------|--------|
| No real PII in repo | Tests, fixtures, docs, examples — synthetic only |
| No real documents in repo | No client files, contracts, court PDFs, etc. |
| No raw input logging | Do not log submitted text |
| No raw values in API | `value_preview` always `***`; no `text` field on entities |
| No raw values in CLI reports | JSON reports are safe summaries only |
| No raw values in stdout/stderr/errors | Including mapping passphrase errors |
| Mapping files are sensitive | Even when encrypted; treat like key material |
| Never commit mappings | `mapping*.json`, `mapping*.json.enc` gitignored |
| Never commit passphrases | Keep `MITHRIL_VEIL_MAPPING_PASSPHRASE` outside the repo |
| No mapping in issues/logs | Do not attach `.json.enc` files or passphrases to tickets |
| GLiNER optional | Default CI must not download model weights |
| Integration tests | Marked `@pytest.mark.integration`; excluded from default `pytest` |

**Regression coverage:** `tests/test_mapping_hardening.py`, `tests/test_encrypted_mapping.py`, `tests/test_mapping.py`, CLI/API anonymizer tests.

---

## 11. Current known limitations

- No OCR; no image-only or encrypted PDF support
- No RTF ingestion
- No format-preserving DOCX/PDF output
- No batch directory CLI
- No web UI
- No de-anonymization / restore CLI or API (decrypt helper exists for tests/local tooling only)
- API mapping file output intentionally unsupported
- Person names often need Natasha/GLiNER or a suitable preset; regex-only runs may leave names unchanged
- No dedicated `ADDRESS` or `DATE_OF_BIRTH` regex detectors (backlog)
- OGRN/bank extended checksum validation still backlog
- No user-supplied custom preset paths (bundled YAML only)
- `pyproject.toml` version and `app.__version__` updated manually
- First GLiNER use may download Hugging Face weights (manual integration workflow only in CI)

---

## 12. Recommended next slices (ranked)

Small, reviewable slices — **no broad rewrites**.

### A. Slice 9 — Threat model and security regression documentation — **done** (`56b7538`)

### B. Slice 10 — Batch directory processing (CLI) (recommended next)

- Process a directory of supported documents → sanitized text outputs per file
- Safe per-file reports + aggregate safe summary (no raw values in aggregate)
- Mapping excluded by default; only with explicit future design if needed

### C. Slice 11 — RTF ingestion

- Safe RTF text extraction if dependency is acceptable
- Synthetic fixtures only; no formatting preservation

### D. Slice 12 — De-anonymization design document only

- Design restore workflow **without** implementation
- Cover risks: mapping possession, passphrase handling, accidental re-identification, audit logging

**Architectural note:** Do **not** implement restore/de-anonymize or web UI until de-anonymization design (Slice 12) is written and reviewed.

---

## 13. Development commands

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

**Pseudonymize + mapping (CLI only):**

```bash
export MITHRIL_VEIL_MAPPING_PASSPHRASE="your-local-secret"
mithril-veil anonymize-file \
  --input in.txt --output out.txt \
  --mode pseudonymize \
  --mapping-output mapping.json.enc \
  --report report.json
```

---

## 14. New-chat prompt (copy-paste for ChatGPT / architect)

```text
You are the architect and technical lead for Mithril Veil (open-source, self-hosted Russian PII anonymization).

Repository: https://github.com/Kirill-Murashev/mithril-veil

Before any implementation:
1. Read the latest handoff: handoffs/handoff-2026-05-20-post-slice-8-1.md
2. Verify GitHub main if needed (expected HEAD: 56b7538 or later)
3. Confirm hard security invariants (no real PII, no raw values in API/reports/logs, mapping CLI-only and encrypted)

Current baseline: version 0.1.0, modes replace/redact/pseudonymize, 158 tests (1 deselected), canonical mapping in app/core/mapping.py + app/security/encrypted_mapping.py, threat model in docs/threat_model.md.

Recommended next slice: Slice 10 — batch directory CLI (or Slice 12 design-only for de-anonymization).

Your task: write the next Cursor Composer prompt for exactly ONE small slice. Do not request web UI, de-anonymization implementation, or architecture rewrites unless the user explicitly overrides. Include quality gates, synthetic-data-only rules, and a final report template.
```

---

## 15. Handoff file lineage

| File | Status |
|------|--------|
| `handoffs/handoff-2026-05-20.md` | **Superseded archive** — ends at `7d58a65`; kept for history |
| `handoffs/handoff-2026-05-20-post-slice-8-1.md` | **Current** — this document |

---

## 16. When to create the next handoff

Create a new handoff after:

- Slice 10+ product slice ships or threat model changes materially;
- Web UI or OCR work begins;
- De-anonymization is implemented or seriously designed;
- Security model or mapping format changes materially;
- Chat context reaches ~70%.
