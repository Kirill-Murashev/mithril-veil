"""ODT ingestion hardening tests (synthetic fixtures only)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from app.cli.main import main
from app.core.exceptions import MithrilVeilError
from app.document_io.odt import (
    MAX_ODT_CONTENT_XML_BYTES,
    MAX_ODT_CONTENT_XML_COMPRESSION_RATIO,
    _validate_content_xml_entry,
    read_odt_text,
)
from tests.fixtures_generators import SYNTHETIC_INN, write_synthetic_odt

SYNTHETIC_EMAIL = "test@example.local"

_ODT_WRAPPER_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
    ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"'
    ' xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"'
    ' xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0">'
)
_ODT_WRAPPER_TAIL = "</office:document-content>"


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


def _write_odt_content_xml(path: Path, inner_xml: str) -> None:
    content = (_ODT_WRAPPER_HEAD + inner_xml + _ODT_WRAPPER_TAIL).encode("utf-8")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        archive.writestr("content.xml", content)


def test_odt_oversized_content_xml_rejected(tmp_path: Path):
    payload = "x" * (MAX_ODT_CONTENT_XML_BYTES + 1)
    path = tmp_path / "huge.odt"
    inner = f"<office:body><office:text><text:p>{payload}</text:p></office:text></office:body>"
    _write_odt_content_xml(path, inner)
    with pytest.raises(MithrilVeilError, match="too large to process safely"):
        read_odt_text(path)


def test_odt_suspicious_compression_ratio_rejected(tmp_path: Path):
    repetitive = "A" * 400_000
    path = tmp_path / "bomb.odt"
    _write_odt_content_xml(
        path,
        f"<office:body><office:text><text:p>{repetitive}</text:p></office:text></office:body>",
    )
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo("content.xml")
        assert info.file_size > info.compress_size * MAX_ODT_CONTENT_XML_COMPRESSION_RATIO
    with pytest.raises(MithrilVeilError, match="too large to process safely"):
        read_odt_text(path)


def test_validate_content_xml_entry_rejects_inflated_zipinfo():
    info = zipfile.ZipInfo("content.xml")
    info.compress_size = 100
    info.file_size = 100 * MAX_ODT_CONTENT_XML_COMPRESSION_RATIO + 1
    with pytest.raises(MithrilVeilError, match="too large to process safely"):
        _validate_content_xml_entry(info)


def test_odt_missing_content_xml_rejected(tmp_path: Path):
    path = tmp_path / "no_xml.odt"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/vnd.oasis.opendocument.text")
    with pytest.raises(MithrilVeilError, match="Cannot extract text from ODT"):
        read_odt_text(path)


def test_odt_malformed_xml_rejected(tmp_path: Path):
    path = tmp_path / "broken.odt"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.xml", b"<office:document-content><unclosed>")
    with pytest.raises(MithrilVeilError, match="Cannot extract text from ODT"):
        read_odt_text(path)


def test_odt_missing_office_text_rejected(tmp_path: Path):
    path = tmp_path / "no_text.odt"
    _write_odt_content_xml(path, "<office:body><office:spreadsheet/></office:body>")
    with pytest.raises(MithrilVeilError, match="Cannot extract text from ODT"):
        read_odt_text(path)


def test_odt_missing_office_body_rejected(tmp_path: Path):
    path = tmp_path / "no_body.odt"
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0">'
        "<office:meta/>"
        "</office:document-content>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.xml", content.encode("utf-8"))
    with pytest.raises(MithrilVeilError, match="Cannot extract text from ODT"):
        read_odt_text(path)


def test_odt_embedded_frame_image_not_extracted(tmp_path: Path):
    path = tmp_path / "embedded.odt"
    inner = (
        "<office:body><office:text>"
        f"<text:p>Visible {SYNTHETIC_EMAIL}</text:p>"
        '<draw:frame><draw:image href="Pictures/binary.png">'
        "<office:binary-data>DEADBEEFCAFEBABE</office:binary-data>"
        "</draw:image></draw:frame>"
        "</office:text></office:body>"
    )
    _write_odt_content_xml(path, inner)
    text = read_odt_text(path)
    assert SYNTHETIC_EMAIL in text
    assert "DEADBEEF" not in text
    assert "binary.png" not in text


def test_odt_hardening_errors_contain_no_raw_pii(tmp_path: Path):
    path = tmp_path / "bad.odt"
    _write_odt_content_xml(
        path,
        f"<office:body><office:text><text:p>{SYNTHETIC_EMAIL}</text:p></office:body>",
    )
    path.unlink(missing_ok=True)
    path.write_bytes(b"not-a-zip")
    with pytest.raises(MithrilVeilError) as exc_info:
        read_odt_text(path)
    assert SYNTHETIC_EMAIL not in str(exc_info.value)
    assert SYNTHETIC_INN not in str(exc_info.value)


def test_odt_paragraph_table_extraction_still_works(tmp_path: Path):
    path = tmp_path / "ok.odt"
    write_synthetic_odt(
        path,
        paragraphs=[f"Email {SYNTHETIC_EMAIL}"],
        table_rows=[["Col", SYNTHETIC_INN]],
        heading="Заголовок",
    )
    text = read_odt_text(path)
    assert SYNTHETIC_EMAIL in text
    assert SYNTHETIC_INN in text
    assert "Заголовок" in text


def test_batch_mixed_odt_directory_safe_report(tmp_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    write_synthetic_odt(input_dir / "good.odt")
    (input_dir / "bad.odt").write_bytes(b"PK\x03\x04")
    (input_dir / "plain.txt").write_text(f"Контакт: {SYNTHETIC_EMAIL}", encoding="utf-8")
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
    assert SYNTHETIC_INN not in out
    assert SYNTHETIC_INN not in err
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["failed_count"] == 1
    assert report["processed_count"] == 2
    failed = [f for f in report["files"] if f["status"] == "failed"]
    assert failed[0]["relative_path"] == "bad.odt"
    assert SYNTHETIC_EMAIL not in json.dumps(report)
    assert SYNTHETIC_INN not in json.dumps(report)
    assert (output_dir / "good.anonymized.txt").is_file()
    assert (output_dir / "plain.anonymized.txt").is_file()
    assert SYNTHETIC_EMAIL not in (output_dir / "good.anonymized.txt").read_text(encoding="utf-8")
