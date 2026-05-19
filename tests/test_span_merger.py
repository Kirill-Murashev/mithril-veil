from app.core.entities import DetectedEntity
from app.core.span_merger import merge_entities
from tests.conftest import SYNTHETIC_INN_10


def test_merge_inn_wins_over_lower_priority_overlap():
    # INN (90) vs EMAIL (70) on overlapping region
    entities = [
        DetectedEntity.create("EMAIL", 0, 12, "x@example.local", confidence=0.9),
        DetectedEntity.create("INN", 0, 10, SYNTHETIC_INN_10, confidence=0.95, priority=90),
    ]
    merged = merge_entities(entities)
    assert len(merged) == 1
    assert merged[0].type == "INN"


def test_merge_longer_span_when_priority_equal():
    entities = [
        DetectedEntity.create("PHONE", 0, 8, "+7900111", confidence=0.85, priority=70),
        DetectedEntity.create("PHONE", 0, 14, "+79001112233", confidence=0.85, priority=70),
    ]
    merged = merge_entities(entities)
    assert len(merged) == 1
    assert merged[0].length == 14


def test_merge_higher_confidence_when_priority_and_length_equal():
    entities = [
        DetectedEntity.create("EMAIL", 5, 20, "a@b.local", confidence=0.7, priority=70),
        DetectedEntity.create("EMAIL", 5, 20, "a@b.local", confidence=0.95, priority=70),
    ]
    merged = merge_entities(entities)
    assert len(merged) == 1
    assert merged[0].confidence == 0.95


def test_merge_keeps_non_overlapping_spans():
    entities = [
        DetectedEntity.create("EMAIL", 0, 10, "a@b.c", detector="regex"),
        DetectedEntity.create("PHONE", 20, 30, "+7900", detector="regex"),
    ]
    merged = merge_entities(entities)
    assert len(merged) == 2


def test_merge_is_deterministic():
    entities = [
        DetectedEntity.create("EMAIL", 5, 15, "x@y.z", confidence=0.8),
        DetectedEntity.create("PHONE", 10, 20, "+7900", confidence=0.8),
    ]
    first = merge_entities(entities)
    second = merge_entities(list(reversed(entities)))
    assert [(e.start, e.end, e.type) for e in first] == [(e.start, e.end, e.type) for e in second]


def test_merge_inn_over_generic_numeric_overlap():
    """10-digit INN-like span should beat overlapping weaker numeric match."""
    entities = [
        DetectedEntity.create("INN", 4, 14, SYNTHETIC_INN_10, confidence=0.95, priority=90),
        DetectedEntity.create("KPP", 4, 13, SYNTHETIC_INN_10[:9], confidence=0.85, priority=75),
    ]
    merged = merge_entities(entities)
    assert len(merged) == 1
    assert merged[0].type == "INN"
