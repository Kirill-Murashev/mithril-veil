# Handoff — Mithril Veil — Post Slice 13 — 2026-05-20

> **Supersedes for future context:** [handoff-2026-05-20-post-slice-12-1.md](handoff-2026-05-20-post-slice-12-1.md) (ends at `4df897a`), [handoff-2026-05-20-post-slice-11-1.md](handoff-2026-05-20-post-slice-11-1.md) (ends at `a99f62a`), [handoff-2026-05-20.md](handoff-2026-05-20.md) (archive, ends at `7d58a65`), and [handoff-2026-05-20-post-slice-8-1.md](handoff-2026-05-20-post-slice-8-1.md) (ends at `56b7538`). Those files are **not deleted**; use **this document** as the current baseline.

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
| **HEAD / origin/main** | `b3204a3` — Harden deterministic identifier validation |
| **Version** | `0.1.0` (`app/__init__.py`, `pyproject.toml`) |
| **Tests** | **262 passed**, 1 deselected (`pytest -m 'not integration'`) |
| **ruff check** | Passed |
| **ruff format --check** | Passed |
| **python -m compileall app** | Passed |
| **pytest** | Passed |
| **make check** | Passed |
| **python -m build** | Passed (at last code slice `b3204a3`) |
| **Working tree** | Clean |

**Recent commit chain:**

