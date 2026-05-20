"""Default security policies for Mithril Veil deployments."""

from dataclasses import dataclass

from app.core.gliner_config import GLINER_DEFAULT_THRESHOLD, GLINER_MAX_LABELS, GLINER_MODEL_NAME


@dataclass(frozen=True)
class SecurityPolicy:
    store_original_documents: bool = False
    log_original_text: bool = False
    log_detected_values: bool = False
    local_models_only: bool = True
    external_llm_calls: bool = False
    use_ner: bool = False
    use_gliner: bool = False
    gliner_threshold: float = GLINER_DEFAULT_THRESHOLD
    gliner_model_name: str = GLINER_MODEL_NAME
    gliner_max_labels: int = GLINER_MAX_LABELS


DEFAULT_POLICY = SecurityPolicy()
