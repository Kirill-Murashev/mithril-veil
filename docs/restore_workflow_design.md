# De-anonymization / restore workflow — design document (Slice 14)

> **Status:** Design only — **no restore implementation exists** in Mithril Veil 0.1.x.  
> **Related:** [threat_model.md](threat_model.md), [architecture.md](architecture.md), [SECURITY.md](../SECURITY.md)

This document describes a **possible future** workflow to recover original span text from pseudonymized output using an encrypted mapping file. It is intended for security review and staged implementation planning. **Do not treat this as shipped product behavior.**

---

## 1. Purpose and scope

### What this document is

- A **security-first design** for a hypothetical **restore / de-anonymization** capability.
- Input to future slices (R1–R4 below); **not** a specification for v0.1.0.

### What Mithril Veil does today

| Capability | Current state |
|------------|---------------|
| **`pseudonymize` mode** | Replaces detected spans with deterministic typed placeholders (e.g. `[INN_1]`, `[PERSON_2]`). |
| **In-memory mapping** | `ReversibleMapping` in `app/core/mapping.py` exists **only for the duration of a single run**. |
| **Encrypted mapping on disk** | Optional **CLI-only** write via `--mapping-output path.json.enc` (single-file / text flows). Envelope: `mithril-veil-mapping-v1` in `app/security/encrypted_mapping.py`. |
| **Restore / de-anonymize** | **Not implemented** — no CLI command, no API endpoint, no library API intended for operators. |

### Why restore is security-sensitive

Restore is the **intentional reversal** of a confidentiality control. A successful restore:

- Recreates **original PII** in plaintext.
- Depends on **mapping file + passphrase** (dual secret).
- Amplifies impact of **wrong-file pairing**, **leakage**, or **operator mistake** (accidental re-identification before cloud LLMs, in logs, or in issue trackers).

Restore must therefore be **opt-in, CLI-first, locally controlled**, and governed by the same invariants as pseudonymization (no raw values in reports/logs by default).

---

## 2. Current mapping model

### Pseudonymization pipeline (summary)

```text
DetectedEntity (in-memory span text)
  → anonymizer assigns placeholder via placeholder_for(type, index)
  → ReversibleMapping.record(placeholder, original span text)
  → sanitized text written to output
  → optional serialize_for_encryption() → PBKDF2 + Fernet → .json.enc
```

### Placeholder format

- Pattern: `[{ENTITY_TYPE}_{index}]` (see `app/core/placeholders.py`).
- Deterministic per run ordering; **strict parsing** will be required for any future restore to avoid partial or ambiguous replacements.

### Mapping payload (encrypted file plaintext, before encryption)

- JSON object: **placeholder → original span text** (e.g. `{"[EMAIL_1]": "test@example.local"}`).
- **Synthetic examples only** in tests; never commit real mapping files to the repository.

### Surface matrix (current)

| Surface | In-memory mapping | Writes `.json.enc` | Returns mapping in API/report |
|---------|-------------------|--------------------|------------------------------|
| CLI `replace` / `redact` | No | No | No |
| CLI `pseudonymize` | Yes | Only with `--mapping-output` | Report: `mapping.written` / `mapping.encrypted` flags only |
| API `pseudonymize` | Yes (per request) | **No** | **No** |
| CLI `anonymize-dir` (batch) | **Rejected** | **Rejected** | N/A |

### Operator obligations (current)

1. **Mapping files are critical assets** — encrypted or not, they enable re-identification with the passphrase.
2. **Never commit** `mapping*.json` or `mapping*.json.enc` (gitignored).
3. **Never log, paste, or upload** mapping files or passphrases to GitHub issues, CI, cloud drives, or LLM chats.
4. **Passphrase** via environment variable (`MITHRIL_VEIL_MAPPING_PASSPHRASE` or `--mapping-passphrase-env`) — not in repo.
5. For **irreversible** sanitization before a cloud LLM, use **`replace` or `redact`**, delete any mapping, and do not retain passphrases for that job.

