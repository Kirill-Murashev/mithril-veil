from app.core.anonymizer import anonymize
from app.core.schemas import AnonymizeMode, AnonymizeResponse
from app.core.span_merger import merge_spans
from app.detectors.base import BaseDetector, Span
from app.detectors.regex_detectors import DEFAULT_DETECTORS


def detect_all(text: str, detectors: list[BaseDetector] | None = None) -> list[Span]:
    detectors = detectors or DEFAULT_DETECTORS
    spans: list[Span] = []
    for detector in detectors:
        spans.extend(detector.detect(text))
    return merge_spans(spans)


def run_anonymization(text: str, mode: AnonymizeMode) -> AnonymizeResponse:
    spans = detect_all(text)
    anonymized_text, entities = anonymize(text, spans, mode)
    return AnonymizeResponse(text=anonymized_text, entities=entities, warnings=[])
