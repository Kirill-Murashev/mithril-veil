"""Plain-text extraction from RTF input (no formatting, images, or embedded objects)."""

from __future__ import annotations

import re
from pathlib import Path

from striprtf.striprtf import rtf_to_text

from app.core.exceptions import EmptyExtractedText, MithrilVeilError

# Hex runs left when \\bin groups are stripped (8+ nibbles).
_BIN_HEX_ARTIFACT_RE = re.compile(r"(?<!\w)[0-9a-fA-F]{8,}(?!\w)")
_ANSI_CODE_PAGE_RE = re.compile(r"\\ansicpg(\d+)", re.IGNORECASE)


def _sniff_code_page(header: str) -> str | None:
    match = _ANSI_CODE_PAGE_RE.search(header)
    if not match:
        return None
    page = match.group(1)
    if page in ("1251", "204"):
        return "cp1251"
    if page in ("1252", "1250"):
        return "cp1252"
    if page == "65001":
        return "utf-8"
    return None


def _decode_rtf_bytes(raw: bytes) -> tuple[str, str]:
    """
    Decode RTF file bytes for striprtf.

    Order: UTF-8 (with optional BOM) first for modern fixtures; if bytes are not
    valid UTF-8, use \\ansicpg1251 → cp1251 (common for Russian legacy RTF);
    otherwise latin-1 (byte-preserving) so control-word escapes still parse.
    """
    if not raw.strip():
        return "", "utf-8"

    header = raw[:2048].decode("latin-1", errors="ignore")
    declared = _sniff_code_page(header)

    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8"

    try:
        decoded = raw.decode("utf-8")
        return decoded, declared or "utf-8"
    except UnicodeDecodeError:
        pass

    if declared == "cp1251":
        return raw.decode("cp1251", errors="replace"), "cp1251"

    return raw.decode("latin-1", errors="replace"), declared or "latin-1"


def _striprtf_encoding(codec: str) -> str:
    if codec in ("utf-8", "utf8"):
        return "utf-8"
    if codec == "cp1251":
        return "cp1251"
    if codec in ("cp1252", "latin-1"):
        return "cp1252"
    return "cp1252"


def _sanitize_extracted_text(text: str) -> str:
    """Drop control chars and binary hex artifacts; never inject document bytes into errors."""
    cleaned: list[str] = []
    for char in text:
        if char in "\n\r\t":
            cleaned.append(char)
        elif ord(char) >= 32 or char == "\u00a0":
            cleaned.append(char)
    result = "".join(cleaned)
    result = _BIN_HEX_ARTIFACT_RE.sub(" ", result)
    result = re.sub(r"[ \t]+", " ", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def read_rtf_text(path: Path) -> str:
    """
    Extract plain text from an RTF file using striprtf (best-effort).

    Malformed RTF is parsed leniently when striprtf can recover readable text.
    Embedded \\pict/\\object/\\bin groups are not extracted; leftover \\bin hex
    may be removed in post-processing. Formatting-only documents raise
    ``EmptyExtractedText``. Errors never include raw file content.
    """
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MithrilVeilError("Cannot read RTF file.") from exc

    if not raw.strip():
        raise EmptyExtractedText("RTF file contains no extractable text.")

    rtf_string, codec = _decode_rtf_bytes(raw)

    try:
        extracted = rtf_to_text(
            rtf_string,
            encoding=_striprtf_encoding(codec),
            errors="replace",
        )
    except (ValueError, UnicodeError, LookupError) as exc:
        raise MithrilVeilError("Cannot extract text from RTF file.") from exc
    except Exception as exc:
        raise MithrilVeilError("Cannot extract text from RTF file.") from exc

    combined = _sanitize_extracted_text(extracted)
    if not combined:
        raise EmptyExtractedText("RTF file contains no extractable text.")
    return combined
