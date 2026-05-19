from pathlib import Path

from app.core.exceptions import MithrilVeilError, UnsafeFileOperation, UnsupportedDocumentType

SUPPORTED_TEXT_EXTENSIONS: dict[str, str] = {
    ".txt": "txt",
    ".md": "markdown",
    ".markdown": "markdown",
}


def detect_supported_file_type(path: Path) -> str:
    """Return logical file type for supported text formats; raise for unsupported."""
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_TEXT_EXTENSIONS:
        return SUPPORTED_TEXT_EXTENSIONS[suffix]
    if suffix == ".docx":
        from app.document_io.docx import raise_docx_not_supported

        raise_docx_not_supported()
    if suffix == ".pdf":
        from app.document_io.pdf import raise_pdf_not_supported

        raise_pdf_not_supported()
    if suffix == ".rtf":
        raise UnsupportedDocumentType("RTF is not supported.")
    if suffix:
        raise UnsupportedDocumentType(f"Unsupported file type: {suffix}")
    raise UnsupportedDocumentType("File has no extension; supported types: .txt, .md, .markdown")


def ensure_safe_output_path(
    input_path: Path,
    output_path: Path,
    *,
    force: bool,
) -> None:
    """Refuse to overwrite the input file or an existing output without --force."""
    if input_path.resolve() == output_path.resolve():
        raise UnsafeFileOperation(
            "Output path must not be the same as input path. Refusing to overwrite input."
        )
    if output_path.exists() and not force:
        raise UnsafeFileOperation(
            f"Output file already exists: {output_path}. Use --force to overwrite."
        )


def ensure_safe_report_path(report_path: Path, *, force: bool) -> None:
    if report_path.exists() and not force:
        raise UnsafeFileOperation(
            f"Report file already exists: {report_path}. Use --force to overwrite."
        )


def read_text_file(path: Path) -> str:
    if not path.is_file():
        raise MithrilVeilError(f"Input file not found: {path}")
    detect_supported_file_type(path)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MithrilVeilError(f"Cannot read file: {path}") from exc


def write_text_file(path: Path, text: str, *, force: bool = False) -> None:
    if path.exists() and not force:
        raise UnsafeFileOperation(f"Output file already exists: {path}. Use --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise MithrilVeilError(f"Cannot write file: {path}") from exc
