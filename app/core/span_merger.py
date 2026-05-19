from app.detectors.base import Span

# Higher number = higher priority when spans overlap
ENTITY_PRIORITY: dict[str, int] = {
    "PASSPORT_RU": 90,
    "SNILS": 85,
    "INN": 80,
    "CADASTRAL_NUMBER": 75,
    "COURT_CASE_NUMBER": 70,
    "EMAIL": 50,
    "PHONE": 50,
}


def _span_length(span: Span) -> int:
    return span.end - span.start


def _priority(span: Span) -> int:
    return ENTITY_PRIORITY.get(span.entity_type, 0)


def _overlaps(a: Span, b: Span) -> bool:
    return a.start < b.end and b.start < a.end


def merge_spans(spans: list[Span]) -> list[Span]:
    """
    Sort by start ascending, then longer span first.
    Remove overlapping lower-priority spans; keep deterministic output.
    """
    if not spans:
        return []

    sorted_spans = sorted(
        spans,
        key=lambda s: (s.start, -_span_length(s), -_priority(s), s.entity_type),
    )

    kept: list[Span] = []
    for candidate in sorted_spans:
        discard = False
        to_remove: list[int] = []

        for i, existing in enumerate(kept):
            if not _overlaps(candidate, existing):
                continue

            cand_pri = _priority(candidate)
            exist_pri = _priority(existing)
            cand_len = _span_length(candidate)
            exist_len = _span_length(existing)

            if cand_pri > exist_pri or (cand_pri == exist_pri and cand_len > exist_len):
                to_remove.append(i)
            elif cand_pri < exist_pri or (cand_pri == exist_pri and cand_len < exist_len):
                discard = True
                break
            else:
                # Same priority and length — keep earlier in sort order (existing)
                discard = True
                break

        if discard:
            continue

        for i in reversed(to_remove):
            kept.pop(i)
        kept.append(candidate)

    return sorted(kept, key=lambda s: (s.start, s.entity_type))
