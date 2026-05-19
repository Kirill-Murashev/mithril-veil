# Russian PII taxonomy

| Type | Description | Detector | Validation |
|------|-------------|----------|------------|
| PASSPORT_RU | Internal passport series/number | regex | TODO ranges |
| SNILS | Social insurance number | regex | checksum |
| INN | Tax ID (10/12 digits) | regex | checksum |
| OGRN | Legal entity registration (13 digits) | regex | TODO checksum |
| OGRNIP | Individual entrepreneur OGRN (15 digits) | regex | TODO checksum |
| KPP | Tax registration reason code (9 digits) | regex + context | TODO |
| BIK | Bank identification code | regex | TODO directory |
| BANK_ACCOUNT | Settlement account (20 digits) | regex + context | TODO with BIK |
| CORRESPONDENT_ACCOUNT | Correspondent account (301…) | regex | TODO checksum |
| CARD_NUMBER | Payment card number | regex | TODO Luhn |
| CADASTRAL_NUMBER | Cadastral parcel ID | regex | — |
| COURT_CASE_NUMBER | Court case identifier | regex | TODO formats |
| CONTRACT_NUMBER | Contract reference | regex + keywords | — |
| EMAIL | Email addresses | regex | — |
| PHONE | Russian phone numbers | regex | — |
| IP_ADDRESS | IPv4 addresses | regex | — |
| URL | HTTP(S) URLs | regex | — |
| TELEGRAM_HANDLE | Telegram @username | regex | — |
| DATE_OF_BIRTH | Birth dates | — | preset / TODO |
| ADDRESS | Postal addresses | regex / preset | partial |
| PERSON | Person names | natasha (optional) | probabilistic NER |
| ORGANIZATION | Legal entity names | natasha (optional) | probabilistic NER |
| LOCATION | Places, addresses (NER) | natasha (optional) | probabilistic NER |

## NER notes (Natasha)

- Enabled only when `use_ner=true` (API) or `--use-ner` (CLI).
- Local models only; no cloud calls.
- May miss entities or over-redact harmless text — **manual review recommended**.
- Structured identifiers (INN, SNILS, passport, etc.) keep higher merge priority than NER spans.

## Checksum behavior (INN / SNILS)

- Valid checksum → emitted with `confidence` ≈ 0.95, `metadata.checksum_valid: true`
- Invalid checksum without context keyword → not emitted
- Invalid checksum with context (`ИНН`, `СНИЛС`, etc.) → emitted with lower confidence and `checksum_valid: false`
