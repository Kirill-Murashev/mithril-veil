# Handoff — Mithril Veil — Post Slice 15 — 2026-05-20

> **Supersedes for future context:** [handoff-2026-05-20-post-slice-13.md](handoff-2026-05-20-post-slice-13.md) (ends at `bdebc46` for handoff doc; code baseline through `b3204a3`), [handoff-2026-05-20-post-slice-12-1.md](handoff-2026-05-20-post-slice-12-1.md), and earlier handoff archives. Those files are **not deleted**; use **this document** as the current baseline.

---

## 1. Project identity

| Field | Value |
|-------|-------|
| **Project** | Mithril Veil |
| **Repository** | https://github.com/Kirill-Murashev/mithril-veil |
| **License** | Apache License 2.0 |
| **Version** | `0.1.0` |
| **Branch** | `main` |

**What it is:** An open-source, self-hosted **Russian PII anonymization/sanitization** service for safer LLM workflows. **Local-first** preprocessing: detect and anonymize sensitive data in Russian **text and documents** before content is sent to cloud LLMs.

**Tagline:** *Mithril Veil: a self-hosted Russian PII anonymization gateway for safer AI workflows.*

**Target users:** Lawyers, appraisers, consultants, accountants, forensic experts, and small companies that need auditable, self-hosted sanitization instead of sending raw client material to third-party APIs.

---

## 2. Current confirmed baseline

Verified at handoff time (local `main`, synced with `origin/main`):

| Item | Status |
|------|--------|
| **HEAD / origin/main** | `a46d60e` — Add card number Luhn validation |
| **Version** | `0.1.0` (`app/__init__.py`, `pyproject.toml`) |
| **Tests** | **271 passed**, 1 deselected (`pytest -m 'not integration'`) |
| **ruff check** | Passed |
| **ruff format --check** | Passed |
| **python -m compileall app** | Passed |
| **pytest** | Passed |
| **make check** | Passed |
| **python -m build** | Passed (at last code slice `a46d60e`) |
| **Working tree** | Clean |

**Recent commit chain:**

```text
a46d60e Add card number Luhn validation
d5e1feb Add restore workflow design document
bdebc46 Add post-slice 13 project handoff
b3204a3 Harden deterministic identifier validation
4df897a Add post-slice 12.1 project handoff
5e83faa Harden ODT text ingestion
1860e9e Add ODT text ingestion
2cf1498 Add post-slice 11.1 project handoff
a99f62a Harden RTF text ingestion
f49c05a Add safe RTF text ingestion
7d58a65 Add CI and release hygiene
```

---

## 3. Implemented slices (chronological)

| Slice | Commit (representative) | Summary |
|-------|-------------------------|---------|
| **1 — Scaffold** | `6371e66` | FastAPI app, `/health`, `/api/v1/anonymize`, regex detection, `replace`/`redact` |
| **2 — Deterministic core** | `b69865c` | `DetectedEntity`, span merger, INN/SNILS checksums, expanded regex types |
| **3 — CLI + text I/O** | `3ed5a3d` | `mithril-veil` CLI, `.txt`/`.md`, safe JSON reports |
| **4A — DOCX/PDF** | `6fcf84a` | `python-docx`, `pypdf`, size/page limits, no OCR |
| **4B — Natasha NER** | `479a54b` | Optional PERSON/ORGANIZATION/LOCATION |
| **5 — GLiNER** | `36b08f7` | Optional zero-shot detector; integration tests off in default CI |
| **6 — Presets** | `37fa090` | Five YAML presets, entity filtering, `GET /api/v1/presets` |
| **7 — CI / release** | `7d58a65` | GitHub Actions, Makefile, CHANGELOG, checklists |
| **8 / 8.1 — Mapping** | `c70d23a`, `5a5b1fd` | `pseudonymize`, encrypted `.json.enc`, path hardening |
| **9 — Threat model** | `56b7538` | `docs/threat_model.md` |
| **10 / 10.1 — Batch** | `dcbf0cc`, `395f540` | `anonymize-dir`, replace/redact only, hardening |
| **11 / 11.1 — RTF** | `f49c05a`, `a99f62a` | `striprtf` ingestion + hardening |
| **12 / 12.1 — ODT** | `1860e9e`, `5e83faa` | ZIP `content.xml` ingestion + hardening |
| **13 — Detector hardening** | `b3204a3` | OGRN/OGRNIP; bank/correspondent checksums when BIK nearby |
| **14 — Restore design** | `d5e1feb` | [restore_workflow_design.md](../docs/restore_workflow_design.md) only |
| **15 — CARD_NUMBER Luhn** | `a46d60e` | Luhn validation for card detector |

