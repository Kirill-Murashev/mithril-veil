# Release checklist (v0.1.x)

Use this checklist before tagging a release or publishing a GitHub release.

## Quality gates

- [ ] Run `make check` locally (ruff, format check, compileall, pytest — no GLiNER model download)
- [ ] Confirm default CI on `main` is green (see [ci.yml](../.github/workflows/ci.yml))

## Security and repository hygiene

- [ ] No real PII in the tree (names, documents, bank data, passports, INN/SNILS, addresses, reversible mappings)
- [ ] No private user documents or logs committed (`data/private/` stays empty and gitignored)
- [ ] README examples use synthetic data only (`test@example.local`, fake IDs)
- [ ] Do not upload real documents, production logs, or mapping files to the release or CI artifacts

## Smoke tests

- [ ] Docker: `docker compose up --build` starts; `curl http://127.0.0.1:8000/health` returns OK
- [ ] API: `POST /api/v1/anonymize` and `GET /api/v1/presets` behave as documented
- [ ] CLI: `mithril-veil version` prints `0.1.0` (or current version)
- [ ] CLI: `mithril-veil list-presets` lists bundled presets
- [ ] CLI: sample `anonymize-text` / `anonymize-file` with `examples/synthetic_input.txt` succeeds

## Package build (optional before tag)

```bash
python -m pip install build
python -m build
```

- [ ] `dist/` artifacts look correct; do not commit `dist/` (gitignored)

## GitHub release

- [ ] Update `CHANGELOG.md` (move items from Unreleased to version section)
- [ ] Tag: `git tag -a v0.1.0 -m "Mithril Veil 0.1.0"`
- [ ] Push tag: `git push origin v0.1.0`
- [ ] Create GitHub release from tag with notes from `CHANGELOG.md`
- [ ] Attach **no** real documents, customer logs, or private data to the release

## Post-release

- [ ] Verify CI badge and release notes on the repository home page
- [ ] Open a follow-up issue for any known limitations listed in `docs/roadmap.md`
