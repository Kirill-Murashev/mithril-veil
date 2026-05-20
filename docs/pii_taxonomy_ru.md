# Russian PII taxonomy

| Type | Description | Detector | Validation |
|------|-------------|----------|------------|
| PASSPORT_RU | Internal passport series/number | regex, gliner (optional) | regex TODO ranges |
| SNILS | Social insurance number | regex | checksum |
| INN | Tax ID (10/12 digits) | regex, gliner (optional) | checksum |
| OGRN | Legal entity registration (13 digits) | regex | TODO checksum |
| OGRNIP | Individual entrepreneur OGRN (15 digits) | regex | TODO checksum |
| KPP | Tax registration reason code (9 digits) | regex + context | TODO |
| BIK | Bank identification code | regex | TODO directory |
| BANK_ACCOUNT | Settlement account (20 digits) | regex, gliner (optional) | regex + context |
| CORRESPONDENT_ACCOUNT | Correspondent account (301…) | regex | TODO checksum |
| CARD_NUMBER | Payment card number | regex | TODO Luhn |
| CADASTRAL_NUMBER | Cadastral parcel ID | regex | — |
| COURT_CASE_NUMBER | Court case identifier | regex, gliner (optional) | regex TODO formats |
| CONTRACT_NUMBER | Contract reference | regex, gliner (optional) | regex + keywords |
| EMAIL | Email addresses | regex, gliner (optional) | — |
| PHONE | Russian phone numbers | regex, gliner (optional) | — |
| VEHICLE_REGISTRATION_NUMBER | Vehicle plate / registration | gliner (optional) | probabilistic |
| IP_ADDRESS | IPv4 addresses | regex | — |
| URL | HTTP(S) URLs | regex | — |
| TELEGRAM_HANDLE | Telegram @username | regex | — |
| DATE_OF_BIRTH | Birth dates | — | preset / TODO |
| ADDRESS | Postal addresses | regex, gliner (optional) | partial |
| PERSON | Person names | natasha, gliner (optional) | probabilistic NER |
| ORGANIZATION | Legal entity names | natasha, gliner (optional) | probabilistic NER |
| LOCATION | Places (NER) | natasha, gliner (optional) | probabilistic NER |

## NER notes (Natasha / GLiNER)

- Natasha: `use_ner=true` / `--use-ner` — Russian news models, local only.
- GLiNER: `use_gliner=true` / `--use-gliner` — configurable labels; install `[gliner]` extra.
- Both are **disabled by default** and probabilistic — **manual review recommended**.
- May miss entities or over-redact harmless text.
- Structured identifiers (INN, SNILS, passport, bank account, etc.) keep higher merge priority.

## Checksum behavior (INN / SNILS)

- Valid checksum → emitted with `confidence` ≈ 0.95, `metadata.checksum_valid: true`
- Invalid checksum without context keyword → not emitted
- Invalid checksum with context (`ИНН`, `СНИЛС`, etc.) → emitted with lower confidence and `checksum_valid: false`
