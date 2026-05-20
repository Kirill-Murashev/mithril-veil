import re

from app.core.entities import (
    CONFIDENCE_DEFAULT,
    CONFIDENCE_VALIDATED,
    CONFIDENCE_WEAK,
    DetectedEntity,
)
from app.detectors.base import BaseDetector
from app.detectors.validators import (
    find_nearby_bik,
    has_keyword_context,
    normalize_digits,
    validate_bank_account,
    validate_card_number,
    validate_correspondent_account,
    validate_inn,
    validate_ogrn,
    validate_ogrnip,
    validate_snils,
)

INN_CONTEXT = ("инн", "inn")
SNILS_CONTEXT = ("снилс", "snils")


def _entities_from_matches(
    entity_type: str,
    text: str,
    pattern: re.Pattern[str],
    *,
    confidence: float = CONFIDENCE_DEFAULT,
    metadata: dict[str, str | int | float | bool | None] | None = None,
) -> list[DetectedEntity]:
    return [
        DetectedEntity.create(
            entity_type,
            m.start(),
            m.end(),
            m.group(),
            confidence=confidence,
            metadata=metadata,
        )
        for m in pattern.finditer(text)
    ]


class EmailDetector(BaseDetector):
    entity_type = "EMAIL"
    _pattern = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    )

    def detect(self, text: str) -> list[DetectedEntity]:
        return _entities_from_matches(self.entity_type, text, self._pattern)


class PhoneDetector(BaseDetector):
    entity_type = "PHONE"
    _pattern = re.compile(
        r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"
        r"|(?:\+7|8)[\s\-]?\d{10}"
        r"|\b7\d{10}\b"
    )

    def detect(self, text: str) -> list[DetectedEntity]:
        return _entities_from_matches(self.entity_type, text, self._pattern)


class InnDetector(BaseDetector):
    entity_type = "INN"
    _pattern = re.compile(r"\b\d{10}\b|\b\d{12}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        for m in self._pattern.finditer(text):
            raw = m.group()
            digits = normalize_digits(raw)
            if len(digits) not in (10, 12):
                continue
            if validate_inn(digits):
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=CONFIDENCE_VALIDATED,
                        metadata={"checksum_valid": True},
                    )
                )
            elif has_keyword_context(text, m.start(), INN_CONTEXT):
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=CONFIDENCE_WEAK,
                        metadata={"checksum_valid": False, "context_matched": True},
                    )
                )
        return entities


class SnilsDetector(BaseDetector):
    entity_type = "SNILS"
    _pattern = re.compile(r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}\b|\b\d{11}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        for m in self._pattern.finditer(text):
            raw = m.group()
            digits = normalize_digits(raw)
            if len(digits) != 11:
                continue
            if validate_snils(digits):
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=CONFIDENCE_VALIDATED,
                        metadata={"checksum_valid": True},
                    )
                )
            elif has_keyword_context(text, m.start(), SNILS_CONTEXT):
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=CONFIDENCE_WEAK,
                        metadata={"checksum_valid": False, "context_matched": True},
                    )
                )
        return entities


class PassportRuDetector(BaseDetector):
    entity_type = "PASSPORT_RU"
    # Require separator so plain 10-digit INN is not matched as passport series+number
    _pattern = re.compile(r"\b\d{2}\s\d{2}\s\d{6}\b|\b\d{4}\s\d{6}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        # TODO: validate passport series/number ranges and issue year
        return _entities_from_matches(self.entity_type, text, self._pattern)


class OgrnDetector(BaseDetector):
    entity_type = "OGRN"
    _pattern = re.compile(r"\b\d{13}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        for m in self._pattern.finditer(text):
            raw = m.group()
            if validate_ogrn(raw):
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=CONFIDENCE_VALIDATED,
                        metadata={"checksum_valid": True},
                    )
                )
        return entities


class OgrnipDetector(BaseDetector):
    entity_type = "OGRNIP"
    _pattern = re.compile(r"\b\d{15}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        for m in self._pattern.finditer(text):
            raw = m.group()
            if validate_ogrnip(raw):
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=CONFIDENCE_VALIDATED,
                        metadata={"checksum_valid": True},
                    )
                )
        return entities


class KppDetector(BaseDetector):
    entity_type = "KPP"
    _pattern = re.compile(r"\b\d{9}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        for m in self._pattern.finditer(text):
            if has_keyword_context(text, m.start(), ("кпп", "kpp")):
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        m.group(),
                        confidence=0.85,
                        metadata={"context_matched": True},
                    )
                )
        return entities


