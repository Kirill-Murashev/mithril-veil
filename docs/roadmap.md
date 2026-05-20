# Roadmap

## 0.1.0 (released — 2026-05-20)

Tagged **`v0.1.0`** at commit `f379872` (`f379872fbd2df803bff1ed4b33c04f4f9d6fc01a`). First public alpha.

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
- [x] **Release:** annotated git tag `v0.1.0` (no separate GitHub Release page required for tag existence)

## v0.1.1 — patch / hardening candidates (not scheduled)

Small, backward-compatible improvements; no new major surfaces without explicit approval.

- [ ] Publish **GitHub Release** notes from `CHANGELOG.md` `[0.1.0]` (maintainer; optional)
- [ ] NER/GLiNER precision/recall tuning and preset-driven label profiles
- [ ] Optional broader card-number recall (13/15/19 ungrouped PAN) — product decision only
- [ ] CI workflow maintenance (e.g. GitHub Actions Node 24 migration when upgrading actions)
- [ ] Documentation and operator-guide polish from production feedback
- [ ] Dependency patch bumps with full `make check` / default CI (no GLiNER in default CI)

## v0.2.0 — feature candidates (explicit approval required)

Larger scope; each item needs threat-model review and a dedicated slice plan.

- [ ] HTTP document upload pipeline with strict no-persistence defaults
- [ ] Audit log without PII
- [ ] Helm chart and hardened production deployment guide
- [ ] Custom preset paths from disk (if ever supported)
- [ ] Dedicated `ADDRESS` / `DATE_OF_BIRTH` regex detectors (backlog)

## Design-only / later (no implementation without maintainer re-scope)

- **De-anonymization / restore implementation** — [restore_workflow_design.md](restore_workflow_design.md) only; CLI-first future design; **not in 0.1.x**
- **OCR** for image-only PDFs (optional, local-only)
- **Web UI**
- **Format-preserving** DOCX/PDF/RTF/ODT output
- **API restore** endpoint
- **Batch `pseudonymize` / batch mapping**
- Server-side mapping persistence
- BIK Central Bank directory validation; card network classification
- Formal privacy guarantees (k-anonymity, differential privacy)

**Invariants for all future work:** no real PII/documents/mappings/passphrases in repo; `value_preview` always `***`; mapping CLI-only and encrypted; GLiNER optional; default CI must not download model weights.
