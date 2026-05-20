# CLI examples (synthetic data only)

All examples use **synthetic** placeholders. Do not paste real client data, INN/SNILS, passports, or production documents into issues or logs.

Install first:

```bash
pip install -e ".[dev]"
```

## version

```bash
mithril-veil version
# Mithril Veil 0.1.0
```

## list-presets

```bash
mithril-veil list-presets
# general_ru      General RU
# legal_ru        Legal RU
# valuation_ru    Valuation RU
# banking_ru      Banking RU
# court_case_ru   Court case RU
```

## anonymize-text

Inline text with `replace` and a preset:

```bash
mithril-veil anonymize-text \
  --text "Контакт: test@example.local, ИНН 7701010017" \
  --mode replace \
  --preset general_ru
```

Optional Natasha NER (probabilistic — review results):

```bash
mithril-veil anonymize-text \
  --text "Иван Тестович работает в ООО Тестовая Организация." \
  --mode replace \
  --use-ner
```

Optional GLiNER (requires `pip install -e ".[gliner]"`; may download weights on first use):

```bash
mithril-veil anonymize-text \
  --text "Иван Тестович работает в ООО Тестовая Организация." \
  --mode replace \
  --use-gliner \
  --gliner-label person \
  --gliner-label organization
```

## anonymize-stdin

```bash
echo "Контакт: test@example.local" | mithril-veil anonymize-stdin --mode replace
```

## anonymize-file

Text or document input; plain-text output. Use `examples/synthetic_input.txt` from the repository:

```bash
mithril-veil anonymize-file \
  --input examples/synthetic_input.txt \
  --output /tmp/anonymized.txt \
  --mode replace \
  --report /tmp/report.json
```

DOCX or text-based PDF (output is plain text; formatting not preserved):

```bash
mithril-veil anonymize-file \
  --input /path/to/synthetic.docx \
  --output /tmp/sanitized.txt \
  --mode replace \
  --report /tmp/report.json
```

Supported extensions: `.txt`, `.md`, `.markdown`, `.docx`, `.odt`, `.rtf`, text-based `.pdf`.

## anonymize-dir

Batch processing for **replace** or **redact** only. Writes `*.anonymized.txt` under `--output-dir` and optional aggregate safe report:

```bash
mithril-veil anonymize-dir ./documents \
  --output-dir ./sanitized \
  --mode replace \
  --report ./batch-report.json
```

`pseudonymize` and `--mapping-output` are **not** supported in batch. Use `anonymize-file` per document instead.

## pseudonymize with encrypted mapping

**Warning:** `pseudonymize` is **reversible** when you keep the mapping file and passphrase. Mapping files are highly sensitive (treat like key material). The HTTP API never writes or returns mappings. **Restore / de-anonymization is not implemented** in 0.1.x — see [restore_workflow_design.md](restore_workflow_design.md).

```bash
export MITHRIL_VEIL_MAPPING_PASSPHRASE="your-local-secret-only"
mithril-veil anonymize-file \
  --input examples/synthetic_input.txt \
  --output /tmp/pseudonymized.txt \
  --mode pseudonymize \
  --mapping-output /tmp/mapping.json.enc \
  --report /tmp/report.json
```

Requirements:

- `--mapping-output` path must end with `.json.enc`
- Passphrase via `MITHRIL_VEIL_MAPPING_PASSPHRASE` or `--mapping-passphrase-env`
- Mapping path must differ from `--input`, `--output`, and `--report`
- Use `--force` to overwrite an existing mapping file

For irreversible sanitization before a cloud LLM, prefer `replace` or `redact`.

## Related docs

- [README.md](../README.md) — overview, API, security warnings
- [release_checklist.md](release_checklist.md)
- [security_checklist.md](security_checklist.md)