class BikDetector(BaseDetector):
    entity_type = "BIK"
    _pattern = re.compile(r"\b04\d{7}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        # TODO: verify BIK against Central Bank directory
        return _entities_from_matches(self.entity_type, text, self._pattern)


class BankAccountDetector(BaseDetector):
    entity_type = "BANK_ACCOUNT"
    _pattern = re.compile(r"\b\d{20}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        for m in self._pattern.finditer(text):
            if not has_keyword_context(
                text,
                m.start(),
                ("р/с", "рс", "расчетный", "расчётный", "счет", "счёт", "account"),
            ):
                continue
            raw = m.group()
            bik = find_nearby_bik(text, m.start())
            if bik is not None:
                if not validate_bank_account(raw, bik):
                    continue
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=CONFIDENCE_VALIDATED,
                        metadata={"checksum_valid": True, "context_matched": True},
                    )
                )
            else:
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=0.88,
                        metadata={"context_matched": True},
                    )
                )
        return entities


class CorrespondentAccountDetector(BaseDetector):
    entity_type = "CORRESPONDENT_ACCOUNT"
    _pattern = re.compile(r"\b301\d{17}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        for m in self._pattern.finditer(text):
            raw = m.group()
            bik = find_nearby_bik(text, m.start())
            if bik is not None:
                if not validate_correspondent_account(raw, bik):
                    continue
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=CONFIDENCE_VALIDATED,
                        metadata={"checksum_valid": True},
                    )
                )
            else:
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=CONFIDENCE_DEFAULT,
                    )
                )
        return entities


class CardNumberDetector(BaseDetector):
    entity_type = "CARD_NUMBER"
    _pattern = re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        for m in self._pattern.finditer(text):
            raw = m.group()
            if validate_card_number(raw):
                entities.append(
                    DetectedEntity.create(
                        self.entity_type,
                        m.start(),
                        m.end(),
                        raw,
                        confidence=CONFIDENCE_VALIDATED,
                        metadata={"checksum_valid": True},
                    )
                )
        return entities


class CadastralNumberDetector(BaseDetector):
    entity_type = "CADASTRAL_NUMBER"
    _pattern = re.compile(r"\b\d{2}:\d{2}:\d{6,7}:\d{1,7}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        return _entities_from_matches(self.entity_type, text, self._pattern)


class CourtCaseNumberDetector(BaseDetector):
    entity_type = "COURT_CASE_NUMBER"
    _pattern = re.compile(
        r"\b[А-ЯA-ZЁ]{1,3}\d{1,3}-\d{1,6}/\d{4}\b",
        re.IGNORECASE,
    )

    def detect(self, text: str) -> list[DetectedEntity]:
        # TODO: expand court case formats per jurisdiction
        return _entities_from_matches(self.entity_type, text, self._pattern)


class ContractNumberDetector(BaseDetector):
    entity_type = "CONTRACT_NUMBER"
    _pattern = re.compile(
        r"(?:договор|контракт|contract)\s*(?:№|#)?\s*[\w\-/]+",
        re.IGNORECASE,
    )

    def detect(self, text: str) -> list[DetectedEntity]:
        return _entities_from_matches(self.entity_type, text, self._pattern, confidence=0.8)


class IpAddressDetector(BaseDetector):
    entity_type = "IP_ADDRESS"
    _pattern = re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b"
    )

    def detect(self, text: str) -> list[DetectedEntity]:
        return _entities_from_matches(self.entity_type, text, self._pattern)


class UrlDetector(BaseDetector):
    entity_type = "URL"
    _pattern = re.compile(
        r"https?://[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=%\-]+",
        re.IGNORECASE,
    )

    def detect(self, text: str) -> list[DetectedEntity]:
        return _entities_from_matches(self.entity_type, text, self._pattern)


class TelegramHandleDetector(BaseDetector):
    entity_type = "TELEGRAM_HANDLE"
    _pattern = re.compile(r"(?<![\w.])@[a-zA-Z][a-zA-Z0-9_]{4,31}\b")

    def detect(self, text: str) -> list[DetectedEntity]:
        return _entities_from_matches(self.entity_type, text, self._pattern)


DEFAULT_DETECTORS: list[BaseDetector] = [
    PassportRuDetector(),
    SnilsDetector(),
    InnDetector(),
    OgrnDetector(),
    OgrnipDetector(),
    KppDetector(),
    BikDetector(),
    BankAccountDetector(),
    CorrespondentAccountDetector(),
    CardNumberDetector(),
    CadastralNumberDetector(),
    CourtCaseNumberDetector(),
    ContractNumberDetector(),
    EmailDetector(),
    PhoneDetector(),
    IpAddressDetector(),
    UrlDetector(),
    TelegramHandleDetector(),
]
