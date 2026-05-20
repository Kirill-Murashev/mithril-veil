import json

import pytest
from app.cli.main import main
from app.core.pipeline import run_anonymization
from app.core.presets import (
    REQUIRED_PRESET_IDS,
    InvalidPresetError,
    UnknownPresetError,
    apply_preset_to_options,
    list_presets,
    load_preset,
    resolve_anonymization_options,
    validate_preset_config,
)
from app.core.report import build_anonymization_report
from app.core.schemas import AnonymizeMode, AnonymizeRequest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

SYNTHETIC_EMAIL = "test@example.local"
SYNTHETIC_EMAIL_TEXT = f"Контакт: {SYNTHETIC_EMAIL}."
SYNTHETIC_NER_TEXT = "Иван Тестович работает в ООО Тестовая Организация."
SYNTHETIC_PERSON = "Иван"
SYNTHETIC_ORG = "ООО Тестовая Организация"
SYNTHETIC_URL_TEXT = "Сайт: https://example.local/docs."


def test_loads_all_required_presets():
    for preset_id in REQUIRED_PRESET_IDS:
        config = load_preset(preset_id)
        assert config.id == preset_id
        assert config.name
        assert config.description
        assert config.enabled_entities
        assert config.detectors.regex is True


def test_list_presets_returns_safe_info():
    infos = list_presets()
    assert len(infos) == len(REQUIRED_PRESET_IDS)
    ids = {info.id for info in infos}
    assert ids == set(REQUIRED_PRESET_IDS)
    for info in infos:
        assert info.enabled_entities
        assert "***" not in info.description


def test_unknown_preset_raises_safe_error():
    with pytest.raises(UnknownPresetError) as exc_info:
        load_preset("nonexistent_preset")
    message = str(exc_info.value)
    assert "nonexistent_preset" in message
    assert SYNTHETIC_EMAIL not in message


def test_malformed_preset_rejected(tmp_path, monkeypatch):
    bad_dir = tmp_path / "presets"
    bad_dir.mkdir()
    bad_file = bad_dir / "general_ru.yml"
    bad_file.write_text("id: general_ru\nenabled_entities: []\n", encoding="utf-8")
    monkeypatch.setattr("app.core.presets.PRESETS_DIR", bad_dir)
    from app.core.presets import load_preset

    load_preset.cache_clear()
    with pytest.raises((InvalidPresetError, UnknownPresetError)):
        load_preset("general_ru")


def test_validate_preset_config_rejects_unknown_entity():
    with pytest.raises(InvalidPresetError):
        validate_preset_config(
            {
                "id": "bad",
                "name": "Bad",
                "description": "x",
                "enabled_entities": ["NOT_A_REAL_TYPE"],
            },
            source="test",
        )


def test_general_ru_disables_ner_by_default():
    options = resolve_anonymization_options(preset_id="general_ru")
    assert options.use_ner is False
    assert options.use_gliner is False
    assert "EMAIL" in options.enabled_entities


def test_legal_ru_enables_ner_by_default():
    options = resolve_anonymization_options(preset_id="legal_ru")
    assert options.use_ner is True
    assert options.use_gliner is False


def test_explicit_use_ner_overrides_preset():
    options = resolve_anonymization_options(preset_id="legal_ru", use_ner=False)
    assert options.use_ner is False


def test_entity_filtering_excludes_disabled_types():
    text = SYNTHETIC_URL_TEXT
    response, _ = run_anonymization(
        text,
        AnonymizeMode.REPLACE,
        preset="banking_ru",
    )
    assert not any(e.type == "URL" for e in response.entities)
    assert "URL" not in response.summary.entity_counts


def test_general_ru_filters_email_only_profile():
    response, _ = run_anonymization(
        SYNTHETIC_EMAIL_TEXT,
        AnonymizeMode.REPLACE,
        preset="general_ru",
    )
    types = {e.type for e in response.entities}
    assert "EMAIL" in types
    assert "URL" not in types


