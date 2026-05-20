"""Encrypted local persistence for reversible pseudonymization mappings."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.exceptions import (
    InvalidEncryptedMappingPath,
    MappingPassphraseInvalid,
    MappingPassphraseMissing,
    MithrilVeilError,
    UnsafeFileOperation,
)

DEFAULT_MAPPING_PASSPHRASE_ENV = "MITHRIL_VEIL_MAPPING_PASSPHRASE"
ENCRYPTED_MAPPING_SUFFIX = ".json.enc"
MAPPING_FORMAT_ID = "mithril-veil-mapping-v1"
KDF_ALGORITHM = "PBKDF2-HMAC-SHA256"
KDF_ITERATIONS = 600_000
KDF_SALT_BYTES = 16


def require_encrypted_mapping_path(path: Path) -> None:
    """Ensure the path uses the encrypted mapping file suffix."""
    name = path.name.lower()
    if not name.endswith(ENCRYPTED_MAPPING_SUFFIX) or name == ENCRYPTED_MAPPING_SUFFIX:
        raise InvalidEncryptedMappingPath(
            f"Mapping output path must end with {ENCRYPTED_MAPPING_SUFFIX!r}."
        )


def load_mapping_passphrase(
    *,
    passphrase_env: str = DEFAULT_MAPPING_PASSPHRASE_ENV,
) -> str:
    """Read passphrase from environment; never log or return it in error messages."""
    value = os.environ.get(passphrase_env)
    if value is None or not value.strip():
        raise MappingPassphraseMissing(
            f"Mapping passphrase is not set. Set the {passphrase_env} environment variable."
        )
    return value


def _derive_fernet_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def _encrypt_mapping_payload(mapping: dict[str, str], passphrase: str) -> dict[str, Any]:
    salt = os.urandom(KDF_SALT_BYTES)
    fernet = Fernet(_derive_fernet_key(passphrase, salt))
    plaintext = json.dumps(mapping, ensure_ascii=False, sort_keys=True).encode("utf-8")
    token = fernet.encrypt(plaintext).decode("ascii")
    return {
        "format": MAPPING_FORMAT_ID,
        "encrypted": True,
        "kdf": KDF_ALGORITHM,
        "iterations": KDF_ITERATIONS,
        "salt": base64.urlsafe_b64encode(salt).decode("ascii"),
        "ciphertext": token,
    }


def _decrypt_mapping_envelope(envelope: dict[str, Any], passphrase: str) -> dict[str, str]:
    if envelope.get("format") != MAPPING_FORMAT_ID or not envelope.get("encrypted"):
        raise MappingPassphraseInvalid("Mapping file is not a supported encrypted format.")
    if envelope.get("kdf") != KDF_ALGORITHM:
        raise MappingPassphraseInvalid("Mapping file uses an unsupported key derivation function.")
    iterations = envelope.get("iterations")
    if iterations != KDF_ITERATIONS:
        raise MappingPassphraseInvalid("Mapping file uses unsupported encryption parameters.")
    salt_b64 = envelope.get("salt")
    ciphertext = envelope.get("ciphertext")
    if not isinstance(salt_b64, str) or not isinstance(ciphertext, str):
        raise MappingPassphraseInvalid("Mapping file is missing required encryption fields.")
    try:
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        fernet = Fernet(_derive_fernet_key(passphrase, salt))
        plaintext = fernet.decrypt(ciphertext.encode("ascii"))
    except (InvalidToken, ValueError, TypeError) as exc:
        raise MappingPassphraseInvalid(
            "Cannot decrypt mapping file. Check the passphrase and file integrity."
        ) from exc
    try:
        payload = json.loads(plaintext.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MappingPassphraseInvalid("Mapping file payload is invalid.") from exc
    if not isinstance(payload, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in payload.items()
    ):
        raise MappingPassphraseInvalid("Mapping file payload is invalid.")
    return payload


def write_encrypted_mapping_file(
    path: Path,
    mapping: dict[str, str],
    *,
    force: bool = False,
    passphrase_env: str = DEFAULT_MAPPING_PASSPHRASE_ENV,
) -> None:
    """Write mapping to an encrypted file only when explicitly called.

    The mapping dict must use placeholder keys and original values. Raw values are
    never logged or included in raised error messages.
    """
    require_encrypted_mapping_path(path)
    if path.exists() and not force:
        raise UnsafeFileOperation(f"Mapping file already exists: {path}. Use --force to overwrite.")
    passphrase = load_mapping_passphrase(passphrase_env=passphrase_env)
    envelope = _encrypt_mapping_payload(mapping, passphrase)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise MithrilVeilError(f"Cannot write mapping file: {path}") from exc


def read_encrypted_mapping_file(
    path: Path,
    *,
    passphrase_env: str = DEFAULT_MAPPING_PASSPHRASE_ENV,
) -> dict[str, str]:
    """Decrypt a mapping file (for local restore workflows and tests)."""
    require_encrypted_mapping_path(path)
    if not path.is_file():
        raise MithrilVeilError(f"Mapping file not found: {path}")
    passphrase = load_mapping_passphrase(passphrase_env=passphrase_env)
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MappingPassphraseInvalid("Mapping file is not valid encrypted JSON.") from exc
    if not isinstance(envelope, dict):
        raise MappingPassphraseInvalid("Mapping file is not valid encrypted JSON.")
    return _decrypt_mapping_envelope(envelope, passphrase)
