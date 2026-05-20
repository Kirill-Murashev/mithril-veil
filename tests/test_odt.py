"""ODT plain-text ingestion tests (synthetic fixtures only)."""

from __future__ import annotations

import json
import zipfile

import pytest
from app.cli.main import main
from app.core.exceptions import EmptyExtractedText, MithrilVeilError
from app.document_io.base import detect_supported_file_type, read_document_file
from app.document_io.odt import read_odt_text
from tests.fixtures_generators import SYNTHETIC_INN, write_synthetic_odt

SYNTHETIC_EMAIL = "test@example.local"


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


def test_detect_supported_odt(tmp_path):
    path = tmp_path / "sample.odt"
    write_synthetic_odt(path)
    assert detect_supported_file_type(path) == "odt"


def test_detect_supported_odt_uppercase_extension(tmp_path):
    path = tmp_path / "SAMPLE.ODT"
    write_synthetic_odt(path)
    assert detect_supported_file_type(path) == "odt"


def test_read_odt_extracts_synthetic_text(tmp_path):
    path = tmp_path / "in.odt"
    write_synthetic_odt(path)
    text = read_odt_text(path)
    assert SYNTHETIC_EMAIL in text
    assert SYNTHETIC_INN in text


def test_read_odt_table_extraction(tmp_path):
    path = tmp_path / "table.odt"
    write_synthetic_odt(
        path,
        paragraphs=[],
        table_rows=[["Ячейка A", f"Email {SYNTHETIC_EMAIL}"], ["ИНН", SYNTHETIC_INN]],
    )
    text = read_odt_text(path)
    assert "Ячейка A" in text
    assert SYNTHETIC_EMAIL in text
    assert SYNTHETIC_INN in text


def test_read_document_file_odt_metadata(tmp_path):
    path = tmp_path / "in.odt"
    write_synthetic_odt(path)
    text, source = read_document_file(path)
    assert SYNTHETIC_EMAIL in text
    assert source["input_type"] == "odt"
    assert source["file_size_bytes"] > 0


def test_empty_odt_raises(tmp_path):
    path = tmp_path / "empty.odt"
    write_synthetic_odt(path, paragraphs=[""], table_rows=None)
    with pytest.raises(EmptyExtractedText):
        read_odt_text(path)


def test_formatting_only_odt_raises(tmp_path):
    path = tmp_path / "blank.odt"
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
        ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
        "<office:body><office:text><text:p/></office:text></office:body>"
        "</office:document-content>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.xml", content.encode("utf-8"))
    with pytest.raises(EmptyExtractedText):
        read_odt_text(path)


def test_invalid_zip_odt_raises(tmp_path):
    path = tmp_path / "bad.odt"
    path.write_bytes(b"not a zip archive")
    with pytest.raises(MithrilVeilError, match="Cannot read ODT"):
        read_odt_text(path)


def test_missing_content_xml_raises(tmp_path):
    path = tmp_path / "no_content.odt"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/vnd.oasis.opendocument.text")
    with pytest.raises(MithrilVeilError, match="Cannot extract text from ODT"):
        read_odt_text(path)


def test_malformed_xml_raises(tmp_path):
    path = tmp_path / "broken.odt"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.xml", b"<office:document-content><unclosed>")
    with pytest.raises(MithrilVeilError, match="Cannot extract text from ODT"):
        read_odt_text(path)


def test_odt_error_messages_contain_no_raw_email(tmp_path):
    path = tmp_path / "empty.odt"
    write_synthetic_odt(path, paragraphs=[SYNTHETIC_EMAIL])
    path.unlink(missing_ok=True)
    path.write_bytes(b"PK\x03\x04")  # truncated zip
    with pytest.raises(MithrilVeilError) as exc_info:
        read_odt_text(path)
    assert SYNTHETIC_EMAIL not in str(exc_info.value)


def test_anonymize_file_odt_to_txt(tmp_path):
    input_path = tmp_path / "in.odt"
    output_path = tmp_path / "out.txt"
    report_path = tmp_path / "report.json"
    write_synthetic_odt(input_path)
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
    out_text = output_path.read_text(encoding="utf-8")
    assert "[EMAIL_1]" in out_text
    assert SYNTHETIC_EMAIL not in out_text
    assert SYNTHETIC_EMAIL not in err
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["source"]["input_type"] == "odt"
    assert report["entities"][0]["value_preview"] == "***"
    assert SYNTHETIC_EMAIL not in json.dumps(report)


def test_batch_processes_odt_file(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    write_synthetic_odt(input_dir / "memo.odt")
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
    out_file = output_dir / "memo.anonymized.txt"
    assert out_file.is_file()
    assert SYNTHETIC_EMAIL not in out_file.read_text(encoding="utf-8")
    assert "[EMAIL_1]" in out_file.read_text(encoding="utf-8")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["report_type"] == "batch"
    assert report["processed_count"] == 1
    assert SYNTHETIC_EMAIL not in json.dumps(report)
    assert SYNTHETIC_EMAIL not in out
    assert SYNTHETIC_EMAIL not in err
