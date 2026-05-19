from app.core.anonymizer import anonymize
from app.core.entities import DetectedEntity
from app.core.schemas import AnonymizeMode, AnonymizeResponse
from app.core.span_merger import merge_entities
from app.core.summary import build_detection_summary
from app.detectors.base import BaseDetector
from app.detectors.regex_detectors import DEFAULT_DETECTORS


def detect_all(text: str, detectors: list[BaseDetector] | None = None) -> list[DetectedEntity]:
    detectors = detectors or DEFAULT_DETECTORS
    entities: list[DetectedEntity] = []
    for detector in detectors:
        entities.extend(detector.detect(text))
    return merge_entities(entities)


def run_anonymization(text: str, mode: AnonymizeMode) -> AnonymizeResponse:
    entities = detect_all(text)
    anonymized_text, api_entities = anonymize(text, entities, mode)
    summary = build_detection_summary(entities)
    return AnonymizeResponse(
        text=anonymized_text,
        entities=api_entities,
        warnings=[],
        summary=summary,
    )