---

## 4. Implemented capabilities (summary)

| Area | Capability |
|------|------------|
| **Detection** | Deterministic regex/checksum detectors; safe detection summaries; priority span merger |
| **Checksum validation** | INN, SNILS, OGRN, OGRNIP; BANK_ACCOUNT / CORRESPONDENT_ACCOUNT when BIK nearby; **CARD_NUMBER Luhn** |
| **CLI** | `version`, `list-presets`, `anonymize-text`, `anonymize-stdin`, `anonymize-file`, `anonymize-dir` |
| **API** | `GET /health`, `GET /api/v1/presets`, `POST /api/v1/anonymize` |
| **Inputs** | Direct text, stdin, `.txt`, `.md`, `.markdown`, `.docx`, `.odt`, `.rtf`, text-based `.pdf`; batch directory |
| **Optional ML** | Natasha NER; GLiNER (optional extra, off in default CI) |
| **Presets** | `general_ru`, `legal_ru`, `valuation_ru`, `banking_ru`, `court_case_ru` |
| **Modes** | `replace`, `redact`, `pseudonymize` |
| **Mapping** | Encrypted CLI-only reversible mapping for `pseudonymize` (`.json.enc`) |
| **Batch** | `anonymize-dir` for `replace`/`redact` only; aggregate safe JSON report |
| **Docs** | Threat model, security checklist, architecture, roadmap, PII taxonomy, **restore design (no implementation)** |
| **Document I/O** | RTF and ODT ingestion hardened (Slices 11.1 / 12.1) |

**Key modules:** `app/detectors/validators.py`, `app/detectors/regex_detectors.py`, `app/core/mapping.py`, `app/security/encrypted_mapping.py`, `app/document_io/`.

**Regression tests:** `tests/test_validators.py`, `tests/test_regex_detectors.py`, `tests/test_report.py`, `tests/test_mapping_hardening.py`, plus API/CLI/batch/ODT/RTF suites.

---

## 5. Slice 14 — restore workflow design (no implementation)

| Topic | Status |
|-------|--------|
| **Document** | [docs/restore_workflow_design.md](../docs/restore_workflow_design.md) |
| **Implementation** | **None** — no restore CLI, API, or batch restore |
| **Mapping format** | Unchanged (`mithril-veil-mapping-v1`, `.json.enc` only) |

**Design principles (summary):**

- Future restore should be **CLI-only first**, with passphrase from **environment variable** (never CLI argv), distinct paths, `--force` for overwrite, safe errors, no raw values in reports/logs/stdout by default.
- **API restore endpoint** remains **strongly discouraged / out of scope** for v0.1.x; would need a separate threat model and explicit approval.
- **Batch restore** deferred until separately designed.
- Staged plan in design doc: R1 envelope hardening → R2 design tests → R3 CLI restore → R4 safety hardening.

**Operator reminder:** `pseudonymize` is reversible when mapping + passphrase exist; `replace`/`redact` are not. Do not upload mapping files or restored text to cloud LLMs or issue trackers.

---

## 6. Slice 15 — CARD_NUMBER Luhn validation

Implemented in `app/detectors/validators.py` and `CardNumberDetector` in `app/detectors/regex_detectors.py`.

### `validate_luhn(digits)`

- Standard **Luhn (mod 10)** on an ASCII digit string (typically after normalization).

### `validate_card_number(value)`

- **`normalize_digits()`** — strips spaces and hyphens (and other non-digits).
- **Length** 13–19 digits after normalization.
- **Rejects** all-identical digit strings (e.g. `0000 0000 0000 0000`) even if Luhn passes.
- Delegates to `validate_luhn()` for checksum.

### `CardNumberDetector` behavior

