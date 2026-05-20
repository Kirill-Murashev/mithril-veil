# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

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
