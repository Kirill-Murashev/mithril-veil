# Release decision note — v0.1.0

**Date:** 2026-05-20  
**Slice:** Release-planning / maintainer-readiness verification (no tag cut)

## Baseline verification

| Check | Result |
|-------|--------|
| Working tree before slice | Clean |
| `git fetch origin --prune --tags` | Succeeded |
| Local `HEAD` | `f32ca47` — Add post-slice 16 project handoff |
| `origin/main` | `f32ca47` (matches local `main`) |
| RC code baseline (handoff) | `3f3b6be` — Prepare v0.1.0 release candidate hygiene (parent of handoff commit) |
| Recent chain | `f32ca47` → `3f3b6be` → `3baab02` → `a46d60e` → … |

**Handoff vs repository:** [handoffs/handoff-2026-05-20-post-slice-16.md](../handoffs/handoff-2026-05-20-post-slice-16.md) records `HEAD` / `origin/main` as `3f3b6be`. The repository is one commit ahead: `f32ca47` adds only that handoff document (no application code change). Treat `3f3b6be` as the RC **code** baseline and `f32ca47` as the current **documentation** tip on `main`.

## Tag status

| Location | `v0.1.0` tag |
|----------|----------------|
| Local | **Does not exist** (`git tag --list "v0.1.0"` empty) |
| Remote `origin` | **Does not exist** (`git ls-remote --tags origin refs/tags/v0.1.0` empty) |

## Version consistency

| Source | Version | RC wording |
|--------|---------|------------|
| `app/__init__.py` | `0.1.0` | — |
| `pyproject.toml` | `0.1.0` | — |
| `mithril-veil version` | `0.1.0` | — |
| `README.md` | — | **v0.1.0 release candidate** |
| `docs/roadmap.md` | — | **0.1.0 (release candidate — current)** |
| `docs/TODO.md` | — | Shipped (0.1.0 RC); tag pending maintainer decision |
| `docs/release_checklist.md` | — | v0.1.0 release candidate |
| `CHANGELOG.md` | `[0.1.0] - 2026-05-20` section present; **Slices 14–16 remain under `[Unreleased]`** | Accurate for pre-tag RC; maintainer should move Unreleased entries when tagging (per release checklist) |

No version-metadata contradictions found. Pre-tag CHANGELOG housekeeping is expected at tag time, not a blocker for this verification slice.

## Local quality gates

Run from project venv (`pip install -e ".[dev]"`):

| Gate | Result |
|------|--------|
| `ruff check app tests` | **Pass** |
| `ruff format --check app tests` | **Pass** |
| `python -m compileall app` | **Pass** |
| `pytest -m "not integration"` | **Pass** — 271 passed, 1 deselected |
| `make check` | **Pass** |
| `python -m build` | **Pass** — `mithril_veil-0.1.0.tar.gz`, `mithril_veil-0.1.0-py3-none-any.whl` |

Smoke (CLI): `mithril-veil version` → `0.1.0`; `list-presets` → five bundled presets.

## GitHub Actions verification

`gh` available and authenticated.

