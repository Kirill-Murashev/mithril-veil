from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.gliner_config import validate_gliner_labels


class AnonymizeMode(StrEnum):
    REPLACE = "replace"
    REDACT = "redact"


class PresetDetectorsResponse(BaseModel):
    regex: bool = True
    natasha: bool = False
    gliner: bool = False


class PresetInfoResponse(BaseModel):
    id: str
    name: str
    description: str
    enabled_entities: list[str]
    detectors: PresetDetectorsResponse


class AnonymizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Input text to anonymize")
    mode: AnonymizeMode = Field(
        default=AnonymizeMode.REPLACE,
        description="replace: typed placeholders; redact: [REDACTED]",
    )
    preset: str | None = Field(
        default=None,
        description="Policy preset id (e.g. general_ru, legal_ru)",
    )
    use_ner: bool | None = Field(
        default=None,
        description="Enable Natasha NER; null uses preset default or false",
    )
    use_gliner: bool | None = Field(
        default=None,
        description="Enable GLiNER; null uses preset default or false",
    )
    gliner_labels: list[str] | None = Field(
        default=None,
        description="Optional GLiNER label list (max 50)",
    )
    gliner_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum GLiNER score; null uses preset default or 0.5",
    )
    gliner_model_name: str | None = Field(
        default=None,
        description="Hugging Face GLiNER model id (default: urchade/gliner_mediumv2.1)",
    )

    @field_validator("gliner_labels")
    @classmethod
    def validate_gliner_labels_field(cls, value: list[str] | None) -> list[str] | None:
        try:
            return validate_gliner_labels(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc


class DetectedEntityResponse(BaseModel):
    """API-safe entity; never includes original detected text."""

    type: str
    start: int
    end: int
    value_preview: str = "***"
    replacement: str
    detector: str
    confidence: float
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @field_validator("value_preview")
    @classmethod
    def mask_preview(cls, value: str) -> str:
        return "***"


class DetectionSummary(BaseModel):
    total_entities: int
    entity_counts: dict[str, int]
    detectors: dict[str, int]


class AnonymizeResponse(BaseModel):
    text: str
    entities: list[DetectedEntityResponse]
    warnings: list[str] = Field(default_factory=list)
    summary: DetectionSummary


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "mithril-veil"
    version: str = "0.1.0"
