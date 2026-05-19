"""Default security policies for Mithril Veil deployments."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityPolicy:
    store_original_documents: bool = False
    log_original_text: bool = False
    log_detected_values: bool = False
    local_models_only: bool = True
    external_llm_calls: bool = False


DEFAULT_POLICY = SecurityPolicy()
