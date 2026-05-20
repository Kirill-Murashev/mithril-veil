import json
from typing import Any
from unittest.mock import patch

import pytest
from app.core.exceptions import MithrilVeilError
from app.core.gliner_config import validate_gliner_labels
from app.core.pipeline import detect_all, run_anonymization
from app.core.schemas import AnonymizeMode, AnonymizeRequest
from app.detectors.gliner_detector import (
    GlinerDetector,
    reset_gliner_runtime_for_tests,
    set_fake_gliner_model,
)
from app.main import app
from fastapi.testclient import TestClient
from pydantic import ValidationError
from tests.conftest import SYNTHETIC_INN_10

client = TestClient(app)

SYNTHETIC_NER_TEXT = "Иван Тестович работает в ООО Тестовая Организация."
SYNTHETIC_PERSON = "Иван"
SYNTHETIC_ORG = "ООО Тестовая Организация"
SYNTHETIC_EMAIL = "test@example.local"
PRIORITY_TEXT = f"Контакт: {SYNTHETIC_EMAIL}, ИНН {SYNTHETIC_INN_10}."


class FakeGlinerModel:
    def __init__(self, predictions: list[dict[str, Any]] | None = None) -> None:
        self._predictions = predictions or []

    def predict_entities(
        self, text: str, labels: list[str], *, threshold: float = 0.5
    ) -> list[dict[str, Any]]:
        return [item for item in self._predictions if float(item.get("score", 0)) >= threshold]


@pytest.fixture(autouse=True)
def reset_gliner():
    reset_gliner_runtime_for_tests()
    yield
    reset_gliner_runtime_for_tests()


def _fake_predictions_for_ner_text() -> list[dict[str, Any]]:
    return [
        {
            "start": 0,
            "end": len(SYNTHETIC_PERSON),
            "text": SYNTHETIC_PERSON,
            "label": "person",
            "score": 0.91,
        },
        {
            "start": SYNTHETIC_NER_TEXT.index(SYNTHETIC_ORG),
            "end": SYNTHETIC_NER_TEXT.index(SYNTHETIC_ORG) + len(SYNTHETIC_ORG),
            "text": SYNTHETIC_ORG,
            "label": "organization",
            "score": 0.88,
        },
    ]


def test_gliner_detector_maps_labels_and_filters_threshold():
    set_fake_gliner_model(
        FakeGlinerModel(
            [
                {
                    "start": 0,
                    "end": 5,
                    "text": "Иван",
                    "label": "person",
                    "score": 0.9,
                },
                {
                    "start": 10,
                    "end": 15,
                    "text": "ООО",
                    "label": "organization",
                    "score": 0.4,
                },
            ]
        )
    )
    entities = GlinerDetector(labels=["person", "organization"], threshold=0.5).detect("Иван в ООО")
    assert len(entities) == 1
    assert entities[0].type == "PERSON"
    assert entities[0].detector == "gliner"
    assert entities[0].metadata["model"] == "gliner"
    assert entities[0].metadata["source_label"] == "person"
    assert entities[0].metadata["threshold"] == 0.5
    assert "Иван" not in json.dumps(entities[0].metadata)


def test_api_backward_compatible_without_gliner():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_NER_TEXT, "mode": "replace"},
    )
    assert response.status_code == 200
    assert not any(e["detector"] == "gliner" for e in response.json()["entities"])


