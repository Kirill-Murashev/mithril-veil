# Security checklist

Use this checklist when changing detection, I/O, logging, CI, or release workflows. See also [SECURITY.md](../SECURITY.md).

## Logging and runtime data

- [ ] Do not log original input text or full document content
- [ ] Do not log raw detected entity values
- [ ] API responses and CLI output use safe `value_preview` (masked, e.g. `***`) only
- [ ] JSON reports never include raw detected values in any field
- [ ] Warnings and error messages do not echo sensitive substrings from user input

## Repository and fixtures

- [ ] Tests and `examples/` use **synthetic** data only
- [ ] No real names, contracts, court files, bank statements, or valuation reports in the repo
- [ ] No reversible mapping files committed (`mapping*.json`, `mapping*.json.enc`, and similar stay gitignored)
- [ ] Report metadata does not embed sensitive filenames or paths from user machines

## CI and automation

- [ ] Default CI ([ci.yml](../.github/workflows/ci.yml)) does **not** install GLiNER or download model weights
- [ ] Default pytest run excludes `integration` tests (no network model fetch in PR checks)
- [ ] CI does not upload artifacts containing raw text, documents, or secrets
- [ ] CI logs do not print environment secrets

## GLiNER and optional ML

- [ ] GLiNER remains optional (`[gliner]` extra); not required for core install or default CI
- [ ] Document that first GLiNER use may download Hugging Face weights; pre-cache for air-gapped hosts
- [ ] Manual [gliner-integration.yml](../.github/workflows/gliner-integration.yml) only via `workflow_dispatch`
- [ ] Natasha/GLiNER outputs are probabilistic — operators must review results

## Private data handling

- [ ] Real documents and mappings live **outside** the repo, or only under `data/private/` (gitignored)
- [ ] Never commit contents of `data/private/`
- [ ] VPS and local operators process files only on infrastructure they control

## Cloud agents and third parties

- [ ] Do not grant cloud coding agents or external automation access to private documents processed by your instance
- [ ] Do not paste real documents into public issues, PRs, or shared CI logs

## Disclosure

- [ ] Report vulnerabilities via [SECURITY.md](../SECURITY.md) (private advisory when available)
