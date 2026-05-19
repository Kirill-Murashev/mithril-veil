from app.core.exceptions import UnsupportedDocumentType


def raise_docx_not_supported() -> None:
    raise UnsupportedDocumentType("DOCX support is planned but not implemented yet.")
