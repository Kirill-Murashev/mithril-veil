from app.detectors.regex_detectors import EmailDetector, InnDetector, PhoneDetector


def test_email_detector_finds_synthetic_email():
    text = "Пишите на test@example.local для связи."
    spans = EmailDetector().detect(text)
    assert len(spans) == 1
    assert spans[0].entity_type == "EMAIL"
    assert spans[0].value == "test@example.local"


def test_phone_detector_finds_synthetic_phone():
    text = "Телефон: +7 (900) 000-00-00."
    spans = PhoneDetector().detect(text)
    assert len(spans) >= 1
    assert spans[0].entity_type == "PHONE"


def test_inn_detector_finds_synthetic_inn():
    text = "ИНН 123456789012 указан в форме."
    spans = InnDetector().detect(text)
    assert any(s.value == "123456789012" for s in spans)
    assert all(s.entity_type == "INN" for s in spans)
