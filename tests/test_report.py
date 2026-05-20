import json

from app.core.mapping import PseudonymizationSession
from app.core.pipeline import run_anonymization
from app.core.report import build_anonymization_report
from app.core.schemas import AnonymizeMode
from app.detectors.validators import normalize_digits
from tests.conftest import SYNTHETIC_CARD_VISA, SYNTHETIC_INN_10

SYNTHETIC_EMAIL = "test@example.local"
SYNTHETIC_PERSON = "Иван Тестович"


def test_report_shape_and_safety():
    text = f"Контакт: {SYNTHETIC_EMAIL}, ИНН {SYNTHETIC_INN_10}."
    response, _policy = run_anonymization(text, AnonymizeMode.REPLACE)
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


def test_report_masks_synthetic_card_number():
    text = f"Оплата картой {SYNTHETIC_CARD_VISA}."
    response, _policy = run_anonymization(text, AnonymizeMode.REPLACE)
    report = build_anonymization_report(response, AnonymizeMode.REPLACE)

    raw = json.dumps(report, ensure_ascii=False)
    assert SYNTHETIC_CARD_VISA not in raw
    assert normalize_digits(SYNTHETIC_CARD_VISA) not in raw

    card_entities = [e for e in report["entities"] if e["type"] == "CARD_NUMBER"]
    assert len(card_entities) == 1
    assert card_entities[0]["value_preview"] == "***"


def test_report_includes_safe_source_metadata():
    text = f"Контакт: {SYNTHETIC_EMAIL}."
    response, _policy = run_anonymization(text, AnonymizeMode.REPLACE)
    report = build_anonymization_report(
        response,
        AnonymizeMode.REPLACE,
        source={"input_type": "pdf", "page_count": 2, "file_size_bytes": 1234},
    )
    assert report["source"] == {
        "input_type": "pdf",
        "page_count": 2,
        "file_size_bytes": 1234,
    }
    assert SYNTHETIC_EMAIL not in json.dumps(report)


def test_report_mapping_metadata_written_encrypted_only():
    text = f"{SYNTHETIC_PERSON}, {SYNTHETIC_EMAIL}, ИНН {SYNTHETIC_INN_10}."
    session = PseudonymizationSession.reversible()
    response, _ = run_anonymization(text, AnonymizeMode.PSEUDONYMIZE, session=session)
    session.mark_mapping_written(encrypted=True)
    report = build_anonymization_report(
        response,
        AnonymizeMode.PSEUDONYMIZE,
        mapping_metadata=session.mapping_metadata,
    )
    assert report["mapping"] == {"written": True, "encrypted": True}
    raw = json.dumps(report, ensure_ascii=False)
    assert SYNTHETIC_PERSON not in raw
    assert SYNTHETIC_EMAIL not in raw
    assert SYNTHETIC_INN_10 not in raw


def test_report_omits_mapping_metadata_when_not_written():
    text = f"Контакт: {SYNTHETIC_EMAIL}."
    response, _ = run_anonymization(text, AnonymizeMode.PSEUDONYMIZE)
    report = build_anonymization_report(response, AnonymizeMode.PSEUDONYMIZE)
    assert "mapping" not in report
