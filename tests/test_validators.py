from app.detectors.validators import normalize_digits, validate_inn, validate_snils
from tests.conftest import (
    INVALID_INN_12,
    SYNTHETIC_INN_10,
    SYNTHETIC_INN_12,
    SYNTHETIC_SNILS,
    SYNTHETIC_SNILS_DIGITS,
)


def test_normalize_digits_strips_formatting():
    assert normalize_digits("087-654-303 00") == "08765430300"


def test_validate_inn_10_digit_synthetic():
    assert validate_inn(SYNTHETIC_INN_10) is True


def test_validate_inn_12_digit_synthetic():
    assert validate_inn(SYNTHETIC_INN_12) is True


def test_validate_inn_rejects_invalid_checksum():
    assert validate_inn(INVALID_INN_12) is False
    assert validate_inn("1234567890") is False


def test_validate_snils_synthetic_formatted():
    assert validate_snils(SYNTHETIC_SNILS) is True


def test_validate_snils_synthetic_plain():
    assert validate_snils(SYNTHETIC_SNILS_DIGITS) is True


def test_validate_snils_rejects_invalid_checksum():
    # Synthetic SNILS with wrong control digits (valid format, invalid checksum)
    assert validate_snils("087-654-303 99") is False