```text
b3204a3 Harden deterministic identifier validation
4df897a Add post-slice 12.1 project handoff
5e83faa Harden ODT text ingestion
1860e9e Add ODT text ingestion
2cf1498 Add post-slice 11.1 project handoff
a99f62a Harden RTF text ingestion
f49c05a Add safe RTF text ingestion
395f540 Harden CLI batch directory processing
dcbf0cc Add CLI batch directory anonymization
56b7538 Add threat model documentation
7d58a65 Add CI and release hygiene
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
| **11.1 handoff** | `2cf1498` | Post–Slice 11.1 project handoff document |
| **12 — ODT ingestion** | `1860e9e` | `.odt` via ZIP + `content.xml`, stdlib XML, single-file and batch |
| **12.1 — ODT hardening** | `5e83faa` | ZipInfo size/ratio checks, XML limits, embedded subtree skip, batch mixed-dir tests |
| **12.1 handoff** | `4df897a` | Post–Slice 12.1 project handoff document |
| **13 — Detector hardening** | `b3204a3` | OGRN/OGRNIP checksums; bank/correspondent account checksums when BIK is nearby |

---

## 4. Implemented capabilities (summary)

| Area | Capability |
|------|------------|
| **Detection** | Deterministic regex/checksum detectors; safe detection summaries; priority span merger |
| **Checksum validation** | INN, SNILS, OGRN, OGRNIP; BANK_ACCOUNT and CORRESPONDENT_ACCOUNT when BIK is nearby (~120 char window) |
| **CLI** | `version`, `list-presets`, `anonymize-text`, `anonymize-stdin`, `anonymize-file`, `anonymize-dir` |
| **API** | `GET /health`, `GET /api/v1/presets`, `POST /api/v1/anonymize` |
| **Inputs** | Direct text, stdin, `.txt`, `.md`, `.markdown`, `.docx`, `.odt`, `.rtf`, text-based `.pdf`; batch directory for supported types |
| **Optional ML** | Natasha NER; GLiNER zero-shot (optional extra, off in default CI) |
| **Presets** | `general_ru`, `legal_ru`, `valuation_ru`, `banking_ru`, `court_case_ru` |
| **Modes** | `replace`, `redact`, `pseudonymize` |
| **Mapping** | Encrypted CLI-only reversible mapping for `pseudonymize` (`.json.enc`) |
| **Batch** | `anonymize-dir` for `replace`/`redact` only; aggregate safe JSON report |
| **Docs** | Threat model, security checklist, architecture, roadmap, PII taxonomy |
| **Document I/O** | RTF ingestion hardened (Slice 11.1); ODT ingestion hardened (Slice 12.1) |

**Validators module:** `app/detectors/validators.py`  
**Regex detectors:** `app/detectors/regex_detectors.py`  
**Regression tests:** `tests/test_validators.py`, `tests/test_regex_detectors.py` (synthetic fixtures in `tests/conftest.py`)

---

## 5. Slice 13 — deterministic detector hardening

Pure functions in `app/detectors/validators.py`, wired in `app/detectors/regex_detectors.py`. No new dependencies; no architecture shift.

### `validate_ogrn(value)`

- **13 digits** after `normalize_digits()` (spaces/hyphens stripped)
- `remainder = int(first_12_digits) % 11`
- **Control digit** = `remainder % 10`
- Compared with **digit 13**
- `OgrnDetector` emits only when validation passes

### `validate_ogrnip(value)`

- **15 digits** after normalization
- `remainder = int(first_14_digits) % 13`
- **Control digit** = `remainder % 10`
- Compared with **digit 15**
- `OgrnipDetector` emits only when validation passes

### `validate_bank_account(account, bik)`

- **20-digit** settlement account + **9-digit** BIK
- BIK must **start with `04`**
- Control string: **BIK branch digits** (positions 7–9, `bik[6:9]`) + **20-digit account** → 23 digits
- **Central Bank weighted mod-10:** weights `(7, 1, 3) * 7 + (7, 1)`; sum of digit×weight must be `≡ 0 (mod 10)`
- Used by `BankAccountDetector` only when `find_nearby_bik()` returns a BIK

### `validate_correspondent_account(account, bik)`

- **20-digit** account must **start with `301`**
- Control string: **`0`** + **BIK department digits** (positions 5–6, `bik[4:6]`) + account → 23 digits
- Same weighted mod-10 rule as settlement accounts
- Used by `CorrespondentAccountDetector` when a nearby BIK is found

### `find_nearby_bik(text, position, window=120)`

- Scans a **local text window** (default ±120 characters) for `\b04\d{7}\b`
- Returns the **closest** BIK match to `position`
- **Not** a full banking-requisites parser — only proximity-based context for checksum validation

### Synthetic test fixtures (`tests/conftest.py`)

| Constant | Role |
|----------|------|
| `SYNTHETIC_OGRN` / `INVALID_OGRN` | Valid / invalid 13-digit OGRN |
| `SYNTHETIC_OGRNIP` / `INVALID_OGRNIP` | Valid / invalid 15-digit OGRNIP |
| `SYNTHETIC_BIK` | `044525225` |
| `SYNTHETIC_BANK_ACCOUNT` / `INVALID_BANK_ACCOUNT` | Valid / invalid settlement account with that BIK |
| `SYNTHETIC_CORRESPONDENT_ACCOUNT` / `INVALID_CORRESPONDENT_ACCOUNT` | Valid / invalid `301…` correspondent account |

All values are **fictional** and checksum-derived for tests only.

---

## 6. Detector behavior after Slice 13

| Entity | Behavior |
|--------|----------|
| **OGRN** | Valid checksum → emitted, `metadata.checksum_valid: true`, confidence ≈ 0.95. Invalid checksum → **not emitted** (no weak-context fallback). |
| **OGRNIP** | Same as OGRN. |
| **BANK_ACCOUNT** | Still requires settlement-account **keyword context** (`р/с`, `расчетный`, `счет`, etc.). **With nearby BIK:** valid checksum → validated emission; invalid checksum → **rejected**. **Without nearby BIK:** context-only detection **unchanged** (avoids false negatives on isolated 20-digit numbers). |
| **CORRESPONDENT_ACCOUNT** | **Without nearby BIK:** regex `301…` match still emitted (recall preserved). **With nearby BIK:** valid checksum → validated; invalid → **rejected**. |
| **BIK** | Regex `04\d{7}` only — **no Central Bank directory validation** (backlog). |
| **CARD_NUMBER** | Regex only — **no Luhn validation** (backlog, Slice 15 candidate). |
| **INN / SNILS** | Unchanged: checksum-valid → high confidence; invalid with context keyword → weak emission. |

---

## 7. Current architecture

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

**Batch:** Same pipeline per file; **`replace` and `redact` only**; rejects `pseudonymize` and `--mapping-output`. API does not write or return mappings.

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
| Document I/O | `app/document_io/` (txt, md, docx, pdf, rtf, odt, batch) |
| Detectors | `app/detectors/` (`validators.py`, `regex_detectors.py`, optional NER/GLiNER) |

---

## 8. Public interfaces

### FastAPI

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Service health + version |
| GET | `/api/v1/presets` | List policy presets (safe metadata) |
| POST | `/api/v1/anonymize` | Anonymize text (`replace`, `redact`, `pseudonymize`) |

**Note:** **No file-upload API endpoint.** Document ingestion is CLI-only (and batch directory).

**Anonymize response:** anonymized `text`, masked `entities`, `summary`, `warnings` — never raw detected values or mapping payloads.

### CLI (`mithril-veil`)

| Command | Purpose |
|---------|---------|
| `version` | Print package version |
| `list-presets` | List preset ids and names |
| `anonymize-text` | Inline `--text` |
| `anonymize-stdin` | Read from stdin |
| `anonymize-file` | File in → sanitized text out + optional `--report` |
| `anonymize-dir` | Recursive batch → `*.anonymized.txt` + optional aggregate `--report` |

**Common flags:** `--mode`, `--preset`, `--use-ner` / `--no-use-ner`, `--use-gliner` / `--no-use-gliner`, GLiNER flags, `--mapping-output`, `--mapping-passphrase-env`, `--force`.

**Batch-only flags:** `--output-dir`, `--include-hidden`, `--fail-fast`, `--max-files`.

---

## 9. Supported inputs, outputs, and limits

### Supported input

- Direct text (`anonymize-text`), stdin (`anonymize-stdin`)
- Files: `.txt`, `.md`, `.markdown`, `.docx`, `.odt`, `.rtf`, text-based `.pdf`
- Batch directory: same extensions (case-insensitive), recursive by default

### Document ingestion notes

| Format | Extraction | Hardening |
|--------|------------|-----------|
| **ODT** | ZIP `content.xml` only; stdlib XML | 8 MB cap, 100:1 compression ratio, XML depth/element limits, skip embedded subtrees; safe errors |
| **RTF** | `striprtf` plain text | UTF-8 / cp1251 / latin-1; malformed best-effort; `\bin` hex stripped; safe errors |
| **DOCX / PDF** | `python-docx` / `pypdf` | 10 MB file cap; PDF 50-page cap; no OCR |

### Output

- Sanitized plain text (stdout or `--output`)
- Safe JSON reports (`--report`): entities, summary, policy — no raw values
- Optional CLI-only encrypted mapping (`.json.enc`) for `pseudonymize`
- Batch: `*.anonymized.txt` + optional aggregate report (`report_type: batch`)

**Limits:** `MAX_INPUT_FILE_BYTES` (10 MB); `MAX_PDF_PAGES` (50); ODT `content.xml` 8 MB + ratio guard.

---

## 10. Entity types

### Deterministic (regex/checksum)

`EMAIL`, `PHONE`, `INN`, `SNILS`, `PASSPORT_RU`, `OGRN`, `OGRNIP`, `KPP`, `BIK`, `BANK_ACCOUNT`, `CORRESPONDENT_ACCOUNT`, `CARD_NUMBER`, `CADASTRAL_NUMBER`, `COURT_CASE_NUMBER`, `CONTRACT_NUMBER`, `IP_ADDRESS`, `URL`, `TELEGRAM_HANDLE`.

Structured identifiers keep priority over probabilistic detectors in the span merger.

### Optional NER-derived

`PERSON`, `ORGANIZATION`, `LOCATION` (Natasha and/or GLiNER when enabled).

### Policy presets

`general_ru`, `legal_ru`, `valuation_ru`, `banking_ru`, `court_case_ru` — YAML in `app/presets/`; filtering after merge; explicit CLI/API flags override defaults; GLiNER off in bundled presets unless user enables it.

---

## 11. Security invariants

These rules are **non-negotiable** for all future slices:

| Rule | Detail |
|------|--------|
| No real PII in repo | Tests, fixtures, docs, examples — **synthetic only** |
| No real documents in repo | No client files, contracts, court PDFs, etc. |
| No raw input logging | Do not log submitted text |
| No raw values in API | `value_preview` always `***` |
| No raw values in CLI reports | JSON reports are safe summaries only |
| No raw values in stdout/stderr/errors | Including RTF/ODT parsers and mapping passphrase errors |
| Mapping files are sensitive | Even when encrypted; treat like key material |
| Never commit mappings | `mapping*.json`, `mapping*.json.enc` gitignored |
| Never commit passphrases | Keep `MITHRIL_VEIL_MAPPING_PASSPHRASE` outside the repo |
| No mapping in issues/logs | Do not attach `.json.enc` files or passphrases to tickets |
| GLiNER optional | Default CI must **not** download model weights |
| Integration tests | `@pytest.mark.integration`; excluded from default `pytest` |
| Batch reports | Aggregate/safe only — no raw text or detected values |
| RTF/ODT errors | Must **never** include raw document content or XML fragments |
| New document formats | Plain-text extraction only unless separately designed and threat-modeled |

**Threat model:** `docs/threat_model.md` — read before security-sensitive slices.

**Regression coverage (representative):** `tests/test_mapping_hardening.py`, `tests/test_encrypted_mapping.py`, `tests/test_cli_batch.py`, `tests/test_rtf_hardening.py`, `tests/test_odt.py`, `tests/test_odt_hardening.py`, `tests/test_validators.py`, `tests/test_regex_detectors.py`, API/CLI anonymizer tests.

---

## 12. Known unsupported / out of scope

- OCR
- Image-only PDF
- Encrypted PDF
- Format-preserving DOCX/PDF/RTF/ODT output
- Web UI
- Batch mapping / batch `pseudonymize`
- De-anonymization / restore workflow (no CLI/API)
- Server-side mapping persistence
- API file upload endpoint
- Macro execution in documents
- Embedded object/image extraction as product feature
- **BIK directory validation** (Central Bank registry lookup)
- **CARD_NUMBER Luhn validation** (backlog)
- Formal privacy guarantees (k-anonymity, differential privacy, etc.)
- Bundled presets only (no user-supplied custom preset YAML paths)
- Dedicated `ADDRESS` / `DATE_OF_BIRTH` regex detectors (backlog)

---

## 13. Recommended next slices (ranked)

Small, reviewable slices — **no broad rewrites**.

### A. Slice 14 — De-anonymization / restore workflow design document only (**recommended next**)

- **No implementation**
- Threat model and UX/security discussion
- CLI-only vs API boundary
- Mapping possession, passphrase handling, accidental re-identification risks

### B. Slice 15 — CARD_NUMBER Luhn validation

- Small deterministic detector hardening slice
- Synthetic tests only; preserve safe reporting

### C. Slice 16 — Release candidate hygiene for v0.1.0

- README polish, CLI examples, limitations
- Release checklist, security checklist, known limitations
- CI confirmation

### D. Later (design-only unless user overrides)

- Web UI design only
- Format-preserving output design only
- OCR design only — **strong warning:** OCR is out-of-scope for current security model

**Architectural note:** Do **not** implement restore/de-anonymize, web UI, or OCR without explicit user approval and updated threat model.

---

## 14. Development commands

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

## 15. New-chat prompt (copy-paste for ChatGPT / architect)

```text
You are the architect and technical lead for Mithril Veil (open-source, self-hosted Russian PII anonymization).

