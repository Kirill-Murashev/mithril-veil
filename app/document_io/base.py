from pathlib import Path

from app.core.exceptions import (
    InputFileTooLarge,
    MithrilVeilError,
    UnsafeFileOperation,
    UnsupportedDocumentType,
)
from app.document_io.limits import MAX_INPUT_FILE_BYTES

SUPPORTED_INPUT_EXTENSIONS: dict[str, str] = {
    ".txt": "txt",
    ".md": "markdown",
    ".markdown": "markdown",
    ".docx": "docx",
    ".pdf": "pdf",
    ".rtf": "rtf",
    ".odt": "odt",
}

SUPPORTED_OUTPUT_EXTENSIONS: frozenset[str] = frozenset({".txt", ".md", ".markdown"})

SourceMetadata = dict[str, str | int]


def detect_supported_file_type(path: Path) -> str:
    """Return logical input file type; raise for unsupported extensions."""
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_INPUT_EXTENSIONS:
        return SUPPORTED_INPUT_EXTENSIONS[suffix]
    if suffix:
        raise UnsupportedDocumentType(f"Unsupported file type: {suffix}")
    raise UnsupportedDocumentType(
        "File has no extension; supported types: .txt, .md, .markdown, .docx, .pdf, .rtf, .odt"
    )


def detect_supported_output_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return "txt"
    if suffix in (".md", ".markdown"):
        return "markdown"
    raise UnsupportedDocumentType(
        f"Unsupported output file type: {suffix or '(none)'}. Use .txt, .md, or .markdown."
    )


def check_input_file_size(path: Path) -> int:
    if not path.is_file():
        raise MithrilVeilError(f"Input file not found: {path}")
    size = path.stat().st_size
    if size > MAX_INPUT_FILE_BYTES:
        raise InputFileTooLarge(f"Input file exceeds maximum size ({MAX_INPUT_FILE_BYTES} bytes).")
    return size


def ensure_safe_output_path(
    input_path: Path,
    output_path: Path,
    *,
    force: bool,
) -> None:
    if input_path.resolve() == output_path.resolve():
        raise UnsafeFileOperation(
            "Output path must not be the same as input path. Refusing to overwrite input."
        )
    detect_supported_output_type(output_path)
    if output_path.exists() and not force:
        raise UnsafeFileOperation(
            f"Output file already exists: {output_path}. Use --force to overwrite."
        )


def ensure_safe_report_path(report_path: Path, *, force: bool) -> None:
    if report_path.exists() and not force:
        raise UnsafeFileOperation(
            f"Report file already exists: {report_path}. Use --force to overwrite."
        )


def ensure_safe_mapping_path(mapping_path: Path, *, force: bool) -> None:
    """Validate encrypted mapping suffix and refuse overwrite without --force."""
    from app.security.encrypted_mapping import require_encrypted_mapping_path

    require_encrypted_mapping_path(mapping_path)
    if mapping_path.exists() and not force:
        raise UnsafeFileOperation(
            f"Mapping file already exists: {mapping_path}. Use --force to overwrite."
        )


def ensure_mapping_path_distinct(
    mapping_path: Path,
    *,
    input_path: Path | None = None,
    output_path: Path | None = None,
    report_path: Path | None = None,
) -> None:
    """Refuse mapping output that would overwrite input, anonymized output, or report."""
    resolved = mapping_path.resolve()
    for label, other in (
        ("input", input_path),
        ("output", output_path),
        ("report", report_path),
    ):
        if other is not None and other.resolve() == resolved:
            raise UnsafeFileOperation(
                f"Mapping path must not be the same as the {label} path: {mapping_path}."
            )


def read_document_file(path: Path) -> tuple[str, SourceMetadata]:
    """Read supported input document and return text plus safe source metadata."""
    file_size = check_input_file_size(path)
    input_type = detect_supported_file_type(path)
    source: SourceMetadata = {
        "input_type": input_type,
        "file_size_bytes": file_size,
    }

    if input_type in ("txt", "markdown"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise MithrilVeilError(f"Cannot read file: {path}") from exc
    elif input_type == "docx":
        from app.document_io.docx import read_docx_text

        text = read_docx_text(path)
    elif input_type == "pdf":
        from app.document_io.pdf import read_pdf_text

        text, page_count = read_pdf_text(path)
        source["page_count"] = page_count
    elif input_type == "rtf":
        from app.document_io.rtf import read_rtf_text

        text = read_rtf_text(path)
    elif input_type == "odt":
        from app.document_io.odt import read_odt_text

        text = read_odt_text(path)
    else:
        raise UnsupportedDocumentType(f"Unsupported input type: {input_type}")

    return text, source


def read_text_file(path: Path) -> str:
    """Backward-compatible reader returning text only."""
    text, _ = read_document_file(path)
    return text


def write_text_file(path: Path, text: str, *, force: bool = False) -> None:
    detect_supported_output_type(path)
    if path.exists() and not force:
        raise UnsafeFileOperation(f"Output file already exists: {path}. Use --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise MithrilVeilError(f"Cannot write file: {path}") from exc
