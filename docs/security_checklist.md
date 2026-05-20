# Security checklist

Use this checklist when changing detection, I/O, logging, mapping, CI, or release workflows. See also [SECURITY.md](../SECURITY.md) and the [threat model](threat_model.md).

## API, CLI output, and reports

- [ ] Do not log original input text or full document content
- [ ] Do not log raw detected entity values
- [ ] API responses and CLI entity listings use safe `value_preview` only — **`value_preview == "***"`** always
- [ ] JSON reports never include raw detected values in any field
- [ ] Warnings and error messages do not echo sensitive substrings from user input
- [ ] Mapping passphrases never appear in logs, stdout, stderr, or exception messages
- [ ] Batch aggregate reports contain counts and safe metadata only — no raw text or per-entity values

## Repository and fixtures

- [ ] Tests and `examples/` use **synthetic** data only
- [ ] No real names, contracts, court files, bank statements, or valuation reports in the repo
- [ ] No reversible mapping files committed (`mapping*.json`, `mapping*.json.enc` stay gitignored)
- [ ] Report metadata does not embed sensitive filenames or paths from user machines
- [ ] No passphrases in repo, issues, PRs, or CI configuration

## CI and automation

- [ ] Default CI ([ci.yml](../.github/workflows/ci.yml)) does **not** install GLiNER or download model weights
- [ ] Default pytest run excludes `integration` tests (`pytest -m 'not integration'` / `addopts` in `pyproject.toml`)
- [ ] CI does not upload artifacts containing raw text, documents, or secrets
- [ ] CI logs do not print `MITHRIL_VEIL_MAPPING_PASSPHRASE` or other secrets
- [ ] Manual [gliner-integration.yml](../.github/workflows/gliner-integration.yml) only via `workflow_dispatch`

## GLiNER and optional ML

- [ ] GLiNER remains optional (`[gliner]` extra); not required for core install or default CI
- [ ] Document that first GLiNER use may download Hugging Face weights; pre-cache for air-gapped hosts
- [ ] Natasha/GLiNER outputs are probabilistic — operators must review results

## Document parsers

- [ ] Document parser errors are safe (no raw document/XML/RTF content in messages)
- [ ] RTF: plain-text extraction only; no embedded object/image extraction as a product feature
- [ ] ODT: `content.xml` text only; draw/image/object subtrees skipped; zip-bomb guards active
- [ ] DOCX/PDF: plain-text extraction; no format-preserving output

## Private data handling

- [ ] Real documents and mappings live **outside** the repo, or only under `data/private/` (gitignored)
- [ ] Never commit contents of `data/private/`
- [ ] VPS and local operators process files only on infrastructure they control

## Batch CLI (`anonymize-dir`)

- [ ] Batch supports **replace** and **redact** only; reject `pseudonymize` and `--mapping-output`
- [ ] Output directory must not equal or sit inside the input directory (resolved paths)
- [ ] Symlinked files skipped; symlinked directories not traversed
- [ ] Hidden path segments skipped unless `--include-hidden`
- [ ] Duplicate output targets rejected before processing; `--report` not inside input or equal to an output path
- [ ] Aggregate batch report contains no raw text or detected values; deterministic file entry ordering
- [ ] Unsupported extensions are skipped with safe warnings only; exit code `1` if any file failed

## Restore, API scope, and out-of-scope features

- [ ] [restore_workflow_design.md](restore_workflow_design.md) exists; **no restore implementation** in 0.1.x
- [ ] No restore CLI, batch restore, or **API restore endpoint**
- [ ] **OCR** not implemented (image-only PDFs unsupported)
- [ ] **Web UI** not implemented
- [ ] **Format-preserving** DOCX/PDF/RTF/ODT output not implemented

## Cloud agents and third parties

- [ ] Do not grant cloud coding agents or external automation access to private documents processed by your instance
- [ ] Do not paste real documents into public issues, PRs, or shared CI logs
- [ ] Do not attach `.json.enc` mapping files or passphrases to issues or chat

## Reversible mapping / pseudonymization checklist

Use when touching `pseudonymize` mode, `app/core/mapping.py`, `app/security/encrypted_mapping.py`, or CLI mapping flags.

- [ ] Mapping output is **CLI-only** (no API field to write or return mapping files)
- [ ] Mapping file is written only when the user passes explicit `--mapping-output`
- [ ] Mapping output path must end with **`.json.enc`** (`require_encrypted_mapping_path`)
- [ ] Mapping write requires passphrase env (`MITHRIL_VEIL_MAPPING_PASSPHRASE` or `--mapping-passphrase-env`)
- [ ] Mapping overwrite is refused unless **`--force`**
- [ ] Mapping path must not equal **input**, **output**, or **report** path when applicable (`ensure_mapping_path_distinct`)
- [ ] JSON reports expose only **`mapping.written`** and **`mapping.encrypted`** — never placeholder→original pairs
- [ ] API responses do not include `mapping`, `mapping_metadata`, `placeholder_to_original`, or `original_to_placeholder`
- [ ] No raw placeholder→original pairs in stdout, stderr, errors, or reports
- [ ] `mapping*.json` and `mapping*.json.enc` remain in `.gitignore`
- [ ] Wrong passphrase raises safe error (no passphrase or raw values in message) — see `MappingPassphraseInvalid`
- [ ] Tampered ciphertext fails decrypt safely — covered in `tests/test_encrypted_mapping.py`
- [ ] Regression tests still pass:
  - Missing passphrase env — `tests/test_mapping_hardening.py`
  - Invalid suffix (not `.json.enc`) — `tests/test_mapping_hardening.py`, `tests/test_encrypted_mapping.py`
  - Existing mapping file without `--force` — CLI and encrypted_mapping tests
  - Wrong passphrase / tampered ciphertext — `tests/test_encrypted_mapping.py`, `tests/test_mapping_hardening.py`
  - No raw leakage in API/CLI/report — `tests/test_mapping_hardening.py`, `tests/test_anonymizer.py`, `tests/test_cli.py`
- [ ] Production path uses **`app/security/encrypted_mapping.py` only** (no duplicate `mapping_io` writer)

## Before release (v0.1.0 RC)

- [ ] Run `make check` (or equivalent: ruff, compileall, pytest with default markers)
- [ ] Confirm default CI workflow still excludes `integration` tests and does not install `[gliner]`
- [ ] Grep or review that no known **synthetic** raw tokens were accidentally copied into generated report/log fixtures in the repo
- [ ] Confirm no real PII in repository (manual spot-check of new tests/docs/examples)
- [ ] Verify [README.md](../README.md) and [SECURITY.md](../SECURITY.md) warnings match current behavior (pseudonymize reversible, mapping CLI-only, restore not implemented, GLiNER optional)
- [ ] Verify [threat_model.md](threat_model.md) reflects security-relevant behavior for 0.1.x
- [ ] Version strings consistent (`app/__version__`, `pyproject.toml`, release notes)

## Disclosure

- [ ] Report vulnerabilities via [SECURITY.md](../SECURITY.md) (private advisory when available)
