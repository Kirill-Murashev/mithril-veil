# Implementation backlog

- Wire YAML presets (`app/presets/*.yml`) into the detection pipeline
- Add checksum validation for INN, SNILS, and passport numbers
- NER detectors for PERSON, ORGANIZATION, ADDRESS (local models only per policy)
- Document upload pipeline with strict no-persistence defaults
- Reversible tokenization behind encrypted local mapping (never commit mapping files)
