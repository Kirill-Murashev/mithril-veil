"""Checksum and normalization helpers for Russian identifiers."""

import re

_DIGITS_ONLY = re.compile(r"\D")


def normalize_digits(value: str) -> str:
    return _DIGITS_ONLY.sub("", value)


def validate_inn(value: str) -> bool:
    """
    Validate 10-digit (legal entity) or 12-digit (individual) Russian INN checksum.
    """
    digits = normalize_digits(value)
    if not digits.isdigit():
        return False
    if len(digits) == 10:
        coeffs = (2, 4, 10, 3, 5, 9, 4, 6, 8)
        total = sum(int(digits[i]) * coeffs[i] for i in range(9))
        check = total % 11 % 10
        return check == int(digits[9])
    if len(digits) == 12:
        coeffs_11 = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
        total_11 = sum(int(digits[i]) * coeffs_11[i] for i in range(10))
        check_11 = total_11 % 11 % 10
        if check_11 != int(digits[10]):
            return False
        coeffs_12 = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
        total_12 = sum(int(digits[i]) * coeffs_12[i] for i in range(11))
        check_12 = total_12 % 11 % 10
        return check_12 == int(digits[11])
    return False


def validate_snils(value: str) -> bool:
    """Validate Russian SNILS control number (11 digits, formatted or plain)."""
    digits = normalize_digits(value)
    if len(digits) != 11 or not digits.isdigit():
        return False

    number_part = digits[:9]
    control = int(digits[9:11])

    # Numbers below this threshold use a simplified legacy rule
    if int(number_part) < 1001998:
        return control < 100

    total = sum(int(number_part[i]) * (9 - i) for i in range(9))
    if total < 100:
        expected = total
    elif total in (100, 101):
        expected = 0
    else:
        expected = total % 101
        if expected == 100:
            expected = 0

    return control == expected


def has_keyword_context(text: str, start: int, keywords: tuple[str, ...], window: int = 48) -> bool:
    snippet = text[max(0, start - window) : start].lower()
    return any(kw in snippet for kw in keywords)
