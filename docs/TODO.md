# Implementation backlog

## Shipped (0.1.0 RC)

- [x] Slice 7: CI and release hygiene (workflows, `make check`, CHANGELOG, release/security docs)
- [x] Slice 16: release candidate hygiene (README, [cli_examples.md](cli_examples.md), checklists)
- [x] Wire YAML presets (`app/presets/*.yml`) into the detection pipeline
- [x] OGRN/OGRNIP/BANK_ACCOUNT checksum validation with BIK linkage (Slice 13)
- [x] Luhn validation for CARD_NUMBER (Slice 15)
- [x] Reversible pseudonymization with encrypted CLI mapping (Slice 8 / 8.1)

## Post-v0.1.0

- [ ] v0.1.0 tag and GitHub release (maintainer decision)
- Improve NER/GLiNER precision/recall tuning and preset-driven label profiles
- Optional broader card-number recall (design/product only)

## Later (not implemented; approval required)

- [ ] Restore / de-anonymization CLI (see [restore_workflow_design.md](restore_workflow_design.md) — **no implementation in 0.1.x**)
- [ ] OCR for image-only PDFs
- [ ] Web UI
- [ ] Formatted DOCX/PDF output (preserve layout)
- [ ] HTTP document upload pipeline with strict no-persistence defaults
- [ ] Batch `pseudonymize` / batch mapping
