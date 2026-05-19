from collections import Counter

from app.core.entities import DetectedEntity
from app.core.schemas import DetectionSummary


def build_detection_summary(entities: list[DetectedEntity]) -> DetectionSummary:
    type_counts = Counter(e.type for e in entities)
    detector_counts = Counter(e.detector for e in entities)
    return DetectionSummary(
        total_entities=len(entities),
        entity_counts=dict(sorted(type_counts.items())),
        detectors=dict(sorted(detector_counts.items())),
    )
