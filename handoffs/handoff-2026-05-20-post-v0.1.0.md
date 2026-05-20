# Handoff — Mithril Veil — Post v0.1.0 — 2026-05-20

> **Supersedes for future context:** [handoff-2026-05-20-post-slice-16.md](handoff-2026-05-20-post-slice-16.md) and earlier handoff archives. Those files are **not deleted**; use **this document** as the current baseline after the **v0.1.0** release.

---

## 1. Project identity

| Field | Value |
|-------|-------|
| **Project** | Mithril Veil |
| **Repository** | https://github.com/Kirill-Murashev/mithril-veil |
| **License** | Apache License 2.0 |
| **Released version** | **`0.1.0`** (package metadata unchanged on `main` until next version bump) |
| **Branch** | `main` |
| **Status** | **v0.1.0 released** — annotated tag pushed; **no GitHub Release page** created in the release-execution slice |

**Tagline:** *Mithril Veil: a self-hosted Russian PII anonymization gateway for safer AI workflows.*

---

## 2. Release record

| Item | Value |
|------|--------|
| **Tag** | `v0.1.0` (annotated) |
| **Tag message** | `Release v0.1.0` |
| **Tagged commit** | `f379872fbd2df803bff1ed4b33c04f4f9d6fc01a` (`f379872`) |
| **Commit subject** | Fix release decision note HEAD after CHANGELOG CI |
| **CHANGELOG** | `[0.1.0] - 2026-05-20` finalized; `[Unreleased]` empty for future work |
| **GitHub Release page** | **Not created** (tag visible on GitHub; optional Release notes remain a maintainer task) |

Pre-tag verification: [docs/release_decision_note_v0.1.0.md](../docs/release_decision_note_v0.1.0.md).

---

## 3. Current baseline (post-housekeeping)

| Item | Status |
|------|--------|
| **HEAD / origin/main** | Synced at housekeeping commit (after `f379872`) |
| **Package version** | `0.1.0` in `app/__init__.py`, `pyproject.toml` |
| **Working tree** | Clean after housekeeping commit |

**Last known gates (at tag time, `f379872`):**

| Gate | Result |
|------|--------|
| `ruff check app tests` | Pass |
| `ruff format --check app tests` | Pass |
| `python -m compileall app` | Pass |
| `pytest -m 'not integration'` | **271 passed**, 1 deselected |
| `make check` | Pass |
| `python -m build` | Pass — `mithril_veil-0.1.0` sdist + wheel |

**Last known CI:** success on `f379872` — GitHub Actions run [26186973616](https://github.com/Kirill-Murashev/mithril-veil/actions/runs/26186973616).

---

## 4. Housekeeping slice (this document)

**Goal:** Post-release documentation only — no feature implementation, no version bump, no new tag.

**Files updated (typical):**

- [README.md](../README.md) — status: v0.1.0 released
- [docs/roadmap.md](../docs/roadmap.md) — released 0.1.0; v0.1.1 / v0.2.0 / design-only sections
- [docs/TODO.md](../docs/TODO.md) — shipped v0.1.0; ranked backlog
- [handoffs/handoff-2026-05-20-post-v0.1.0.md](handoff-2026-05-20-post-v0.1.0.md) — this file

**Not changed:** application code, `pyproject.toml` version, `CHANGELOG.md` structure (unless a factual fix was required), CI workflows.

---

## 5. Security and product constraints (unchanged)

| Rule | Detail |
|------|--------|
| No real PII / documents in repo | Synthetic fixtures only |
| `value_preview` | Always **`"***"`** in API/reports |
| Mapping | CLI-only, encrypted `.json.enc`; never in API responses |
| Batch | `anonymize-dir`: `replace`/`redact` only |
| Restore | **Design only** — [restore_workflow_design.md](../docs/restore_workflow_design.md) |
| GLiNER | Optional extra; **default CI must not download weights** |
| Out of scope without re-scope | Restore impl, web UI, OCR, API file upload, API restore, batch `pseudonymize` |

---

## 6. Recommended next slices (ranked)

1. **GitHub Release notes (optional)** — Publish a Release from tag `v0.1.0` using `CHANGELOG.md` `[0.1.0]`; still no product code changes.
2. **v0.1.1 patch/hardening planning** — NER/GLiNER tuning, docs/CI maintenance, small detector tweaks; one vertical slice at a time.
3. **v0.2.0 scoped feature planning** — e.g. HTTP upload, audit log, Helm; requires threat-model update per item.

**Do not start** restore implementation, web UI, OCR, API upload/restore, batch pseudonymize, or broad architecture rewrites **without explicit maintainer re-scope** and an updated threat model.

---

## 7. New-chat prompt (copy-paste)

```text
You are the architect for Mithril Veil (self-hosted Russian PII anonymization).

Repository: https://github.com/Kirill-Murashev/mithril-veil

Read first: handoffs/handoff-2026-05-20-post-v0.1.0.md

Baseline: v0.1.0 RELEASED — tag v0.1.0 at f379872; package version 0.1.0; CHANGELOG [0.1.0] shipped; [Unreleased] empty. No GitHub Release page unless maintainer adds one. Security invariants unchanged (value_preview ***, mapping CLI-only .json.enc, no restore/OCR/web UI/API upload in 0.1.x unless re-scoped).

Next work: optional GitHub Release notes, then v0.1.1 hardening or v0.2.0 planning — one small slice only. Do not implement restore, web UI, OCR, API upload/restore, or batch pseudonymize without explicit re-scope.
```

---

## 8. Handoff lineage

| File | Status |
|------|--------|
| `handoff-2026-05-20-post-slice-16.md` | **Superseded** (pre-tag RC) |
| `handoff-2026-05-20-post-v0.1.0.md` | **Current** — post-release |

Create the next handoff after a shipped slice, version bump, threat-model change, or when chat context is ~70% full.
