# Handoff — Mithril Veil — Post Slice 16 — 2026-05-20

> **Supersedes for future context:** [handoff-2026-05-20-post-slice-15.md](handoff-2026-05-20-post-slice-15.md) (code baseline through `a46d60e`; handoff doc at `3baab02`), [handoff-2026-05-20-post-slice-13.md](handoff-2026-05-20-post-slice-13.md), and earlier handoff archives. Those files are **not deleted**; use **this document** as the current baseline.

---

## 1. Project identity

| Field | Value |
|-------|-------|
| **Project** | Mithril Veil |
| **Repository** | https://github.com/Kirill-Murashev/mithril-veil |
| **License** | Apache License 2.0 |
| **Version** | `0.1.0` |
| **Branch** | `main` |
| **Status** | **v0.1.0 release candidate** (feature set complete; tag not cut yet) |

**What it is:** An open-source, self-hosted, **local-first** **Russian PII anonymization/sanitization** service. Preprocess Russian **text and documents** on infrastructure you control before sending content to cloud LLMs.

**Tagline:** *Mithril Veil: a self-hosted Russian PII anonymization gateway for safer AI workflows.*

**Target users:** Lawyers, appraisers, consultants, accountants, forensic experts, and small companies that need auditable, self-hosted sanitization instead of sending raw client material to third-party APIs.

---

## 2. Current confirmed baseline

Verified at handoff time (local `main`, synced with `origin/main`):

| Item | Status |
|------|--------|
| **HEAD / origin/main** | `3f3b6be` — Prepare v0.1.0 release candidate hygiene |
| **Version** | `0.1.0` (`app/__init__.py`, `pyproject.toml`) |
| **Tests** | **271 passed**, 1 deselected (`pytest -m 'not integration'`) |
| **ruff check** | Passed |
| **ruff format --check** | Passed |
| **python -m compileall app** | Passed |
| **make check** | Passed |
| **python -m build** | Passed — `mithril_veil-0.1.0` sdist + wheel |
| **Working tree** | Clean |

**Recent commit chain:**

