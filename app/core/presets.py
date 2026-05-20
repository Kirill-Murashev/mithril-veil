"""YAML policy presets for detector and entity configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import MithrilVeilError
from app.core.gliner_config import GLINER_DEFAULT_THRESHOLD, validate_gliner_labels

PRESETS_DIR = Path(__file__).resolve().parent.parent / "presets"

KNOWN_ENTITY_TYPES: frozenset[str] = frozenset(
    {
        "ADDRESS",
        "BANK_ACCOUNT",
        "BIK",
        "CADASTRAL_NUMBER",
        "CARD_NUMBER",
        "CONTRACT_NUMBER",
        "CORRESPONDENT_ACCOUNT",
        "COURT_CASE_NUMBER",
        "DATE_OF_BIRTH",
        "EMAIL",
        "INN",
        "IP_ADDRESS",
        "KPP",
        "LOCATION",
        "OGRN",
        "OGRNIP",
        "ORGANIZATION",
        "PASSPORT_RU",
        "PERSON",
        "PHONE",
        "SNILS",
        "TELEGRAM_HANDLE",
        "URL",
        "VEHICLE_REGISTRATION_NUMBER",
    }
)

REQUIRED_PRESET_IDS: frozenset[str] = frozenset(
    {
        "general_ru",
        "legal_ru",
        "valuation_ru",
        "banking_ru",
        "court_case_ru",
    }
)


class UnknownPresetError(MithrilVeilError):
    """Raised when a preset id is not found."""


class InvalidPresetError(MithrilVeilError):
    """Raised when a preset file is malformed or invalid."""


class PresetDetectorsConfig(BaseModel):
    regex: bool = True
    natasha: bool = False
    gliner: bool = False


class PresetGlinerConfig(BaseModel):
    labels: list[str] = Field(default_factory=list)
    threshold: float = Field(default=GLINER_DEFAULT_THRESHOLD, ge=0.0, le=1.0)


class PresetConfig(BaseModel):
    id: str
    name: str
    description: str
    enabled_entities: list[str]
    detectors: PresetDetectorsConfig = Field(default_factory=PresetDetectorsConfig)
    gliner: PresetGlinerConfig = Field(default_factory=PresetGlinerConfig)
    notes: list[str] = Field(default_factory=list)

    @field_validator("enabled_entities")
    @classmethod
    def validate_entities(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("enabled_entities must not be empty.")
        unknown = [entity for entity in value if entity not in KNOWN_ENTITY_TYPES]
        if unknown:
            raise ValueError(f"Unknown entity types: {', '.join(sorted(unknown))}")
        return value


class PresetInfo(BaseModel):
    id: str
    name: str
    description: str
    enabled_entities: list[str]
    detectors: PresetDetectorsConfig
    notes: list[str] = Field(default_factory=list)


class PolicyMetadata(BaseModel):
    preset: str
    enabled_entities: list[str]
    detectors: PresetDetectorsConfig


class ResolvedAnonymizationOptions(BaseModel):
    use_ner: bool = False
    use_gliner: bool = False
    gliner_labels: list[str] | None = None
    gliner_threshold: float = GLINER_DEFAULT_THRESHOLD
    gliner_model_name: str | None = None
    enabled_entities: frozenset[str] | None = None
    policy: PolicyMetadata | None = None


def validate_preset_config(data: dict[str, Any], *, source: str) -> PresetConfig:
    """Validate raw YAML/dict data into a PresetConfig."""
    if not isinstance(data, dict):
        raise InvalidPresetError(f"Invalid preset file: {source}")
    preset_id = data.get("id") or data.get("name")
    if not preset_id or not isinstance(preset_id, str):
        raise InvalidPresetError(f"Preset must define id: {source}")
    try:
        return PresetConfig.model_validate(data)
    except Exception as exc:
        raise InvalidPresetError(f"Invalid preset {preset_id!r}: {exc}") from exc


def _preset_path(preset_id: str) -> Path:
    return PRESETS_DIR / f"{preset_id}.yml"


@lru_cache(maxsize=32)
def load_preset(preset_id: str) -> PresetConfig:
    """Load and validate a preset by id."""
    if preset_id not in REQUIRED_PRESET_IDS:
        available = ", ".join(sorted(REQUIRED_PRESET_IDS))
        raise UnknownPresetError(f"Unknown preset: {preset_id!r}. Available: {available}.")
    path = _preset_path(preset_id)
    if not path.is_file():
        raise UnknownPresetError(f"Unknown preset: {preset_id!r}.")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise UnknownPresetError(f"Cannot load preset: {preset_id!r}.") from exc
    except yaml.YAMLError as exc:
        raise InvalidPresetError(f"Invalid YAML in preset {preset_id!r}.") from exc
    config = validate_preset_config(raw or {}, source=str(path))
    if config.id != preset_id:
        raise InvalidPresetError(
            f"Preset id mismatch in {path.name}: expected {preset_id!r}, got {config.id!r}."
        )
    return config


def list_presets() -> list[PresetInfo]:
    """Return safe metadata for all bundled presets."""
    result: list[PresetInfo] = []
    for preset_id in sorted(REQUIRED_PRESET_IDS):
        config = load_preset(preset_id)
        result.append(
            PresetInfo(
                id=config.id,
                name=config.name,
                description=config.description,
                enabled_entities=list(config.enabled_entities),
                detectors=config.detectors,
                notes=list(config.notes),
            )
        )
    return result


def preset_to_api_dict(info: PresetInfo) -> dict[str, Any]:
    return {
        "id": info.id,
        "name": info.name,
        "description": info.description,
        "enabled_entities": info.enabled_entities,
        "detectors": info.detectors.model_dump(),
    }


def apply_preset_to_options(
    preset: PresetConfig,
    *,
    use_ner: bool | None = None,
    use_gliner: bool | None = None,
    gliner_labels: list[str] | None = None,
    gliner_threshold: float | None = None,
    gliner_model_name: str | None = None,
) -> ResolvedAnonymizationOptions:
    """Merge explicit user options over preset defaults."""
    resolved_ner = preset.detectors.natasha if use_ner is None else use_ner
    resolved_gliner = preset.detectors.gliner if use_gliner is None else use_gliner
    labels = gliner_labels
    if labels is None and preset.gliner.labels:
        labels = list(preset.gliner.labels)
    threshold = gliner_threshold if gliner_threshold is not None else preset.gliner.threshold
    if labels is not None:
        labels = validate_gliner_labels(labels)
    return ResolvedAnonymizationOptions(
        use_ner=resolved_ner,
        use_gliner=resolved_gliner,
        gliner_labels=labels,
        gliner_threshold=threshold,
        gliner_model_name=gliner_model_name,
        enabled_entities=frozenset(preset.enabled_entities),
        policy=PolicyMetadata(
            preset=preset.id,
            enabled_entities=list(preset.enabled_entities),
            detectors=preset.detectors,
        ),
    )


def resolve_anonymization_options(
    *,
    preset_id: str | None = None,
    use_ner: bool | None = None,
    use_gliner: bool | None = None,
    gliner_labels: list[str] | None = None,
    gliner_threshold: float | None = None,
    gliner_model_name: str | None = None,
) -> ResolvedAnonymizationOptions:
    """Resolve final detection options from optional preset and explicit overrides."""
    if preset_id is None:
        threshold = gliner_threshold if gliner_threshold is not None else GLINER_DEFAULT_THRESHOLD
        labels = validate_gliner_labels(gliner_labels) if gliner_labels is not None else None
        return ResolvedAnonymizationOptions(
            use_ner=use_ner if use_ner is not None else False,
            use_gliner=use_gliner if use_gliner is not None else False,
            gliner_labels=labels,
            gliner_threshold=threshold,
            gliner_model_name=gliner_model_name,
            enabled_entities=None,
            policy=None,
        )
    preset = load_preset(preset_id)
    return apply_preset_to_options(
        preset,
        use_ner=use_ner,
        use_gliner=use_gliner,
        gliner_labels=gliner_labels,
        gliner_threshold=gliner_threshold,
        gliner_model_name=gliner_model_name,
    )


def filter_entities_by_enabled_types(
    entities: list,
    enabled_entities: frozenset[str] | None,
) -> list:
    """Drop entities whose type is not in enabled_entities (deterministic, no raw values)."""
    if enabled_entities is None:
        return entities
    return [entity for entity in entities if entity.type in enabled_entities]
