from app.core.anonymizer import anonymize
from app.core.entities import DetectedEntity
from app.core.gliner_config import GLINER_DEFAULT_THRESHOLD, GLINER_MODEL_NAME
from app.core.schemas import AnonymizeMode, AnonymizeResponse
from app.core.span_merger import merge_entities
from app.core.summary import build_detection_summary
from app.detectors.base import BaseDetector
from app.detectors.regex_detectors import DEFAULT_DETECTORS


def build_detectors(
    *,
    use_ner: bool = False,
    use_gliner: bool = False,
    gliner_labels: list[str] | None = None,
    gliner_threshold: float = GLINER_DEFAULT_THRESHOLD,
    gliner_model_name: str | None = None,
) -> list[BaseDetector]:
    """Regex/checksum always; optional Natasha NER and GLiNER when enabled."""
    detectors: list[BaseDetector] = list(DEFAULT_DETECTORS)
    if use_ner:
        from app.detectors.natasha_detector import NatashaDetector

        detectors.append(NatashaDetector())
    if use_gliner:
        from app.detectors.gliner_detector import GlinerDetector

        detectors.append(
            GlinerDetector(
                labels=gliner_labels,
                threshold=gliner_threshold,
                model_name=gliner_model_name or GLINER_MODEL_NAME,
            )
        )
    return detectors


def detect_all(
    text: str,
    detectors: list[BaseDetector] | None = None,
    *,
    use_ner: bool = False,
    use_gliner: bool = False,
    gliner_labels: list[str] | None = None,
    gliner_threshold: float = GLINER_DEFAULT_THRESHOLD,
    gliner_model_name: str | None = None,
) -> list[DetectedEntity]:
    active = (
        detectors
        if detectors is not None
        else build_detectors(
            use_ner=use_ner,
            use_gliner=use_gliner,
            gliner_labels=gliner_labels,
            gliner_threshold=gliner_threshold,
            gliner_model_name=gliner_model_name,
        )
    )
    entities: list[DetectedEntity] = []
    for detector in active:
        entities.extend(detector.detect(text))
    return merge_entities(entities)


def run_anonymization(
    text: str,
    mode: AnonymizeMode,
    *,
    use_ner: bool = False,
    use_gliner: bool = False,
    gliner_labels: list[str] | None = None,
    gliner_threshold: float = GLINER_DEFAULT_THRESHOLD,
    gliner_model_name: str | None = None,
) -> AnonymizeResponse:
    entities = detect_all(
        text,
        use_ner=use_ner,
        use_gliner=use_gliner,
        gliner_labels=gliner_labels,
        gliner_threshold=gliner_threshold,
        gliner_model_name=gliner_model_name,
    )
    anonymized_text, api_entities = anonymize(text, entities, mode)
    summary = build_detection_summary(entities)
    return AnonymizeResponse(
        text=anonymized_text,
        entities=api_entities,
        warnings=[],
        summary=summary,
    )
