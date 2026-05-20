# Threat model — Mithril Veil (0.1.x)

This document describes security-relevant assets, trust boundaries, threats, mitigations, and residual risks for Mithril Veil after **Slice 8 / 8.1** (reversible `pseudonymize` mode and encrypted CLI mapping). It is intended for operators, contributors, and security reviewers.

**Related documents:** [SECURITY.md](../SECURITY.md), [security_checklist.md](security_checklist.md), [architecture.md](architecture.md).

---

## 1. Project scope

Mithril Veil is **local-first preprocessing** for Russian text and documents before content is sent to cloud LLMs or other third-party tools. Typical deployment: CLI on a workstation, or self-hosted FastAPI on a VPS under the operator’s control.

**What it is:**

- A detection + anonymization/sanitization pipeline with optional reversible pseudonymization (CLI-only encrypted mapping).
- An aid to **reduce exposure risk** when using external AI services.

**What it is not:**

- A full **Data Loss Prevention (DLP)** platform or enterprise DLP agent.
- A **legal compliance** guarantee (152-FZ, GDPR, sector rules, etc.).
- Proof of **irreversible** anonymization or formal privacy (k-anonymity, differential privacy).
- A substitute for organizational policies, access control, or legal review.

**Mode semantics (critical):**

| Mode | Reversible? | Notes |
|------|-------------|-------|
| `replace` | No (by design for mapping) | Typed placeholders; no mapping file |
| `redact` | No | Constant `[REDACTED]` |
| `pseudonymize` | **Yes** if mapping is kept | Same placeholders as `replace`; optional encrypted `.json.enc` on CLI |

Users who need **irreversible** sanitization before a cloud LLM must use `replace` or `redact`, not `pseudonymize`, and must not retain mapping files.

---

## 2. Assets

| Asset | Sensitivity | Where it lives | Notes |
|-------|-------------|----------------|-------|
| Raw input text/documents | **Critical** | Process memory, stdin, API request body, temp read buffers | Never logged or returned by API |
| Detected PII spans (internal) | **Critical** | In-memory `DetectedEntity.text` | Stripped before API/report serialization |
| Sanitized output text | **High** | stdout, `--output` files, API `text` field | May still contain **undetected** sensitive data |
| Safe JSON reports | **Medium** | `--report` files | No raw values; may reveal counts, types, structure |
| Encrypted mapping files (`.json.enc`) | **Critical** | Local filesystem (CLI only) | Reversible with passphrase |
| Mapping passphrases | **Critical** | Environment variables, operator secret stores | Never in repo, logs, or API |
| Preset YAML (`app/presets/`) | **Low** | Repository | Policy configuration, not user data |
| Logs / stdout / stderr | **High** | Terminal, container logs, CI | Must not contain raw spans or passphrases |
| Natasha / GLiNER model weights | **Medium** | Local cache (optional) | Downloaded only when NER/GLiNER enabled |
| Test fixtures | **Low** (if synthetic) | `tests/`, `examples/` | Must remain synthetic only |
| Build artifacts (`dist/`) | **Low** | Local/CI | Gitignored |

---

## 3. Trust boundaries

```text
┌─────────────────────────────────────────────────────────────────┐
│ Operator host (VPS or workstation)                              │
│  ┌──────────────┐    ┌─────────────────────────────────────┐   │
│  │ CLI process  │    │ FastAPI (optional)                   │   │
│  │  boundary    │    │  HTTP request/response boundary      │   │
│  └──────┬───────┘    └──────────────┬──────────────────────┘   │
│         │                            │                          │
│         ▼                            ▼                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Document I/O (read .txt/.md/.docx/.pdf)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Detectors: regex (always) | Natasha | GLiNER (optional)   │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Anonymizer + optional in-memory mapping (pseudonymize)    │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                       │
│         ├──► safe stdout / output file / API JSON               │
│         ├──► safe report JSON                                   │
│         └──► optional .json.enc (CLI + explicit path only)      │
│              ▲ passphrase env boundary                          │
└──────────────┼──────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ External (untrusted from MV’s perspective)                       │
│  • Cloud LLM APIs (operator sends sanitized text — out of band) │
│  • Hugging Face (only if GLiNER installed and run — model fetch) │
│  • GitHub / CI (public repo; must not receive real PII)         │
└──────────────────────────────────────────────────────────────────┘
```

