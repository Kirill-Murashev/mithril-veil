# Implementation backlog

- Wire YAML presets (`app/presets/*.yml`) into the detection pipeline
- OGRN/OGRNIP/BANK_ACCOUNT checksum validation with BIK linkage
- Luhn validation for CARD_NUMBER
- NER detectors for PERSON, ORGANIZATION, ADDRESS (local models only per policy)
- DOCX/PDF readers in `app/document_io/` (stubs exist; implement with no PII logging)
- HTTP document upload pipeline with strict no-persistence defaults
- Reversible tokenization behind encrypted local mapping (never commit mapping files)