def test_api_list_presets():
    response = client.get("/api/v1/presets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(REQUIRED_PRESET_IDS)
    assert all(item["detectors"]["gliner"] is False for item in data)


def test_api_anonymize_with_preset_general_ru():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_EMAIL_TEXT, "mode": "replace", "preset": "general_ru"},
    )
    assert response.status_code == 200
    data = response.json()
    assert SYNTHETIC_EMAIL not in data["text"]
    assert any(e["type"] == "EMAIL" for e in data["entities"])


def test_api_unknown_preset_safe_error():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_EMAIL_TEXT, "mode": "replace", "preset": "unknown_xyz"},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "unknown_xyz" in detail
    assert SYNTHETIC_EMAIL not in detail


def test_api_use_ner_override_legal_preset():
    response = client.post(
        "/api/v1/anonymize",
        json={
            "text": SYNTHETIC_NER_TEXT,
            "mode": "replace",
            "preset": "legal_ru",
            "use_ner": False,
        },
    )
    assert response.status_code == 200
    assert not any(e["detector"] == "natasha" for e in response.json()["entities"])


def test_api_never_exposes_raw_values_with_preset():
    response = client.post(
        "/api/v1/anonymize",
        json={"text": SYNTHETIC_EMAIL_TEXT, "mode": "replace", "preset": "general_ru"},
    )
    raw = json.dumps(response.json())
    assert SYNTHETIC_EMAIL not in raw
    for entity in response.json()["entities"]:
        assert entity["value_preview"] == "***"


def test_anonymize_request_backward_compatible_defaults():
    req = AnonymizeRequest(text="x")
    assert req.preset is None
    assert req.use_ner is None
    assert req.use_gliner is None


def test_cli_list_presets(capsys):
    code = main(["list-presets"])
    assert code == 0
    out = capsys.readouterr().out
    assert "general_ru" in out
    assert "legal_ru" in out
    assert "valuation_ru" in out


def test_cli_anonymize_text_with_preset(capsys):
    code = main(
        [
            "anonymize-text",
            "--text",
            SYNTHETIC_EMAIL_TEXT,
            "--mode",
            "replace",
            "--preset",
            "general_ru",
        ]
    )
    assert code == 0
    assert SYNTHETIC_EMAIL not in capsys.readouterr().out


def test_cli_unknown_preset_fails(capsys):
    code = main(
        [
            "anonymize-text",
            "--text",
            "x",
            "--preset",
            "bad_preset",
        ]
    )
    assert code == 1
    err = capsys.readouterr().err
    assert "bad_preset" in err
    assert "x" not in err or "Unknown preset" in err


def test_cli_report_includes_safe_policy_metadata(tmp_path):
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.txt"
    report_path = tmp_path / "report.json"
    input_path.write_text(SYNTHETIC_EMAIL_TEXT, encoding="utf-8")
    code = main(
        [
            "anonymize-file",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--mode",
            "replace",
            "--preset",
            "valuation_ru",
            "--report",
            str(report_path),
        ]
    )
    assert code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["policy"]["preset"] == "valuation_ru"
    assert "EMAIL" in report["policy"]["enabled_entities"]
    assert report["policy"]["detectors"]["gliner"] is False
    assert SYNTHETIC_EMAIL not in json.dumps(report)


def test_report_policy_metadata_safe():
    response, policy = run_anonymization(
        SYNTHETIC_EMAIL_TEXT,
        AnonymizeMode.REPLACE,
        preset="general_ru",
    )
    report = build_anonymization_report(response, AnonymizeMode.REPLACE, policy=policy)
    assert report["policy"]["preset"] == "general_ru"
    assert SYNTHETIC_EMAIL not in json.dumps(report)


def test_banking_ru_keeps_high_priority_inn():
    from tests.conftest import SYNTHETIC_INN_10

    text = f"ИНН {SYNTHETIC_INN_10}."
    response, _ = run_anonymization(text, AnonymizeMode.REPLACE, preset="banking_ru")
    assert any(e.type == "INN" for e in response.entities)


def test_apply_preset_gliner_stays_off():
    preset = load_preset("legal_ru")
    options = apply_preset_to_options(preset, use_gliner=None)
    assert options.use_gliner is False
