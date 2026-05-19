from app.core.schemas import AnonymizeMode, DetectedEntity
from app.detectors.base import Span

MASK_PREVIEW = "***"
REDACTED = "[REDACTED]"


def _placeholder(entity_type: str, index: int) -> str:
    return f"[{entity_type}_{index}]"


def anonymize(
    text: str,
    spans: list[Span],
    mode: AnonymizeMode,
) -> tuple[str, list[DetectedEntity]]:
    """
    Apply replacements right-to-left so indices stay valid.
    Deterministic counters per entity type for replace mode.
    """
    if not spans:
        return text, []

    counters: dict[str, int] = {}
    entities: list[DetectedEntity] = []

    ordered = sorted(spans, key=lambda s: s.start)
    replacements: list[tuple[int, int, str, Span]] = []

    for span in ordered:
        counters[span.entity_type] = counters.get(span.entity_type, 0) + 1
        idx = counters[span.entity_type]

        if mode == AnonymizeMode.REDACT:
            replacement = REDACTED
        else:
            replacement = _placeholder(span.entity_type, idx)

        entities.append(
            DetectedEntity(
                type=span.entity_type,
                start=span.start,
                end=span.end,
                value_preview=MASK_PREVIEW,
                replacement=replacement,
                detector=span.detector,
            )
        )
        replacements.append((span.start, span.end, replacement, span))

    result = text
    for start, end, replacement, _ in sorted(replacements, key=lambda r: r[0], reverse=True):
        result = result[:start] + replacement + result[end:]

    return result, entities