| Boundary | Crosses with | Trust assumption |
|----------|--------------|----------------|
| **CLI local process** | User shell, filesystem | Operator controls host; CLI is not sandboxed from user data |
| **FastAPI request/response** | HTTP clients on network | TLS + network isolation recommended in production |
| **Document I/O** | User-selected paths | Malformed/large files bounded by size/page limits |
| **Natasha / GLiNER** | Local ML libraries | Probabilistic; no document sent to cloud LLM by MV |
| **Local filesystem** | Input, output, report, mapping paths | Path validation and overwrite guards |
| **Mapping file** | `.json.enc` on disk | Encrypted; still highly sensitive |
| **Passphrase env** | `MITHRIL_VEIL_MAPPING_PASSPHRASE` (or custom) | Process environment visible to same-user attackers |
| **CI / test** | GitHub Actions, pytest | Synthetic data only; integration tests off by default |
| **Future VPS deployment** | Reverse proxy, TLS, secrets | See [deployment_vps.md](deployment_vps.md) |

---

## 4. Main threat scenarios

| # | Threat | Impact | Likelihood (qualitative) |
|---|--------|--------|---------------------------|
| T1 | Real PII committed to git (tests, docs, fixtures) | Permanent public exposure | Medium (human error) |
| T2 | Raw PII written to application or container logs | Exposure via log aggregation | Medium |
| T3 | Raw detected values in API JSON | Downstream systems store secrets | Medium if regression |
| T4 | Raw values in CLI JSON report | Report files leaked | Medium if regression |
| T5 | Raw values in stdout/stderr/errors | Terminal scrollback, CI logs | Medium if regression |
| T6 | Mapping file committed or attached to issue | Full reversible mapping exposure | Medium |
| T7 | Mapping passphrase in repo, `.env` commit, or chat | Decrypt all mapping files | Medium |
| T8 | Encrypted mapping file exfiltrated (backup, sync, malware) | Re-identification if passphrase also obtained | Medium |
| T9 | User assumes `pseudonymize` is irreversible | Sends “sanitized” text to LLM while retaining mapping elsewhere; or false sense of safety | High (misuse) |
| T10 | Wrong mode/preset; cloud LLM receives unsanitized input | Direct PII leakage to third party | High (operational) |
| T11 | GLiNER downloads model weights unexpectedly | Network egress, supply-chain surface | Low if optional install only |
| T12 | Malicious or malformed document (zip bomb, parser bugs) | DoS, possible parser vulnerabilities | Low–Medium |
| T13 | Image-only PDF treated as empty/safe text | User believes document was sanitized | Medium (misunderstanding) |
| T14 | Path overwrite/collision (output = input, mapping = report) | Data loss or wrong artifact overwritten | Low (mitigated in 8.1) |
| T15 | CI runs integration tests → downloads GLiNER weights | Unwanted network, non-reproducible CI | Low (mitigated) |
| T16 | Undetected entities remain in “sanitized” output | Quasi-identifiers, names without NER, free-text facts | **High** (inherent) |
| T17 | NER false negatives / false positives | Missed PII or over-redaction | Medium |
| T18 | Self-hosted API exposed without TLS/auth | Network adversary reads submissions | Medium (deployment) |
| T19 | Batch output directory inside input tree | Re-processing sanitized files on later runs | Low (mitigated: path rejection) |

---

## 5. Existing mitigations

| Threat area | Mitigation (current) |
|-------------|----------------------|
| T1 | `SECURITY.md`, contributor culture, synthetic fixtures; `.gitignore` for `mapping*.json*` |
| T2–T5 | No raw logging policy; `value_preview` forced to `***`; `entity_to_api_dict`; safe report builder; tests in `test_anonymizer.py`, `test_cli.py`, `test_mapping_hardening.py` |
| T6–T7 | Gitignore patterns; docs; no mapping in API; passphrase from env only |
| T8 | PBKDF2 (600k iter) + Fernet; `.json.enc` only; operator filesystem permissions (operational) |
| T9–T10 | Docs (this file, README, SECURITY); mode names; presets; operator training |
| T11 | GLiNER optional extra; disabled in bundled presets; default CI skips integration |
| T12 | `MAX_INPUT_FILE_BYTES` (10 MB), `MAX_PDF_PAGES` (50); typed exceptions |
| T13 | `EmptyExtractedText` / rejection for image-only PDF; no OCR |
| T14 | `ensure_safe_output_path`, `ensure_safe_report_path`, `ensure_safe_mapping_path`, `ensure_mapping_path_distinct`; `--force` explicit |
| T15 | `pytest -m 'not integration'` in CI; manual `gliner-integration.yml` only |
| T16–T17 | Regex/checksum primary; optional NER; preset entity filters; human review recommended |
| Mapping architecture | Single path: `app/security/encrypted_mapping.py`; `mapping_io.py` removed (8.1) |
| Encrypted PDF | Rejected safely |
| API mapping | No write, no response fields for mapping payloads |

