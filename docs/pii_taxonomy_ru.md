# Russian PII taxonomy (MVP)

| Type | Description | MVP detector |
|------|-------------|--------------|
| EMAIL | Email addresses | regex |
| PHONE | Russian phone numbers | regex |
| INN | Tax ID (10/12 digits) | regex (no checksum yet) |
| SNILS | Social insurance number | regex |
| PASSPORT_RU | Internal passport series/number | regex |
| CADASTRAL_NUMBER | Cadastral parcel ID | regex |
| COURT_CASE_NUMBER | Court case identifier | regex |
| PERSON | Person names | preset only (TODO) |
| ORGANIZATION | Legal entities | preset only (TODO) |
| ADDRESS | Postal addresses | preset only (TODO) |
| CONTRACT_NUMBER | Contract refs | preset only (TODO) |
| BANK_ACCOUNT | Bank account numbers | preset only (TODO) |
