"""RTF ingestion hardening tests (synthetic data only)."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.core.exceptions import EmptyExtractedText, InputFileTooLarge, MithrilVeilError
from app.document_io.base import read_document_file
from app.document_io.limits import MAX_INPUT_FILE_BYTES
from app.document_io.rtf import read_rtf_text
from tests.fixtures_generators import (
    write_synthetic_rtf,
    write_synthetic_rtf_cp1251,
    write_synthetic_rtf_unicode_escapes,
)

SYNTHETIC_EMAIL = "test@example.local"


def test_rtf_utf8_cyrillic_extraction(tmp_path: Path):
    path = tmp_path / "utf8.rtf"
    write_synthetic_rtf(path, "Иван Тестович " + SYNTHETIC_EMAIL)
    text = read_rtf_text(path)
    assert "Иван" in text
    assert SYNTHETIC_EMAIL in text


def test_rtf_cp1251_legacy_encoding(tmp_path: Path):
    path = tmp_path / "legacy.rtf"
    write_synthetic_rtf_cp1251(path, "Контакт: " + SYNTHETIC_EMAIL)
    text = read_rtf_text(path)
    assert "Контакт" in text
    assert SYNTHETIC_EMAIL in text


def test_rtf_unicode_escape_sequences(tmp_path: Path):
    path = tmp_path / "unicode.rtf"
    write_synthetic_rtf_unicode_escapes(path)
    text = read_rtf_text(path)
    assert "И" in text
    assert SYNTHETIC_EMAIL in text


def test_rtf_malformed_braces_best_effort(tmp_path: Path):
    path = tmp_path / "broken.rtf"
    path.write_text(
        "{\\rtf1\\ansi hello {unclosed " + SYNTHETIC_EMAIL,
        encoding="utf-8",
    )
    text = read_rtf_text(path)
    assert "hello" in text
    assert SYNTHETIC_EMAIL in text


def test_rtf_formatting_only_raises_empty(tmp_path: Path):
    path = tmp_path / "format.rtf"
    path.write_text("{\\rtf1\\ansi \\b \\i \\par \\par}", encoding="utf-8")
    with pytest.raises(EmptyExtractedText):
        read_rtf_text(path)


def test_rtf_pict_group_no_binary_in_output(tmp_path: Path):
    path = tmp_path / "pict.rtf"
    path.write_text(
        "{\\rtf1\\ansi " + SYNTHETIC_EMAIL + " Contact \\pict\\pngblip\\x01\\x02\\x03}",
        encoding="utf-8",
    )
    text = read_rtf_text(path)
    assert SYNTHETIC_EMAIL in text
    assert "\x01" not in text
    assert "pngblip" not in text
    assert "Contact" in text


def test_rtf_object_group_strips_embedded_payload(tmp_path: Path):
    path = tmp_path / "object.rtf"
    path.write_text(
        "{\\rtf1\\ansi before {\\object\\objemb secret-payload} after " + SYNTHETIC_EMAIL + "}",
        encoding="utf-8",
    )
    text = read_rtf_text(path)
    assert SYNTHETIC_EMAIL in text
    assert "secret-payload" not in text
    assert "objemb" not in text


def test_rtf_bin_group_hex_stripped_from_output(tmp_path: Path):
    path = tmp_path / "bin.rtf"
    path.write_text(
        "{\\rtf1\\ansi Contact: " + SYNTHETIC_EMAIL + " \\bin8 0102030405060708}",
        encoding="utf-8",
    )
    text = read_rtf_text(path)
    assert SYNTHETIC_EMAIL in text
    assert "0102030405060708" not in text


def test_rtf_input_file_too_large(tmp_path: Path):
    path = tmp_path / "big.rtf"
    path.write_bytes(b"{\\rtf1\\ansi " + b"x" * (MAX_INPUT_FILE_BYTES + 1) + b"}")
    with pytest.raises(InputFileTooLarge):
        read_document_file(path)


def test_rtf_striprtf_failure_wrapped_safely(monkeypatch, tmp_path: Path):
    path = tmp_path / "fail.rtf"
    write_synthetic_rtf(path)

    def boom(_rtf: str, **_kwargs: object) -> str:
        raise RuntimeError("synthetic parser failure with " + SYNTHETIC_EMAIL)

    monkeypatch.setattr("app.document_io.rtf.rtf_to_text", boom)
    with pytest.raises(MithrilVeilError, match="Cannot extract text from RTF file"):
        read_rtf_text(path)


def test_rtf_errors_never_echo_document_content(tmp_path: Path):
    path = tmp_path / "empty.rtf"
    path.write_text("{\\rtf1}", encoding="utf-8")
    with pytest.raises(EmptyExtractedText) as exc_info:
        read_rtf_text(path)
    assert SYNTHETIC_EMAIL not in str(exc_info.value)


def test_rtf_malformed_raises_safe_error_when_unparseable(monkeypatch, tmp_path: Path):
    path = tmp_path / "bad.rtf"
    path.write_bytes(b"\xff\xfe\xfd")

    def boom(_rtf: str, **_kwargs: object) -> str:
        raise ValueError("decode failed with " + SYNTHETIC_EMAIL)

    monkeypatch.setattr("app.document_io.rtf.rtf_to_text", boom)
    with pytest.raises(MithrilVeilError, match="Cannot extract text from RTF file") as exc_info:
        read_rtf_text(path)
    assert SYNTHETIC_EMAIL not in str(exc_info.value)
