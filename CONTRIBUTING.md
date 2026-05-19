# Contributing to Mithril Veil

Thank you for helping improve a self-hosted Russian PII anonymization tool.

## Before you start

- Read [SECURITY.md](SECURITY.md): **never** commit real PII or real documents
- Use synthetic fixtures in tests only
- Prefer small, focused pull requests

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Quality checks

```bash
ruff check app tests
ruff format app tests
pytest
```

## Pull requests

- Describe the problem and approach
- Include tests for behavior changes
- Confirm no real personal data is included

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
