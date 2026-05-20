"""CLI batch anonymize-dir tests (synthetic data only)."""

from __future__ import annotations

import json
from pathlib import Path

from app.cli.main import main
from tests.fixtures_generators import (
    write_synthetic_docx,
    write_synthetic_pdf,
    write_synthetic_rtf,
)

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
    write_synthetic_rtf(root / "nested" / "contact.rtf")
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
    rtf_out = output_dir / "nested" / "contact.anonymized.txt"
    pdf_out = output_dir / "scan.anonymized.txt"
    assert plain_out.is_file()
    assert nested_md.is_file()
    assert doc_out.is_file()
    assert rtf_out.is_file()
    assert pdf_out.is_file()
    assert SYNTHETIC_EMAIL not in rtf_out.read_text(encoding="utf-8")
    assert SYNTHETIC_EMAIL not in plain_out.read_text(encoding="utf-8")
    assert "[EMAIL_1]" in plain_out.read_text(encoding="utf-8")
    assert SYNTHETIC_PHONE not in nested_md.read_text(encoding="utf-8")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["report_type"] == "batch"
    assert report["processed_count"] == 5
    assert report["skipped_count"] >= 1
    rtf_entries = [f for f in report["files"] if f["relative_path"].endswith(".rtf")]
    assert any(e["status"] == "processed" for e in rtf_entries)
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
    assert code == 2
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


def test_batch_processes_rtf_uppercase_extension(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    write_synthetic_rtf(input_dir / "NOTE.RTF")
    output_dir = tmp_path / "out"
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--mode",
        "replace",
    )
    assert code == 0
    assert (output_dir / "NOTE.anonymized.txt").is_file()
    assert SYNTHETIC_EMAIL not in err


def test_batch_malformed_rtf_failed_report_no_raw_leak(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "bad.rtf").write_text("{\\rtf1}", encoding="utf-8")
    write_synthetic_rtf(input_dir / "good.rtf")
    output_dir = tmp_path / "out"
    report_path = tmp_path / "report.json"
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
    assert code == 1
    assert SYNTHETIC_EMAIL not in out
    assert SYNTHETIC_EMAIL not in err
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["failed_count"] == 1
    failed = [f for f in report["files"] if f["status"] == "failed"]
    assert failed[0]["relative_path"] == "bad.rtf"
    assert SYNTHETIC_EMAIL not in json.dumps(report)
    assert (output_dir / "good.anonymized.txt").is_file()


def test_batch_fail_fast_on_malformed_rtf(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "bad.rtf").write_text("{\\rtf1}", encoding="utf-8")
    write_synthetic_rtf(input_dir / "good.rtf")
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


def test_batch_skips_symlinked_rtf(tmp_path: Path):
    import os

    input_dir = tmp_path / "in"
    input_dir.mkdir()
    real = input_dir / "real.rtf"
    write_synthetic_rtf(real)
    os.symlink(real, input_dir / "link.rtf")
    output_dir = tmp_path / "out"
    report_path = tmp_path / "report.json"
    code, _, err = run_main(
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
    assert (output_dir / "real.anonymized.txt").is_file()
    assert not (output_dir / "link.anonymized.txt").exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["skipped_symlink_count"] == 1
    assert SYNTHETIC_EMAIL not in err


def test_batch_skips_hidden_rtf_by_default(tmp_path: Path):
    input_dir = tmp_path / "in"
    hidden = input_dir / ".vault"
    hidden.mkdir(parents=True)
    write_synthetic_rtf(hidden / "secret.rtf")
    write_synthetic_rtf(input_dir / "visible.rtf")
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
    assert not (output_dir / ".vault" / "secret.anonymized.txt").exists()


def test_batch_include_hidden_rtf(tmp_path: Path):
    input_dir = tmp_path / "in"
    hidden = input_dir / ".vault"
    hidden.mkdir(parents=True)
    write_synthetic_rtf(hidden / "secret.rtf")
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
    assert (output_dir / ".vault" / "secret.anonymized.txt").is_file()


def test_batch_empty_rtf_fails_without_raw_leak(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "empty.rtf").write_text("{\\rtf1}", encoding="utf-8")
    (input_dir / "good.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
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
    assert SYNTHETIC_EMAIL not in err


def test_batch_case_insensitive_extensions(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "UPPER.TXT").write_text(SYNTHETIC_TEXT, encoding="utf-8")
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
    assert (output_dir / "UPPER.anonymized.txt").is_file()


def test_batch_skips_symlinked_file(tmp_path: Path):
    import os

    input_dir = tmp_path / "in"
    input_dir.mkdir()
    real = input_dir / "real.txt"
    real.write_text(SYNTHETIC_TEXT, encoding="utf-8")
    os.symlink(real, input_dir / "link.txt")
    output_dir = tmp_path / "out"
    report_path = tmp_path / "report.json"
    code, _, err = run_main(
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
    assert (output_dir / "real.anonymized.txt").is_file()
    assert not (output_dir / "link.anonymized.txt").exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["skipped_symlink_count"] == 1
    assert SYNTHETIC_EMAIL not in err


def test_batch_output_collision_preflight_no_writes(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    (input_dir / "a.md").write_text("heading", encoding="utf-8")
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
    assert "collision" in err.lower() or "duplicate" in err.lower()
    assert not output_dir.exists() or not any(output_dir.iterdir())


def test_batch_report_must_not_be_inside_input(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(tmp_path / "out"),
        "--mode",
        "replace",
        "--report",
        str(input_dir / "batch.json"),
    )
    assert code == 2
    assert "inside" in err.lower() or "input" in err.lower()
    assert SYNTHETIC_EMAIL not in err


def test_batch_report_must_not_equal_output_path(tmp_path: Path):
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
        "replace",
        "--report",
        str(output_dir / "a.anonymized.txt"),
    )
    assert code == 2
    assert "output" in err.lower() or "report" in err.lower()


def test_batch_report_ordering_is_stable(tmp_path: Path):
    input_dir = _setup_batch_input(tmp_path)
    output_dir = tmp_path / "output"
    report_a = tmp_path / "report_a.json"
    report_b = tmp_path / "report_b.json"
    for report_path in (report_a, report_b):
        code, _, _ = run_main(
            "anonymize-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--mode",
            "replace",
            "--force",
            "--report",
            str(report_path),
        )
        assert code == 0
    paths_a = [e["relative_path"] for e in json.loads(report_a.read_text())["files"]]
    paths_b = [e["relative_path"] for e in json.loads(report_b.read_text())["files"]]
    assert paths_a == paths_b == sorted(paths_a)


def test_batch_exit_zero_when_only_skips_no_failures(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "only.csv").write_text("a,b", encoding="utf-8")
    code, _, _ = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(tmp_path / "out"),
        "--mode",
        "replace",
    )
    assert code == 0


def test_batch_relative_paths_reject_nested_output(tmp_path: Path):
    base = tmp_path / "tree"
    input_dir = base / "input"
    input_dir.mkdir(parents=True)
    out_nested = input_dir / "nested" / "out"
    out_nested.mkdir(parents=True)
    (input_dir / "a.txt").write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, err = run_main(
        "anonymize-dir",
        str(input_dir),
        "--output-dir",
        str(out_nested),
        "--mode",
        "replace",
    )
    assert code == 2
    assert SYNTHETIC_EMAIL not in err
