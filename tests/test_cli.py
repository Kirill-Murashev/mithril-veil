import json
import subprocess
import sys

import pytest
from app.cli.main import main
from tests.conftest import SYNTHETIC_INN_10
from tests.fixtures_generators import write_synthetic_docx, write_synthetic_pdf

SYNTHETIC_TEXT = "Контакт: test@example.local"
SYNTHETIC_EMAIL = "test@example.local"


def run_main(*argv: str) -> tuple[int, str, str]:
    """Invoke CLI main and capture stdout/stderr as UTF-8 text."""
    import io

    stdout = io.StringIO()
    stderr = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout, stderr
    try:
        code = main(list(argv))
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, stdout.getvalue(), stderr.getvalue()


def test_version_command():
    code, out, _ = run_main("version")
    assert code == 0
    assert out.strip() == "Mithril Veil 0.1.0"


def test_anonymize_text_replace_mode():
    code, out, err = run_main("anonymize-text", "--text", SYNTHETIC_TEXT, "--mode", "replace")
    assert code == 0
    assert SYNTHETIC_EMAIL not in out
    assert "[EMAIL_1]" in out
    assert SYNTHETIC_EMAIL not in err


def test_anonymize_text_redact_mode():
    code, out, _ = run_main("anonymize-text", "--text", SYNTHETIC_TEXT, "--mode", "redact")
    assert code == 0
    assert "[REDACTED]" in out
    assert SYNTHETIC_EMAIL not in out


def test_anonymize_stdin_via_subprocess():
    result = subprocess.run(
        [sys.executable, "-m", "app.cli.main", "anonymize-stdin", "--mode", "replace"],
        input=SYNTHETIC_TEXT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert SYNTHETIC_EMAIL not in result.stdout
    assert "[EMAIL_1]" in result.stdout
    assert SYNTHETIC_EMAIL not in result.stderr


def test_anonymize_file_creates_output(tmp_path):
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.txt"
    input_path.write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, _ = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "replace",
    )
    assert code == 0
    assert SYNTHETIC_EMAIL not in output_path.read_text(encoding="utf-8")
    assert "[EMAIL_1]" in output_path.read_text(encoding="utf-8")


def test_anonymize_file_creates_safe_report(tmp_path):
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.txt"
    report_path = tmp_path / "report.json"
    text = f"Email test@example.local, ИНН {SYNTHETIC_INN_10}."
    input_path.write_text(text, encoding="utf-8")
    code, _, _ = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "replace",
        "--report",
        str(report_path),
    )
    assert code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["service"] == "mithril-veil"
    assert report["version"] == "0.1.0"
    assert report["summary"]["total_entities"] >= 1
    assert SYNTHETIC_EMAIL not in json.dumps(report)
    assert SYNTHETIC_INN_10 not in json.dumps(report)
    for entity in report["entities"]:
        assert entity["value_preview"] == "***"
        assert "text" not in entity


def test_anonymize_file_rejects_input_equals_output(tmp_path):
    path = tmp_path / "same.txt"
    path.write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, err = run_main(
        "anonymize-file",
        "--input",
        str(path),
        "--output",
        str(path),
        "--mode",
        "replace",
    )
    assert code == 2
    assert "same" in err.lower() or "input" in err.lower()
    assert SYNTHETIC_EMAIL in path.read_text(encoding="utf-8")


def test_anonymize_file_rejects_overwrite_output(tmp_path):
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.txt"
    input_path.write_text(SYNTHETIC_TEXT, encoding="utf-8")
    output_path.write_text("existing", encoding="utf-8")
    code, _, _ = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "replace",
    )
    assert code == 2


def test_anonymize_file_force_overwrites_output(tmp_path):
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.txt"
    input_path.write_text(SYNTHETIC_TEXT, encoding="utf-8")
    output_path.write_text("existing", encoding="utf-8")
    code, _, _ = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "replace",
        "--force",
    )
    assert code == 0
    assert "[EMAIL_1]" in output_path.read_text(encoding="utf-8")


def test_anonymize_file_rejects_overwrite_report(tmp_path):
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.txt"
    report_path = tmp_path / "report.json"
    input_path.write_text(SYNTHETIC_TEXT, encoding="utf-8")
    report_path.write_text("{}", encoding="utf-8")
    code, _, _ = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "replace",
        "--report",
        str(report_path),
    )
    assert code == 2


def test_unsupported_rtf_exit_code_2(tmp_path):
    input_path = tmp_path / "in.rtf"
    output_path = tmp_path / "out.txt"
    input_path.write_text("{\\rtf1}", encoding="utf-8")
    code, _, err = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "replace",
    )
    assert code == 2
    assert "RTF" in err
    assert SYNTHETIC_EMAIL not in err


def test_anonymize_file_docx_to_txt(tmp_path):
    input_path = tmp_path / "in.docx"
    output_path = tmp_path / "out.txt"
    report_path = tmp_path / "report.json"
    write_synthetic_docx(input_path)
    code, _, err = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "replace",
        "--report",
        str(report_path),
    )
    assert code == 0
    assert SYNTHETIC_EMAIL not in output_path.read_text(encoding="utf-8")
    assert "[EMAIL_1]" in output_path.read_text(encoding="utf-8")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["source"]["input_type"] == "docx"
    assert SYNTHETIC_EMAIL not in json.dumps(report)
    assert SYNTHETIC_EMAIL not in err


def test_anonymize_file_pdf_to_txt(tmp_path):
    input_path = tmp_path / "in.pdf"
    output_path = tmp_path / "out.txt"
    report_path = tmp_path / "report.json"
    write_synthetic_pdf(input_path)
    code, _, err = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "replace",
        "--report",
        str(report_path),
    )
    assert code == 0
    assert SYNTHETIC_EMAIL not in output_path.read_text(encoding="utf-8")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["source"]["input_type"] == "pdf"
    assert "page_count" in report["source"]
    assert SYNTHETIC_EMAIL not in json.dumps(report)
    assert SYNTHETIC_EMAIL not in err


def test_anonymize_file_rejects_docx_output(tmp_path):
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.docx"
    input_path.write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, err = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "replace",
    )
    assert code == 2
    assert "output" in err.lower()


def test_cli_report_does_not_expose_raw_values(tmp_path):
    input_path = tmp_path / "in.md"
    output_path = tmp_path / "out.md"
    report_path = tmp_path / "report.json"
    raw = "test@example.local"
    input_path.write_text(raw, encoding="utf-8")
    run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--report",
        str(report_path),
        "--mode",
        "replace",
    )
    report_text = report_path.read_text(encoding="utf-8")
    assert raw not in report_text


def test_cli_stderr_does_not_expose_raw_values():
    _, _, err = run_main("anonymize-text", "--text", SYNTHETIC_TEXT, "--mode", "replace")
    assert SYNTHETIC_EMAIL not in err
    if err.strip():
        assert "EMAIL" in err or "Detected" in err


@pytest.mark.parametrize("ext", [".md", ".markdown"])
def test_anonymize_file_markdown_extensions(tmp_path, ext: str):
    input_path = tmp_path / f"in{ext}"
    output_path = tmp_path / f"out{ext}"
    input_path.write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, _, _ = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "replace",
    )
    assert code == 0
