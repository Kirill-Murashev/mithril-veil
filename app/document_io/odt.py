"""Plain-text extraction from ODT input (ZIP + content.xml; no formatting or embedded objects)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from app.core.exceptions import EmptyExtractedText, MithrilVeilError

_CONTENT_XML = "content.xml"
_TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
_TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
_OFFICE_NS = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"

_TEXT_P = f"{{{_TEXT_NS}}}p"
_TEXT_H = f"{{{_TEXT_NS}}}h"
_TEXT_SPAN = f"{{{_TEXT_NS}}}span"
_TEXT_LINE_BREAK = f"{{{_TEXT_NS}}}line-break"
_TABLE_TABLE = f"{{{_TABLE_NS}}}table"
_TABLE_ROW = f"{{{_TABLE_NS}}}table-row"
_TABLE_CELL = f"{{{_TABLE_NS}}}table-cell"
_OFFICE_BODY = f"{{{_OFFICE_NS}}}body"
_OFFICE_TEXT = f"{{{_OFFICE_NS}}}text"

_BLOCK_TAGS = frozenset({_TEXT_P, _TEXT_H, _TABLE_ROW})


def _collect_inline_text(element: ET.Element) -> str:
    """Gather character data and line breaks from inline ODF text markup."""
    chunks: list[str] = []
    if element.text:
        chunks.append(element.text)
    for child in element:
        if child.tag == _TEXT_LINE_BREAK:
            chunks.append("\n")
        else:
            chunks.append(_collect_inline_text(child))
        if child.tail:
            chunks.append(child.tail)
    return "".join(chunks)


def _extract_block_text(element: ET.Element) -> str:
    return _collect_inline_text(element).strip()


def _walk_office_text(office_text: ET.Element, parts: list[str]) -> None:
    """Traverse ``office:text`` children in document order."""
    for child in office_text:
        tag = child.tag
        if tag in (_TEXT_P, _TEXT_H):
            text = _extract_block_text(child)
            if text:
                parts.append(text)
        elif tag == _TABLE_TABLE:
            _walk_table(child, parts)
        elif tag == _TABLE_ROW:
            _walk_table_row(child, parts)
        else:
            _walk_office_text(child, parts)


def _walk_table(table: ET.Element, parts: list[str]) -> None:
    for child in table:
        if child.tag == _TABLE_ROW:
            _walk_table_row(child, parts)
        elif child.tag == _TABLE_TABLE:
            _walk_table(child, parts)


def _walk_table_row(row: ET.Element, parts: list[str]) -> None:
    for cell in row:
        if cell.tag != _TABLE_CELL:
            continue
        cell_parts: list[str] = []
        for child in cell:
            if child.tag in (_TEXT_P, _TEXT_H):
                text = _extract_block_text(child)
                if text:
                    cell_parts.append(text)
            elif child.tag == _TABLE_TABLE:
                _walk_table(child, cell_parts)
            else:
                _walk_office_text(child, cell_parts)
        if cell_parts:
            parts.extend(cell_parts)


def _find_office_text(root: ET.Element) -> ET.Element | None:
    for body in root.iter(_OFFICE_BODY):
        for office_text in body:
            if office_text.tag == _OFFICE_TEXT:
                return office_text
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
            try:
                raw_xml = archive.read(_CONTENT_XML)
            except KeyError as exc:
                raise MithrilVeilError("Cannot extract text from ODT file.") from exc
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

    parts: list[str] = []
    _walk_office_text(office_text, parts)
    combined = "\n".join(parts).strip()
    if not combined:
        raise EmptyExtractedText("ODT file contains no extractable text.")
    return combined
