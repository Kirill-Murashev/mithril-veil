"""Checksum and normalization helpers for Russian identifiers."""

import re

_DIGITS_ONLY = re.compile(r"\D")
_BIK_PATTERN = re.compile(r"\b04\d{7}\b")
_BANK_CONTROL_WEIGHTS = (7, 1, 3) * 7 + (7, 1)


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


def validate_ogrn(value: str) -> bool:
    """
    Validate 13-digit Russian OGRN control digit.

    Control digit = (first 12 digits as integer) % 11 % 10, compared to digit 13.
    """
    digits = normalize_digits(value)
    if len(digits) != 13 or not digits.isdigit():
        return False
    remainder = int(digits[:12]) % 11
    return (remainder % 10) == int(digits[12])


def validate_ogrnip(value: str) -> bool:
    """
    Validate 15-digit Russian OGRNIP control digit.

    Control digit = (first 14 digits as integer) % 13 % 10, compared to digit 15.
    """
    digits = normalize_digits(value)
    if len(digits) != 15 or not digits.isdigit():
        return False
    remainder = int(digits[:14]) % 13
    return (remainder % 10) == int(digits[14])


def _bank_control_sum(control_string: str) -> bool:
    if len(control_string) != 23 or not control_string.isdigit():
        return False
    total = sum(int(control_string[i]) * _BANK_CONTROL_WEIGHTS[i] for i in range(23))
    return total % 10 == 0


def validate_bank_account(account: str, bik: str) -> bool:
    """
    Validate a 20-digit settlement account when a 9-digit BIK is available.

    Uses BIK branch digits (positions 7-9) concatenated with the account number.
    """
    account_digits = normalize_digits(account)
    bik_digits = normalize_digits(bik)
    if len(account_digits) != 20 or len(bik_digits) != 9 or not bik_digits.isdigit():
        return False
    if not bik_digits.startswith("04"):
        return False
    return _bank_control_sum(bik_digits[6:9] + account_digits)


def validate_correspondent_account(account: str, bik: str) -> bool:
    """
    Validate a 20-digit correspondent account (301…) when a 9-digit BIK is available.

    Uses ``0`` + BIK department digits (positions 5-6) + account number.
    """
    account_digits = normalize_digits(account)
    bik_digits = normalize_digits(bik)
    if len(account_digits) != 20 or len(bik_digits) != 9 or not bik_digits.isdigit():
        return False
    if not account_digits.startswith("301"):
        return False
    return _bank_control_sum("0" + bik_digits[4:6] + account_digits)


def find_nearby_bik(text: str, position: int, window: int = 120) -> str | None:
    """Return the BIK match closest to ``position`` within a local text window."""
    start = max(0, position - window)
    end = min(len(text), position + window)
    snippet = text[start:end]
    best: tuple[int, str] | None = None
    for match in _BIK_PATTERN.finditer(snippet):
        distance = abs((start + match.start()) - position)
        candidate = (distance, match.group())
        if best is None or candidate[0] < best[0]:
            best = candidate
    return best[1] if best else None


def has_keyword_context(text: str, start: int, keywords: tuple[str, ...], window: int = 48) -> bool:
    snippet = text[max(0, start - window) : start].lower()
    return any(kw in snippet for kw in keywords)
