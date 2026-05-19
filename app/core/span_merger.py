from app.core.entities import DetectedEntity


def _overlaps(a: DetectedEntity, b: DetectedEntity) -> bool:
    return a.start < b.end and b.start < a.end


def _span_sort_key(entity: DetectedEntity) -> tuple:
    return (
        entity.start,
        -entity.length,
        -entity.priority,
        -entity.confidence,
        entity.type,
    )


def _wins_over(candidate: DetectedEntity, existing: DetectedEntity) -> bool:
    """Return True if candidate should replace existing on overlap."""
    if candidate.priority != existing.priority:
        return candidate.priority > existing.priority
    if candidate.length != existing.length:
        return candidate.length > existing.length
    if candidate.confidence != existing.confidence:
        return candidate.confidence > existing.confidence
    return candidate.type < existing.type


def merge_entities(entities: list[DetectedEntity]) -> list[DetectedEntity]:
    """
    Merge overlapping entities deterministically.

    On overlap: higher priority, then longer span, then higher confidence.
    """
    if not entities:
        return []

    sorted_entities = sorted(entities, key=_span_sort_key)
    kept: list[DetectedEntity] = []

    for candidate in sorted_entities:
        discard = False
        to_remove: list[int] = []

        for i, existing in enumerate(kept):
            if not _overlaps(candidate, existing):
                continue

            if _wins_over(candidate, existing):
                to_remove.append(i)
            else:
                discard = True
                break

        if discard:
            continue

        for i in reversed(to_remove):
            kept.pop(i)
        kept.append(candidate)

    return sorted(kept, key=lambda e: (e.start, e.type))


# Backward-compatible alias used during refactor
merge_spans = merge_entities