```text
3f3b6be Prepare v0.1.0 release candidate hygiene
3baab02 Add post-slice 15 project handoff
a46d60e Add card number Luhn validation
d5e1feb Add restore workflow design document
bdebc46 Add post-slice 13 project handoff
b3204a3 Harden deterministic identifier validation
4df897a Add post-slice 12.1 project handoff
5e83faa Harden ODT text ingestion
1860e9e Add ODT text ingestion
2cf1498 Add post-slice 11.1 project handoff
a99f62a Harden RTF text ingestion
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
| **16 — RC hygiene** | `3f3b6be` | README, CLI examples, release/security checklists, roadmap/TODO (docs only) |

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
| **Docs** | Threat model, security checklist, release checklist, [cli_examples.md](../docs/cli_examples.md), architecture, roadmap, PII taxonomy, **restore design (no implementation)** |
| **Document I/O** | RTF and ODT ingestion hardened (Slices 11.1 / 12.1) |

**Key modules:** `app/detectors/validators.py`, `app/detectors/regex_detectors.py`, `app/core/mapping.py`, `app/security/encrypted_mapping.py`, `app/document_io/`.

**Regression tests:** `tests/test_validators.py`, `tests/test_regex_detectors.py`, `tests/test_report.py`, `tests/test_mapping_hardening.py`, plus API/CLI/batch/ODT/RTF suites.

---

## 5. Slice 16 — Release candidate hygiene (documentation only)

Slice 16 commit `3f3b6be` changed **documentation only** — no application code, tests, dependencies, CI workflows, or packaging metadata.

| Deliverable | Path | Notes |
|-------------|------|-------|
| README RC polish | [README.md](../README.md) | Self-hosted positioning, CLI quickstart, API/detector tables, security warnings, supported/unsupported inputs |
| CLI examples | [docs/cli_examples.md](../docs/cli_examples.md) | **New** — synthetic examples for all CLI commands including pseudonymize + mapping |
| Release checklist | [docs/release_checklist.md](../docs/release_checklist.md) | Expanded v0.1.0 RC gates, CI rules, tag steps |
| Security checklist | [docs/security_checklist.md](../docs/security_checklist.md) | Restore/OCR/web UI scope, `value_preview == "***"`, pre-release RC section |
| Changelog | [CHANGELOG.md](../CHANGELOG.md) | Slice 16 entry under Unreleased |
| Roadmap / TODO | [docs/roadmap.md](../docs/roadmap.md), [docs/TODO.md](../docs/TODO.md) | Slice 16 complete; post-v0.1.0 items listed |

**Verified during Slice 16 (no changes made):**

- Version `0.1.0` consistent in `app/__init__.py` and `pyproject.toml`
- Default CI ([ci.yml](../.github/workflows/ci.yml)) installs `.[dev]` only — no GLiNER model download
- [gliner-integration.yml](../.github/workflows/gliner-integration.yml) remains manual (`workflow_dispatch` only)

---

## 6. Slice 14 — restore workflow design (no implementation)

| Topic | Status |
|-------|--------|
| **Document** | [docs/restore_workflow_design.md](../docs/restore_workflow_design.md) |
| **Implementation** | **None** — no restore CLI, API, or batch restore |
| **Mapping format** | Unchanged (`mithril-veil-mapping-v1`, `.json.enc` only) |

**Operator reminder:** `pseudonymize` is reversible when mapping + passphrase exist; `replace`/`redact` are not. Do not upload mapping files or restored text to cloud LLMs or issue trackers.

---

## 7. Slice 15 — CARD_NUMBER Luhn validation (code baseline)

Implemented in `app/detectors/validators.py` and `CardNumberDetector` in `app/detectors/regex_detectors.py`.

- **Luhn-valid** grouped 16-digit matches → emitted (`checksum_valid: true`, confidence ≈ 0.95)
- **Invalid Luhn** or all-identical digits → not emitted
- Regex scope: `\b(?:\d{4}[\s\-]?){3}\d{4}\b` — broader 13/15/19 ungrouped recall **not** shipped

Synthetic fixtures: `SYNTHETIC_CARD_VISA` (`4111 1111 1111 1111`), `SYNTHETIC_CARD_MASTERCARD`, `INVALID_CARD_VISA`, `INVALID_CARD_REPEATED` in `tests/conftest.py`.

---

## 8. Deterministic detector behavior (Slices 13 + 15)

| Entity | Behavior |
|--------|----------|
| **INN / SNILS** | Valid checksum → high confidence; invalid + context keyword → weak emission |
| **OGRN / OGRNIP** | Valid checksum only; invalid → not emitted |
| **BANK_ACCOUNT** | Keyword context required; validated when BIK nearby; context-only without BIK |
| **CORRESPONDENT_ACCOUNT** | Regex without BIK; validated/rejected when BIK nearby |
| **CARD_NUMBER** | Luhn-valid grouped matches; invalid/repeated → not emitted |
| **BIK** | Regex only — no directory validation |

---

## 9. Current architecture

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

## 10. Public interfaces

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

CLI examples: [docs/cli_examples.md](../docs/cli_examples.md).

---

## 11. Security invariants

| Rule | Detail |
|------|--------|
| No real PII in repo | Synthetic fixtures and public test card numbers only |
| No real documents in repo | No client files in tree |
| No raw input logging | Ever |
| No raw values in API | `value_preview` must remain **`"***"`** always |
| No raw values in CLI reports / stdout / stderr / errors | Including parsers and mapping errors |
| Mapping files | Highly sensitive even when encrypted; `mapping*.json` / `mapping*.json.enc` gitignored |
| Passphrases | Never committed, logged, or pasted into issues |
| GLiNER | Optional; default CI must **not** download weights |
| Batch reports | Aggregate/safe only |
| RTF/ODT errors | No raw document/XML in messages |
| Restore | Design only — [restore_workflow_design.md](../docs/restore_workflow_design.md); **no implementation** |
| API restore | **Out of scope** for v0.1.x |
| OCR / web UI | **Out of scope** — not implemented |

**Threat model:** [docs/threat_model.md](../docs/threat_model.md)  
**Security checklist:** [docs/security_checklist.md](../docs/security_checklist.md)

---

## 12. Known unsupported / out of scope

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

## 13. Release status and recommended next actions

| Topic | Status |
|-------|--------|
| **v0.1.0 RC hygiene** | **Complete** (Slice 16) |
| **Git tag `v0.1.0`** | **Not cut yet** |
| **GitHub release** | Not published yet |

**Recommended next step (maintainer, not feature slice):** Run [docs/release_checklist.md](../docs/release_checklist.md):

1. Verify local gates (`make check`, `python -m build`)
2. Confirm GitHub Actions CI green on `main`
3. Review README, CHANGELOG, SECURITY, release/security checklists
4. Confirm no real PII, documents, or mapping files in repo
5. **Decide** whether to tag `v0.1.0` and publish GitHub release notes

If tagging is approved, the next slice should be **release/tag planning** (CHANGELOG finalization, tag, release notes) — **not** new product features.

**Do not** implement restore, web UI, OCR, or broad new detectors without explicit user re-scope and threat-model update.

---

## 14. Development commands

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

See [docs/cli_examples.md](../docs/cli_examples.md) for full synthetic examples.

---

## 15. New-chat prompt (copy-paste for ChatGPT / architect)

```text
You are the architect and technical lead for Mithril Veil (open-source, self-hosted Russian PII anonymization).

