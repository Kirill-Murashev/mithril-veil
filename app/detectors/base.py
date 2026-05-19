from abc import ABC, abstractmethod

from app.core.entities import DetectedEntity


class BaseDetector(ABC):
    entity_type: str

    @abstractmethod
    def detect(self, text: str) -> list[DetectedEntity]:
        """Return raw detection spans (may overlap; merged later)."""
