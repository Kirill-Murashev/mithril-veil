# Implementation backlog

- Wire YAML presets (`app/presets/*.yml`) into the detection pipeline
- OGRN/OGRNIP/BANK_ACCOUNT checksum validation with BIK linkage
- Luhn validation for CARD_NUMBER
- Improve NER precision/recall tuning; optional GLiNER or other local models
- OCR for image-only PDFs (not in scope for 4A)
- Formatted DOCX/PDF output (preserve layout)
- HTTP document upload pipeline with strict no-persistence defaults
- Reversible tokenization behind encrypted local mapping (never commit mapping files)
