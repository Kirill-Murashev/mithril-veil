"""In-memory reversible pseudonymization mapping (session-scoped, never API-safe)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from app.core.entities import DetectedEntity
from app.core.placeholders import placeholder_for


class MappingReportMetadata(BaseModel):
    """Safe report fragment: persistence flags only, no raw values."""

    written: bool = False
    encrypted: bool = False

    def to_report_fragment(self) -> dict[str, Any]:
        return {"mapping": self.model_dump()}


@dataclass(frozen=True)
class MappingEntry:
    """One pseudonym assignment (placeholder is API-safe; original stays internal)."""

    placeholder: str
    entity_type: str
    index: int
    start: int
    end: int


@dataclass
class ReversibleMapping:
    """
    Session-scoped mapping from deterministic placeholder to original span text.

    Original values must never be logged, printed, returned by the API, or written
    to safe reports. Use :meth:`serialize_for_encryption` only for encrypted export.
    """

    _entries: list[tuple[MappingEntry, str]] = field(default_factory=list)

    def record(
        self,
        entity: DetectedEntity,
        *,
        index: int,
        placeholder: str | None = None,
    ) -> MappingEntry:
        token = placeholder or placeholder_for(entity.type, index)
        entry = MappingEntry(
            placeholder=token,
            entity_type=entity.type,
            index=index,
            start=entity.start,
            end=entity.end,
        )
        self._entries.append((entry, entity.text))
        return entry

    def entries(self) -> tuple[MappingEntry, ...]:
        return tuple(entry for entry, _ in self._entries)

    def placeholder_to_original(self) -> dict[str, str]:
        """Reversal lookup: placeholder -> original (for local de-anonymization)."""
        return {entry.placeholder: original for entry, original in self._entries}

    def original_to_placeholder(self) -> dict[str, str]:
        """Forward lookup: original span text -> placeholder."""
        return {original: entry.placeholder for entry, original in self._entries}

    def serialize_for_encryption(self) -> dict[str, str]:
        """
        JSON-serializable payload for encrypted mapping files.

        Keys are placeholders (e.g. ``[PERSON_1]``); values are original span text.
        """
        return self.placeholder_to_original()

    def __len__(self) -> int:
        return len(self._entries)

    def __bool__(self) -> bool:
        return bool(self._entries)


@dataclass
class PseudonymizationSession:
    """
    Optional reversible pseudonymization state for a single run.

    When ``mapping`` is set, the anonymizer records placeholder assignments in memory.
    ``mapping_metadata`` is the only mapping-related data safe for reports.
    """

    mapping: ReversibleMapping | None = None
    mapping_metadata: MappingReportMetadata = field(default_factory=MappingReportMetadata)

    @classmethod
    def reversible(cls) -> PseudonymizationSession:
        return cls(mapping=ReversibleMapping())

    def mark_mapping_written(self, *, encrypted: bool) -> None:
        self.mapping_metadata = MappingReportMetadata(written=True, encrypted=encrypted)
