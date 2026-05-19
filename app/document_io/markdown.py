from pathlib import Path

from app.document_io.base import read_text_file as _read_text_file
from app.document_io.base import write_text_file as _write_text_file


def read_markdown(path: Path) -> str:
    return _read_text_file(path)


def write_markdown(path: Path, text: str, *, force: bool = False) -> None:
    _write_text_file(path, text, force=force)
