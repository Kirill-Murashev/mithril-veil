from app.core.span_merger import merge_spans
from app.detectors.base import Span


def test_merge_removes_overlapping_lower_priority():
    # Shorter PHONE inside longer PASSPORT-like span — PASSPORT_RU wins by priority
    spans = [
        Span("PHONE", 0, 5, "+7900", "regex"),
        Span("PASSPORT_RU", 0, 11, "0000 000000", "regex"),
    ]
    merged = merge_spans(spans)
    assert len(merged) == 1
    assert merged[0].entity_type == "PASSPORT_RU"


def test_merge_keeps_non_overlapping_spans():
    spans = [
        Span("EMAIL", 0, 10, "a@b.c", "regex"),
        Span("PHONE", 20, 30, "+7900", "regex"),
    ]
    merged = merge_spans(spans)
    assert len(merged) == 2


def test_merge_is_deterministic():
    spans = [
        Span("EMAIL", 5, 15, "x@y.z", "regex"),
        Span("PHONE", 10, 20, "+7900", "regex"),
    ]
    first = merge_spans(spans)
    second = merge_spans(list(reversed(spans)))
    assert [(s.start, s.end, s.entity_type) for s in first] == [
        (s.start, s.end, s.entity_type) for s in second
    ]
