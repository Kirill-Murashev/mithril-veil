from app.core.anonymizer import anonymize
from app.core.entities import DetectedEntity
from app.core.schemas import AnonymizeMode, AnonymizeResponse
from app.core.span_merger import merge_entities
from app.core.summary import build_detection_summary
from app.detectors.base import BaseDetector
from app.detectors.regex_detectors import DEFAULT_DETECTORS


def build_detectors(*, use_ner: bool = False) -> list[BaseDetector]:
    """Deterministic regex/checksum detectors; optional Natasha NER when enabled."""
    detectors: list[BaseDetector] = list(DEFAULT_DETECTORS)
    if use_ner:
        from app.detectors.natasha_detector import NatashaDetector

        detectors.append(NatashaDetector())
    return detectors


def detect_all(
    text: str,
    detectors: list[BaseDetector] | None = None,
    *,
    use_ner: bool = False,
) -> list[DetectedEntity]:
    active = detectors if detectors is not None else build_detectors(use_ner=use_ner)
    entities: list[DetectedEntity] = []
    for detector in active:
        entities.extend(detector.detect(text))
    return merge_entities(entities)


def run_anonymization(
    text: str,
    mode: AnonymizeMode,
    *,
    use_ner: bool = False,
) -> AnonymizeResponse:
    entities = detect_all(text, use_ner=use_ner)
    anonymized_text, api_entities = anonymize(text, entities, mode)
    summary = build_detection_summary(entities)
    return AnonymizeResponse(
        text=anonymized_text,
        entities=api_entities,
        warnings=[],
        summary=summary,
    )
