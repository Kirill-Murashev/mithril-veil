from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    entity_type: str
    start: int
    end: int
    value: str
    detector: str = "regex"


class BaseDetector(ABC):
    entity_type: str

    @abstractmethod
    def detect(self, text: str) -> list[Span]:
        """Return all non-overlapping spans found by this detector (raw, pre-merge)."""
