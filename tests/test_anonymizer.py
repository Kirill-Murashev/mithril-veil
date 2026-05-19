import json

from app.main import app
from fastapi.testclient import TestClient
from tests.conftest import INVALID_INN_12, SYNTHETIC_INN_10, SYNTHETIC_INN_12

client = TestClient(app)

SYNTHETIC_EMAIL_TEXT = (
    "Иван Тестович написал на test@example.local и дублировал test2@example.local."
)
SYNTHETIC_PHONE_TEXT = "Связь: +7 (900) 111-22-33."
SYNTHETIC_INN_TEXT = f"Иван Тестович указал ИНН {SYNTHETIC_INN_12}."


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


def test_anonymize_phone_replace_mode():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_PHONE_TEXT, "mode": "replace"},
    )
    assert response.status_code == 200
    data = response.json()
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
    assert SYNTHETIC_INN_12 not in data["text"]
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


def test_api_never_returns_original_entity_values():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_INN_TEXT, "mode": "replace"},
    )
    data = response.json()
    raw = json.dumps(data)
    assert SYNTHETIC_INN_12 not in raw
    for entity in data["entities"]:
        assert entity["value_preview"] == "***"
        assert "text" not in entity
        assert entity.get("value") is None
        for meta_value in entity.get("metadata", {}).values():
            assert meta_value != SYNTHETIC_INN_12


def test_api_summary_counts():
    text = f"Контакт test@example.local, ИНН {SYNTHETIC_INN_10}, телефон +7 (900) 000-00-00."
    response = client.post(
        "/api/v1/anonymize",
        json={"text": text, "mode": "replace"},
    )
    data = response.json()
    summary = data["summary"]
    assert summary["total_entities"] == len(data["entities"])
    assert summary["total_entities"] >= 3
    assert summary["entity_counts"].get("EMAIL", 0) >= 1
    assert summary["entity_counts"].get("INN", 0) >= 1
    assert summary["detectors"].get("regex", 0) >= summary["total_entities"]


def test_invalid_inn_without_context_not_in_response():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": f"Число {INVALID_INN_12} в тексте.", "mode": "replace"},
    )
    data = response.json()
    assert INVALID_INN_12 in data["text"]  # not anonymized
    assert not any(e["type"] == "INN" for e in data["entities"])
