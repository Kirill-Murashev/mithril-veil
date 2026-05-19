from dataclasses import dataclass, field
from typing import Any

# Default entity priorities for span merging (higher wins on overlap)
ENTITY_PRIORITIES: dict[str, int] = {
    "PASSPORT_RU": 100,
    "SNILS": 95,
    "INN": 90,
    "BANK_ACCOUNT": 90,
    "CARD_NUMBER": 90,
    "OGRN": 88,
    "OGRNIP": 88,
    "CADASTRAL_NUMBER": 85,
    "COURT_CASE_NUMBER": 80,
    "CORRESPONDENT_ACCOUNT": 78,
    "BIK": 75,
    "KPP": 75,
    "CONTRACT_NUMBER": 72,
    "EMAIL": 70,
    "PHONE": 70,
    "IP_ADDRESS": 68,
    "URL": 68,
    "TELEGRAM_HANDLE": 68,
    "DATE_OF_BIRTH": 65,
    "ADDRESS": 60,
    "ORGANIZATION": 50,
    "PERSON": 50,
    "LOCATION": 50,
}

# Metadata keys safe to expose via API (no raw PII values)
SAFE_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "checksum_valid",
        "context_matched",
        "luhn_valid",
        "model",
        "source_label",
    }
)

CONFIDENCE_VALIDATED = 0.95
CONFIDENCE_DEFAULT = 0.85
CONFIDENCE_WEAK = 0.45


@dataclass(frozen=True)
class DetectedEntity:
    """Internal detection result. ``text`` must never be logged or returned by the API."""

    type: str
    start: int
    end: int
    text: str
    detector: str
    confidence: float
    priority: int
    metadata: dict[str, str | int | float | bool | None] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        entity_type: str,
        start: int,
        end: int,
        text: str,
        *,
        detector: str = "regex",
        confidence: float | None = None,
        priority: int | None = None,
        metadata: dict[str, str | int | float | bool | None] | None = None,
    ) -> "DetectedEntity":
        return cls(
            type=entity_type,
            start=start,
            end=end,
            text=text,
            detector=detector,
            confidence=confidence if confidence is not None else CONFIDENCE_DEFAULT,
            priority=priority if priority is not None else ENTITY_PRIORITIES.get(entity_type, 0),
            metadata=dict(metadata or {}),
        )

    @property
    def length(self) -> int:
        return self.end - self.start


def sanitize_metadata_for_api(
    metadata: dict[str, str | int | float | bool | None],
) -> dict[str, str | int | float | bool | None]:
    """Strip metadata to API-safe keys and scalar values only."""
    result: dict[str, str | int | float | bool | None] = {}
    for key, value in metadata.items():
        if key not in SAFE_METADATA_KEYS:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            result[key] = value
    return result


def entity_to_api_dict(entity: DetectedEntity, replacement: str) -> dict[str, Any]:
    """Build API-safe entity payload (no original text)."""
    return {
        "type": entity.type,
        "start": entity.start,
        "end": entity.end,
        "value_preview": "***",
        "replacement": replacement,
        "detector": entity.detector,
        "confidence": entity.confidence,
        "metadata": sanitize_metadata_for_api(entity.metadata),
    }
