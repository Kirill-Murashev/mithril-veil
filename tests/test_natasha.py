import json

import pytest
from app.core.pipeline import detect_all, run_anonymization
from app.core.schemas import AnonymizeMode
from app.detectors.natasha_detector import NatashaDetector, reset_natasha_runtime_for_tests
from app.main import app
from fastapi.testclient import TestClient
from tests.conftest import SYNTHETIC_INN_10

client = TestClient(app)

SYNTHETIC_NER_TEXT = "Иван Тестович работает в ООО Тестовая Организация."
SYNTHETIC_PERSON = "Иван Тестович"
SYNTHETIC_ORG = "ООО Тестовая Организация"
PRIORITY_TEXT = f"ИНН {SYNTHETIC_INN_10} в ООО Тестовая Организация."


def _natasha_available() -> bool:
    try:
        reset_natasha_runtime_for_tests()
        NatashaDetector().detect("тест")
        return True
    except Exception:
        return False


natasha_required = pytest.mark.skipif(
    not _natasha_available(),
    reason="Natasha models not available in this environment",
)


@natasha_required
def test_natasha_detector_finds_entities():
    reset_natasha_runtime_for_tests()
    entities = NatashaDetector().detect(SYNTHETIC_NER_TEXT)
    types = {entity.type for entity in entities}
    assert types & {"PERSON", "ORGANIZATION", "LOCATION"}
    for entity in entities:
        assert entity.detector == "natasha"
        assert entity.metadata.get("model") == "natasha"
        assert entity.metadata.get("source_label") in {"PER", "ORG", "LOC"}


def test_api_backward_compatible_without_use_ner():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_NER_TEXT, "mode": "replace"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("use_ner") is None
    assert not any(e["detector"] == "natasha" for e in data["entities"])


@natasha_required
def test_api_use_ner_enabled_safe_response():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_NER_TEXT, "mode": "replace", "use_ner": True},
    )
    assert response.status_code == 200
    data = response.json()
    raw = json.dumps(data, ensure_ascii=False)
    assert SYNTHETIC_PERSON not in raw
    assert SYNTHETIC_ORG not in raw
    natasha_entities = [e for e in data["entities"] if e["detector"] == "natasha"]
    assert natasha_entities
    assert any(e["type"] in ("PERSON", "ORGANIZATION", "LOCATION") for e in natasha_entities)
    for entity in data["entities"]:
        assert entity["value_preview"] == "***"
        assert "text" not in entity


@natasha_required
def test_api_default_use_ner_false_explicit():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_NER_TEXT, "mode": "replace", "use_ner": False},
    )
    assert response.status_code == 200
    assert not any(e["detector"] == "natasha" for e in response.json()["entities"])


@natasha_required
def test_span_priority_inn_over_organization():
    entities = detect_all(PRIORITY_TEXT, use_ner=True)
    inn_entities = [e for e in entities if e.type == "INN"]
    assert inn_entities
    assert inn_entities[0].text == SYNTHETIC_INN_10


@natasha_required
def test_summary_includes_natasha_detector():
    response, _policy = run_anonymization(SYNTHETIC_NER_TEXT, AnonymizeMode.REPLACE, use_ner=True)
    assert response.summary.detectors.get("natasha", 0) >= 1


@natasha_required
def test_cli_use_ner_no_raw_values_in_report(tmp_path):
    from app.cli.main import main

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
            "--use-ner",
            "--report",
            str(report_path),
        ]
    )
    assert code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert SYNTHETIC_PERSON not in json.dumps(report)
    assert SYNTHETIC_ORG not in json.dumps(report)
    if report["summary"]["detectors"].get("natasha"):
        assert report["summary"]["detectors"]["natasha"] >= 1


def test_natasha_init_error_is_safe():
    from app.core.exceptions import MithrilVeilError

    reset_natasha_runtime_for_tests()
    import app.detectors.natasha_detector as natasha_module

    natasha_module._init_error = "Cannot initialize Natasha NER."
    natasha_module._ner_tagger = None
    with pytest.raises(MithrilVeilError, match="Cannot initialize") as exc_info:
        NatashaDetector().detect("тест")
    assert "Cannot initialize" in str(exc_info.value)
    assert "тест" not in str(exc_info.value)
    reset_natasha_runtime_for_tests()