| Item | Result |
|------|--------|
| Latest `main` CI run | **Success** — run [26183860141](https://github.com/Kirill-Murashev/mithril-veil/actions/runs/26183860141) for commit `f32ca47` (“Add post-slice 16 project handoff”) |
| Job | `test (3.12)` — ruff, format, compileall, pytest — **passed** (~28s) |
| Prior runs on `main` | Success through `3f3b6be` and earlier RC chain |
| Failed log review | Not required (no failures on latest run) |

**Default CI ([.github/workflows/ci.yml](../.github/workflows/ci.yml)):** `pip install -e ".[dev]"` only — no `[gliner]` extra, no model weight download. Pytest uses `addopts = -q -m 'not integration'` in `pyproject.toml`, so integration tests are excluded even though the workflow invokes `pytest -v` without an explicit marker.

**GLiNER integration ([.github/workflows/gliner-integration.yml](../.github/workflows/gliner-integration.yml)):** `workflow_dispatch` only — not triggered on push/PR.

## Documentation review

Reviewed for RC consistency: `README.md`, `CHANGELOG.md`, `SECURITY.md`, `docs/security_checklist.md`, `docs/release_checklist.md`, `docs/roadmap.md`, `docs/TODO.md`, `pyproject.toml`, `app/__init__.py`, controlling handoff.

- Project documented as **v0.1.0 release candidate**; tag/release called out as maintainer next step.
- Restore, OCR, web UI, API file upload, API restore, and batch `pseudonymize` documented as **out of scope / not implemented**.
- GLiNER optional; default CI must not download weights — matches workflow and docs.
- `docs/release_checklist.md` steps exercised where applicable; checklist items not marked `[x]` in-repo (maintainer may tick at tag time).

No documentation-only corrections required beyond this note.

## Security / hygiene audit

Targeted review (`git grep`, `git ls-files`, app/API scan):

| Invariant | Finding |
|-----------|---------|
| No real PII in tree | **OK** — synthetic fixtures (`test@example.local`, `tests/conftest.py`); public test PAN `4111 1111 1111 1111` only in synthetic test constants |
| No real documents committed | **OK** — no client PDF/DOCX/ODT/RTF in tracked files |
| No mapping files committed | **OK** — only code modules (`app/core/mapping.py`, `app/security/encrypted_mapping.py`); `mapping*.json.enc` gitignored; no `mapping*.json.enc` in `git ls-files` |
| No passphrases/secrets in repo | **OK** — env-var design; test passphrases are synthetic (`synthetic-test-passphrase-only`, etc.) |
| `value_preview` always `***` | **OK** — `app/core/schemas.py`, `app/core/entities.py`, `app/core/anonymizer.py`; tests assert `***` |
| No restore implementation | **OK** — design doc only; `decrypt_encrypted_mapping` for tests/local crypto; no restore CLI/API |
| No API restore / file upload | **OK** — `app/api/` has health, presets, anonymize text only |
| No OCR / web UI | **OK** — PDF path raises “OCR is not implemented”; no web UI code |
| No batch pseudonymize | **OK** — `anonymize-dir` rejects `pseudonymize` / `--mapping-output` |
| Mapping CLI-only, encrypted | **OK** — `.json.enc` suffix enforced; API does not write mappings |

Conservative interpretation: no accidental sensitive artifacts requiring remediation.

## Explicit scope statement

**This slice does not cut or push the `v0.1.0` tag.** No GitHub release was created.

---

## Maintainer decision

Choose one:

### A. Approve tagging v0.1.0

All verification above is acceptable. Before tagging, the maintainer should:

1. Move `[Unreleased]` entries in `CHANGELOG.md` into the `[0.1.0]` section (or finalize release notes as desired).
2. Re-confirm latest `main` CI is green in the GitHub UI if any commits land after this note.

**Commands for maintainer only (do not run as part of this slice):**

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

Then publish GitHub release notes from `CHANGELOG.md` (separate maintainer action).

### B. Hold release pending listed issues

Use if any of the following is unacceptable:

- Pre-tag `CHANGELOG.md` Unreleased vs `[0.1.0]` section layout
- Need explicit sign-off on handoff `HEAD` narrative (`3f3b6be` vs `f32ca47`)
- Any new commits or CI regressions after this verification date

*No blocking product or security defects were found in this slice.*

### C. Re-run checks after new commits

Required if application code, dependencies, CI workflows, or security-sensitive docs change after `f32ca47`. Re-run [docs/release_checklist.md](release_checklist.md) and update or supersede this note.

---

## Slice recommendation

**Ready for explicit maintainer-approved tagging (Option A)** — local gates and `main` CI pass on `457a5e3`; `CHANGELOG.md` finalized for v0.1.0; version metadata and security/hygiene audit clean; `v0.1.0` tag absent. Final approval remains with the maintainer before tag push and GitHub release notes.

---

## Post-push confirmation (2026-05-20)

| Item | Result |
|------|--------|
| Pushed commit | `ecccffe` — Add v0.1.0 release decision note |
| `HEAD` / `origin/main` | Both **`ecccffe`** after push |
| CI on pushed commit | **Success** — run [26185928738](https://github.com/Kirill-Murashev/mithril-veil/actions/runs/26185928738), `head_sha` `ecccffe55b1f8955265a172789fc718f46883a63`, job `test (3.12)` ~28s |
| Prior CI (pre-push) | Success on `f32ca47` — run [26183860141](https://github.com/Kirill-Murashev/mithril-veil/actions/runs/26183860141) |
| `v0.1.0` tag (local / remote) | **Still absent** |
| Tag or GitHub release created | **No** |

**Maintainer:** Tagging `v0.1.0` and publishing a GitHub release remain separate, explicit approvals. This slice pushed the decision note and confirmed CI on `ecccffe` only.

---

## Final pre-tag confirmation (2026-05-20)

| Item | Result |
|------|--------|
| CHANGELOG finalization commit | `457a5e3` — Finalize CHANGELOG for v0.1.0 pre-tag release |
| `CHANGELOG.md` | `[Unreleased]` empty; all RC entries under `[0.1.0] - 2026-05-20` |
| `HEAD` / `origin/main` | **`56ca3f6`** (decision-note update after CHANGELOG); CHANGELOG push at **`457a5e3`** |
| CI on CHANGELOG commit (`457a5e3`) | **Success** — run [26186839511](https://github.com/Kirill-Murashev/mithril-veil/actions/runs/26186839511), job `test (3.12)` ~39s |
| CI on current tip (`56ca3f6`) | **Success** — run [26186907884](https://github.com/Kirill-Murashev/mithril-veil/actions/runs/26186907884), job `test (3.12)` ~42s |
| `v0.1.0` tag (local / remote) | **Still absent** |
| GitHub release | **Not created** |

**Maintainer decision still required** before `git tag -a v0.1.0` and `git push origin v0.1.0`. Publish GitHub release notes from `CHANGELOG.md` `[0.1.0]` after tagging.
