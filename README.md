# Mithril Veil

![CI](https://github.com/Kirill-Murashev/mithril-veil/actions/workflows/ci.yml/badge.svg)

**Mithril Veil: a self-hosted Russian PII anonymization gateway for safer AI workflows.**

Mithril Veil is an open-source, **local-first** service that detects and anonymizes sensitive information in **Russian-language text and documents** before you send content to cloud LLMs. Run it on your laptop or VPS: preprocessing stays on infrastructure you control, with a public codebase you can audit. It targets lawyers, appraisers, consultants, accountants, and small teams who need self-hosted sanitization instead of uploading raw client material to third-party APIs.

> **Status:** **v0.1.0 release candidate** — feature set for first public alpha is complete; APIs may still evolve before 1.0. See [CHANGELOG.md](CHANGELOG.md) and [docs/release_checklist.md](docs/release_checklist.md).

## Security warnings

- **No real PII in this repository** — do not commit real names, INN/SNILS, passports, addresses, bank data, contracts, or client documents. Use synthetic examples only (`test@example.local`, fake IDs). Do not paste real documents into issues or PRs. See [SECURITY.md](SECURITY.md).
- **Mapping files are highly sensitive** — `pseudonymize` with `--mapping-output` writes encrypted `.json.enc` files that can reverse placeholders. Treat them like key material; never commit them or attach them to issues.
- **Restore / de-anonymization is not implemented** — design only: [docs/restore_workflow_design.md](docs/restore_workflow_design.md). There is no restore CLI and no API restore endpoint.
- **Not implemented in 0.1.x:** OCR, web UI, format-preserving DOCX/PDF/RTF/ODT output, API file upload, server-side mapping storage, batch `pseudonymize`.

## Features (0.1.0)

- FastAPI HTTP API: health, presets, text anonymization
- **CLI** for inline text, stdin, single files, and batch directories with safe JSON reports
- **Document I/O:** `.txt`, `.md`, `.markdown`, `.docx`, `.odt`, `.rtf`, text-based `.pdf` (plain-text output; formatting not preserved)
- Deterministic regex/checksum detectors: email, phone, INN, SNILS, passport, OGRN/OGRNIP, KPP, BIK, bank/correspondent accounts, cards (Luhn), cadastral/court/contract numbers, IP, URL, Telegram handles
- **Optional Natasha NER** (PERSON, ORGANIZATION, LOCATION) and **optional GLiNER** zero-shot labels — disabled by default; review probabilistic results
- **Policy presets:** `general_ru`, `legal_ru`, `valuation_ru`, `banking_ru`, `court_case_ru`
- Modes: `replace`, `redact`, `pseudonymize` (reversible with CLI-only encrypted mapping)
- API/CLI never expose original detected values (`value_preview` is always `***`)

See the [threat model](docs/threat_model.md) for trust boundaries and residual risks.

## Requirements

- Python 3.12+

## Installation (local / self-hosted)

```bash
git clone https://github.com/Kirill-Murashev/mithril-veil.git
cd mithril-veil
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Optional GLiNER (local inference; may download Hugging Face weights on first use):
# pip install -e ".[dev,gliner]"
cp .env.example .env   # optional
```

Run the API on `127.0.0.1` for local use, or deploy to a VPS you control ([deployment guide](docs/deployment_vps.md)). No cloud LLM calls are made by the service.

## CLI quickstart

After `pip install -e ".[dev]"`, the `mithril-veil` command is available. Full synthetic examples: [docs/cli_examples.md](docs/cli_examples.md).

```bash
mithril-veil version
mithril-veil list-presets

# Inline text
mithril-veil anonymize-text \
  --text "Контакт: test@example.local, ИНН 7701010017" \
  --mode replace \
  --preset general_ru

# Stdin
echo "Контакт: test@example.local" | mithril-veil anonymize-stdin --mode replace

# Single file + safe report
mithril-veil anonymize-file \
  --input examples/synthetic_input.txt \
  --output /tmp/anonymized.txt \
  --mode replace \
  --report /tmp/report.json

# Batch directory (replace/redact only)
mithril-veil anonymize-dir ./documents \
  --output-dir ./sanitized \
  --mode replace \
  --report ./batch-report.json
```

### Pseudonymize and encrypted mapping

**Warning:** `pseudonymize` is **reversible** if you keep the mapping file and passphrase. For irreversible sanitization before a cloud LLM, use `replace` or `redact`. Mapping files must not be committed or uploaded to issue trackers.

```bash
export MITHRIL_VEIL_MAPPING_PASSPHRASE="your-local-secret-only"
mithril-veil anonymize-file \
  --input examples/synthetic_input.txt \
  --output /tmp/pseudonymized.txt \
  --mode pseudonymize \
  --mapping-output /tmp/mapping.json.enc \
  --report /tmp/report.json
```

- `--mapping-output` must end with `.json.enc`; path must differ from input, output, and report
- HTTP API never writes or returns mapping data
- Batch `anonymize-dir` does **not** support `pseudonymize` or `--mapping-output`

## Supported and unsupported inputs

| Supported input | Notes |
|-----------------|-------|
| `.txt`, `.md`, `.markdown` | UTF-8 text |
| `.docx` | Plain text via `python-docx` |
| `.odt` | Plain text from ZIP `content.xml` (no embedded objects) |
| `.rtf` | Plain text via `striprtf` (no embedded objects) |
| `.pdf` | Text-based PDF only via `pypdf` (no OCR) |

| Output | Plain sanitized `.txt` / `.md` / `.markdown` only |

| Not supported | |
|---------------|---|
| OCR, image-only or encrypted PDFs | |
| Format-preserving DOCX/PDF/RTF/ODT | |
| Embedded RTF/ODT objects as extracted content | |
| Web UI, API file upload, API restore | |
| Batch `pseudonymize` or batch mapping | |

Limits: 10 MB max input; 50 PDF pages max; ODT `content.xml` 8 MB cap with compression-ratio guard. CLI refuses to overwrite the input file (`--output` must differ from `--input`).

## HTTP API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health and version |
| GET | `/api/v1/presets` | Bundled preset metadata |
| POST | `/api/v1/anonymize` | Anonymize JSON body (`replace`, `redact`, `pseudonymize`) |

No file-upload endpoint. No restore endpoint. Responses mask all detected values (`value_preview`: `"***"`).

```bash
uvicorn app.main:app --reload
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/api/v1/anonymize \
  -H "Content-Type: application/json" \
  -d '{"text":"Контакт: test@example.local","mode":"replace"}'
```

## Detectors and checksums

| Area | Behavior |
|------|----------|
| INN / SNILS | Checksum validation; weak candidates with context keywords |
| OGRN / OGRNIP | Valid checksum required |
| BANK_ACCOUNT / CORRESPONDENT_ACCOUNT | Checksum when BIK nearby (~120 chars); keyword context for settlement accounts |
| CARD_NUMBER | Luhn-valid 13–19 digits; rejects all-identical digit strings |
| BIK | Regex only (no directory validation) |
| Natasha / GLiNER | Optional; probabilistic — review output |

Priority span merger prefers deterministic identifiers over NER/GLiNER spans.

## Docker

```bash
docker compose up --build -d
curl -s http://127.0.0.1:8000/health
```

Service listens on port **8000**.

## Development

```bash
make check          # ruff + format check + compileall + pytest (no GLiNER download)
make run-api
python -m build     # dist/ is gitignored
```

Individual gates:

```bash
ruff check app tests
ruff format --check app tests
python -m compileall app
pytest -m 'not integration' -v
```

Default CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs the same checks without GLiNER. Optional GLiNER integration tests: manual [`.github/workflows/gliner-integration.yml`](.github/workflows/gliner-integration.yml).

## Documentation

- [CLI examples (synthetic)](docs/cli_examples.md)
- [Architecture](docs/architecture.md)
- [Threat model](docs/threat_model.md)
- [Russian PII taxonomy](docs/pii_taxonomy_ru.md)
- [Restore workflow design (no implementation)](docs/restore_workflow_design.md)
- [Release checklist](docs/release_checklist.md)
- [Security checklist](docs/security_checklist.md)
- [VPS deployment](docs/deployment_vps.md)
- [Roadmap](docs/roadmap.md)
- [Changelog](CHANGELOG.md)

## Roadmap

See [docs/roadmap.md](docs/roadmap.md). Post-v0.1.0: restore implementation (if approved), OCR, web UI, and format-preserving output remain **out of scope** unless separately approved and threat-modeled.

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
