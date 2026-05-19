"""Optional local Natasha NER for Russian PERSON / ORGANIZATION / LOCATION."""

from __future__ import annotations

from app.core.entities import DetectedEntity
from app.core.exceptions import MithrilVeilError
from app.detectors.base import BaseDetector

# Natasha label → (entity type, default confidence)
NATASHA_LABEL_MAP: dict[str, tuple[str, float]] = {
    "PER": ("PERSON", 0.75),
    "ORG": ("ORGANIZATION", 0.70),
    "LOC": ("LOCATION", 0.70),
}

_segmenter = None
_ner_tagger = None
_init_error: str | None = None


def _initialize_natasha() -> None:
    global _segmenter, _ner_tagger, _init_error
    if _ner_tagger is not None or _init_error is not None:
        return
    try:
        from natasha import NewsEmbedding, NewsNERTagger, Segmenter
    except ImportError:
        _init_error = "Natasha is not installed."
        return
    try:
        _segmenter = Segmenter()
        embedding = NewsEmbedding()
        _ner_tagger = NewsNERTagger(embedding)
    except Exception:
        _init_error = "Cannot initialize Natasha NER."


def reset_natasha_runtime_for_tests() -> None:
    """Reset lazy singleton (tests only)."""
    global _segmenter, _ner_tagger, _init_error
    _segmenter = None
    _ner_tagger = None
    _init_error = None


class NatashaDetector(BaseDetector):
    """Multi-type NER detector backed by local Natasha models."""

    entity_type = "NATASHA"

    def detect(self, text: str) -> list[DetectedEntity]:
        _initialize_natasha()
        if _init_error is not None:
            raise MithrilVeilError(_init_error)
        if _segmenter is None or _ner_tagger is None:
            raise MithrilVeilError("Natasha NER is not available.")

        from natasha import Doc

        doc = Doc(text)
        doc.segment(_segmenter)
        doc.tag_ner(_ner_tagger)

        entities: list[DetectedEntity] = []
        for span in doc.spans:
            mapping = NATASHA_LABEL_MAP.get(span.type)
            if mapping is None:
                continue
            entity_type, confidence = mapping
            entities.append(
                DetectedEntity.create(
                    entity_type,
                    span.start,
                    span.stop,
                    span.text,
                    detector="natasha",
                    confidence=confidence,
                    metadata={
                        "model": "natasha",
                        "source_label": span.type,
                    },
                )
            )
        return entities
