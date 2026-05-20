# Roadmap

## 0.1.x (current)

- [x] Regex detectors for common Russian identifiers
- [x] Deterministic detection hardening (entity model, priorities, checksums, summary)
- [x] Replace and redact modes
- [x] Health and anonymize API
- [x] Slice 3: CLI and safe text document ingestion
- [x] **Slice 4A: DOCX and text-based PDF ingestion** (no OCR)
- [x] **Slice 4B: optional Natasha NER** (PERSON, ORGANIZATION, LOCATION)
- [x] **Slice 5: optional GLiNER** zero-shot labels
- [x] **Slice 6: policy presets** and profile-based entity/detector configuration
- [x] Synthetic test fixtures only

## Next
- OGRN/OGRNIP/BANK_ACCOUNT checksum validation
- OCR for image-only PDFs (optional, local-only)
- Formatted DOCX/PDF output (optional)
- CLI batch / directory mode

## Later

- Reversible tokenization with encrypted local mapping
- Audit log without PII
- Helm chart and hardened production guide
