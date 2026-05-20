"""Plain-text extraction from ODT input (ZIP + content.xml; no formatting or embedded objects)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from app.core.exceptions import EmptyExtractedText, MithrilVeilError

_CONTENT_XML = "content.xml"

# Conservative cap on content.xml uncompressed bytes (zip-bomb defense; archive also capped).
MAX_ODT_CONTENT_XML_BYTES = 8 * 1024 * 1024

# Reject content.xml when claimed uncompressed / compressed exceeds this ratio.
MAX_ODT_CONTENT_XML_COMPRESSION_RATIO = 100

# Guard against pathological XML trees without a full validator.
MAX_ODT_XML_DEPTH = 128
MAX_ODT_XML_ELEMENT_COUNT = 250_000

_TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
_TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
_OFFICE_NS = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"

_TEXT_P = f"{{{_TEXT_NS}}}p"
_TEXT_H = f"{{{_TEXT_NS}}}h"
_TEXT_LINE_BREAK = f"{{{_TEXT_NS}}}line-break"
_TABLE_TABLE = f"{{{_TABLE_NS}}}table"
_TABLE_ROW = f"{{{_TABLE_NS}}}table-row"
_TABLE_CELL = f"{{{_TABLE_NS}}}table-cell"

# Local tag names whose subtrees are never scanned for text (images, objects, metadata).
_SKIP_SUBTREE_LOCAL_TAGS = frozenset(
    {
        "annotation",
        "binary-data",
        "bookmark",
        "bookmark-start",
        "bookmark-end",
        "frame",
        "image",
        "object",
        "object-ole",
        "reference-ref",
        "sequence-decls",
    }
)

_BLOCK_LOCAL_TAGS = frozenset({"p", "h", "table-row"})
_TABLE_LOCAL_TAGS = frozenset({"table", "table-row", "table-cell"})


class _OdtXmlBudget:
    """Track XML traversal depth and element count during extraction."""

    __slots__ = ("depth", "elements")

    def __init__(self) -> None:
        self.depth = 0
        self.elements = 0

    def enter(self) -> None:
        self.depth += 1
        self.elements += 1
        if self.depth > MAX_ODT_XML_DEPTH:
            raise MithrilVeilError("Cannot extract text from ODT file.")
        if self.elements > MAX_ODT_XML_ELEMENT_COUNT:
            raise MithrilVeilError("Cannot extract text from ODT file.")

    def leave(self) -> None:
        self.depth -= 1


def _local_name(tag: str) -> str:
    if tag and tag[0] == "{":
        return tag.rsplit("}", 1)[-1]
    return tag


def _is_block_element(element: ET.Element) -> bool:
    return _local_name(element.tag) in _BLOCK_LOCAL_TAGS or element.tag in (
        _TEXT_P,
        _TEXT_H,
        _TABLE_ROW,
    )


def _is_table_element(element: ET.Element) -> bool:
    return _local_name(element.tag) in _TABLE_LOCAL_TAGS or element.tag in (
        _TABLE_TABLE,
        _TABLE_ROW,
        _TABLE_CELL,
    )


def _should_skip_subtree(element: ET.Element) -> bool:
    return _local_name(element.tag) in _SKIP_SUBTREE_LOCAL_TAGS


def _validate_content_xml_entry(info: zipfile.ZipInfo) -> None:
    """Reject dangerous content.xml ZipInfo before reading bytes from the archive."""
    if info.is_dir():
        raise MithrilVeilError("Cannot extract text from ODT file.")

    uncompressed = info.file_size
    if uncompressed > MAX_ODT_CONTENT_XML_BYTES:
        raise MithrilVeilError("ODT file is too large to process safely.")

    compressed = info.compress_size
    if compressed > 0 and uncompressed > compressed * MAX_ODT_CONTENT_XML_COMPRESSION_RATIO:
        raise MithrilVeilError("ODT file is too large to process safely.")


def _read_content_xml(archive: zipfile.ZipFile) -> bytes:
    try:
        info = archive.getinfo(_CONTENT_XML)
    except KeyError as exc:
        raise MithrilVeilError("Cannot extract text from ODT file.") from exc

    _validate_content_xml_entry(info)
    try:
        raw_xml = archive.read(_CONTENT_XML)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise MithrilVeilError("Cannot extract text from ODT file.") from exc

    if len(raw_xml) > MAX_ODT_CONTENT_XML_BYTES:
        raise MithrilVeilError("ODT file is too large to process safely.")
    return raw_xml


def _collect_inline_text(element: ET.Element, budget: _OdtXmlBudget) -> str:
    """Gather character data and line breaks from inline ODF text markup."""
    chunks: list[str] = []
    if element.text:
        chunks.append(element.text)
    for child in element:
        budget.enter()
        try:
            if _should_skip_subtree(child):
                continue
            if _local_name(child.tag) == "line-break" or child.tag == _TEXT_LINE_BREAK:
                chunks.append("\n")
            else:
                chunks.append(_collect_inline_text(child, budget))
        finally:
            budget.leave()
        if child.tail:
            chunks.append(child.tail)
    return "".join(chunks)


def _extract_block_text(element: ET.Element, budget: _OdtXmlBudget) -> str:
    return _collect_inline_text(element, budget).strip()


def _walk_office_text(office_text: ET.Element, parts: list[str], budget: _OdtXmlBudget) -> None:
    """Traverse ``office:text`` children in document order."""
    for child in office_text:
        budget.enter()
        try:
            if _should_skip_subtree(child):
                continue
            if _is_block_element(child):
                text = _extract_block_text(child, budget)
                if text:
                    parts.append(text)
            elif _is_table_element(child) or _local_name(child.tag) == "table":
                _walk_table(child, parts, budget)
            else:
                _walk_office_text(child, parts, budget)
        finally:
            budget.leave()


def _walk_table(table: ET.Element, parts: list[str], budget: _OdtXmlBudget) -> None:
    for child in table:
        budget.enter()
        try:
            if _should_skip_subtree(child):
                continue
            local = _local_name(child.tag)
            if local == "table-row" or child.tag == _TABLE_ROW:
                _walk_table_row(child, parts, budget)
            elif local == "table" or child.tag == _TABLE_TABLE:
                _walk_table(child, parts, budget)
        finally:
            budget.leave()


def _walk_table_row(row: ET.Element, parts: list[str], budget: _OdtXmlBudget) -> None:
    for cell in row:
        budget.enter()
        try:
            if _local_name(cell.tag) != "table-cell" and cell.tag != _TABLE_CELL:
                continue
            if _should_skip_subtree(cell):
                continue
            cell_parts: list[str] = []
            for child in cell:
                budget.enter()
                try:
                    if _should_skip_subtree(child):
                        continue
                    if _is_block_element(child):
                        text = _extract_block_text(child, budget)
                        if text:
                            cell_parts.append(text)
                    elif _is_table_element(child) or _local_name(child.tag) == "table":
                        _walk_table(child, cell_parts, budget)
                    else:
                        _walk_office_text(child, cell_parts, budget)
                finally:
                    budget.leave()
            if cell_parts:
                parts.extend(cell_parts)
        finally:
            budget.leave()


def _find_office_text(root: ET.Element) -> ET.Element | None:
    """Locate ``office:text`` under ``office:body`` (namespace-tolerant)."""
    for element in root.iter():
        if _local_name(element.tag) != "body":
            continue
        for child in element:
            if _local_name(child.tag) == "text":
                return child
    return None


def read_odt_text(path: Path) -> str:
    """
    Extract plain text from an ODT file (ZIP archive with ``content.xml``).

    Parses paragraphs, headings, spans, tables, and line breaks only.
    Ignores styles, metadata, images, and embedded objects. Errors never
    include raw file content or XML fragments.
    """
    try:
        with zipfile.ZipFile(path) as archive:
            raw_xml = _read_content_xml(archive)
    except zipfile.BadZipFile as exc:
        raise MithrilVeilError("Cannot read ODT file.") from exc
    except OSError as exc:
        raise MithrilVeilError("Cannot read ODT file.") from exc

    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as exc:
        raise MithrilVeilError("Cannot extract text from ODT file.") from exc

    office_text = _find_office_text(root)
    if office_text is None:
        raise MithrilVeilError("Cannot extract text from ODT file.")

    budget = _OdtXmlBudget()
    parts: list[str] = []
    _walk_office_text(office_text, parts, budget)
    combined = "\n".join(parts).strip()
    if not combined:
        raise EmptyExtractedText("ODT file contains no extractable text.")
    return combined
