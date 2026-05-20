"""Generate synthetic DOCX/PDF fixtures in tests (not committed binaries)."""

from pathlib import Path

SYNTHETIC_CONTACT_LINE = "Контакт: test@example.local"


def write_synthetic_rtf(path: Path, text: str = SYNTHETIC_CONTACT_LINE) -> None:
    """Write a minimal synthetic UTF-8 RTF fixture (plain-text extraction only)."""
    escaped = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    body = f"{{\\rtf1\\ansi {escaped}}}"
    path.write_text(body, encoding="utf-8")


def write_synthetic_rtf_cp1251(path: Path, text: str = SYNTHETIC_CONTACT_LINE) -> None:
    """Write a legacy cp1251 RTF with \\ansicpg1251 (synthetic Cyrillic-safe bytes only)."""
    payload = text.encode("cp1251")
    path.write_bytes(b"{\\rtf1\\ansi\\ansicpg1251 " + payload + b"}")


def write_synthetic_rtf_unicode_escapes(path: Path) -> None:
    """Write RTF using \\u escape sequences for Cyrillic (Иван + synthetic email)."""
    body = r"{\rtf1\ansi \u1048?\u1072?\u1085? test@example.local}"
    path.write_text(body, encoding="utf-8")


def write_synthetic_docx(path: Path, text: str = SYNTHETIC_CONTACT_LINE) -> None:
    from docx import Document

    document = Document()
    document.add_paragraph(text)
    table = document.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "ООО Тестовая Организация"
    document.save(path)


def write_synthetic_pdf(path: Path, text: str = SYNTHETIC_CONTACT_LINE) -> None:
    from reportlab.pdfgen import canvas

    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, text)
    pdf.save()


def write_encrypted_pdf(path: Path, password: str = "synthetic-test") -> None:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt(password)
    with path.open("wb") as handle:
        writer.write(handle)


def write_blank_pdf(path: Path) -> None:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with path.open("wb") as handle:
        writer.write(handle)
