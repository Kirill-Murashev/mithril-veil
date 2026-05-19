from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

SYNTHETIC_EMAIL_TEXT = (
    "Иван Тестович написал на test@example.local и дублировал test2@example.local."
)
SYNTHETIC_PHONE_TEXT = "Связь: +7 (900) 111-22-33."
SYNTHETIC_INN_TEXT = "Иван Тестович указал ИНН 123456789012."


def test_anonymize_email_replace_mode():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_EMAIL_TEXT, "mode": "replace"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "test@example.local" not in data["text"]
    assert "[EMAIL_1]" in data["text"]
    assert "[EMAIL_2]" in data["text"]
    emails = [e for e in data["entities"] if e["type"] == "EMAIL"]
    assert len(emails) == 2
    assert emails[0]["replacement"] == "[EMAIL_1]"
    assert emails[1]["replacement"] == "[EMAIL_2]"


def test_anonymize_phone_replace_mode():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_PHONE_TEXT, "mode": "replace"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "+7" not in data["text"] or "[PHONE_1]" in data["text"]
    phones = [e for e in data["entities"] if e["type"] == "PHONE"]
    assert len(phones) >= 1
    assert phones[0]["replacement"] == "[PHONE_1]"


def test_anonymize_inn_replace_mode():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_INN_TEXT, "mode": "replace"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "123456789012" not in data["text"]
    inns = [e for e in data["entities"] if e["type"] == "INN"]
    assert len(inns) >= 1
    assert inns[0]["replacement"] == "[INN_1]"


def test_anonymize_redact_mode():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": "Email: fake@example.local", "mode": "redact"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "fake@example.local" not in data["text"]
    assert "[REDACTED]" in data["text"]
    assert data["entities"][0]["replacement"] == "[REDACTED]"


def test_api_never_returns_original_entity_values():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_INN_TEXT, "mode": "replace"},
    )
    data = response.json()
    for entity in data["entities"]:
        assert entity["value_preview"] == "***"
        assert "123456789012" not in str(entity)
        assert entity.get("value") is None
