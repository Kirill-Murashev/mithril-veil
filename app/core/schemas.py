from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class AnonymizeMode(StrEnum):
    REPLACE = "replace"
    REDACT = "redact"


class AnonymizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Input text to anonymize")
    mode: AnonymizeMode = Field(
        default=AnonymizeMode.REPLACE,
        description="replace: typed placeholders; redact: [REDACTED]",
    )


class DetectedEntity(BaseModel):
    type: str
    start: int
    end: int
    value_preview: str
    replacement: str
    detector: str


class AnonymizeResponse(BaseModel):
    text: str
    entities: list[DetectedEntity]
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "mithril-veil"
    version: str = "0.1.0"
