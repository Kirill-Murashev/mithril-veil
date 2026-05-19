# Security Policy

## No real PII in the repository

Do **not** include real personal data, real documents, real bank statements, contracts, court files, valuation reports, addresses, passports, INN/SNILS, or reversible mapping files in:

- Issues and pull requests
- Tests and fixtures
- Logs and CI artifacts
- Example payloads in documentation

Use **synthetic** placeholders only (e.g. `test@example.local`, obviously fake IDs).

## Mapping files

Reversible anonymization mapping files must never be committed. Patterns such as `mapping*.json` are gitignored.

## Local-first security model

Mithril Veil is designed for self-hosted deployment. By default:

- Original documents are not stored
- Original text and detected values are not logged
- External LLM calls are disabled in policy defaults

Run the service on infrastructure you control. Use TLS and network isolation in production.

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
