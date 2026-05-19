import re

from app.detectors.base import BaseDetector, Span

# Conservative MVP patterns — TODO: add checksum/validation for INN, SNILS, passport, etc.


class EmailDetector(BaseDetector):
    entity_type = "EMAIL"
    _pattern = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    )

    def detect(self, text: str) -> list[Span]:
        return [
            Span(self.entity_type, m.start(), m.end(), m.group(), "regex")
            for m in self._pattern.finditer(text)
        ]


class PhoneDetector(BaseDetector):
    entity_type = "PHONE"
    # Russian-style numbers: +7, 8, or 7 followed by 10 digits with optional separators
    _pattern = re.compile(
        r"(?:\+7|8|7)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"
        r"|(?:\+7|8)[\s\-]?\d{10}"
    )

    def detect(self, text: str) -> list[Span]:
        return [
            Span(self.entity_type, m.start(), m.end(), m.group(), "regex")
            for m in self._pattern.finditer(text)
        ]


class InnDetector(BaseDetector):
    entity_type = "INN"
    # 10 digits (org) or 12 digits (individual) — word boundaries
    _pattern = re.compile(r"\b\d{10}\b|\b\d{12}\b")

    def detect(self, text: str) -> list[Span]:
        spans: list[Span] = []
        for m in self._pattern.finditer(text):
            value = m.group()
            # TODO: validate INN checksum before accepting
            if len(value) in (10, 12):
                spans.append(Span(self.entity_type, m.start(), m.end(), value, "regex"))
        return spans


class SnilsDetector(BaseDetector):
    entity_type = "SNILS"
    _pattern = re.compile(r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}\b")

    def detect(self, text: str) -> list[Span]:
        return [
            Span(self.entity_type, m.start(), m.end(), m.group(), "regex")
            for m in self._pattern.finditer(text)
        ]
        # TODO: validate SNILS control number


class PassportRuDetector(BaseDetector):
    entity_type = "PASSPORT_RU"
    # Series (4 digits) + number (6 digits), optional space
    _pattern = re.compile(r"\b\d{2}\s?\d{2}\s?\d{6}\b")

    def detect(self, text: str) -> list[Span]:
        return [
            Span(self.entity_type, m.start(), m.end(), m.group(), "regex")
            for m in self._pattern.finditer(text)
        ]
        # TODO: validate passport series/number ranges


class CadastralNumberDetector(BaseDetector):
    entity_type = "CADASTRAL_NUMBER"
    # Format: XX:XX:XXXXXXX:XXXX (simplified)
    _pattern = re.compile(r"\b\d{2}:\d{2}:\d{6,7}:\d{1,7}\b")

    def detect(self, text: str) -> list[Span]:
        return [
            Span(self.entity_type, m.start(), m.end(), m.group(), "regex")
            for m in self._pattern.finditer(text)
        ]


class CourtCaseNumberDetector(BaseDetector):
    entity_type = "COURT_CASE_NUMBER"
    # Simplified: А40-12345/2024 style (Cyrillic letter prefix optional in real cases)
    _pattern = re.compile(
        r"\b[А-ЯA-Z]{1,3}\d{1,3}-\d{1,6}/\d{4}\b",
        re.IGNORECASE,
    )

    def detect(self, text: str) -> list[Span]:
        return [
            Span(self.entity_type, m.start(), m.end(), m.group(), "regex")
            for m in self._pattern.finditer(text)
        ]
        # TODO: expand court case number formats per jurisdiction


DEFAULT_DETECTORS: list[BaseDetector] = [
    EmailDetector(),
    PhoneDetector(),
    InnDetector(),
    SnilsDetector(),
    PassportRuDetector(),
    CadastralNumberDetector(),
    CourtCaseNumberDetector(),
]
