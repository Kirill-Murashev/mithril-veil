"""Encrypted mapping file I/O hooks (no raw values in reports or stdout)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from app.core.exceptions import MithrilVeilError, UnsafeFileOperation
from app.core.mapping import ReversibleMapping


class MappingEncryptionUnavailable(MithrilVeilError):
    """Raised when encrypted persistence is requested but no encryptor is configured."""


class MappingPayloadEncryptor(Protocol):
    """Pluggable encryptor for the Encryption/Security subagent."""

    def encrypt(self, plaintext: bytes, passphrase: str) -> bytes: ...

    def decrypt(self, ciphertext: bytes, passphrase: str) -> bytes: ...


def serialize_mapping_payload(mapping: ReversibleMapping) -> bytes:
    """UTF-8 JSON bytes of placeholder -> original (for encryption only)."""
    payload = mapping.serialize_for_encryption()
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def write_encrypted_mapping_file(
    path: Path,
    mapping: ReversibleMapping,
    *,
    passphrase: str,
    encryptor: MappingPayloadEncryptor | None = None,
    force: bool = False,
) -> None:
    """
    Persist mapping encrypted at ``path``.

    Requires an explicit ``encryptor`` (or a future default from the encryption module).
    Refuses to overwrite unless ``force`` is true.
    """
    if not mapping:
        raise MithrilVeilError("Cannot write an empty reversible mapping.")
    if path.exists() and not force:
        raise UnsafeFileOperation(
            f"Mapping file already exists: {path}. Pass force=True to overwrite."
        )
    if not encryptor:
        raise MappingEncryptionUnavailable(
            "Encrypted mapping persistence requires a MappingPayloadEncryptor. "
            "Wire the encryption module before calling write_encrypted_mapping_file."
        )
    if not passphrase:
        raise MithrilVeilError("Mapping passphrase must not be empty.")

    plaintext = serialize_mapping_payload(mapping)
    ciphertext = encryptor.encrypt(plaintext, passphrase)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_bytes(ciphertext)
    except OSError as exc:
        raise MithrilVeilError(f"Cannot write mapping file: {path}") from exc


def read_encrypted_mapping_file(
    path: Path,
    *,
    passphrase: str,
    encryptor: MappingPayloadEncryptor,
) -> dict[str, str]:
    """Decrypt and parse placeholder -> original mapping."""
    if not path.is_file():
        raise MithrilVeilError(f"Mapping file not found: {path}")
    if not passphrase:
        raise MithrilVeilError("Mapping passphrase must not be empty.")
    try:
        ciphertext = path.read_bytes()
    except OSError as exc:
        raise MithrilVeilError(f"Cannot read mapping file: {path}") from exc
    plaintext = encryptor.decrypt(ciphertext, passphrase)
    try:
        data = json.loads(plaintext.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MithrilVeilError("Mapping file is not valid encrypted JSON.") from exc
    if not isinstance(data, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in data.items()
    ):
        raise MithrilVeilError("Mapping file must be a JSON object of string keys and values.")
    return data
