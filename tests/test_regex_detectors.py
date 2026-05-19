from app.detectors.regex_detectors import (
    BankAccountDetector,
    BikDetector,
    CadastralNumberDetector,
    ContractNumberDetector,
    CourtCaseNumberDetector,
    EmailDetector,
    InnDetector,
    KppDetector,
    OgrnDetector,
    PhoneDetector,
    SnilsDetector,
    TelegramHandleDetector,
    UrlDetector,
)
from tests.conftest import INVALID_INN_12, SYNTHETIC_INN_10, SYNTHETIC_INN_12, SYNTHETIC_SNILS


def test_email_detector_finds_synthetic_email():
    text = "Пишите на test@example.local для связи."
    spans = EmailDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].type == "EMAIL"
    assert spans[0].text == "test@example.local"


def test_phone_detector_finds_synthetic_phone():
    text = "Телефон: +7 (900) 000-00-00."
    spans = PhoneDetector().detect(text)
    assert len(spans) >= 1
    assert spans[0].type == "PHONE"


def test_inn_detector_valid_10_digit_synthetic():
    text = f"ИНН организации {SYNTHETIC_INN_10} в форме."
    spans = InnDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].metadata.get("checksum_valid") is True
    assert spans[0].confidence >= 0.9


def test_inn_detector_valid_12_digit_synthetic():
    text = f"ИНН {SYNTHETIC_INN_12} указан."
    spans = InnDetector().detect(text)
    assert any(s.text.replace(" ", "") == SYNTHETIC_INN_12 for s in spans)
    assert spans[0].metadata.get("checksum_valid") is True


def test_inn_detector_invalid_without_context_not_emitted():
    text = f"Номер {INVALID_INN_12} без контекста."
    spans = InnDetector().detect(text)
    assert spans == []


def test_inn_detector_invalid_with_context_weak_confidence():
    text = f"ИНН {INVALID_INN_12} в черновике."
    spans = InnDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].metadata.get("checksum_valid") is False
    assert spans[0].confidence < 0.5


def test_snils_detector_valid_synthetic():
    text = f"СНИЛС: {SYNTHETIC_SNILS}."
    spans = SnilsDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].metadata.get("checksum_valid") is True


def test_snils_detector_invalid_with_context():
    text = "СНИЛС 087-654-303 99 указан."  # synthetic, invalid checksum
    spans = SnilsDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].metadata.get("checksum_valid") is False


def test_ogrn_detector():
    text = "ОГРН 1027700132193 зарегистрирован."  # synthetic length, TODO checksum
    spans = OgrnDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].type == "OGRN"


def test_kpp_detector_with_context():
    text = "КПП 770101001 для филиала."
    spans = KppDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].type == "KPP"


def test_bik_detector():
    text = "БИК 044525225 в реквизитах."
    spans = BikDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].type == "BIK"


def test_bank_account_detector_with_context():
    text = "р/с 40802810400000123456 в банке."  # synthetic 20-digit account
    spans = BankAccountDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].type == "BANK_ACCOUNT"


def test_cadastral_number_detector():
    text = "Кадастр 77:01:0001001:1001."
    spans = CadastralNumberDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].type == "CADASTRAL_NUMBER"


def test_court_case_number_detector():
    text = "Дело А40-12345/2024 рассмотрено."
    spans = CourtCaseNumberDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].type == "COURT_CASE_NUMBER"


def test_contract_number_detector():
    text = "договор №ТЕСТ-2024/01 подписан."
    spans = ContractNumberDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].type == "CONTRACT_NUMBER"


def test_url_detector():
    text = "Сайт https://example.local/docs/page1 опубликован."
    spans = UrlDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].type == "URL"


def test_telegram_handle_detector():
    text = "Telegram: @test_user_demo для связи."
    spans = TelegramHandleDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].type == "TELEGRAM_HANDLE"