| Case | Behavior |
|------|----------|
| Luhn-valid match | Emitted: `metadata.checksum_valid: true`, confidence ≈ **0.95** (`CONFIDENCE_VALIDATED`) |
| Invalid Luhn | **Not emitted** |
| Regex scope | Still `\b(?:\d{4}[\s\-]?){3}\d{4}\b` — primarily **16-digit grouped** patterns; broader 13/15/19-digit recall **not** part of Slice 15 |

### Synthetic test fixtures (`tests/conftest.py`)

| Constant | Role |
|----------|------|
| `SYNTHETIC_CARD_VISA` | `4111 1111 1111 1111` (public test PAN) |
| `SYNTHETIC_CARD_MASTERCARD` | `5555 5555 5555 4444` |
| `INVALID_CARD_VISA` | `4111 1111 1111 1112` (bad checksum) |
| `INVALID_CARD_REPEATED` | `0000 0000 0000 0000` |

**Not in scope for Slice 15:** PCI compliance claims, card network/brand detection, expanded regex for Amex-length cards without 4×4 grouping.

---

## 7. Deterministic detector behavior (Slices 13 + 15)

| Entity | Behavior |
|--------|----------|
| **INN / SNILS** | Valid checksum → high confidence; invalid + context keyword → weak emission |
| **OGRN / OGRNIP** | Valid checksum only; invalid → not emitted |
| **BANK_ACCOUNT** | Keyword context required; validated when BIK nearby; context-only without BIK |
| **CORRESPONDENT_ACCOUNT** | Regex without BIK; validated/rejected when BIK nearby |
| **CARD_NUMBER** | Luhn-valid 16-digit grouped matches only; invalid/repeated → not emitted |
| **BIK** | Regex only — no directory validation |

---

## 8. Current architecture

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

**Batch:** Same pipeline per file; **`replace` and `redact` only**; rejects `pseudonymize` and `--mapping-output`. **API** does not write or return mappings. **Restore** is not in the pipeline.

| Area | Path |
|------|------|
| API | `app/api/` |
| CLI | `app/cli/main.py`, `app/cli/batch_cmd.py` |
| Pipeline | `app/core/pipeline.py` |
| Detectors | `app/detectors/` |
| Mapping | `app/core/mapping.py`, `app/security/encrypted_mapping.py` |
| Document I/O | `app/document_io/` |
| Presets | `app/presets/`, `app/core/presets.py` |

---

## 9. Public interfaces

### FastAPI

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health + version |
| GET | `/api/v1/presets` | Preset metadata |
| POST | `/api/v1/anonymize` | Anonymize text (`replace`, `redact`, `pseudonymize`) |

**No file-upload API.** **No restore API.**

### CLI (`mithril-veil`)

| Command | Purpose |
|---------|---------|
| `version` | Package version |
| `list-presets` | Preset list |
| `anonymize-text` | Inline text |
| `anonymize-stdin` | Stdin |
| `anonymize-file` | Single file + optional report/mapping |
| `anonymize-dir` | Batch directory (replace/redact only) |

---

## 10. Security invariants

| Rule | Detail |
|------|--------|
| No real PII in repo | Synthetic fixtures and public test card numbers only |
| No real documents in repo | No client files in tree |
| No raw input logging | Ever |
| No raw values in API | `value_preview` always `***` |
| No raw values in CLI reports / stdout / stderr / errors | Including parsers and mapping errors |
| Mapping files | Highly sensitive; `mapping*.json` / `mapping*.json.enc` gitignored |
| Passphrases | Never committed, logged, or pasted into issues |
| GLiNER | Optional; default CI must **not** download weights |
| Batch reports | Aggregate/safe only |
| RTF/ODT errors | No raw document/XML in messages |
| New formats | Plain-text extraction only unless threat-modeled |

**Threat model:** `docs/threat_model.md`  
**Restore design:** `docs/restore_workflow_design.md` (design only)

---

## 11. Known unsupported / out of scope

