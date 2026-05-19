from app.core.entities import DetectedEntity, entity_to_api_dict
from app.core.schemas import AnonymizeMode, DetectedEntityResponse

MASK_PREVIEW = "***"
REDACTED = "[REDACTED]"


def _placeholder(entity_type: str, index: int) -> str:
    return f"[{entity_type}_{index}]"


def anonymize(
    text: str,
    entities: list[DetectedEntity],
    mode: AnonymizeMode,
) -> tuple[str, list[DetectedEntityResponse]]:
    """
    Apply replacements right-to-left so indices stay valid.
    Deterministic counters per entity type for replace mode.
    """
    if not entities:
        return text, []

    counters: dict[str, int] = {}
    responses: list[DetectedEntityResponse] = []
    replacements: list[tuple[int, int, str]] = []

    ordered = sorted(entities, key=lambda e: e.start)
    for entity in ordered:
        counters[entity.type] = counters.get(entity.type, 0) + 1
        idx = counters[entity.type]

        if mode == AnonymizeMode.REDACT:
            replacement = REDACTED
        else:
            replacement = _placeholder(entity.type, idx)

        payload = entity_to_api_dict(entity, replacement)
        responses.append(
            DetectedEntityResponse(
                type=payload["type"],
                start=payload["start"],
                end=payload["end"],
                value_preview=MASK_PREVIEW,
                replacement=payload["replacement"],
                detector=payload["detector"],
                confidence=payload["confidence"],
                metadata=payload["metadata"],
            )
        )
        replacements.append((entity.start, entity.end, replacement))

    result = text
    for start, end, replacement in sorted(replacements, key=lambda r: r[0], reverse=True):
        result = result[:start] + replacement + result[end:]

    return result, responses
