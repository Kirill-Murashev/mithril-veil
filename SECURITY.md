# Security Policy

## No real PII in the repository

Do **not** include real personal data, real documents, real bank statements, contracts, court files, valuation reports, addresses, passports, INN/SNILS, or reversible mapping files in:

- Issues and pull requests
- Tests and fixtures
- Logs and CI artifacts
- Example payloads in documentation

Use **synthetic** placeholders only (e.g. `test@example.local`, obviously fake IDs).

For contributor and release checks, see [docs/security_checklist.md](docs/security_checklist.md). For assets, trust boundaries, threats, and residual risks, see [docs/threat_model.md](docs/threat_model.md).

## Mapping files

Reversible anonymization mapping files must never be committed. Patterns such as `mapping*.json` and `mapping*.json.enc` are gitignored.

CLI mapping output is **encrypted only** (`.json.enc` envelope with PBKDF2 + Fernet via `app/security/encrypted_mapping.py`). The HTTP API never writes or returns mapping data. **`pseudonymize` is reversible** if you keep the mapping file and passphrase; use `replace` or `redact` when you need irreversible sanitization before a cloud LLM. Store passphrases **outside the repository** (e.g. `MITHRIL_VEIL_MAPPING_PASSPHRASE`); never commit passphrases or attach mapping files to issues, CI logs, or chat. Even encrypted mapping files are highly sensitive—treat them like key material: restrict filesystem permissions and delete when no longer needed.

## Local-first security model

Mithril Veil is designed for self-hosted deployment. By default:

- Original documents are not stored
- Original text and detected values are not logged
- External LLM calls are disabled in policy defaults

Run the service on infrastructure you control. Use TLS and network isolation in production.

Optional GLiNER models may download weights from Hugging Face on first use. Pre-cache models for air-gapped deployments. Inference remains local; no document content is sent to cloud LLM APIs.

## Cloud agents

Do not grant cloud coding agents or third-party automation access to private documents processed by your instance.

## Responsible disclosure

If you discover a security vulnerability, please report it responsibly.

**Placeholder contact:** open a private security advisory on GitHub when the repository is published, or contact the maintainers through the channel listed in the repository profile.

We will acknowledge reports and work on fixes according to severity.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Best effort (alpha) |
