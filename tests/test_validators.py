from app.detectors.validators import (
    find_nearby_bik,
    normalize_digits,
    validate_bank_account,
    validate_correspondent_account,
    validate_inn,
    validate_ogrn,
    validate_ogrnip,
    validate_snils,
)
from tests.conftest import (
    INVALID_BANK_ACCOUNT,
    INVALID_CORRESPONDENT_ACCOUNT,
    INVALID_INN_12,
    INVALID_OGRN,
    INVALID_OGRNIP,
    SYNTHETIC_BANK_ACCOUNT,
    SYNTHETIC_BIK,
    SYNTHETIC_CORRESPONDENT_ACCOUNT,
    SYNTHETIC_INN_10,
    SYNTHETIC_INN_12,
    SYNTHETIC_OGRN,
    SYNTHETIC_OGRNIP,
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


def test_validate_ogrn_synthetic_valid():
    assert validate_ogrn(SYNTHETIC_OGRN) is True


def test_validate_ogrn_rejects_invalid_checksum():
    assert validate_ogrn(INVALID_OGRN) is False


def test_validate_ogrnip_synthetic_valid():
    assert validate_ogrnip(SYNTHETIC_OGRNIP) is True


def test_validate_ogrnip_rejects_invalid_checksum():
    assert validate_ogrnip(INVALID_OGRNIP) is False


def test_validate_bank_account_with_bik_synthetic():
    assert validate_bank_account(SYNTHETIC_BANK_ACCOUNT, SYNTHETIC_BIK) is True


def test_validate_bank_account_rejects_invalid_checksum():
    assert validate_bank_account(INVALID_BANK_ACCOUNT, SYNTHETIC_BIK) is False


def test_validate_bank_account_requires_bik_shape():
    assert validate_bank_account(SYNTHETIC_BANK_ACCOUNT, "123456789") is False


def test_validate_correspondent_account_with_bik_synthetic():
    assert validate_correspondent_account(SYNTHETIC_CORRESPONDENT_ACCOUNT, SYNTHETIC_BIK) is True


def test_validate_correspondent_account_rejects_invalid_checksum():
    assert validate_correspondent_account(INVALID_CORRESPONDENT_ACCOUNT, SYNTHETIC_BIK) is False


def test_find_nearby_bik_returns_closest_match():
    text = f"БИК {SYNTHETIC_BIK} и р/с {SYNTHETIC_BANK_ACCOUNT}."
    account_pos = text.index(SYNTHETIC_BANK_ACCOUNT)
    assert find_nearby_bik(text, account_pos) == SYNTHETIC_BIK
