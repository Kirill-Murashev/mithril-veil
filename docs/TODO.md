# Implementation backlog

- Wire YAML presets (`app/presets/*.yml`) into the detection pipeline
- OGRN/OGRNIP/BANK_ACCOUNT checksum validation with BIK linkage
- Luhn validation for CARD_NUMBER
- NER detectors for PERSON, ORGANIZATION, ADDRESS (local models only per policy)
- OCR for image-only PDFs (not in scope for 4A)
- Formatted DOCX/PDF output (preserve layout)
- HTTP document upload pipeline with strict no-persistence defaults
- Reversible tokenization behind encrypted local mapping (never commit mapping files)
