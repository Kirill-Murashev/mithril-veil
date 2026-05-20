"""Slice 8.1 security regression tests for encrypted pseudonymization mapping."""

from __future__ import annotations

import json

import pytest
from app.core.exceptions import UnsafeFileOperation
from app.document_io.base import ensure_mapping_path_distinct
from app.main import app
from app.security.encrypted_mapping import (
    DEFAULT_MAPPING_PASSPHRASE_ENV,
    write_encrypted_mapping_file,
)
from fastapi.testclient import TestClient
from tests.conftest import SYNTHETIC_INN_10
from tests.test_cli import SYNTHETIC_EMAIL, SYNTHETIC_PERSON, SYNTHETIC_TEXT, run_main

client = TestClient(app)

SYNTHETIC_MAPPING = {"[EMAIL_1]": SYNTHETIC_EMAIL}


@pytest.fixture
def mapping_passphrase(monkeypatch: pytest.MonkeyPatch) -> str:
    secret = "synthetic-hardening-passphrase"
    monkeypatch.setenv(DEFAULT_MAPPING_PASSPHRASE_ENV, secret)
    return secret


def test_api_pseudonymize_response_has_no_mapping_keys():
    response = client.post(
        "/api/v1/anonymize",
        json={
            "text": f"{SYNTHETIC_PERSON}, {SYNTHETIC_EMAIL}, ИНН {SYNTHETIC_INN_10}.",
            "mode": "pseudonymize",
            "use_ner": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    raw = json.dumps(data, ensure_ascii=False)
    forbidden_keys = (
        "mapping",
        "mapping_metadata",
        "original_to_placeholder",
        "placeholder_to_original",
    )
    for key in forbidden_keys:
        assert key not in data
    assert SYNTHETIC_EMAIL not in raw
    assert SYNTHETIC_PERSON not in raw
    assert SYNTHETIC_INN_10 not in raw
    for entity in data["entities"]:
        assert entity["value_preview"] == "***"


def test_api_replace_redact_unchanged():
    for mode in ("replace", "redact"):
        response = client.post(
            "/api/v1/anonymize",
            json={"text": SYNTHETIC_TEXT, "mode": mode},
        )
        assert response.status_code == 200
        data = response.json()
        assert "mapping" not in data
        assert SYNTHETIC_EMAIL not in json.dumps(data)


def test_api_presets_unaffected():
    response = client.get("/api/v1/presets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_cli_pseudonymize_stdout_stderr_no_raw_values(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(DEFAULT_MAPPING_PASSPHRASE_ENV, "synthetic-cli-secret")
    code, out, err = run_main(
        "anonymize-text",
        "--text",
        SYNTHETIC_TEXT,
        "--mode",
        "pseudonymize",
    )
    assert code == 0
    assert SYNTHETIC_EMAIL not in out
    assert SYNTHETIC_EMAIL not in err


def test_cli_missing_passphrase_error_has_no_raw_values(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(DEFAULT_MAPPING_PASSPHRASE_ENV, raising=False)
    mapping_path = tmp_path / "mapping.json.enc"
    code, out, err = run_main(
        "anonymize-text",
        "--text",
        SYNTHETIC_TEXT,
        "--mode",
        "pseudonymize",
        "--mapping-output",
        str(mapping_path),
    )
    assert code == 1
    assert SYNTHETIC_EMAIL not in out
    assert SYNTHETIC_EMAIL not in err
    assert DEFAULT_MAPPING_PASSPHRASE_ENV in err


def test_cli_invalid_mapping_suffix_error_has_no_raw_values(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv(DEFAULT_MAPPING_PASSPHRASE_ENV, "synthetic-cli-secret")
    code, out, err = run_main(
        "anonymize-text",
        "--text",
        SYNTHETIC_TEXT,
        "--mode",
        "pseudonymize",
        "--mapping-output",
        str(tmp_path / "mapping.json"),
    )
    assert code == 1
    assert SYNTHETIC_EMAIL not in out
    assert SYNTHETIC_EMAIL not in err
    assert ".json.enc" in err


def test_cli_mapping_exists_error_has_no_raw_values(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(DEFAULT_MAPPING_PASSPHRASE_ENV, "synthetic-cli-secret")
    mapping_path = tmp_path / "mapping.json.enc"
    mapping_path.write_text("{}", encoding="utf-8")
    code, out, err = run_main(
        "anonymize-text",
        "--text",
        SYNTHETIC_TEXT,
        "--mode",
        "pseudonymize",
        "--mapping-output",
        str(mapping_path),
    )
    assert code == 2
    assert SYNTHETIC_EMAIL not in out
    assert SYNTHETIC_EMAIL not in err


def test_cli_custom_passphrase_env(tmp_path, monkeypatch: pytest.MonkeyPatch):
    env_name = "CUSTOM_HARDENING_SECRET"
    monkeypatch.setenv(env_name, "custom-synthetic-secret")
    mapping_path = tmp_path / "mapping.json.enc"
    code, out, err = run_main(
        "anonymize-text",
        "--text",
        SYNTHETIC_TEXT,
        "--mode",
        "pseudonymize",
        "--mapping-output",
        str(mapping_path),
        "--mapping-passphrase-env",
        env_name,
    )
    assert code == 0
    assert SYNTHETIC_EMAIL not in out
    assert SYNTHETIC_EMAIL not in err
    body = mapping_path.read_text(encoding="utf-8")
    assert SYNTHETIC_EMAIL not in body


def test_encrypted_mapping_file_body_has_no_plaintext_original(tmp_path, mapping_passphrase: str):
    del mapping_passphrase
    path = tmp_path / "mapping.json.enc"
    write_encrypted_mapping_file(path, SYNTHETIC_MAPPING)
    body = path.read_text(encoding="utf-8")
    assert SYNTHETIC_EMAIL not in body
    assert SYNTHETIC_PERSON not in body
    envelope = json.loads(body)
    assert envelope.get("encrypted") is True
    assert "ciphertext" in envelope


def test_wrong_passphrase_error_has_no_raw_values(tmp_path, mapping_passphrase: str, monkeypatch):
    del mapping_passphrase
    from app.core.exceptions import MappingPassphraseInvalid
    from app.security.encrypted_mapping import read_encrypted_mapping_file

    path = tmp_path / "mapping.json.enc"
    write_encrypted_mapping_file(path, SYNTHETIC_MAPPING)
    monkeypatch.setenv(DEFAULT_MAPPING_PASSPHRASE_ENV, "wrong-passphrase")
    with pytest.raises(MappingPassphraseInvalid) as exc_info:
        read_encrypted_mapping_file(path)
    message = str(exc_info.value)
    assert SYNTHETIC_EMAIL not in message
    assert "wrong-passphrase" not in message


def test_tampered_ciphertext_error_has_no_raw_values(tmp_path, mapping_passphrase: str):
    del mapping_passphrase
    from app.core.exceptions import MappingPassphraseInvalid
    from app.security.encrypted_mapping import read_encrypted_mapping_file

    path = tmp_path / "mapping.json.enc"
    write_encrypted_mapping_file(path, SYNTHETIC_MAPPING)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["ciphertext"] = envelope["ciphertext"][:-4] + "XXXX"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(MappingPassphraseInvalid) as exc_info:
        read_encrypted_mapping_file(path)
    assert SYNTHETIC_EMAIL not in str(exc_info.value)


def test_anonymize_file_mapping_path_must_differ_from_report(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv(DEFAULT_MAPPING_PASSPHRASE_ENV, "synthetic-cli-secret")
    input_path = tmp_path / "in.txt"
    output_path = tmp_path / "out.txt"
    shared_path = tmp_path / "bundle.json.enc"
    input_path.write_text(SYNTHETIC_TEXT, encoding="utf-8")
    code, out, err = run_main(
        "anonymize-file",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--mode",
        "pseudonymize",
        "--mapping-output",
        str(shared_path),
        "--report",
        str(shared_path),
    )
    assert code == 2
    assert "report" in err.lower() or "mapping" in err.lower()
    assert SYNTHETIC_EMAIL not in err


def test_ensure_mapping_path_distinct_rejects_same_resolved_path(tmp_path):
    shared = tmp_path / "data.json.enc"
    shared.touch()
    with pytest.raises(UnsafeFileOperation):
        ensure_mapping_path_distinct(
            shared,
            report_path=shared,
        )
