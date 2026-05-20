"""Safe aggregate JSON report for CLI batch anonymization."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app import __version__
from app.core.schemas import AnonymizeMode
from app.document_io.base import ensure_safe_report_path
from app.document_io.batch import BatchFileResult, BatchFileStatus


@dataclass(frozen=True)
class BatchResultCounts:
    processed: int
    skipped: int
    failed: int
    skipped_unsupported: int
    skipped_hidden: int
    skipped_symlink: int


def build_batch_anonymization_report(
    *,
    mode: AnonymizeMode,
    input_dir: Path,
    output_dir: Path,
    total_files_seen: int,
    counts: BatchResultCounts,
    file_results: list[BatchFileResult],
    warnings: list[str],
    preset: str | None = None,
) -> dict[str, Any]:
    """Build a safe batch report (no raw text or detected values)."""
    ordered = sorted(file_results, key=lambda entry: (entry.relative_path, entry.status.value))
    payload: dict[str, Any] = {
        "service": "mithril-veil",
        "version": __version__,
        "report_type": "batch",
        "mode": mode.value,
        "input_dir": str(input_dir.resolve()),
        "output_dir": str(output_dir.resolve()),
        "total_files_seen": total_files_seen,
        "processed_count": counts.processed,
        "skipped_count": counts.skipped,
        "failed_count": counts.failed,
        "skipped_unsupported_count": counts.skipped_unsupported,
        "skipped_hidden_count": counts.skipped_hidden,
        "skipped_symlink_count": counts.skipped_symlink,
        "files": [
            {
                "relative_path": entry.relative_path,
                "status": entry.status.value,
                **(
                    {"output_relative_path": entry.output_relative_path}
                    if entry.output_relative_path
                    else {}
                ),
                **({"error_message": entry.error_message} if entry.error_message else {}),
                **(
                    {
                        "summary": {
                            "total_entities": entry.total_entities,
                            "entity_counts": entry.entity_counts,
                        }
                    }
                    if entry.total_entities is not None and entry.entity_counts is not None
                    else {}
                ),
            }
            for entry in ordered
        ],
        "warnings": list(warnings),
    }
    if preset is not None:
        payload["preset"] = preset
    return payload


def write_batch_anonymization_report(
    report_path: Path,
    payload: dict[str, Any],
    *,
    force: bool = False,
) -> None:
    ensure_safe_report_path(report_path, force=force)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        report_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        from app.core.exceptions import MithrilVeilError

        raise MithrilVeilError(f"Cannot write report: {report_path}") from exc


def count_batch_results(file_results: list[BatchFileResult]) -> BatchResultCounts:
    processed = sum(1 for r in file_results if r.status == BatchFileStatus.PROCESSED)
    skipped_unsupported = sum(
        1 for r in file_results if r.status == BatchFileStatus.SKIPPED_UNSUPPORTED
    )
    skipped_hidden = sum(1 for r in file_results if r.status == BatchFileStatus.SKIPPED_HIDDEN)
    skipped_symlink = sum(1 for r in file_results if r.status == BatchFileStatus.SKIPPED_SYMLINK)
    failed = sum(1 for r in file_results if r.status == BatchFileStatus.FAILED)
    skipped = skipped_unsupported + skipped_hidden + skipped_symlink
    return BatchResultCounts(
        processed=processed,
        skipped=skipped,
        failed=failed,
        skipped_unsupported=skipped_unsupported,
        skipped_hidden=skipped_hidden,
        skipped_symlink=skipped_symlink,
    )
