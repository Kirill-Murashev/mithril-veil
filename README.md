# Mithril Veil

![CI](https://github.com/Kirill-Murashev/mithril-veil/actions/workflows/ci.yml/badge.svg)

**Mithril Veil: a self-hosted Russian PII anonymization gateway for safer AI workflows.**

> **Status:** Pre-release / active development (0.1.x alpha). APIs and presets may change before a stable 1.0 release. See [CHANGELOG.md](CHANGELOG.md) and [docs/release_checklist.md](docs/release_checklist.md).

Detect and anonymize sensitive information in Russian text before sending it to cloud LLMs. Designed for local or VPS deployment with a public, auditable codebase. See the [threat model](docs/threat_model.md) for security boundaries and residual risks.

## Warning

**Do not commit real PII** to this repository — no real names, documents, bank data, passports, INN/SNILS, addresses, or reversible mapping files. Use synthetic fixtures only. Do not paste real documents into issues, tests, or examples. See [SECURITY.md](SECURITY.md).

## Features (0.1.x)

- FastAPI HTTP API with health check and text anonymization
- **CLI** for text, stdin, and file-based anonymization with safe JSON reports
- **Document I/O** for `.txt`, `.md`, `.markdown`, **DOCX**, and **text-based PDF** (output is plain text; formatting not preserved)
- Deterministic regex/checksum detectors: email, phone, INN, SNILS, passport, OGRN/OGRNIP, KPP, BIK, bank/correspondent accounts, cards, cadastral/court/contract numbers, IP, URL, Telegram handles
- **Optional local Natasha NER** for Russian PERSON, ORGANIZATION, LOCATION (disabled by default; probabilistic — review results)
- **Optional GLiNER** zero-shot labels (`pip install -e ".[gliner]"`; disabled by default; may download Hugging Face weights on first use)
- **Policy presets** (`general_ru`, `legal_ru`, `valuation_ru`, `banking_ru`, `court_case_ru`) for workflow-specific entity and detector profiles
- INN/SNILS checksum validation with context-aware weak candidates
- Priority-based span merging with confidence tie-breaking
- Detection summary (`entity_counts`, `detectors`) in API and CLI reports
- Modes: `replace` (typed placeholders), `redact`, and `pseudonymize` (reversible placeholders; optional encrypted CLI-only mapping — not irreversible anonymization)
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

# Optional GLiNER support (local inference; model weights may download on first use):
# pip install -e ".[dev,gliner]"
cp .env.example .env   # optional
```

## CLI

After editable install, the `mithril-veil` command is available:

```bash
mithril-veil version
# Mithril Veil 0.1.0

mithril-veil list-presets
# general_ru      General RU
# legal_ru        Legal RU
# ...

mithril-veil anonymize-text --text "Контакт: test@example.local" --mode replace --preset general_ru

mithril-veil anonymize-text \
  --text "Иван Тестович работает в ООО Тестовая Организация." \
  --mode replace \
  --use-ner

# Preset for legal workflows (Natasha NER on by default for this preset):
mithril-veil anonymize-text \
  --text "Иван Тестович работает в ООО Тестовая Организация." \
  --mode replace \
  --preset legal_ru

# Explicit flags override preset defaults (disable NER despite legal_ru default):
mithril-veil anonymize-text \
  --text "Иван Тестович работает в ООО Тестовая Организация." \
  --mode replace \
  --preset legal_ru \
  --no-use-ner

# GLiNER (requires [gliner] extra; probabilistic — review results):
mithril-veil anonymize-text \
  --text "Иван Тестович работает в ООО Тестовая Организация." \
  --mode replace \
  --use-gliner \
  --gliner-label person \
  --gliner-label organization

echo "Контакт: test@example.local" | mithril-veil anonymize-stdin --mode replace

mithril-veil anonymize-file \
  --input examples/synthetic_input.txt \
  --output /tmp/anonymized.txt \
  --mode replace \
  --report /tmp/report.json

# Batch directory (replace/redact only; no encrypted mapping in batch):
mithril-veil anonymize-dir ./documents --output-dir ./sanitized \
  --mode replace --report ./batch-report.json
```

- **`anonymize-dir`** — recursively processes supported files under a directory (case-insensitive extensions); writes `*.anonymized.txt` under `--output-dir`; optional aggregate safe `--report`. Skips symlinked files and hidden paths (unless `--include-hidden`); rejects duplicate output stems and unsafe report paths before processing. Supports **`replace` and `redact` only** (rejects `pseudonymize` and `--mapping-output`). Exit code `1` if any file fails. See [threat model](docs/threat_model.md).
- Supported **input**: `.txt`, `.md`, `.markdown`, `.docx`, `.pdf` (text-based only)
- Supported **output**: `.txt`, `.md`, `.markdown` (sanitized plain text)
- **Not supported**: OCR, image-only PDFs, encrypted PDFs, `.rtf`
- Limits: 10 MB max input size; 50 PDF pages max
- The CLI refuses to overwrite the input file (`--output` must differ from `--input`)
- Use `--force` to overwrite an existing output or report file
- JSON reports never contain raw detected values (optional safe `source` and `policy` metadata only)
- **`pseudonymize` + mapping (CLI only):** `--mode pseudonymize` with `--mapping-output path.json.enc` (suffix required); passphrase via `MITHRIL_VEIL_MAPPING_PASSPHRASE` or `--mapping-passphrase-env`. Mapping path must differ from `--input`, `--output`, and `--report`. The HTTP API never returns mapping data. Reports include only `mapping.written` / `mapping.encrypted` when a mapping file was written—never placeholder→original entries. Mapping files are gitignored (`mapping*.json`, `mapping*.json.enc`).
- **`--preset`** selects a bundled YAML profile; **`list-presets`** lists available ids
- Available presets: `general_ru`, `legal_ru`, `valuation_ru`, `banking_ru`, `court_case_ru`
- Explicit `--use-ner`, `--no-use-ner`, `--use-gliner`, `--no-use-gliner`, and GLiNER flags override preset defaults
- GLiNER remains disabled in all bundled presets unless you enable it explicitly
- Natasha NER is probabilistic — always review results when enabled

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

# List presets:
# curl -s http://127.0.0.1:8000/api/v1/presets

# Use a preset (explicit use_ner overrides preset default):
# -d '{"text":"Иван Тестович работает в ООО Тестовая Организация.","mode":"replace","preset":"legal_ru"}'
# -d '{"text":"...","mode":"replace","preset":"legal_ru","use_ner":false}'
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
docker compose up --build -d
curl -s http://127.0.0.1:8000/health
```

Service listens on port **8000**.

## Makefile

After `pip install -e ".[dev]"`:

```bash
make check          # ruff + format check + compileall + pytest (no GLiNER download)
make install        # pip install -e ".[dev]"
make install-gliner # pip install -e ".[dev,gliner]"
make lint           # ruff check
make format         # ruff format
make test           # pytest -v
make run-api        # uvicorn app.main:app --reload
```

Install equivalents without Make:

```bash
pip install -e ".[dev]"
pip install -e ".[dev,gliner]"   # optional GLiNER extra
```

## Package build

```bash
python -m pip install build
python -m build
```

Produces `dist/` wheels and sdists (gitignored; do not commit).

## Development

Run the same gates as CI:

```bash
make check
```

Or individually:

```bash
ruff check app tests
ruff format --check app tests
python -m compileall app
pytest -v
```

## Documentation

- [Architecture](docs/architecture.md)
- [Threat model](docs/threat_model.md)
- [Russian PII taxonomy](docs/pii_taxonomy_ru.md)
- [VPS deployment](docs/deployment_vps.md)
- [Release checklist](docs/release_checklist.md)
- [Security checklist](docs/security_checklist.md)
- [Roadmap](docs/roadmap.md)
- [Changelog](CHANGELOG.md)

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) — batch CLI, RTF, de-anonymization design (planned).

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
