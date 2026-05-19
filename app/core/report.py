import json
from pathlib import Path
from typing import Any

from app import __version__
from app.core.schemas import AnonymizeMode, AnonymizeResponse
from app.document_io.base import ensure_safe_report_path


def build_anonymization_report(
    response: AnonymizeResponse,
    mode: AnonymizeMode,
) -> dict[str, Any]:
    """Build a safe JSON-serializable report (no raw detected values)."""
    return {
        "service": "mithril-veil",
        "version": __version__,
        "mode": mode.value,
        "summary": response.summary.model_dump(),
        "entities": [entity.model_dump() for entity in response.entities],
        "warnings": list(response.warnings),
    }


def write_anonymization_report(
    report_path: Path,
    response: AnonymizeResponse,
    mode: AnonymizeMode,
    *,
    force: bool = False,
) -> None:
    ensure_safe_report_path(report_path, force=force)
    payload = build_anonymization_report(response, mode)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        report_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        from app.core.exceptions import MithrilVeilError

        raise MithrilVeilError(f"Cannot write report: {report_path}") from exc
