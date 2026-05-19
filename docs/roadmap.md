# Roadmap

## 0.1.x (current)

- [x] Regex detectors for common Russian identifiers
- [x] Deterministic detection hardening (entity model, priorities, checksums, summary)
- [x] Replace and redact modes
- [x] Health and anonymize API
- [x] **Slice 3: CLI and safe text document ingestion** (`.txt`, `.md`, `.markdown`, JSON reports)
- [x] Synthetic test fixtures only

## Next

- Preset-driven entity selection
- OGRN/OGRNIP/BANK_ACCOUNT checksum validation
- DOCX and PDF document ingestion
- Local NER for PERSON / ORGANIZATION / ADDRESS
- CLI batch / directory mode

## Later

- Reversible tokenization with encrypted local mapping
- Audit log without PII
- Helm chart and hardened production guide
