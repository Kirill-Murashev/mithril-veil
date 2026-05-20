import json
from pathlib import Path
from typing import Any

from app import __version__
from app.core.presets import PolicyMetadata
from app.core.schemas import AnonymizeMode, AnonymizeResponse
from app.document_io.base import SourceMetadata, ensure_safe_report_path


def build_anonymization_report(
    response: AnonymizeResponse,
    mode: AnonymizeMode,
    *,
    source: SourceMetadata | None = None,
    policy: PolicyMetadata | None = None,
) -> dict[str, Any]:
    """Build a safe JSON-serializable report (no raw detected values)."""
    payload: dict[str, Any] = {
        "service": "mithril-veil",
        "version": __version__,
        "mode": mode.value,
        "summary": response.summary.model_dump(),
        "entities": [entity.model_dump() for entity in response.entities],
        "warnings": list(response.warnings),
    }
    if policy is not None:
        payload["policy"] = {
            "preset": policy.preset,
            "enabled_entities": list(policy.enabled_entities),
            "detectors": policy.detectors.model_dump(),
        }
    if source:
        payload["source"] = {
            key: value
            for key, value in source.items()
            if key in ("input_type", "page_count", "file_size_bytes")
        }
    return payload


def write_anonymization_report(
    report_path: Path,
    response: AnonymizeResponse,
    mode: AnonymizeMode,
    *,
    force: bool = False,
    source: SourceMetadata | None = None,
    policy: PolicyMetadata | None = None,
) -> None:
    ensure_safe_report_path(report_path, force=force)
    payload = build_anonymization_report(response, mode, source=source, policy=policy)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        report_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        from app.core.exceptions import MithrilVeilError

        raise MithrilVeilError(f"Cannot write report: {report_path}") from exc
