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
    SKIPPED_HIDDEN = "skipped_hidden"
    SKIPPED_SYMLINK = "skipped_symlink"
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


@dataclass(frozen=True)
class BatchCollectResult:
    """Files discovered during batch collection (deterministic ordering)."""

    supported: list[BatchInputFile]
    skipped_unsupported: list[str]
    skipped_hidden: list[str]
    skipped_symlink: list[str]


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


def _relative_from_input(path: Path, input_resolved: Path) -> Path | None:
    try:
        return path.relative_to(input_resolved)
    except ValueError:
        return None


def collect_batch_input_files(
    input_dir: Path,
    *,
    include_hidden: bool = False,
    max_files: int | None = None,
) -> BatchCollectResult:
    """
    Recursively collect supported input files without following symlinked directories.

    Symlinked files are listed in ``skipped_symlink`` (not processed). Hidden path
    segments (e.g. ``.cache/notes.txt``) are listed in ``skipped_hidden`` when
    ``include_hidden`` is false.
    """
    input_resolved = input_dir.resolve()
    supported: list[BatchInputFile] = []
    skipped_unsupported: list[str] = []
    skipped_hidden: list[str] = []
    skipped_symlink: list[str] = []

    for dirpath, dirnames, filenames in input_resolved.walk(follow_symlinks=False):
        root = Path(dirpath)
        dirnames[:] = sorted(
            d for d in dirnames if not (root / d).is_symlink() and d not in (".", "..")
        )
        for name in sorted(filenames):
            path = root / name
            if not path.is_file():
                continue
            relative = _relative_from_input(path, input_resolved)
            if relative is None:
                continue
            rel_posix = relative.as_posix()

            if path.is_symlink():
                skipped_symlink.append(rel_posix)
                continue

            if not include_hidden and is_hidden_relative_path(relative):
                skipped_hidden.append(rel_posix)
                continue

            if is_supported_batch_input(path):
                supported.append(BatchInputFile(absolute_path=path, relative_path=relative))
                if max_files is not None and len(supported) > max_files:
                    raise MithrilVeilError(
                        f"Batch limit exceeded: more than {max_files} supported files found."
                    )
            elif path.suffix:
                skipped_unsupported.append(rel_posix)

    return BatchCollectResult(
        supported=supported,
        skipped_unsupported=skipped_unsupported,
        skipped_hidden=skipped_hidden,
        skipped_symlink=skipped_symlink,
    )


def find_batch_output_collisions(
    supported: list[BatchInputFile],
) -> list[str]:
    """Return safe error messages when two inputs map to the same output relative path."""
    seen: dict[str, str] = {}
    errors: list[str] = []
    for batch_file in supported:
        out_rel = batch_output_relative_path(batch_file.relative_path).as_posix()
        rel_str = batch_file.relative_path.as_posix()
        if out_rel in seen:
            errors.append(
                f"Duplicate batch output target '{out_rel}' for inputs "
                f"'{seen[out_rel]}' and '{rel_str}'."
            )
        else:
            seen[out_rel] = rel_str
    return errors


def preflight_batch_output_paths(
    input_dir: Path,
    output_dir: Path,
    supported: list[BatchInputFile],
    *,
    force: bool,
) -> None:
    """Ensure every planned output is writable before any file is processed."""
    for batch_file in supported:
        output_path = resolve_batch_output_path(input_dir, output_dir, batch_file.relative_path)
        ensure_batch_output_writable(output_path, force=force)


def ensure_safe_batch_report_path(
    report_path: Path,
    input_dir: Path,
    output_dir: Path,
    supported: list[BatchInputFile],
    *,
    force: bool,
) -> None:
    """Reject report paths that collide with outputs or sit inside the input tree."""
    from app.document_io.base import ensure_safe_report_path

    ensure_safe_report_path(report_path, force=force)
    report_resolved = report_path.resolve()
    input_resolved = input_dir.resolve()
    try:
        report_resolved.relative_to(input_resolved)
    except ValueError:
        pass
    else:
        raise UnsafeFileOperation(
            "Report path must not be inside the input directory "
            "(would risk reading the report as batch input)."
        )

    for batch_file in supported:
        output_path = resolve_batch_output_path(input_dir, output_dir, batch_file.relative_path)
        if report_resolved == output_path.resolve():
            raise UnsafeFileOperation(
                "Report path must not be the same as a batch output file path."
            )


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
