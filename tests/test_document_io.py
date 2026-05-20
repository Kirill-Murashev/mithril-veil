import pytest
from app.core.exceptions import (
    EmptyExtractedText,
    EncryptedDocumentUnsupported,
    InputFileTooLarge,
    MithrilVeilError,
    UnsafeFileOperation,
    UnsupportedDocumentType,
)
from app.document_io.base import (
    detect_supported_file_type,
    ensure_safe_output_path,
    read_document_file,
    read_text_file,
    write_text_file,
)
from app.document_io.docx import read_docx_text
from app.document_io.limits import MAX_INPUT_FILE_BYTES, MAX_PDF_PAGES
from app.document_io.pdf import read_pdf_text
from app.document_io.rtf import read_rtf_text
from tests.fixtures_generators import (
    write_blank_pdf,
    write_encrypted_pdf,
    write_synthetic_docx,
    write_synthetic_pdf,
    write_synthetic_rtf,
)

SYNTHETIC_EMAIL = "test@example.local"


def test_detect_supported_txt(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("hello", encoding="utf-8")
    assert detect_supported_file_type(path) == "txt"


def test_detect_supported_md(tmp_path):
    path = tmp_path / "sample.md"
    path.write_text("# title", encoding="utf-8")
    assert detect_supported_file_type(path) == "markdown"


def test_detect_supported_docx(tmp_path):
    path = tmp_path / "sample.docx"
    write_synthetic_docx(path)
    assert detect_supported_file_type(path) == "docx"


def test_detect_supported_pdf(tmp_path):
    path = tmp_path / "sample.pdf"
    write_synthetic_pdf(path)
    assert detect_supported_file_type(path) == "pdf"


def test_detect_supported_rtf(tmp_path):
    path = tmp_path / "sample.rtf"
    write_synthetic_rtf(path)
    assert detect_supported_file_type(path) == "rtf"


def test_detect_supported_rtf_uppercase_extension(tmp_path):
    path = tmp_path / "SAMPLE.RTF"
    write_synthetic_rtf(path)
    assert detect_supported_file_type(path) == "rtf"


def test_read_docx_extracts_synthetic_text(tmp_path):
    path = tmp_path / "in.docx"
    write_synthetic_docx(path)
    text = read_docx_text(path)
    assert SYNTHETIC_EMAIL in text
    assert "Тестовая Организация" in text


def test_read_pdf_extracts_synthetic_text(tmp_path):
    path = tmp_path / "in.pdf"
    write_synthetic_pdf(path)
    text, pages = read_pdf_text(path)
    assert SYNTHETIC_EMAIL in text
    assert pages >= 1


def test_read_document_file_docx_metadata(tmp_path):
    path = tmp_path / "in.docx"
    write_synthetic_docx(path)
    text, source = read_document_file(path)
    assert SYNTHETIC_EMAIL in text
    assert source["input_type"] == "docx"
    assert source["file_size_bytes"] > 0


def test_read_document_file_pdf_metadata(tmp_path):
    path = tmp_path / "in.pdf"
    write_synthetic_pdf(path)
    text, source = read_document_file(path)
    assert SYNTHETIC_EMAIL in text
    assert source["input_type"] == "pdf"
    assert source["page_count"] >= 1


def test_empty_docx_raises(tmp_path):
    from docx import Document

    path = tmp_path / "empty.docx"
    Document().save(path)
    with pytest.raises(EmptyExtractedText):
        read_docx_text(path)


def test_encrypted_pdf_raises(tmp_path):
    path = tmp_path / "locked.pdf"
    write_encrypted_pdf(path)
    with pytest.raises(EncryptedDocumentUnsupported, match="Encrypted"):
        read_pdf_text(path)


def test_blank_pdf_raises_no_text(tmp_path):
    path = tmp_path / "blank.pdf"
    write_blank_pdf(path)
    with pytest.raises(UnsupportedDocumentType, match="no extractable text"):
        read_pdf_text(path)


def test_input_file_too_large(tmp_path, monkeypatch):
    path = tmp_path / "big.txt"
    path.write_bytes(b"x" * (MAX_INPUT_FILE_BYTES + 1))
    with pytest.raises(InputFileTooLarge):
        read_document_file(path)


def test_pdf_page_limit(tmp_path, monkeypatch):
    from pypdf import PdfWriter

    path = tmp_path / "many.pdf"
    writer = PdfWriter()
    for _ in range(MAX_PDF_PAGES + 1):
        writer.add_blank_page(width=200, height=200)
    with path.open("wb") as handle:
        writer.write(handle)

    with pytest.raises(UnsupportedDocumentType, match="page limit"):
        read_pdf_text(path)


def test_read_write_txt_roundtrip(tmp_path):
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.txt"
    input_path.write_text(f"Контакт: {SYNTHETIC_EMAIL}", encoding="utf-8")
    content = read_text_file(input_path)
    write_text_file(output_path, content.replace(SYNTHETIC_EMAIL, "[EMAIL_1]"))
    assert "[EMAIL_1]" in output_path.read_text(encoding="utf-8")


def test_read_rtf_extracts_synthetic_text(tmp_path):
    path = tmp_path / "in.rtf"
    write_synthetic_rtf(path)
    text = read_rtf_text(path)
    assert SYNTHETIC_EMAIL in text


def test_read_document_file_rtf_metadata(tmp_path):
    path = tmp_path / "in.rtf"
    write_synthetic_rtf(path)
    text, source = read_document_file(path)
    assert SYNTHETIC_EMAIL in text
    assert source["input_type"] == "rtf"
    assert source["file_size_bytes"] > 0


def test_empty_rtf_raises(tmp_path):
    path = tmp_path / "empty.rtf"
    path.write_text("{\\rtf1}", encoding="utf-8")
    with pytest.raises(EmptyExtractedText):
        read_rtf_text(path)


def test_empty_rtf_file_bytes_raises(tmp_path):
    path = tmp_path / "blank.rtf"
    path.write_bytes(b"   ")
    with pytest.raises(EmptyExtractedText):
        read_rtf_text(path)


def test_rtf_binary_blob_does_not_crash(tmp_path):
    path = tmp_path / "with_bin.rtf"
    path.write_text(
        "{\\rtf1\\ansi Contact: test@example.local \\bin8 0102030405060708}",
        encoding="utf-8",
    )
    text = read_rtf_text(path)
    assert SYNTHETIC_EMAIL in text


def test_rtf_error_messages_contain_no_raw_email(tmp_path):
    path = tmp_path / "empty.rtf"
    path.write_text("{\\rtf1}", encoding="utf-8")
    with pytest.raises(EmptyExtractedText) as exc_info:
        read_rtf_text(path)
    assert SYNTHETIC_EMAIL not in str(exc_info.value)


def test_unsupported_output_extension(tmp_path):
    path = tmp_path / "out.pdf"
    with pytest.raises(UnsupportedDocumentType, match="output"):
        write_text_file(path, "text", force=False)


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
        read_document_file(tmp_path / "missing.txt")
