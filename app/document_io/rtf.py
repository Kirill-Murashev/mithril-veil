"""Plain-text extraction from RTF input (no formatting, images, or embedded objects)."""

from __future__ import annotations

from pathlib import Path

from striprtf.striprtf import rtf_to_text

from app.core.exceptions import EmptyExtractedText, MithrilVeilError


def _decode_rtf_bytes(raw: bytes) -> str:
    if not raw:
        return ""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")


def read_rtf_text(path: Path) -> str:
    """
    Extract plain text from an RTF file using striprtf.

    Limitations: formatting is not preserved; embedded objects and images are not
    extracted (binary picture groups are stripped by the parser). Complex macros
    or OLE payloads are not executed.
    """
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MithrilVeilError("Cannot read RTF file.") from exc

    if not raw.strip():
        raise EmptyExtractedText("RTF file contains no extractable text.")

    try:
        text = rtf_to_text(_decode_rtf_bytes(raw))
    except (ValueError, UnicodeError) as exc:
        raise MithrilVeilError("Cannot extract text from RTF file.") from exc
    except Exception as exc:
        raise MithrilVeilError("Cannot extract text from RTF file.") from exc

    combined = text.strip()
    if not combined:
        raise EmptyExtractedText("RTF file contains no extractable text.")
    return combined
