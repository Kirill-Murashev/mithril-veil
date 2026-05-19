# Mithril Veil

**Mithril Veil: a self-hosted Russian PII anonymization gateway for safer AI workflows.**

Detect and anonymize sensitive information in Russian text before sending it to cloud LLMs. Designed for local or VPS deployment with a public, auditable codebase.

## Warning

**Do not commit real PII** to this repository — no real names, documents, bank data, passports, INN/SNILS, addresses, or reversible mapping files. Use synthetic fixtures only. See [SECURITY.md](SECURITY.md).

## Features (0.1.x)

- FastAPI HTTP API with health check and text anonymization
- Deterministic regex detectors: email, phone, INN, SNILS, passport, OGRN/OGRNIP, KPP, BIK, bank/correspondent accounts, cards, cadastral/court/contract numbers, IP, URL, Telegram handles
- INN/SNILS checksum validation with context-aware weak candidates
- Priority-based span merging with confidence tie-breaking
- Detection summary (`entity_counts`, `detectors`) in anonymize responses
- Modes: `replace` (typed placeholders) and `redact`
- API responses never include original detected values (`value_preview` is always masked)

## Requirements

- Python 3.12+

## Local installation

```bash
git clone https://github.com/Kirill-Murashev/mithril-veil.git
cd mithril-veil
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # optional
```

## Running the API

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/health

### Example request

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/anonymize \
  -H "Content-Type: application/json" \
  -d '{"text":"Иван Тестович: test@example.local, ИНН 7701010017","mode":"replace"}'
```

Example response shape:

```json
{
  "text": "...",
  "entities": [
    {
      "type": "EMAIL",
      "start": 0,
      "end": 0,
      "value_preview": "***",
      "replacement": "[EMAIL_1]",
      "detector": "regex"
    }
  ],
  "warnings": [],
  "summary": {
    "total_entities": 2,
    "entity_counts": { "EMAIL": 1, "INN": 1 },
    "detectors": { "regex": 2 }
  }
}
```

## Docker

```bash
docker compose up --build
```

Service listens on port **8000**.

## Development

```bash
ruff check app tests
ruff format app tests
pytest
```

## Documentation

- [Architecture](docs/architecture.md)
- [Threat model](docs/threat_model.md)
- [Russian PII taxonomy](docs/pii_taxonomy_ru.md)
- [VPS deployment](docs/deployment_vps.md)
- [Roadmap](docs/roadmap.md)

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) — presets, checksum validation, local NER, document ingestion, encrypted reversible mapping.

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
