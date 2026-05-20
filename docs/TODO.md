# Implementation backlog

- [x] Slice 7: CI and release hygiene (workflows, `make check`, CHANGELOG, release/security docs)
- [x] Wire YAML presets (`app/presets/*.yml`) into the detection pipeline
- OGRN/OGRNIP/BANK_ACCOUNT checksum validation with BIK linkage
- Luhn validation for CARD_NUMBER
- Improve NER/GLiNER precision/recall tuning and preset-driven label profiles
- OCR for image-only PDFs (not in scope for 4A)
- Formatted DOCX/PDF output (preserve layout)
- HTTP document upload pipeline with strict no-persistence defaults
- Reversible tokenization behind encrypted local mapping (never commit mapping files)
