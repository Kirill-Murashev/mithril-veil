# Mithril Veil

**Mithril Veil: a self-hosted Russian PII anonymization gateway for safer AI workflows.**

Detect and anonymize sensitive information in Russian text before sending it to cloud LLMs. Designed for local or VPS deployment with a public, auditable codebase.

## Warning

**Do not commit real PII** to this repository — no real names, documents, bank data, passports, INN/SNILS, addresses, or reversible mapping files. Use synthetic fixtures only. Do not paste real documents into issues, tests, or examples. See [SECURITY.md](SECURITY.md).

## Features (0.1.x)

- FastAPI HTTP API with health check and text anonymization
- **CLI** for text, stdin, and file-based anonymization with safe JSON reports
- **Document I/O** for `.txt`, `.md`, `.markdown`, **DOCX**, and **text-based PDF** (output is plain text; formatting not preserved)
- Deterministic regex detectors: email, phone, INN, SNILS, passport, OGRN/OGRNIP, KPP, BIK, bank/correspondent accounts, cards, cadastral/court/contract numbers, IP, URL, Telegram handles
- INN/SNILS checksum validation with context-aware weak candidates
- Priority-based span merging with confidence tie-breaking
- Detection summary (`entity_counts`, `detectors`) in API and CLI reports
- Modes: `replace` (typed placeholders) and `redact`
- API/CLI never expose original detected values (`value_preview` is always masked)

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

## CLI

After editable install, the `mithril-veil` command is available:

```bash
mithril-veil version
# Mithril Veil 0.1.0

mithril-veil anonymize-text --text "Контакт: test@example.local" --mode replace

echo "Контакт: test@example.local" | mithril-veil anonymize-stdin --mode replace

mithril-veil anonymize-file \
  --input examples/synthetic_input.txt \
  --output /tmp/anonymized.txt \
  --mode replace \
  --report /tmp/report.json
```

- Supported **input**: `.txt`, `.md`, `.markdown`, `.docx`, `.pdf` (text-based only)
- Supported **output**: `.txt`, `.md`, `.markdown` (sanitized plain text)
- **Not supported**: OCR, image-only PDFs, encrypted PDFs, `.rtf`
- Limits: 10 MB max input size; 50 PDF pages max
- The CLI refuses to overwrite the input file (`--output` must differ from `--input`)
- Use `--force` to overwrite an existing output or report file
- JSON reports never contain raw detected values (optional safe `source` metadata only)

```bash
mithril-veil anonymize-file \
  --input input.docx \
  --output sanitized.txt \
  --mode replace \
  --report report.json

mithril-veil anonymize-file \
  --input input.pdf \
  --output sanitized.txt \
  --mode replace \
  --report report.json
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
      "detector": "regex",
      "confidence": 0.85,
      "metadata": {}
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

See [docs/roadmap.md](docs/roadmap.md) — presets, NER, DOCX/PDF ingestion, encrypted reversible mapping.

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
