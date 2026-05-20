"""CLI handler for anonymize-dir batch processing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.core.batch_report import (
    build_batch_anonymization_report,
    count_batch_results,
    write_batch_anonymization_report,
)
from app.core.exceptions import (
    EmptyExtractedText,
    EncryptedDocumentUnsupported,
    InputFileTooLarge,
    MithrilVeilError,
    UnsafeFileOperation,
    UnsupportedDocumentType,
)
from app.core.pipeline import run_anonymization
from app.core.schemas import AnonymizeMode
from app.document_io.base import read_document_file, write_text_file
from app.document_io.batch import (
    BatchFileResult,
    BatchFileStatus,
    collect_batch_input_files,
    ensure_safe_batch_directories,
    ensure_safe_batch_report_path,
    find_batch_output_collisions,
    preflight_batch_output_paths,
    resolve_batch_output_path,
)

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_UNSAFE = 2

BATCH_MODES = (AnonymizeMode.REPLACE, AnonymizeMode.REDACT)


def validate_batch_cli_args(args: argparse.Namespace) -> AnonymizeMode:
    if getattr(args, "mapping_output", None):
        raise MithrilVeilError(
            "Batch anonymize-dir does not support --mapping-output. "
            "Use anonymize-file with --mode pseudonymize for encrypted mapping."
        )
    mode_value = args.mode
    if mode_value == AnonymizeMode.PSEUDONYMIZE.value:
        raise MithrilVeilError(
            "Batch anonymize-dir supports only replace and redact modes. "
            "Reversible mapping for directories is not implemented in this release."
        )
    try:
        mode = AnonymizeMode(mode_value)
    except ValueError as exc:
        raise MithrilVeilError(
            f"Invalid batch mode: {mode_value!r}. Use 'replace' or 'redact'."
        ) from exc
    if mode not in BATCH_MODES:
        raise MithrilVeilError("Batch anonymize-dir supports only replace and redact modes.")
    return mode


def _append_skip_results(
    file_results: list[BatchFileResult],
    paths: list[str],
    status: BatchFileStatus,
) -> None:
    for rel in sorted(paths):
        file_results.append(BatchFileResult(relative_path=rel, status=status))


def cmd_anonymize_dir(
    args: argparse.Namespace,
    *,
    anonymization_kwargs: dict,
) -> int:
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    force = bool(args.force)
    fail_fast = bool(getattr(args, "fail_fast", False))
    include_hidden = bool(getattr(args, "include_hidden", False))
    max_files = getattr(args, "max_files", None)

    try:
        mode = validate_batch_cli_args(args)
        ensure_safe_batch_directories(input_dir, output_dir)
    except UnsafeFileOperation as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_UNSAFE
    except MithrilVeilError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    report_path = Path(args.report) if getattr(args, "report", None) else None

    try:
        collected = collect_batch_input_files(
            input_dir,
            include_hidden=include_hidden,
            max_files=max_files,
        )
    except MithrilVeilError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    supported_files = collected.supported
    skipped_paths = collected.skipped_unsupported

    collision_errors = find_batch_output_collisions(supported_files)
    if collision_errors:
        for msg in collision_errors:
            print(f"Error: {msg}", file=sys.stderr)
        return EXIT_ERROR

    if report_path:
        try:
            ensure_safe_batch_report_path(
                report_path,
                input_dir,
                output_dir,
                supported_files,
                force=force,
            )
        except UnsafeFileOperation as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return EXIT_UNSAFE

    try:
        preflight_batch_output_paths(
            input_dir,
            output_dir,
            supported_files,
            force=force,
        )
    except UnsafeFileOperation as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_UNSAFE

    warnings: list[str] = []
    for rel in skipped_paths:
        msg = f"Skipped unsupported file: {rel}"
        warnings.append(msg)
        print(f"Warning: {msg}", file=sys.stderr)

    file_results: list[BatchFileResult] = []
    _append_skip_results(file_results, skipped_paths, BatchFileStatus.SKIPPED_UNSUPPORTED)
    _append_skip_results(file_results, collected.skipped_hidden, BatchFileStatus.SKIPPED_HIDDEN)
    _append_skip_results(file_results, collected.skipped_symlink, BatchFileStatus.SKIPPED_SYMLINK)

    for batch_file in supported_files:
        rel_str = batch_file.relative_path.as_posix()
        output_path = resolve_batch_output_path(input_dir, output_dir, batch_file.relative_path)
        try:
            content, _source = read_document_file(batch_file.absolute_path)
            response, _policy = run_anonymization(content, mode, _resolved=anonymization_kwargs)
            write_text_file(output_path, response.text, force=force)
            out_rel = output_path.relative_to(output_dir.resolve()).as_posix()
            file_results.append(
                BatchFileResult(
                    relative_path=rel_str,
                    status=BatchFileStatus.PROCESSED,
                    output_relative_path=out_rel,
                    total_entities=response.summary.total_entities,
                    entity_counts=dict(response.summary.entity_counts),
                )
            )
        except (
            UnsupportedDocumentType,
            EncryptedDocumentUnsupported,
            InputFileTooLarge,
            EmptyExtractedText,
            UnsafeFileOperation,
        ) as exc:
            file_results.append(
                BatchFileResult(
                    relative_path=rel_str,
                    status=BatchFileStatus.FAILED,
                    error_message=str(exc),
                )
            )
            print(f"Error ({rel_str}): {exc}", file=sys.stderr)
            if fail_fast:
                break
        except MithrilVeilError as exc:
            file_results.append(
                BatchFileResult(
                    relative_path=rel_str,
                    status=BatchFileStatus.FAILED,
                    error_message=str(exc),
                )
            )
            print(f"Error ({rel_str}): {exc}", file=sys.stderr)
            if fail_fast:
                break

    counts = count_batch_results(file_results)
    total_seen = (
        len(skipped_paths)
        + len(collected.skipped_hidden)
        + len(collected.skipped_symlink)
        + len(supported_files)
    )

    if report_path:
        preset = getattr(args, "preset", None)
        payload = build_batch_anonymization_report(
            mode=mode,
            input_dir=input_dir,
            output_dir=output_dir,
            total_files_seen=total_seen,
            counts=counts,
            file_results=file_results,
            warnings=warnings,
            preset=preset,
        )
        try:
            write_batch_anonymization_report(report_path, payload, force=force)
        except (UnsafeFileOperation, MithrilVeilError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return EXIT_UNSAFE if isinstance(exc, UnsafeFileOperation) else EXIT_ERROR

    print(
        f"Batch complete: {counts.processed} processed, {counts.skipped} skipped, "
        f"{counts.failed} failed.",
        file=sys.stderr,
    )

    if counts.failed > 0:
        return EXIT_ERROR
    return EXIT_SUCCESS
