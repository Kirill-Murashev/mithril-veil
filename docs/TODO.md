# Implementation backlog

## Shipped — v0.1.0 (released 2026-05-20)

Tag **`v0.1.0`** at `f379872`. See [CHANGELOG.md](../CHANGELOG.md) `[0.1.0]`.

- [x] Slices 1–16 (scaffold through RC hygiene)
- [x] CI and release hygiene (workflows, `make check`, CHANGELOG, release/security docs)
- [x] Wire YAML presets (`app/presets/*.yml`) into the detection pipeline
- [x] OGRN/OGRNIP/BANK_ACCOUNT checksum validation with BIK linkage (Slice 13)
- [x] Luhn validation for CARD_NUMBER (Slice 15)
- [x] Reversible pseudonymization with encrypted CLI mapping (Slice 8 / 8.1)
- [x] Annotated git tag `v0.1.0` pushed to `origin`

## A. v0.1.1 — patch / hardening (candidates)

- [ ] GitHub Release page from `CHANGELOG.md` `[0.1.0]` (maintainer; optional)
- [ ] Improve NER/GLiNER precision/recall tuning and preset-driven label profiles
- [ ] Optional broader card-number recall (design/product only)
- [ ] CI/actions maintenance; dependency patch bumps (default CI stays without GLiNER weights)

## B. v0.2.0 — feature candidates (approval required)

- [ ] HTTP document upload pipeline with strict no-persistence defaults
- [ ] Audit log without PII
- [ ] Helm chart / production hardening guide
- [ ] Custom preset loading from operator disk paths (if approved)

## C. Design-only — do not implement without explicit re-scope

- [ ] Restore / de-anonymization CLI — [restore_workflow_design.md](restore_workflow_design.md) (**design only**)
- [ ] OCR for image-only PDFs
- [ ] Web UI
- [ ] Formatted DOCX/PDF/RTF/ODT output (preserve layout)
- [ ] API restore endpoint
- [ ] Batch `pseudonymize` / batch mapping

**Constraints:** restore/OCR/web UI/API upload/API restore/batch pseudonymize remain forbidden unless maintainer re-scopes; GLiNER optional; `value_preview` `***`; mapping CLI-only `.json.enc`; synthetic data only in repo.
