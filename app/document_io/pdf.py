from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.exceptions import (
    EncryptedDocumentUnsupported,
    MithrilVeilError,
    UnsupportedDocumentType,
)
from app.document_io.limits import MAX_PDF_PAGES


def read_pdf_text(path: Path) -> tuple[str, int]:
    """Extract text from a text-based PDF. Returns (text, page_count)."""
    try:
        reader = PdfReader(path, strict=False)
    except (OSError, PdfReadError, ValueError) as exc:
        raise MithrilVeilError("Cannot read PDF file.") from exc

    if reader.is_encrypted:
        raise EncryptedDocumentUnsupported("Encrypted PDF files are not supported.")

    page_count = len(reader.pages)
    if page_count > MAX_PDF_PAGES:
        raise UnsupportedDocumentType(f"PDF exceeds maximum page limit ({MAX_PDF_PAGES} pages).")

    parts: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        if extracted.strip():
            parts.append(extracted.strip())

    combined = "\n".join(parts).strip()
    if not combined:
        raise UnsupportedDocumentType("PDF has no extractable text. OCR is not implemented.")

    return combined, page_count
