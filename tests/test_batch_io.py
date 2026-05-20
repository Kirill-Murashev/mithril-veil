"""Unit tests for batch directory I/O helpers (no CLI)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from app.core.exceptions import UnsafeFileOperation
from app.document_io.batch import (
    batch_output_relative_path,
    collect_batch_input_files,
    ensure_safe_batch_directories,
    ensure_safe_batch_report_path,
    find_batch_output_collisions,
    is_hidden_relative_path,
    is_supported_batch_input,
)


def test_is_supported_batch_input_case_insensitive(tmp_path: Path):
    for name in ("doc.TXT", "note.Md", "paper.PDF", "sheet.DOCX"):
        path = tmp_path / name
        path.write_text("x", encoding="utf-8")
        assert is_supported_batch_input(path)


def test_is_hidden_relative_path_detects_hidden_dirs():
    assert is_hidden_relative_path(Path(".cache/notes.txt"))
    assert not is_hidden_relative_path(Path("visible/notes.txt"))


def test_collect_skips_symlinked_file(tmp_path: Path):
    root = tmp_path / "in"
    root.mkdir()
    real = root / "real.txt"
    real.write_text("data", encoding="utf-8")
    link = root / "link.txt"
    os.symlink(real, link)
    collected = collect_batch_input_files(root)
    assert len(collected.supported) == 1
    assert collected.supported[0].relative_path == Path("real.txt")
    assert collected.skipped_symlink == ["link.txt"]


def test_collect_does_not_follow_symlinked_directory(tmp_path: Path):
    root = tmp_path / "in"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_text("data", encoding="utf-8")
    os.symlink(outside, root / "linked_dir")
    collected = collect_batch_input_files(root)
    assert collected.supported == []
    assert collected.skipped_symlink == []


def test_collect_skips_hidden_directory_by_default(tmp_path: Path):
    root = tmp_path / "in"
    hidden_dir = root / ".vault"
    hidden_dir.mkdir(parents=True)
    (hidden_dir / "secret.txt").write_text("data", encoding="utf-8")
    (root / "open.txt").write_text("data", encoding="utf-8")
    collected = collect_batch_input_files(root)
    assert len(collected.supported) == 1
    assert collected.supported[0].relative_path == Path("open.txt")
    assert collected.skipped_hidden == [".vault/secret.txt"]


def test_collect_include_hidden_directory(tmp_path: Path):
    root = tmp_path / "in"
    hidden_dir = root / ".vault"
    hidden_dir.mkdir(parents=True)
    (hidden_dir / "secret.txt").write_text("data", encoding="utf-8")
    collected = collect_batch_input_files(root, include_hidden=True)
    assert len(collected.supported) == 1
    assert collected.skipped_hidden == []


def test_find_batch_output_collisions_stem_clash():
    from app.document_io.batch import BatchInputFile

    files = [
        BatchInputFile(Path("/a.txt"), Path("a.txt")),
        BatchInputFile(Path("/a.md"), Path("a.md")),
    ]
    errors = find_batch_output_collisions(files)
    assert len(errors) == 1
    assert "a.anonymized.txt" in errors[0]


def test_ensure_safe_batch_directories_resolves_relative_paths(tmp_path: Path):
    base = tmp_path / "tree"
    base.mkdir()
    input_dir = base / "input"
    input_dir.mkdir()
    sibling = base / "output"
    sibling.mkdir()
    os.chdir(base)
    ensure_safe_batch_directories(Path("input"), Path("output"))


def test_ensure_safe_batch_directories_rejects_output_inside_input_via_dotdot(
    tmp_path: Path,
):
    base = tmp_path / "tree"
    input_dir = base / "input"
    nested = input_dir / "nested"
    nested.mkdir(parents=True)
    with pytest.raises(UnsafeFileOperation):
        ensure_safe_batch_directories(input_dir, nested / ".." / "nested" / "out")


def test_ensure_safe_batch_report_rejects_inside_input(tmp_path: Path):
    root = tmp_path / "in"
    root.mkdir()
    (root / "a.txt").write_text("x", encoding="utf-8")
    report = root / "report.json"
    collected = collect_batch_input_files(root)
    with pytest.raises(UnsafeFileOperation, match="inside the input"):
        ensure_safe_batch_report_path(
            report,
            root,
            tmp_path / "out",
            collected.supported,
            force=False,
        )


def test_batch_output_relative_path_convention():
    assert batch_output_relative_path(Path("docs/a.docx")) == Path("docs/a.anonymized.txt")
    assert batch_output_relative_path(Path("note.md")) == Path("note.anonymized.txt")
