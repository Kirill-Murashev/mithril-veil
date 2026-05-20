from app.core.entities import DetectedEntity, entity_to_api_dict
from app.core.mapping import ReversibleMapping
from app.core.placeholders import placeholder_for
from app.core.schemas import AnonymizeMode, DetectedEntityResponse

MASK_PREVIEW = "***"
REDACTED = "[REDACTED]"


def anonymize(
    text: str,
    entities: list[DetectedEntity],
    mode: AnonymizeMode,
    *,
    reversible_mapping: ReversibleMapping | None = None,
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
            replacement = placeholder_for(entity.type, idx)
            if reversible_mapping is not None and mode == AnonymizeMode.PSEUDONYMIZE:
                reversible_mapping.record(entity, index=idx, placeholder=replacement)

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