### What restore would add (future)

- Read sanitized text + decrypt mapping + substitute placeholders → **restored text containing original PII**.
- **Out of scope for this document’s implementation** — see §9 Non-goals.

---

## 3. Trust boundaries

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ Operator workstation / self-hosted VPS (trusted by operator policy)      │
│  ┌────────────────┐   ┌──────────────────┐   ┌─────────────────────┐  │
│  │ CLI restore     │   │ Process memory    │   │ Local filesystem     │  │
│  │ (future)        │──►│ mapping plaintext │◄──│ .json.enc, I/O files │  │
│  └────────┬────────┘   └────────▲─────────┘   └──────────▲──────────┘  │
│           │                       │                         │              │
│           │              passphrase env boundary            │              │
│           │         MITHRIL_VEIL_MAPPING_PASSPHRASE         │              │
│  ┌────────▼────────┐   ┌──────────────────┐   ┌───────────┴──────────┐  │
│  │ Sanitized text  │   │ Safe CLI report   │   │ Encrypted mapping     │  │
│  │ (placeholders)  │   │ (no raw values)   │   │ file (.json.enc)      │  │
│  └────────┬────────┘   └──────────────────┘   └──────────────────────┘  │
└───────────┼──────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Must NOT cross without explicit operator action                            │
│  • Cloud LLM APIs (restored text = raw PII risk)                           │
│  • Application/container logs, CI stdout                                   │
│  • Git repository / public issue tracker                                   │
│  • Backup/sync services (Dropbox, etc.) for mapping files                  │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│ FastAPI (current): pseudonymize in-memory only; no mapping on disk/API     │
│ Future API restore endpoint: **strongly discouraged** — separate TM needed │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│ Future web UI (not implemented): would add browser storage, session, XSS   │
│ Restore via web UI: **out of scope** unless re-threat-modeled              │
└───────────────────────────────────────────────────────────────────────────┘
```

| Boundary | Data crossing | Trust assumption |
|----------|---------------|------------------|
| **Local user / VPS** | All restore I/O | Operator controls host and access policy |
| **CLI process memory** | Decrypted mapping dict, restored text | Same-user attackers can read memory |
| **Encrypted mapping file** | Ciphertext on disk | Confidentiality if passphrase safe; **integrity not cryptographically signed** today |
| **Passphrase env** | KDF input | Visible to same-user processes; not for CLI argv |
| **Sanitized text** | Placeholders only (prior step) | Wrong file pairing is an operational threat |
| **Cloud LLM** | Operator may send sanitized text today | **Must not** receive mapping or restored text |
| **Logs / reports** | Safe summaries only | Restore must not echo raw values by default |
| **Git / issues** | Source, docs, synthetic tests | No real mappings or passphrases |
| **Future API** | HTTP body with mapping? | **Out of scope v0.1.x** — high abuse and persistence risk |

---

## 4. Restore workflow options (future, not implemented)

### A. CLI-only restore command (recommended first ship)

**Proposed shape (illustrative):**

```bash
# Hypothetical — NOT available today
mithril-veil restore-text \
  --input sanitized.txt \
  --mapping mapping.json.enc \
  --output restored.txt \
  --mapping-passphrase-env MITHRIL_VEIL_MAPPING_PASSPHRASE
