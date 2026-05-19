# Threat model (draft)

## Assets

- User documents and text submitted for anonymization
- Optional local mapping files for reversible tokenization (out of repo scope)

## Trust boundaries

- **Client → Mithril Veil**: Private network or TLS-terminated reverse proxy
- **Mithril Veil → external LLM**: Disabled by default (`external_llm_calls = False`)

## Risks

| Risk | Mitigation (current / planned) |
|------|--------------------------------|
| PII in logs | Default policy: no original text or detected values logged |
| PII in git | `.gitignore`, synthetic fixtures only, SECURITY.md |
| Incomplete detection | Conservative regex MVP; presets and NER later |
| Cloud agent access to docs | Local-first deployment; do not point agents at private uploads |

## Out of scope (MVP)

- Authentication and multi-tenancy
- Encrypted mapping store implementation