Repository: https://github.com/Kirill-Murashev/mithril-veil

Language convention:
- User-facing replies in chat: Russian
- Cursor Composer implementation prompts: English

Before any implementation:
1. Read the latest handoff: handoffs/handoff-2026-05-20-post-slice-16.md
2. Verify GitHub main when current status matters (expected HEAD: 3f3b6be or later)
3. Confirm hard security invariants (no real PII, no raw values in API/reports/logs, value_preview always ***, mapping CLI-only and encrypted, batch replace/redact only, no restore implementation)
4. Do not start broad architecture rewrites — continue by small vertical slices only

Current baseline: version 0.1.0 release candidate; 271 tests (1 deselected); Slices 1–16 shipped; last code slice a46d60e (CARD_NUMBER Luhn); Slice 16 was docs-only RC hygiene at 3f3b6be; inputs .txt/.md/.docx/.odt/.rtf/.pdf + batch; README, cli_examples, release/security checklists updated; no v0.1.0 tag yet.

Recommended next step: maintainer release checklist / v0.1.0 tag planning — NOT restore implementation, NOT web UI, NOT OCR, NOT new features unless explicitly re-scoped.

Your task: write the next Cursor Composer prompt for exactly ONE small slice. Do not request broad architecture rewrites. Include quality gates, synthetic-data-only rules, and a final report template.
```

---

## 16. Handoff file lineage

| File | Status |
|------|--------|
| `handoffs/handoff-2026-05-20.md` | **Superseded archive** — ends at `7d58a65` |
| `handoffs/handoff-2026-05-20-post-slice-8-1.md` | **Superseded** |
| `handoffs/handoff-2026-05-20-post-slice-11-1.md` | **Superseded** |
| `handoffs/handoff-2026-05-20-post-slice-12-1.md` | **Superseded** |
| `handoffs/handoff-2026-05-20-post-slice-13.md` | **Superseded** |
| `handoffs/handoff-2026-05-20-post-slice-15.md` | **Superseded** — ends at `3baab02` (handoff commit); code through `a46d60e` |
| `handoffs/handoff-2026-05-20-post-slice-16.md` | **Current** — this document |

---

## 17. When to create the next handoff

Create a new handoff after:

- **v0.1.0 release tag** is cut or release notes are published;
- A new feature slice ships (restore, OCR, web UI, detectors, etc.);
- Threat model or mapping format changes materially;
- Chat context reaches ~70%.

Documentation-only handoffs (like this file) should be committed when the baseline narrative changes materially after a slice or RC milestone.
