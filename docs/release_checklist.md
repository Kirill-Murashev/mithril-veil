# Release checklist (v0.1.0 release candidate)

Use this checklist before tagging **v0.1.0** or publishing a GitHub release.

## Version consistency

- [ ] `app/__init__.py` `__version__` matches `pyproject.toml` `version` (currently **0.1.0**)
- [ ] `mithril-veil version` and `GET /health` report the same version
- [ ] `CHANGELOG.md` reflects shipped slices; Unreleased section accurate

## Quality gates (local)

Run from a clean venv with `pip install -e ".[dev]"`:

```bash
ruff check app tests
ruff format --check app tests
python -m compileall app
pytest -m 'not integration' -v
make check
python -m build
```

- [ ] `ruff check app tests` — pass
- [ ] `ruff format --check app tests` — pass
- [ ] `python -m compileall app` — pass
- [ ] `pytest -m 'not integration'` — pass (expect **271 passed**, 1 deselected integration test)
- [ ] `make check` — pass (lint + format + compile + pytest)
- [ ] `python -m build` — pass; `dist/` artifacts look correct and are **not** committed (gitignored)

## GitHub Actions

- [ ] Default [ci.yml](../.github/workflows/ci.yml) green on `main` (ruff, format, compileall, pytest)
- [ ] Default CI installs **`.[dev]` only** — no GLiNER extra, no model weight download
- [ ] [gliner-integration.yml](../.github/workflows/gliner-integration.yml) remains **manual** (`workflow_dispatch` only)

## Package metadata

- [ ] `pyproject.toml`: `readme = "README.md"`, Apache-2.0 license, `requires-python >=3.12`
- [ ] Default `dependencies` do not pull GLiNER or Hugging Face weights
- [ ] Optional extras: `[dev]`, `[gliner]` documented and correct

## Documentation review

- [ ] [README.md](../README.md) — install, CLI quickstart, synthetic examples only, limitations (restore/OCR/web UI/format-preserving)
- [ ] [docs/cli_examples.md](cli_examples.md) — synthetic CLI examples current
- [ ] [CHANGELOG.md](../CHANGELOG.md) — accurate for release candidate
- [ ] [SECURITY.md](../SECURITY.md) — mapping, disclosure, no real PII
- [ ] [docs/security_checklist.md](security_checklist.md) — pre-release section current
- [ ] [docs/threat_model.md](threat_model.md) — matches 0.1.x behavior

## Repository hygiene

- [ ] No real PII in tree (names, INN/SNILS, passports, addresses, bank data)
- [ ] No real user documents or production logs committed
- [ ] No `mapping*.json` or `mapping*.json.enc` files committed
- [ ] No passphrases in repo, CI logs, or issues
- [ ] `data/private/` empty and gitignored
- [ ] Examples and tests use synthetic fixtures only (`test@example.local`, public test card numbers)

## Smoke tests

- [ ] `mithril-veil version` prints `0.1.0`
- [ ] `mithril-veil list-presets` lists five bundled presets
- [ ] `mithril-veil anonymize-text` with synthetic string succeeds
- [ ] `mithril-veil anonymize-file --input examples/synthetic_input.txt` succeeds
- [ ] API: `GET /health`, `GET /api/v1/presets`, `POST /api/v1/anonymize` behave as documented
- [ ] Optional: `docker compose up --build` and `curl http://127.0.0.1:8000/health`

## Tag and GitHub release (when approved)

- [ ] Move [CHANGELOG.md](../CHANGELOG.md) items from Unreleased to `[0.1.0]` if not already done
- [ ] Tag: `git tag -a v0.1.0 -m "Mithril Veil 0.1.0"`
- [ ] Push tag: `git push origin v0.1.0`
- [ ] Create GitHub release from tag; notes from `CHANGELOG.md`
- [ ] Attach **no** real documents, customer logs, mapping files, or private data to the release

## Post-release

- [ ] CI badge green on repository home page
- [ ] Track post-v0.1.0 items in [roadmap.md](roadmap.md) (restore implementation, OCR, web UI remain out of scope unless separately approved)
