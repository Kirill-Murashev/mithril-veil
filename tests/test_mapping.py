import json

from app.core.anonymizer import anonymize
from app.core.mapping import (
    MappingReportMetadata,
    PseudonymizationSession,
    ReversibleMapping,
)
from app.core.pipeline import run_anonymization
from app.core.placeholders import placeholder_for
from app.core.report import build_anonymization_report
from app.core.schemas import AnonymizeMode
from app.security.mapping_io import (
    MappingEncryptionUnavailable,
    MappingPayloadEncryptor,
    serialize_mapping_payload,
    write_encrypted_mapping_file,
)
from tests.conftest import SYNTHETIC_INN_10

SYNTHETIC_EMAIL = "test@example.local"
SYNTHETIC_PERSON = "Иван Тестович"


class _XorTestEncryptor:
    """Test-only stub; not for production."""

    def encrypt(self, plaintext: bytes, passphrase: str) -> bytes:
        key = passphrase.encode("utf-8")
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(plaintext))

    def decrypt(self, ciphertext: bytes, passphrase: str) -> bytes:
        return self.encrypt(ciphertext, passphrase)


def test_placeholder_for_matches_replace_mode():
    assert placeholder_for("EMAIL", 1) == "[EMAIL_1]"
    assert placeholder_for("PERSON", 2) == "[PERSON_2]"


def test_reversible_mapping_records_placeholder_to_original():
    text = f"Контакт {SYNTHETIC_EMAIL}, ИНН {SYNTHETIC_INN_10}."
    session = PseudonymizationSession.reversible()
    response, _ = run_anonymization(
        text,
        AnonymizeMode.PSEUDONYMIZE,
        session=session,
    )
    mapping = session.mapping
    assert mapping is not None
    assert len(mapping) >= 2
    serialized = mapping.serialize_for_encryption()
    assert "[EMAIL_1]" in serialized
    assert serialized["[EMAIL_1]"] == SYNTHETIC_EMAIL
    assert SYNTHETIC_INN_10 in serialized.values()
    assert SYNTHETIC_EMAIL not in response.text


def test_redact_mode_does_not_record_mapping():
    mapping = ReversibleMapping()
    from app.core.entities import DetectedEntity

    entity = DetectedEntity.create("EMAIL", 0, len(SYNTHETIC_EMAIL), SYNTHETIC_EMAIL)
    anonymize(
        f"Email: {SYNTHETIC_EMAIL}",
        [entity],
        AnonymizeMode.REDACT,
        reversible_mapping=mapping,
    )
    assert len(mapping) == 0


def test_report_mapping_metadata_has_no_raw_values():
    text = f"{SYNTHETIC_PERSON}, {SYNTHETIC_EMAIL}"
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
    assert "[PERSON_1]" not in raw


def test_mapping_report_metadata_default_is_safe():
    meta = MappingReportMetadata()
    assert meta.to_report_fragment() == {"mapping": {"written": False, "encrypted": False}}


def test_write_encrypted_mapping_file_with_stub_encryptor(tmp_path):
    mapping = ReversibleMapping()
    entity_text = SYNTHETIC_EMAIL
    from app.core.entities import DetectedEntity

    entity = DetectedEntity.create("EMAIL", 0, len(entity_text), entity_text)
    mapping.record(entity, index=1, placeholder=placeholder_for("EMAIL", 1))
    path = tmp_path / "mapping.json.enc"
    encryptor: MappingPayloadEncryptor = _XorTestEncryptor()
    write_encrypted_mapping_file(
        path,
        mapping,
        passphrase="test-passphrase",
        encryptor=encryptor,
    )
    assert path.is_file()
    assert SYNTHETIC_EMAIL not in path.read_bytes().decode("latin-1")


def test_write_encrypted_mapping_requires_encryptor(tmp_path):
    mapping = ReversibleMapping()
    from app.core.entities import DetectedEntity

    entity = DetectedEntity.create("EMAIL", 0, 5, "a@b.c")
    mapping.record(entity, index=1)
    path = tmp_path / "mapping.json.enc"
    try:
        write_encrypted_mapping_file(path, mapping, passphrase="x", encryptor=None)
    except MappingEncryptionUnavailable:
        pass
    else:
        raise AssertionError("expected MappingEncryptionUnavailable")


def test_serialize_mapping_payload_is_placeholder_keys_only():
    mapping = ReversibleMapping()
    from app.core.entities import DetectedEntity

    entity = DetectedEntity.create("INN", 10, 20, SYNTHETIC_INN_10)
    mapping.record(entity, index=1, placeholder="[INN_1]")
    payload = json.loads(serialize_mapping_payload(mapping).decode("utf-8"))
    assert payload == {"[INN_1]": SYNTHETIC_INN_10}