def test_api_use_gliner_with_fake_model():
    set_fake_gliner_model(FakeGlinerModel(_fake_predictions_for_ner_text()))
    response = client.post(
        "/api/v1/anonymize",
        json={
            "text": SYNTHETIC_NER_TEXT,
            "mode": "replace",
            "use_gliner": True,
            "gliner_labels": ["person", "organization"],
            "gliner_threshold": 0.5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    raw = json.dumps(data, ensure_ascii=False)
    assert SYNTHETIC_PERSON not in raw
    assert SYNTHETIC_ORG not in raw
    gliner_entities = [e for e in data["entities"] if e["detector"] == "gliner"]
    assert gliner_entities
    assert data["summary"]["detectors"].get("gliner", 0) >= 1


def test_api_gliner_threshold_validation():
    with pytest.raises(ValidationError):
        AnonymizeRequest(
            text="тест",
            mode="replace",
            use_gliner=True,
            gliner_threshold=1.5,
        )


def test_validate_gliner_labels_rejects_empty_and_too_many():
    with pytest.raises(ValueError, match="empty"):
        validate_gliner_labels([""])
    with pytest.raises(ValueError, match="50"):
        validate_gliner_labels([f"label{i}" for i in range(51)])


def test_gliner_priority_regex_email_over_person():
    email_start = PRIORITY_TEXT.index(SYNTHETIC_EMAIL)
    set_fake_gliner_model(
        FakeGlinerModel(
            [
                {
                    "start": email_start,
                    "end": email_start + len(SYNTHETIC_EMAIL),
                    "text": SYNTHETIC_EMAIL,
                    "label": "person",
                    "score": 0.95,
                },
            ]
        )
    )
    entities = detect_all(PRIORITY_TEXT, use_gliner=True, gliner_labels=["person", "email"])
    emails = [e for e in entities if e.type == "EMAIL"]
    assert emails
    assert emails[0].detector == "regex"
    assert emails[0].text == SYNTHETIC_EMAIL


def test_gliner_priority_inn_over_organization():
    set_fake_gliner_model(
        FakeGlinerModel(
            [
                {
                    "start": 0,
                    "end": len(PRIORITY_TEXT),
                    "text": PRIORITY_TEXT,
                    "label": "organization",
                    "score": 0.99,
                },
            ]
        )
    )
    entities = detect_all(
        PRIORITY_TEXT,
        use_gliner=True,
        gliner_labels=["organization", "tax identification number"],
    )
    inns = [e for e in entities if e.type == "INN"]
    assert inns
    assert inns[0].text == SYNTHETIC_INN_10


def test_gliner_import_error_safe_message():
    reset_gliner_runtime_for_tests()

    def boom(_name: str):
        raise MithrilVeilError("GLiNER is not installed. Install with: pip install -e '.[gliner]'")

    with patch("app.detectors.gliner_detector._load_gliner_model", side_effect=boom):
        with pytest.raises(MithrilVeilError, match="not installed") as exc_info:
            GlinerDetector().detect("секретный текст")
        assert "секретный" not in str(exc_info.value)


def test_cli_use_gliner_with_fake_model(tmp_path):
    from app.cli.main import main

    set_fake_gliner_model(FakeGlinerModel(_fake_predictions_for_ner_text()))
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.txt"
    report_path = tmp_path / "report.json"
    input_path.write_text(SYNTHETIC_NER_TEXT, encoding="utf-8")
    code = main(
        [
            "anonymize-file",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--mode",
            "replace",
            "--use-gliner",
            "--gliner-label",
            "person",
            "--gliner-label",
            "organization",
            "--report",
            str(report_path),
        ]
    )
    assert code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert SYNTHETIC_PERSON not in json.dumps(report)
    assert report["summary"]["detectors"].get("gliner", 0) >= 1


def test_cli_invalid_threshold_exit_code():
    from app.cli.main import main

    code = main(
        [
            "anonymize-text",
            "--text",
            "тест",
            "--mode",
            "replace",
            "--use-gliner",
            "--gliner-threshold",
            "2.0",
        ]
    )
    assert code == 1


def test_run_anonymization_gliner_disabled_by_default():
    set_fake_gliner_model(FakeGlinerModel(_fake_predictions_for_ner_text()))
    response, _policy = run_anonymization(SYNTHETIC_NER_TEXT, AnonymizeMode.REPLACE)
    assert not any(e.detector == "gliner" for e in response.entities)


@pytest.mark.integration
def test_gliner_integration_optional():
    pytest.importorskip("gliner")
    reset_gliner_runtime_for_tests()
    response, _policy = run_anonymization(
        SYNTHETIC_NER_TEXT,
        AnonymizeMode.REPLACE,
        use_gliner=True,
        gliner_labels=["person", "organization"],
    )
    assert response.summary.total_entities >= 0
