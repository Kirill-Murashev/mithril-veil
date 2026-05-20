"""Batch directory ingestion for CLI anonymize-dir (safe paths, no raw values in reports)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.core.exceptions import MithrilVeilError, UnsafeFileOperation
from app.document_io.base import SUPPORTED_INPUT_EXTENSIONS

BATCH_OUTPUT_SUFFIX = ".anonymized.txt"


class BatchFileStatus(StrEnum):
    PROCESSED = "processed"
    SKIPPED_UNSUPPORTED = "skipped_unsupported"
    FAILED = "failed"


@dataclass(frozen=True)
class BatchInputFile:
    """A supported file under the input directory (relative path from input root)."""

    absolute_path: Path
    relative_path: Path


@dataclass
class BatchFileResult:
    relative_path: str
    status: BatchFileStatus
    output_relative_path: str | None = None
    error_message: str | None = None
    total_entities: int | None = None
    entity_counts: dict[str, int] | None = None


def is_supported_batch_input(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS


def is_hidden_relative_path(relative: Path) -> bool:
    return any(part.startswith(".") and part not in (".", "..") for part in relative.parts)


def batch_output_relative_path(relative_input: Path) -> Path:
    """Map ``docs/a.docx`` → ``docs/a.anonymized.txt`` (plain text output)."""
    return relative_input.parent / f"{relative_input.stem}{BATCH_OUTPUT_SUFFIX}"


def ensure_safe_batch_directories(input_dir: Path, output_dir: Path) -> None:
    if not input_dir.is_dir():
        raise MithrilVeilError(f"Input directory not found: {input_dir}")
    input_resolved = input_dir.resolve()
    output_resolved = output_dir.resolve()
    if input_resolved == output_resolved:
        raise UnsafeFileOperation("Output directory must not be the same as the input directory.")
    try:
        output_resolved.relative_to(input_resolved)
    except ValueError:
        return
    raise UnsafeFileOperation(
        "Output directory must not be inside the input directory "
        "(would risk re-processing sanitized outputs)."
    )


def collect_batch_input_files(
    input_dir: Path,
    *,
    include_hidden: bool = False,
    max_files: int | None = None,
) -> tuple[list[BatchInputFile], list[str]]:
    """
    Recursively collect supported input files.

    Returns (files, skipped_relative_paths) for unsupported extensions encountered.
    """
    input_resolved = input_dir.resolve()
    supported: list[BatchInputFile] = []
    skipped: list[str] = []

    for path in sorted(input_resolved.rglob("*")):
        if not path.is_file():
            continue
        try:
            relative = path.relative_to(input_resolved)
        except ValueError:
            continue
        if not include_hidden and is_hidden_relative_path(relative):
            continue
        if is_supported_batch_input(path):
            supported.append(BatchInputFile(absolute_path=path, relative_path=relative))
            if max_files is not None and len(supported) > max_files:
                raise MithrilVeilError(
                    f"Batch limit exceeded: more than {max_files} supported files found."
                )
        elif path.suffix:
            skipped.append(relative.as_posix())

    return supported, skipped


def resolve_batch_output_path(
    input_dir: Path,
    output_dir: Path,
    relative_input: Path,
) -> Path:
    relative_out = batch_output_relative_path(relative_input)
    return output_dir.resolve() / relative_out


def ensure_batch_output_writable(output_path: Path, *, force: bool) -> None:
    if output_path.exists() and not force:
        raise UnsafeFileOperation(
            f"Output file already exists: {output_path}. Use --force to overwrite."
        )