- OCR; image-only PDF; encrypted PDF
- Format-preserving DOCX/PDF/RTF/ODT output
- Web UI
- Batch mapping / batch `pseudonymize`
- **De-anonymization / restore implementation**
- Server-side mapping persistence
- API file upload; **API restore endpoint**
- Macro execution; embedded object extraction as product feature
- BIK Central Bank directory validation
- Card network / brand classification
- **Broader card-number recall** beyond current 4×4-grouped regex (13/15/19 ungrouped)
- Formal privacy guarantees (k-anonymity, differential privacy, legal anonymization proof)
- Bundled presets only (no custom preset paths from disk)
- Dedicated `ADDRESS` / `DATE_OF_BIRTH` regex detectors (backlog)

---

## 12. Recommended next slices (ranked)

### A. Slice 16 — Release candidate hygiene for v0.1.0 (**recommended next**)

- README polish, CLI examples, limitations
- Release checklist, security checklist updates
- CI confirmation
- **No broad feature work**

### B. Optional Slice 17 — Broader card-number recall (design or small code)

- Only if product needs 13/15/19-digit ungrouped PAN recall
- Avoid PCI/network claims; synthetic tests only

### C. Later (design-only unless approved)

- Web UI design only
- Format-preserving output design only
- OCR design only (**strong warning** — out of current security model)
- **Restore implementation** only after explicit approval + updated threat model (see Slice 14 design)

**Do not** implement restore, web UI, or OCR without explicit user approval and threat-model update.

---

## 13. Development commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

make check
make run-api
python -m build

mithril-veil anonymize-text --text "Контакт: test@example.local" --mode replace
```

**Batch (replace/redact only):**

```bash
mithril-veil anonymize-dir ./documents --output-dir ./sanitized --mode replace
```

**Pseudonymize + mapping (CLI single-file only):**

```bash
export MITHRIL_VEIL_MAPPING_PASSPHRASE="your-local-secret"
mithril-veil anonymize-file --input in.txt --output out.txt \
  --mode pseudonymize --mapping-output mapping.json.enc
```

---

## 14. New-chat prompt (copy-paste for ChatGPT / architect)

```text
You are the architect and technical lead for Mithril Veil (open-source, self-hosted Russian PII anonymization).

Repository: https://github.com/Kirill-Murashev/mithril-veil

Language convention:
- User-facing replies in chat: Russian
- Cursor Composer implementation prompts: English

Before any implementation:
1. Read the latest handoff: handoffs/handoff-2026-05-20-post-slice-15.md
2. Verify GitHub main when current status matters (expected HEAD: a46d60e or later)
3. Confirm hard security invariants (no real PII, no raw values in API/reports/logs, mapping CLI-only and encrypted, batch replace/redact only, no restore implementation)

Current baseline: version 0.1.0; 271 tests (1 deselected); Slices 13–15 shipped (OGRN/OGRNIP/bank checksums, restore design doc only, CARD_NUMBER Luhn); inputs .txt/.md/.docx/.odt/.rtf/.pdf + batch; threat model and restore_workflow_design.md in docs/.

Recommended next slice: Slice 16 — Release candidate hygiene for v0.1.0, unless the user chooses otherwise. NOT restore implementation, NOT web UI, NOT OCR.

Your task: write the next Cursor Composer prompt for exactly ONE small slice. Do not request broad architecture rewrites. Include quality gates, synthetic-data-only rules, and a final report template.
```

---

## 15. Handoff file lineage

| File | Status |
|------|--------|
| `handoffs/handoff-2026-05-20.md` | **Superseded archive** — ends at `7d58a65` |
| `handoffs/handoff-2026-05-20-post-slice-8-1.md` | **Superseded** |
| `handoffs/handoff-2026-05-20-post-slice-11-1.md` | **Superseded** |
| `handoffs/handoff-2026-05-20-post-slice-12-1.md` | **Superseded** |
| `handoffs/handoff-2026-05-20-post-slice-13.md` | **Superseded** — ends at `bdebc46` (handoff commit) |
| `handoffs/handoff-2026-05-20-post-slice-15.md` | **Current** — this document |

---

## 16. When to create the next handoff

Create a new handoff after:

- Slice 16+ ships or v0.1.0 release tag is cut;
- Threat model or mapping format changes materially;
- Restore, web UI, or OCR **implementation** begins;
- Chat context reaches ~70%.

Documentation-only handoffs should be committed when the baseline narrative changes materially (as with this file after Slices 14–15).
