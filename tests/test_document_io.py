import pytest
from app.core.exceptions import MithrilVeilError, UnsafeFileOperation, UnsupportedDocumentType
from app.document_io.base import (
    detect_supported_file_type,
    ensure_safe_output_path,
    read_text_file,
    write_text_file,
)


def test_detect_supported_txt(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("hello", encoding="utf-8")
    assert detect_supported_file_type(path) == "txt"


def test_detect_supported_md(tmp_path):
    path = tmp_path / "sample.md"
    path.write_text("# title", encoding="utf-8")
    assert detect_supported_file_type(path) == "markdown"


def test_detect_supported_markdown_extension(tmp_path):
    path = tmp_path / "sample.markdown"
    path.write_text("body", encoding="utf-8")
    assert detect_supported_file_type(path) == "markdown"


def test_read_write_txt_roundtrip(tmp_path):
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.txt"
    input_path.write_text("Контакт: test@example.local", encoding="utf-8")
    content = read_text_file(input_path)
    write_text_file(output_path, content.replace("test@example.local", "[EMAIL_1]"))
    assert "[EMAIL_1]" in output_path.read_text(encoding="utf-8")


def test_read_write_md_roundtrip(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("**test@example.local**", encoding="utf-8")
    assert detect_supported_file_type(path) == "markdown"
    assert "test@example.local" in read_text_file(path)


def test_docx_unsupported(tmp_path):
    path = tmp_path / "file.docx"
    path.write_text("not a real docx", encoding="utf-8")
    with pytest.raises(UnsupportedDocumentType, match="DOCX"):
        detect_supported_file_type(path)


def test_pdf_unsupported(tmp_path):
    path = tmp_path / "file.pdf"
    path.write_text("not a real pdf", encoding="utf-8")
    with pytest.raises(UnsupportedDocumentType, match="PDF"):
        detect_supported_file_type(path)


def test_rtf_unsupported(tmp_path):
    path = tmp_path / "file.rtf"
    path.write_text("{\\rtf1}", encoding="utf-8")
    with pytest.raises(UnsupportedDocumentType, match="RTF"):
        detect_supported_file_type(path)


def test_write_refuses_existing_without_force(tmp_path):
    path = tmp_path / "out.txt"
    path.write_text("existing", encoding="utf-8")
    with pytest.raises(UnsafeFileOperation):
        write_text_file(path, "new", force=False)


def test_ensure_safe_output_rejects_input_equals_output(tmp_path):
    path = tmp_path / "same.txt"
    path.write_text("data", encoding="utf-8")
    with pytest.raises(UnsafeFileOperation, match="same as input"):
        ensure_safe_output_path(path, path, force=False)


def test_read_missing_file(tmp_path):
    with pytest.raises(MithrilVeilError, match="not found"):
        read_text_file(tmp_path / "missing.txt")