```

| Aspect | Design intent |
|--------|---------------|
| Inputs | Sanitized text file or stdin; encrypted mapping path; passphrase from env |
| Output | **Required `--output` file** by default (restored plaintext on disk) |
| Stdout | **No restored text to stdout by default** — avoids terminal scrollback leakage |
| Paths | Mapping path **distinct** from input, output, report (reuse 8.1 path guards) |
| Overwrite | Refuse unless `--force` |
| Errors | Generic messages only — no passphrase, no mapping entries, no restored spans |

### B. Partial restore / selected placeholders

- Restore only selected entity types (e.g. only `[INN_*]`) or an allowlist of placeholders.
- **Use case:** Controlled legal review without full re-identification.
- **Risks:** Inconsistent document context; placeholders left in text may confuse readers or LLMs; ordering of replacement must be deterministic (longest-token-first or fixed placeholder sort).

### C. Dry-run restore

- Report **safe aggregates only** by default: placeholder count, entity type counts, whether mapping decrypts, format version OK.
- **No raw values** in default dry-run output.
- Optional `--verbose-local` (name TBD) might exist only under explicit operator flag for air-gapped debugging — must be threat-modeled before implementation.

### D. API restore endpoint

| Verdict | Rationale |
|---------|-----------|
| **Strongly discouraged for v0.1.x and likely beyond** | Mapping upload → server memory/disk risk; authentication, rate limits, audit, multi-tenant isolation, and “no persistence” guarantees become a new product class. |
| If ever considered | Separate threat model, no server-side mapping storage, short-lived memory, authn/z, no logging of bodies, probably **still CLI-only** for regulated users. |

**Default project position:** **API restore remains out of scope** unless explicitly approved by maintainers and documented in an updated threat model.

---

## 5. Security requirements for any future implementation

These requirements apply to **all** restore slices unless a later threat-model revision explicitly relaxes them.

| # | Requirement |
|---|-------------|
| S1 | **CLI-only first** — no API restore in initial implementation |
| S2 | **No server-side mapping persistence** — decrypt in process memory; no DB/cache |
| S3 | **No API restore endpoint in v0.1.x** |
| S4 | **Passphrase** only via environment variable or secure interactive prompt — **never** `--passphrase` CLI argument (shell history) |
| S5 | **Mapping path** must differ from `--input`, `--output`, and `--report` paths |
| S6 | **Refuse overwrite** of output/report unless `--force` |
| S7 | **Safe errors only** — no mapping payload, no original spans, no passphrase hints in messages |
| S8 | **No raw values** in logs, safe JSON reports, or default stdout/stderr |
| S9 | **No mapping payload** in anonymization or restore JSON reports |
| S10 | **No batch restore** until separately designed (collision, partial failure, aggregate leakage) |
| S11 | **No restore from unencrypted** mapping files — `.json.enc` only |
| S12 | **Reject unsupported** `mithril-veil-mapping-v1` envelope mutations / unknown format IDs |
| S13 | **Strict placeholder parsing** — match `[TYPE_N]` tokens; deterministic replacement order |
| S14 | **Deterministic behavior** — same inputs → same restored text |
| S15 | **Synthetic tests only** — no real PII in repository fixtures |
| S16 | **Decrypt via** `app/security/encrypted_mapping.py` only — single canonical path |
| S17 | **Document pairing** — optional metadata hook (future) to bind mapping to source hash; not in v0.1.x format today |

---

## 6. UX constraints

### Warnings and mental model

1. **Banner / stderr notice** before restore: restored output contains **original personal data**.
2. **Distinguish modes clearly:**
   - `replace` / `redact` → **not reversible** via mapping.
   - `pseudonymize` → **reversible** if mapping + passphrase retained.
3. **Cloud LLM warning:** Do not send restored text to external AI services.

### Output handling

| Default | Rationale |
|---------|-----------|
| **`--output` required** (or strong default path) | Prevents accidental terminal leakage |
| Stdout restore | Only with explicit flag (e.g. `--stdout`) after additional warning |
| Report file | Optional safe dry-run report — counts only |

### Mapping file lifecycle (operator guidance)

| Phase | Guidance |
|-------|----------|
| **Create** | Only when reversible workflow needed; minimal retention |
| **Store** | Encrypted filesystem; restrict permissions; separate from sanitized exports |
| **Rotate / delete** | Delete mapping when case closes; rotate passphrase if exposed |
| **Backup** | Treat backup like secret key material — encrypted backup channels only |
| **Destroy** | Secure delete mapping and passphrase when irreversible archive is final |

---

## 7. Risk analysis

| Risk | Description | Mitigations (future implementation) |
|------|-------------|-------------------------------------|
| **Accidental re-identification** | Operator restores text and pastes into LLM/email | Required output file; warnings; no default stdout |
| **Wrong mapping file** | Mapping from job A applied to sanitized text from job B | Path discipline; future content hash in envelope; dry-run counts mismatch |
| **Placeholder collision / tampering** | Manual edit of sanitized text breaks placeholders | Strict token grammar; fail on unknown tokens; optional strict mode |
| **Leaked mapping file** | Backup, sync, malware | Encryption; operator training; short retention |
| **Leaked passphrase** | Env leak, `.env` commit, chat | Env-only; never in repo; security checklist |
| **Shell history** | Passphrase on CLI argv | Forbid argv passphrase (S4) |
| **CI / log leakage** | Restore in CI prints PII | No restore in default CI; synthetic tests only |
| **Cloud upload of mapping** | User uploads `.json.enc` to Drive/GitHub | Docs; never attach to issues |
| **Issue tracker leakage** | Mapping pasted in bug report | SECURITY.md; review process |
| **Partial restore** | Mixed placeholders + restored spans misleads readers | Document inconsistency; dry-run preview |
| **Malicious mapping file** | Crafted JSON after decrypt — huge values, binary | Size limits; validate keys match placeholder pattern |
| **Stale / incompatible version** | Old tool reads new envelope | Strict `format` field check (S12) |
| **Batch restore** | Wrong file pairing at scale | Deferred — separate design |
| **API restore abuse** | Remote attacker submits mapping | Keep API out of scope (S3) |
| **Memory forensics** | Decrypted mapping in RAM | Accept residual risk; document for high-threat users |

---

## 8. Suggested future implementation plan

Small staged slices — **no broad rewrite**.

| Slice | Focus | Deliverable |
|-------|--------|-------------|
| **R1** | Mapping envelope validation hardening (if needed before restore) | Stricter decrypt errors; optional metadata for pairing; tests with **synthetic** encrypted fixtures only |
| **R2** | Restore **design tests** / pure functions | Placeholder substitution unit tests; no CLI yet; synthetic mapping dicts in memory only |
| **R3** | **CLI-only restore command** | `restore-text` or `restore-file`; env passphrase; required `--output`; path guards |
| **R4** | Restore safety hardening | Dry-run mode; partial restore flag; regression tests for safe errors and no stdout leakage |

**Explicitly deferred:** API restore, web UI restore, batch restore, cloud mapping storage.

**Approval gate:** Any API restore requires updated [threat_model.md](threat_model.md) and maintainer sign-off.

---

## 9. Non-goals

The following are **not** part of Slice 14 or the recommended R1–R4 plan unless explicitly re-scoped:

- **No implementation** in Slice 14 (this document only)
- **No API restore endpoint**
- **No web UI restore**
- **No server-side mapping store**
- **No batch restore**
- **No cloud storage** of mappings by the product
- **No legal anonymization guarantee** — restore proves reversibility
- **No formal privacy guarantee** (k-anonymity, differential privacy)
- **No automatic restore** after anonymize in the same command (separate explicit step)
- **No de-anonymization of `replace`/`redact` outputs** (no mapping exists)

---

## 10. References (current code)

| Topic | Location |
|-------|----------|
| In-memory mapping | `app/core/mapping.py` — `ReversibleMapping`, `serialize_for_encryption()` |
| Placeholders | `app/core/placeholders.py` — `placeholder_for()` |
| Encrypted file I/O | `app/security/encrypted_mapping.py` — `MAPPING_FORMAT_ID`, encrypt/decrypt |
| Path safety | CLI helpers used by `anonymize-file` (mapping distinct from I/O paths) |
| Security tests | `tests/test_encrypted_mapping.py`, `tests/test_mapping_hardening.py` |
| Threat model | `docs/threat_model.md` — assets T6–T9, invariant #7 |

---

## Document history

| Version | Slice | Notes |
|---------|-------|-------|
| 0.1.x design | **Slice 14** | Initial restore workflow design; no product implementation |
