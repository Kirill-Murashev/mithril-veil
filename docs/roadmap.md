# Roadmap

## 0.1.0 (release candidate — current)

- [x] Regex detectors for common Russian identifiers
- [x] Deterministic detection hardening (entity model, priorities, checksums, summary)
- [x] Replace, redact, and **pseudonymize** modes
- [x] Health and anonymize API
- [x] Slice 3: CLI and safe text document ingestion
- [x] **Slice 4A: DOCX and text-based PDF ingestion** (no OCR)
- [x] **Slice 4B: optional Natasha NER** (PERSON, ORGANIZATION, LOCATION)
- [x] **Slice 5: optional GLiNER** zero-shot labels
- [x] **Slice 6: policy presets** and profile-based entity/detector configuration
- [x] **Slice 7: CI and release hygiene** (GitHub Actions, Makefile, CHANGELOG, release/security checklists)
- [x] **Slice 8 / 8.1: reversible pseudonymization** with encrypted CLI mapping (`.json.enc`)
- [x] **Slice 9: threat model and security regression documentation**
- [x] **Slice 10: CLI batch directory anonymization** (`anonymize-dir`, no batch mapping)
- [x] **Slice 10.1: batch CLI hardening** (symlinks, collisions, report safety, exit codes)
- [x] **Slice 11: RTF text ingestion** (plain text via `striprtf`; no embedded objects/OCR)
- [x] **Slice 11.1: RTF ingestion hardening** (encoding, malformed RTF, binary artifact filter)
- [x] **Slice 12: ODT text ingestion** (ZIP `content.xml`, stdlib XML; no embedded objects/OCR)
- [x] **Slice 12.1: ODT ingestion hardening** (zip-bomb checks, malformed XML, embedded object ignoring, batch safety)
- [x] Synthetic test fixtures only
- [x] **Slice 13: deterministic identifier hardening** (OGRN/OGRNIP checksums; bank/correspondent account checksums when BIK is nearby)
- [x] **Slice 14: de-anonymization / restore workflow design document only** ([restore_workflow_design.md](restore_workflow_design.md); no implementation)
- [x] **Slice 15: CARD_NUMBER Luhn validation**
- [x] **Slice 16: release candidate hygiene** (README, CLI examples doc, release/security checklists)

## Post-v0.1.0 (not scheduled)

- Tag **v0.1.0** and GitHub release (when maintainers approve)
- Optional broader card-number recall (13/15/19 ungrouped PAN) — product decision only
- NER/GLiNER precision tuning and preset-driven label profiles

## Later (explicit approval required)

- **De-anonymization / restore implementation** — only after threat model update and approval ([restore_workflow_design.md](restore_workflow_design.md) is design-only today)
- **OCR** for image-only PDFs (optional, local-only; out of current security model)
- **Web UI** (not implemented)
- **Format-preserving** DOCX/PDF/RTF/ODT output (not implemented)
- HTTP document upload with strict no-persistence defaults
- Audit log without PII
- Helm chart and hardened production guide
