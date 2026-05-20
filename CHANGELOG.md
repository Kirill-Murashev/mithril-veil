# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **CARD_NUMBER Luhn validation (Slice 15)** — `validate_luhn` / `validate_card_number` in validators; `CardNumberDetector` emits only Luhn-valid candidates (13–19 digits; rejects all-identical digits).
- **Restore workflow design (Slice 14)** — [docs/restore_workflow_design.md](docs/restore_workflow_design.md): security-first design for a possible future CLI-only de-anonymization workflow; no restore implementation, API endpoint, or mapping format changes.
- **Deterministic identifier hardening (Slice 13)** — OGRN and OGRNIP checksum validation in regex detectors; bank/correspondent account checksum validators with optional nearby-BIK validation (isolated accounts without BIK context keep prior recall).
- **ODT text ingestion (Slice 12)** — `.odt` input via ZIP `content.xml` plain-text extraction (`zipfile` + stdlib XML) for `anonymize-file` and `anonymize-dir` (paragraphs, headings, tables; no formatting, embedded objects, or images).
- **RTF text ingestion (Slice 11)** — `.rtf` input via `striprtf` plain-text extraction for `anonymize-file` and `anonymize-dir` (no formatting, embedded objects, or images).
- **CLI `anonymize-dir`** — recursive batch processing for `.txt`, `.md`, `.markdown`, `.docx`, and text-based `.pdf`; outputs `*.anonymized.txt` under `--output-dir`; aggregate safe JSON report; `replace`/`redact` only (no batch mapping or `pseudonymize`).

### Changed

- **Slice 12.1 ODT hardening** — ZipInfo checks on `content.xml` (size and compression ratio); 8 MB `content.xml` cap; XML depth/element limits; skip draw/image/object subtrees; safe errors without XML or PII leakage; batch mixed-directory regression tests.
- **Slice 11.1 RTF hardening** — UTF-8/cp1251/latin-1 decode paths; best-effort malformed RTF; post-filter for `\\bin` hex artifacts and control chars; safe exception wrapping without document content in messages.
- **Slice 10.1 batch hardening** — do not follow symlinked directories; skip symlinked supported files; skip hidden path segments (including under hidden directories) unless `--include-hidden`; case-insensitive extension matching; preflight duplicate output targets and output writability before processing; reject `--report` inside input or equal to a batch output path; deterministic batch report ordering and per-status skip counts; exit code `1` when any file fails, `2` for unsafe path/report conflicts.
- **Threat model (Slice 9)** — expanded [docs/threat_model.md](docs/threat_model.md) for encrypted mapping, passphrase handling, trust boundaries, and residual risks.
- **Security checklist** — reversible mapping / pseudonymization section and pre-release checks in [docs/security_checklist.md](docs/security_checklist.md).

- **`pseudonymize` mode** — deterministic typed placeholders with optional reversible mapping kept in memory during a run; API responses never include mapping payloads or raw detected values.
- **Encrypted local mapping files** — CLI `--mapping-output` (`.json.enc` only) with passphrase from `MITHRIL_VEIL_MAPPING_PASSPHRASE` (override via `--mapping-passphrase-env`); refuse overwrite unless `--force`.
- **Safe report mapping metadata** — reports may include only `mapping.written` and `mapping.encrypted` flags, never placeholder-to-original entries.

### Changed

- **Slice 8.1 hardening** — removed unused `app/security/mapping_io.py`; single canonical path `app/security/encrypted_mapping.py`; CLI refuses mapping path equal to input/output/report; expanded security regression tests for pseudonymize/mapping errors.

## [0.1.0] - 2026-05-20

First public alpha release. Functionality was delivered in incremental slices:

### Slice 1 — Project scaffold

- FastAPI application skeleton with health endpoint
- Apache 2.0 licensing, project layout, synthetic examples
- Initial regex-based PII detection and anonymization API

### Slice 2 — Deterministic detection core

- Entity model with priorities and confidence tie-breaking
- INN/SNILS checksum validation with context-aware weak candidates
- Expanded Russian identifier detectors (OGRN/OGRNIP, KPP, BIK, bank accounts, cards, cadastral/court/contract numbers, and more)
- Detection summary (`entity_counts`, `detectors`) in API responses
- Safe `value_preview` masking (never exposes raw detected values)

### Slice 3 — CLI and safe text ingestion

- `mithril-veil` CLI: `version`, `anonymize-text`, `anonymize-stdin`, `anonymize-file`
- Safe JSON reports without raw detected values
- `.txt`, `.md`, `.markdown` document ingestion with size limits and overwrite protection

### Slice 4A — DOCX and text-based PDF ingestion

- DOCX text extraction via `python-docx`
- Text-based PDF extraction via `pypdf` (no OCR)
- Plain-text output; formatting not preserved

### Slice 4B — Optional Natasha NER

- Local Natasha NER for Russian PERSON, ORGANIZATION, LOCATION
- Disabled by default; probabilistic — review results when enabled

### Slice 5 — Optional GLiNER

- Zero-shot GLiNER detector behind optional `[gliner]` extra
- Disabled by default; may download Hugging Face weights on first use
- Integration tests excluded from default CI

### Slice 6 — Policy presets

- Bundled YAML presets: `general_ru`, `legal_ru`, `valuation_ru`, `banking_ru`, `court_case_ru`
- `GET /api/v1/presets` and `mithril-veil list-presets`
- Preset-driven entity and detector profiles with explicit flag overrides

### Slice 7 — CI and release hygiene

- GitHub Actions CI (ruff, format check, compileall, pytest without GLiNER downloads)
- Manual `workflow_dispatch` GLiNER integration workflow
- Makefile with `make check` and related local targets
- `CHANGELOG.md`, release checklist, and security checklist
- README CI badge, development status, and build instructions

[Unreleased]: https://github.com/Kirill-Murashev/mithril-veil/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Kirill-Murashev/mithril-veil/releases/tag/v0.1.0
