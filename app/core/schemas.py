from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AnonymizeMode(StrEnum):
    REPLACE = "replace"
    REDACT = "redact"


class AnonymizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Input text to anonymize")
    mode: AnonymizeMode = Field(
        default=AnonymizeMode.REPLACE,
        description="replace: typed placeholders; redact: [REDACTED]",
    )
    use_ner: bool = Field(
        default=False,
        description="Enable local Natasha NER for PERSON, ORGANIZATION, LOCATION",
    )


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
