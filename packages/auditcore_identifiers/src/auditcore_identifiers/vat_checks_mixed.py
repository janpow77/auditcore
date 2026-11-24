"""Check digits of VAT numbers whose number part has several variants.

These states use different number types under the same prefix (legal entities,
natural persons with a birth-date based number, foreigners). The function tries the
variant the structure indicates and returns a
:class:`~auditcore_identifiers.result.CheckDigit`, or ``None`` if the structure itself
is impossible (e.g. a birth number with a non-existing date). Cross-checked offline
against python-stdnum 2.2 like :mod:`auditcore_identifiers.vat_checks`.
"""

from __future__ import annotations

import datetime

from auditcore_identifiers.result import CheckDigit
from auditcore_identifiers.vat_checks import bg_legal, luhn_ok, weighted_sum

_IE_LETTERS = "WABCDEFGHIJKLMNOPQRSTUV"
_ES_DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_ES_CIF_LETTERS = "JABCDEFGHI"
_ES_CIF_ENTITIES = "ABCDEFGHJNPQRSUVW"


def _result(ok: bool) -> CheckDigit:
    return CheckDigit.VERIFIED if ok else CheckDigit.FAILED


def _date_exists(year: int, month: int, day: int) -> bool:
    try:
        datetime.date(year, month, day)
    except ValueError:
        return False
    return True


def _bg_egn(number: str) -> bool:
    """Bulgarian personal number (EGN): birth date (month +20/+40 for 18xx/20xx)."""
    year, month, day = 1900 + int(number[:2]), int(number[2:4]), int(number[4:6])
    if month > 40:
        year, month = year + 100, month - 40
    elif month > 20:
        year, month = year - 100, month - 20
    check = weighted_sum(number, (2, 4, 8, 5, 10, 9, 7, 3, 6)) % 11 % 10
    return _date_exists(year, month, day) and check == int(number[9])


def bg(number: str) -> CheckDigit:
    """Bulgaria: 9 digits legal entity; 10 digits EGN, foreigner number (LNCh) or
    other taxable persons – valid if one of the three procedures holds."""
    if len(number) == 9:
        return bg_legal(number)
    foreigner = weighted_sum(number, (21, 19, 17, 13, 11, 9, 7, 3, 1)) % 10 == int(number[9])
    other = (11 - weighted_sum(number, (4, 3, 2, 7, 6, 5, 4, 3, 2))) % 11 == int(number[9])
    return _result(_bg_egn(number) or foreigner or other)


def _birth_number(number: str) -> CheckDigit | None:
    """Czech/Slovak birth number (rodné číslo): 9 digits until 1953 without check digit,
    10 digits since 1954 with ``number mod 11`` (remainder 10 written as 0)."""
    year, month, day = 1900 + int(number[:2]), int(number[2:4]) % 50 % 20, int(number[4:6])
    if len(number) == 9:
        year -= 100 if year >= 1980 else 0
        if year > 1953:
            return None
    elif year < 1954:
        year += 100
    if not _date_exists(year, month, day):
        return None
    if len(number) == 9:
        return CheckDigit.NONE
    return _result(int(number[:9]) % 11 % 10 == int(number[9]))


def cz(number: str) -> CheckDigit | None:
    """Czechia (DIČ): 8 digits legal entity (weights 8 … 2, mod 11); 9 digits starting
    with 6 for individuals without birth number; otherwise the birth number."""
    if len(number) == 8:
        check = (11 - weighted_sum(number[:7], (8, 7, 6, 5, 4, 3, 2))) % 11
        return _result((check or 1) % 10 == int(number[7]))
    if len(number) == 9 and number[0] == "6":
        remainder = weighted_sum(number[1:8], (8, 7, 6, 5, 4, 3, 2)) % 11
        return _result((8 - (10 - remainder) % 11) % 10 == int(number[8]))
    return _birth_number(number)


def sk(number: str) -> CheckDigit | None:
    """Slovakia (IČ DPH): birth number, or legal entity (3rd digit 2, 3, 4, 7, 8, 9 and
    the whole number divisible by 11)."""
    if _birth_number(number) is CheckDigit.VERIFIED:
        return CheckDigit.VERIFIED
    return _result(number[2] in "234789" and int(number) % 11 == 0)


def lv(number: str) -> CheckDigit | None:
    """Latvia (PVN): legal entities (first digit > 3) weighted sum mod 11 = 3; natural
    persons personal code (``DDMMYY`` + century digit, or since 2017 starting ``32``)."""
    if number[0] > "3":
        return _result(weighted_sum(number, (9, 1, 4, 8, 3, 10, 2, 5, 7, 6, 1)) % 11 == 3)
    if not number.startswith("32"):
        day, month = int(number[:2]), int(number[2:4])
        year = 1800 + 100 * int(number[6]) + int(number[4:6])
        if not _date_exists(year, month, day):
            return None
    check = (1 + weighted_sum(number, (10, 5, 8, 4, 2, 1, 6, 3, 7, 9))) % 11 % 10
    return _result(check == int(number[10]))


def _es_cif(number: str) -> CheckDigit:
    digits = number[1:8]
    check = next(str(d) for d in range(10) if luhn_ok(digits + str(d)))
    return _result(number[8] in (check, _ES_CIF_LETTERS[int(check)]))


def es(number: str) -> CheckDigit | None:
    """Spain (NIF): DNI (8 digits + letter mod 23), NIE (X/Y/Z → 0/1/2), K/L/M (letter
    of the seven digits), legal entities (CIF: entity letter, Luhn digit or letter)."""
    first, last = number[0], number[8]
    if not number[1:8].isdigit():
        return None
    if first.isdigit():
        return _result(_ES_DNI_LETTERS[int(number[:8]) % 23] == last)
    if first in "XYZ":
        return _result(_ES_DNI_LETTERS[int(str("XYZ".index(first)) + number[1:8]) % 23] == last)
    if first in "KLM":
        return _result(_ES_DNI_LETTERS[int(number[1:8]) % 23] == last)
    if first in _ES_CIF_ENTITIES:
        return _es_cif(number)
    return None


def ie(number: str) -> CheckDigit:
    """Ireland: weights 8 … 2 over seven digits plus 9 × value of the second letter,
    mod 23; the old form (digit, letter, five digits, letter) is rearranged first."""
    if not number[1].isdigit():  # old form: 1A23456B → 0234561 + B
        number = "0" + number[2:7] + number[0] + number[7:]
    extra = _IE_LETTERS.index(number[8]) if len(number) == 9 else 0
    total = weighted_sum(number[:7], (8, 7, 6, 5, 4, 3, 2)) + 9 * extra
    return _result(_IE_LETTERS[total % 23] == number[7])


def fr(number: str) -> CheckDigit:
    """France: SIREN (last nine digits) with Luhn – except ``000`` (Monaco) – and the
    numeric key ``(12 + 3 × (SIREN mod 97)) mod 97``. Alphanumeric keys of older numbers
    follow no published procedure; they are reported as ``not_checked``."""
    siren = number[2:]
    if siren[:3] != "000" and not luhn_ok(siren):
        return CheckDigit.FAILED
    if not number[:2].isdigit():
        return CheckDigit.NOT_CHECKED
    return _result(int(number[:2]) == int(siren + "12") % 97)


def uk(number: str) -> CheckDigit:
    """GB/XI: HMRC has not published the check-digit procedure (``not_checked``);
    government departments (GD) and health authorities (HA) carry none."""
    return CheckDigit.NONE if number[:2] in ("GD", "HA") else CheckDigit.NOT_CHECKED
