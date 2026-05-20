"""CLI batch anonymize-dir tests (synthetic data only)."""

from __future__ import annotations

import json
from pathlib import Path

from app.cli.main import main
from tests.fixtures_generators import write_synthetic_docx, write_synthetic_pdf

SYNTHETIC_TEXT = "Контакт: test@example.local"
SYNTHETIC_EMAIL = "test@example.local"
SYNTHETIC_PHONE = "+7 (900) 111-22-33"


def run_main(*argv: str) -> tuple[int, str, str]:
    import io
    import sys

    stdout = io.StringIO()
    stderr = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout, stderr
    try:
        code = main(list(argv))
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, stdout.getvalue(), stderr.getvalue()


def _setup_batch_input(tmp_path: Path) -> Path:
    root = tmp_path / "input"
    (root / "nested").mkdir(parents=True)
    (root / "plain.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    (root / "nested" / "note.md").write_text(f"Phone {SYNTHETIC_PHONE}", encoding="utf-8")
    (root / "unsupported.csv").write_text("col1,col2", encoding="utf-8")
    (root / "bad.rtf").write_text("{\\rtf1}", encoding="utf-8")
    write_synthetic_docx(root / "nested" / "doc.docx")
    write_synthetic_pdf(root / "scan.pdf")
    return root


def test_batch_processes_supported_types_and_skips_unsupported(tmp_path: Path):
    input_dir = _setup_batch_input(tmp_path)
    output_dir = tmp_path / "output"
    report_path = tmp_path / "batch_report.json"
    code, out, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--mode",
        "replace",
        "--report",
        str(report_path),
    )
    assert code == 0
    assert SYNTHETIC_EMAIL not in out
    assert SYNTHETIC_EMAIL not in err

    plain_out = output_dir / "plain.anonymized.txt"
    nested_md = output_dir / "nested" / "note.anonymized.txt"
    doc_out = output_dir / "nested" / "doc.anonymized.txt"
    pdf_out = output_dir / "scan.anonymized.txt"
    assert plain_out.is_file()
    assert nested_md.is_file()
    assert doc_out.is_file()
    assert pdf_out.is_file()
    assert SYNTHETIC_EMAIL not in plain_out.read_text(encoding="utf-8")
    assert "[EMAIL_1]" in plain_out.read_text(encoding="utf-8")
    assert SYNTHETIC_PHONE not in nested_md.read_text(encoding="utf-8")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["report_type"] == "batch"
    assert report["processed_count"] == 4
    assert report["skipped_count"] >= 2
    assert SYNTHETIC_EMAIL not in json.dumps(report)
    assert SYNTHETIC_PHONE not in json.dumps(report)


def test_batch_redact_mode(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    output_dir = tmp_path / "out"
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--mode",
        "redact",
    )
    assert code == 0
    text = (output_dir / "a.anonymized.txt").read_text(encoding="utf-8")
    assert "[REDACTED]" in text
    assert SYNTHETIC_EMAIL not in text
    assert SYNTHETIC_EMAIL not in err


def test_batch_rejects_pseudonymize_mode(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(tmp_path / "out"),
        "--mode",
        "pseudonymize",
    )
    assert code == 1
    assert "replace" in err.lower() or "redact" in err.lower()
    assert SYNTHETIC_EMAIL not in err


def test_batch_rejects_mapping_output(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(tmp_path / "out"),
        "--mapping-output",
        str(tmp_path / "m.json.enc"),
    )
    assert code == 1
    assert "mapping" in err.lower()
    assert SYNTHETIC_EMAIL not in err


def test_batch_one_bad_file_continues_by_default(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "good.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    (input_dir / "bad.pdf").write_bytes(b"%PDF-not-valid")
    output_dir = tmp_path / "out"
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--mode",
        "replace",
    )
    assert code == 1
    assert (output_dir / "good.anonymized.txt").is_file()
    good_text = (output_dir / "good.anonymized.txt").read_text(encoding="utf-8")
    assert SYNTHETIC_EMAIL not in err
    assert "[EMAIL_1]" in good_text


def test_batch_fail_fast_stops_after_first_failure(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "bad.pdf").write_bytes(b"%PDF-not-valid")
    (input_dir / "good.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    output_dir = tmp_path / "out"
    code, _, _ = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--mode",
        "replace",
        "--fail-fast",
    )
    assert code == 1
    assert not (output_dir / "good.anonymized.txt").exists()


def test_batch_refuses_overwrite_without_force(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    output_dir = tmp_path / "out"
    existing = output_dir / "a.anonymized.txt"
    output_dir.mkdir(parents=True)
    existing.write_text("existing", encoding="utf-8")
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--mode",
        "replace",
    )
    assert code == 1
    assert "force" in err.lower() or "exists" in err.lower()


def test_batch_force_overwrites(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    output_dir = tmp_path / "out"
    existing = output_dir / "a.anonymized.txt"
    output_dir.mkdir(parents=True)
    existing.write_text("existing", encoding="utf-8")
    code, _, _ = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--mode",
        "replace",
        "--force",
    )
    assert code == 0
    assert "[EMAIL_1]" in existing.read_text(encoding="utf-8")


def test_batch_rejects_same_input_and_output_dir(tmp_path: Path):
    input_dir = tmp_path / "same"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(input_dir),
        "--mode",
        "replace",
    )
    assert code == 2
    assert SYNTHETIC_EMAIL not in err


def test_batch_rejects_output_dir_inside_input_dir(tmp_path: Path):
    input_dir = tmp_path / "in"
    output_dir = input_dir / "out"
    input_dir.mkdir()
    output_dir.mkdir()
    (input_dir / "a.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--mode",
        "replace",
    )
    assert code == 2
    assert "inside" in err.lower() or "input" in err.lower()


def test_batch_skips_hidden_by_default(tmp_path: Path):
    input_dir = tmp_path / "in"
    hidden = input_dir / ".hidden"
    hidden.mkdir(parents=True)
    (hidden / "secret.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    (input_dir / "visible.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    output_dir = tmp_path / "out"
    code, _, _ = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--mode",
        "replace",
    )
    assert code == 0
    assert (output_dir / "visible.anonymized.txt").is_file()
    assert not (output_dir / ".hidden" / "secret.anonymized.txt").exists()


def test_batch_include_hidden(tmp_path: Path):
    input_dir = tmp_path / "in"
    hidden = input_dir / ".hidden"
    hidden.mkdir(parents=True)
    (hidden / "secret.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    output_dir = tmp_path / "out"
    code, _, _ = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--mode",
        "replace",
        "--include-hidden",
    )
    assert code == 0
    assert (output_dir / ".hidden" / "secret.anonymized.txt").is_file()


def test_batch_max_files_limit(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    for i in range(3):
        (input_dir / f"f{i}.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(tmp_path / "out"),
        "--max-files",
        "2",
    )
    assert code == 1
    assert "limit" in err.lower()


def test_batch_module_output_path_convention():
    from app.document_io.batch import batch_output_relative_path

    assert batch_output_relative_path(Path("docs/a.docx")) == Path("docs/a.anonymized.txt")
    assert batch_output_relative_path(Path("note.md")) == Path("note.anonymized.txt")