---

## 6. Residual risks

Operators and reviewers should assume the following **remain true** after mitigations:

1. **Incomplete detection** — Sanitized output may still contain names, addresses, dates, trade secrets, or narrative facts not covered by detectors or presets.
2. **Probabilistic NER** — Natasha and GLiNER can miss or mislabel entities; regex-only runs often miss `PERSON` names.
3. **Reversible pseudonymization** — `pseudonymize` plus a mapping file is **designed** to allow recovery; encrypted mapping is confidentiality, not irreversibility.
4. **Mapping + passphrase compromise** — If both `.json.enc` and passphrase leak, original span text can be recovered offline.
5. **Context leakage** — Placeholders (`[PERSON_1]`) and surrounding text may still enable inference or linkage in LLM outputs.
6. **Safe reports** — Reports intentionally omit raw values but may reveal entity counts, types, positions, and document metadata (`source.input_type`, page count, file size).
7. **No formal privacy proof** — The project does not claim k-anonymity, l-diversity, or differential privacy.
8. **Host security** — Self-hosted deployments depend on OS hardening, TLS, access control, and backup policies outside this codebase.
9. **No audit trail** — No built-in tamper-evident audit log for who anonymized what (future scope).
10. **De-anonymization not implemented** — Restore workflow is undocumented in product; operators must not improvise unsafe scripts that log mappings.

---

## 7. Security invariants (non-negotiable)

These rules apply to **all** contributions and releases:

1. **No real PII** in repository tests, docs, examples, or committed fixtures.
2. **No raw detected values** in API responses, CLI reports, stdout, stderr, or error messages.
3. **No raw input logging** in application code paths.
4. **`value_preview`** is always `***` in externalized entity representations.
5. **Mapping files** (`mapping*.json`, `mapping*.json.enc`) are never committed.
6. **Passphrases** are never committed, logged, or included in issues/PRs.
7. **Mapping persistence** remains **CLI-only** unless a future slice explicitly changes API contracts and threat model.
8. **Default CI** must not install GLiNER or run integration tests that download model weights.
9. **Tests** use synthetic data only (e.g. `test@example.local`, obviously fake INN/SNILS).
10. **Encrypted mapping** uses the canonical module `app/security/encrypted_mapping.py` only.

Violations are treated as security defects, not documentation nits.

---

## 8. Out of scope (current version)

The following are **explicitly out of scope** for 0.1.x:

| Item | Notes |
|------|-------|
| Full DLP | No endpoint agents, no enterprise policy engine |
| Guaranteed legal anonymization | No certification or legal opinion |
| Irreversible privacy proofs | No k-anonymity / DP |
| OCR / image-only PDF | Rejected or empty extract |
| Format-preserving redaction | Output is plain text only |
| RTF ingestion | Plain text via `striprtf` only; no images/objects/format preservation |
| User authentication / multi-tenant SaaS | Single-tenant self-hosted assumption |
| Server-side mapping persistence | API does not write mappings |
| De-anonymization / restore product workflow | Not implemented |
| Central audit log system | Not implemented |
| Enterprise key management (HSM, Vault integration) | Passphrase via env only |
| Web UI | Not implemented |
| Batch API endpoint | CLI-only batch in 0.1.x (`anonymize-dir`) |
| Batch symlink traversal | Not followed; symlinked supported files skipped |
| Batch output stem collisions | Rejected at preflight (e.g. `a.txt` + `a.md` → same `a.anonymized.txt`) |
| Batch encrypted mapping | Not implemented; use per-file `anonymize-file` |
| Telemetry / phone-home | None by design |

Future slices may change scope; this document must be updated when they do.

---

## 9. Regression testing pointers

Security-relevant automated tests (synthetic data only):

| Area | Tests |
|------|-------|
| API safety | `tests/test_anonymizer.py` |
| CLI safety | `tests/test_cli.py` |
| Encrypted mapping crypto | `tests/test_encrypted_mapping.py` |
| Mapping model | `tests/test_mapping.py` |
| Pseudonymize hardening | `tests/test_mapping_hardening.py` |
| Reports | `tests/test_report.py` |

Before release, follow [security_checklist.md](security_checklist.md) including the **Reversible mapping / pseudonymization** and **Before release** sections.

---

## Document history

| Version | Slice | Notes |
|---------|-------|-------|
| Draft | Pre-8 | Short placeholder |
| 0.1.x | **Slice 9** | Full model for pseudonymize + encrypted CLI mapping |
