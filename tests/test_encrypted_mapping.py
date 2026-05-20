import json
from pathlib import Path

import pytest
from app.core.exceptions import (
    InvalidEncryptedMappingPath,
    MappingPassphraseInvalid,
    MappingPassphraseMissing,
    UnsafeFileOperation,
)
from app.security.encrypted_mapping import (
    DEFAULT_MAPPING_PASSPHRASE_ENV,
    ENCRYPTED_MAPPING_SUFFIX,
    KDF_ALGORITHM,
    KDF_ITERATIONS,
    MAPPING_FORMAT_ID,
    load_mapping_passphrase,
    read_encrypted_mapping_file,
    require_encrypted_mapping_path,
    write_encrypted_mapping_file,
)

SYNTHETIC_PLACEHOLDER = "[PERSON_1]"
SYNTHETIC_ORIGINAL = "Иван Тестович"
SYNTHETIC_MAPPING = {SYNTHETIC_PLACEHOLDER: SYNTHETIC_ORIGINAL}


@pytest.fixture
def mapping_passphrase(monkeypatch: pytest.MonkeyPatch) -> str:
    secret = "synthetic-test-passphrase-only"
    monkeypatch.setenv(DEFAULT_MAPPING_PASSPHRASE_ENV, secret)
    return secret


def test_require_encrypted_mapping_path_rejects_plain_json(tmp_path: Path) -> None:
    with pytest.raises(InvalidEncryptedMappingPath):
        require_encrypted_mapping_path(tmp_path / "mapping.json")


def test_load_mapping_passphrase_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(DEFAULT_MAPPING_PASSPHRASE_ENV, raising=False)
    with pytest.raises(MappingPassphraseMissing) as exc_info:
        load_mapping_passphrase()
    message = str(exc_info.value)
    assert DEFAULT_MAPPING_PASSPHRASE_ENV in message
    assert SYNTHETIC_ORIGINAL not in message


def test_write_refuses_overwrite(tmp_path: Path, mapping_passphrase: str) -> None:
    del mapping_passphrase
    path = tmp_path / f"mapping{ENCRYPTED_MAPPING_SUFFIX}"
    write_encrypted_mapping_file(path, SYNTHETIC_MAPPING)
    with pytest.raises(UnsafeFileOperation):
        write_encrypted_mapping_file(path, SYNTHETIC_MAPPING)


def test_write_with_force_overwrites(tmp_path: Path, mapping_passphrase: str) -> None:
    del mapping_passphrase
    path = tmp_path / f"mapping{ENCRYPTED_MAPPING_SUFFIX}"
    write_encrypted_mapping_file(path, SYNTHETIC_MAPPING)
    updated = {SYNTHETIC_PLACEHOLDER: "Другой Тестович"}
    write_encrypted_mapping_file(path, updated, force=True)
    restored = read_encrypted_mapping_file(path)
    assert restored == updated


def test_encrypted_envelope_metadata(tmp_path: Path, mapping_passphrase: str) -> None:
    del mapping_passphrase
    path = tmp_path / f"mapping{ENCRYPTED_MAPPING_SUFFIX}"
    write_encrypted_mapping_file(path, SYNTHETIC_MAPPING)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    assert envelope["format"] == MAPPING_FORMAT_ID
    assert envelope["encrypted"] is True
    assert envelope["kdf"] == KDF_ALGORITHM
    assert envelope["iterations"] == KDF_ITERATIONS
    assert SYNTHETIC_ORIGINAL not in path.read_text(encoding="utf-8")


def test_roundtrip_decrypt(tmp_path: Path, mapping_passphrase: str) -> None:
    del mapping_passphrase
    path = tmp_path / f"mapping{ENCRYPTED_MAPPING_SUFFIX}"
    write_encrypted_mapping_file(path, SYNTHETIC_MAPPING)
    restored = read_encrypted_mapping_file(path)
    assert restored == SYNTHETIC_MAPPING


def test_wrong_passphrase_raises_invalid(
    tmp_path: Path,
    mapping_passphrase: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del mapping_passphrase
    path = tmp_path / f"mapping{ENCRYPTED_MAPPING_SUFFIX}"
    write_encrypted_mapping_file(path, SYNTHETIC_MAPPING)
    monkeypatch.setenv(DEFAULT_MAPPING_PASSPHRASE_ENV, "wrong-passphrase")
    with pytest.raises(MappingPassphraseInvalid) as exc_info:
        read_encrypted_mapping_file(path)
    message = str(exc_info.value)
    assert SYNTHETIC_ORIGINAL not in message
    assert "wrong-passphrase" not in message


def test_tampered_ciphertext_raises_invalid(
    tmp_path: Path,
    mapping_passphrase: str,
) -> None:
    del mapping_passphrase
    path = tmp_path / f"mapping{ENCRYPTED_MAPPING_SUFFIX}"
    write_encrypted_mapping_file(path, SYNTHETIC_MAPPING)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["ciphertext"] = envelope["ciphertext"][:-4] + "XXXX"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(MappingPassphraseInvalid):
        read_encrypted_mapping_file(path)


def test_custom_passphrase_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_name = "CUSTOM_MAPPING_SECRET"
    monkeypatch.setenv(env_name, "custom-synthetic-secret")
    path = tmp_path / f"mapping{ENCRYPTED_MAPPING_SUFFIX}"
    write_encrypted_mapping_file(path, SYNTHETIC_MAPPING, passphrase_env=env_name)
    monkeypatch.delenv(DEFAULT_MAPPING_PASSPHRASE_ENV, raising=False)
    with pytest.raises(MappingPassphraseMissing):
        read_encrypted_mapping_file(path)
    restored = read_encrypted_mapping_file(path, passphrase_env=env_name)
    assert restored == SYNTHETIC_MAPPING
