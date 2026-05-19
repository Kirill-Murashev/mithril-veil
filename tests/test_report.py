import json

from app.core.pipeline import run_anonymization
from app.core.report import build_anonymization_report
from app.core.schemas import AnonymizeMode
from tests.conftest import SYNTHETIC_INN_10

SYNTHETIC_EMAIL = "test@example.local"


def test_report_shape_and_safety():
    text = f"Контакт: {SYNTHETIC_EMAIL}, ИНН {SYNTHETIC_INN_10}."
    response = run_anonymization(text, AnonymizeMode.REPLACE)
    report = build_anonymization_report(response, AnonymizeMode.REPLACE)

    assert report["service"] == "mithril-veil"
    assert report["version"] == "0.1.0"
    assert report["mode"] == "replace"
    assert "summary" in report
    assert report["summary"]["total_entities"] == len(report["entities"])

    raw = json.dumps(report, ensure_ascii=False)
    assert SYNTHETIC_EMAIL not in raw
    assert SYNTHETIC_INN_10 not in raw

    for entity in report["entities"]:
        assert entity["value_preview"] == "***"
        assert "text" not in entity
        for value in entity.get("metadata", {}).values():
            assert value != SYNTHETIC_EMAIL
            assert value != SYNTHETIC_INN_10
