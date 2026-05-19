from app.core.exceptions import UnsupportedDocumentType


def raise_pdf_not_supported() -> None:
    raise UnsupportedDocumentType("PDF support is planned but not implemented yet.")