Repository: https://github.com/Kirill-Murashev/mithril-veil

Language convention:
- User-facing replies in chat: Russian
- Cursor Composer implementation prompts: English

Before any implementation:
1. Read the latest handoff: handoffs/handoff-2026-05-20-post-slice-13.md
2. Verify GitHub main when current status matters (expected HEAD: b3204a3 or later)
3. Confirm hard security invariants (no real PII, no raw values in API/reports/logs, mapping CLI-only and encrypted, batch replace/redact only)

Current baseline: version 0.1.0; 262 tests (1 deselected); Slice 13 shipped OGRN/OGRNIP checksums and bank/correspondent checksums when BIK is nearby; supported inputs include .txt/.md/.docx/.odt/.rtf/.pdf and batch anonymize-dir; ODT/RTF hardened; canonical mapping in app/core/mapping.py + app/security/encrypted_mapping.py; threat model in docs/threat_model.md.

Recommended next slice: Slice 14 — De-anonymization / restore workflow design document only (no implementation), unless the user chooses otherwise. NOT web UI, NOT de-anonymization implementation, NOT OCR.

Your task: write the next Cursor Composer prompt for exactly ONE small slice. Do not request broad architecture rewrites. Include quality gates, synthetic-data-only rules, and a final report template.
```

---

## 16. Handoff file lineage

| File | Status |
|------|--------|
| `handoffs/handoff-2026-05-20.md` | **Superseded archive** — ends at `7d58a65` |
| `handoffs/handoff-2026-05-20-post-slice-8-1.md` | **Superseded** — ends at `56b7538` |
| `handoffs/handoff-2026-05-20-post-slice-11-1.md` | **Superseded** — ends at `a99f62a` |
| `handoffs/handoff-2026-05-20-post-slice-12-1.md` | **Superseded** — ends at `4df897a` |
| `handoffs/handoff-2026-05-20-post-slice-13.md` | **Current** — this document |

---

## 17. When to create the next handoff

Create a new handoff after:

- Slice 14+ product slice ships or threat model changes materially;
- Web UI, OCR, or de-anonymization **implementation** begins;
- Security model or mapping format changes materially;
- Chat context reaches ~70%.

Documentation-only handoffs (like this file) do not require code slices but should be committed when the baseline narrative changes materially.
