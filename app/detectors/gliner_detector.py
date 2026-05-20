"""Optional GLiNER zero-shot PII detector (lazy-loaded, install via [gliner] extra)."""

from __future__ import annotations

from typing import Any, Protocol

from app.core.entities import DetectedEntity
from app.core.exceptions import MithrilVeilError
from app.core.gliner_config import (
    DEFAULT_GLINER_LABELS,
    GLINER_DEFAULT_CONFIDENCE,
    GLINER_DEFAULT_THRESHOLD,
    GLINER_MODEL_NAME,
    map_gliner_label,
)
from app.detectors.base import BaseDetector

_model_cache: dict[str, Any] = {}
_init_errors: dict[str, str] = {}
_fake_model: Any | None = None


class GlinerPredictor(Protocol):
    def predict_entities(
        self, text: str, labels: list[str], *, threshold: float = 0.5
    ) -> list[dict[str, Any]]: ...


def set_fake_gliner_model(model: GlinerPredictor | None) -> None:
    """Inject a fake model for tests (no Hugging Face download)."""
    global _fake_model
    _fake_model = model


def reset_gliner_runtime_for_tests() -> None:
    """Reset lazy GLiNER cache (tests only)."""
    global _model_cache, _init_errors, _fake_model
    _model_cache = {}
    _init_errors = {}
    _fake_model = None


def _load_gliner_model(model_name: str) -> Any:
    if model_name in _model_cache:
        return _model_cache[model_name]
    if model_name in _init_errors:
        raise MithrilVeilError(_init_errors[model_name])
    if _fake_model is not None:
        _model_cache[model_name] = _fake_model
        return _fake_model
    try:
        from gliner import GLiNER
    except ImportError:
        message = "GLiNER is not installed. Install with: pip install -e '.[gliner]'"
        _init_errors[model_name] = message
        raise MithrilVeilError(message) from None
    try:
        model = GLiNER.from_pretrained(model_name)
    except Exception:
        message = "Cannot initialize GLiNER model."
        _init_errors[model_name] = message
        raise MithrilVeilError(message) from None
    _model_cache[model_name] = model
    return model


def _prediction_to_entities(
    predictions: list[dict[str, Any]],
    *,
    threshold: float,
    model_name: str,
) -> list[DetectedEntity]:
    entities: list[DetectedEntity] = []
    for item in predictions:
        label = str(item.get("label", ""))
        entity_type = map_gliner_label(label)
        if entity_type is None:
            continue
        score = item.get("score")
        confidence = float(score) if score is not None else GLINER_DEFAULT_CONFIDENCE
        if confidence < threshold:
            continue
        start = int(item["start"])
        end = int(item["end"])
        text = str(item.get("text", ""))
        entities.append(
            DetectedEntity.create(
                entity_type,
                start,
                end,
                text,
                detector="gliner",
                confidence=confidence,
                metadata={
                    "model": "gliner",
                    "model_name": model_name,
                    "source_label": label,
                    "threshold": threshold,
                },
            )
        )
    return entities


class GlinerDetector(BaseDetector):
    """Multi-label zero-shot detector backed by GLiNER."""

    entity_type = "GLINER"

    def __init__(
        self,
        *,
        labels: list[str] | None = None,
        threshold: float = GLINER_DEFAULT_THRESHOLD,
        model_name: str = GLINER_MODEL_NAME,
    ) -> None:
        self.labels = list(labels if labels is not None else DEFAULT_GLINER_LABELS)
        self.threshold = threshold
        self.model_name = model_name

    def detect(self, text: str) -> list[DetectedEntity]:
        model = _load_gliner_model(self.model_name)
        predictions = model.predict_entities(text, self.labels, threshold=self.threshold)
        return _prediction_to_entities(
            predictions,
            threshold=self.threshold,
            model_name=self.model_name,
        )
