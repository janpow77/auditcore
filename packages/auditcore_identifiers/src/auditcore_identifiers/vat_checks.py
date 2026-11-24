"""Check digits of VAT identification numbers with a plain weighted-sum procedure.

Each function receives the number part (without the prefix) that already matches the
format of :data:`auditcore_identifiers.vat.EU_VAT_FORMATS` and returns a
:class:`~auditcore_identifiers.result.CheckDigit`. The procedures are those of the
national tax administrations (facts, not code); every function was cross-checked
offline against python-stdnum 2.2 (``tools/crosscheck_stdnum.py``) and, where a number
was available, against a VIES confirmation (``docs/test-vectors.md``).
"""

from __future__ import annotations

from collections.abc import Sequence

from auditcore_identifiers.checksums import mod97, mod_11_10_check_digit
from auditcore_identifiers.result import CheckDigit


def _result(ok: bool) -> CheckDigit:
    return CheckDigit.VERIFIED if ok else CheckDigit.FAILED


def weighted_sum(number: str, weights: Sequence[int]) -> int:
    """Sum of digit times weight (digits and weights paired from the left)."""
    return sum(weight * int(digit) for weight, digit in zip(weights, number, strict=False))


def luhn_ok(number: str) -> bool:
    """Luhn (ISO/IEC 7812-1 annex B) over all digits including the check digit."""
    total = 0
    for position, char in enumerate(reversed(number)):
        digit = int(char)
        if position % 2:
            digit = digit * 2 - 9 if digit > 4 else digit * 2
        total += digit
    return total % 10 == 0


def be(number: str) -> CheckDigit:
    """Belgium: last two digits = 97 − (first eight mod 97)."""
    return _result((int(number[:-2]) + int(number[-2:])) % 97 == 0)


def bg_legal(number: str) -> CheckDigit:
    """Bulgaria, 9 digits (legal entities, BULSTAT): weights 1–8, fallback 3–10, mod 11."""
    check = weighted_sum(number[:8], range(1, 9)) % 11
    if check == 10:
        check = weighted_sum(number[:8], range(3, 11)) % 11
    return _result(check % 10 == int(number[8]))


def cy(number: str) -> CheckDigit:
    """Cyprus: check letter from the eight digits (odd positions translated), mod 26."""
    odd = (1, 0, 5, 7, 9, 13, 15, 17, 19, 21)
    total = sum(odd[int(d)] for d in number[0:8:2]) + sum(int(d) for d in number[1:8:2])
    return _result(chr(ord("A") + total % 26) == number[8])


def dk(number: str) -> CheckDigit:
    """Denmark (CVR): weights 2, 7, 6, 5, 4, 3, 2, 1; sum divisible by 11."""
    return _result(weighted_sum(number, (2, 7, 6, 5, 4, 3, 2, 1)) % 11 == 0)


def ee(number: str) -> CheckDigit:
    """Estonia (KMKR): weights 3, 7, 1 repeating; sum divisible by 10."""
    return _result(weighted_sum(number, (3, 7, 1, 3, 7, 1, 3, 7, 1)) % 10 == 0)


def el(number: str) -> CheckDigit:
    """Greece: weights 2^8 … 2^1 over the first eight digits, mod 11, mod 10."""
    total = weighted_sum(number[:8], (256, 128, 64, 32, 16, 8, 4, 2))
    return _result(total % 11 % 10 == int(number[8]))


def fi(number: str) -> CheckDigit:
    """Finland (Y-tunnus): weights 7, 9, 10, 5, 8, 4, 2, 1; sum divisible by 11."""
    return _result(weighted_sum(number, (7, 9, 10, 5, 8, 4, 2, 1)) % 11 == 0)


def hr(number: str) -> CheckDigit:
    """Croatia (OIB): ISO 7064 MOD 11,10."""
    return _result(mod_11_10_check_digit(number[:10]) == int(number[10]))


def hu(number: str) -> CheckDigit:
    """Hungary: weights 9, 7, 3, 1 repeating; sum divisible by 10."""
    return _result(weighted_sum(number, (9, 7, 3, 1, 9, 7, 3, 1)) % 10 == 0)


def it(number: str) -> CheckDigit:
    """Italy (partita IVA): Luhn over all eleven digits."""
    return _result(luhn_ok(number))


def lt(number: str) -> CheckDigit:
    """Lithuania: weights 1–9 cyclic, mod 11; if 10, weights shifted by two."""
    body = number[:-1]
    check = sum((1 + i % 9) * int(d) for i, d in enumerate(body)) % 11
    if check == 10:
        check = sum((1 + (i + 2) % 9) * int(d) for i, d in enumerate(body)) % 11
    return _result(check % 10 == int(number[-1]))


def lu(number: str) -> CheckDigit:
    """Luxembourg: last two digits = first six mod 89."""
    return _result(int(number[:6]) % 89 == int(number[6:]))


def mt(number: str) -> CheckDigit:
    """Malta: weights 3, 4, 6, 7, 8, 9, 10, 1; sum divisible by 37."""
    return _result(weighted_sum(number, (3, 4, 6, 7, 8, 9, 10, 1)) % 37 == 0)


def nl(number: str) -> CheckDigit:
    """Netherlands: RSIN/BSN eleven test (weights 9 … 2, −1) or, for the btw-id of sole
    traders issued since 2020, ISO 7064 MOD 97-10 over ``NL`` + number."""
    eleven = weighted_sum(number[:9], (9, 8, 7, 6, 5, 4, 3, 2, -1)) % 11 == 0
    return _result(eleven or mod97("NL" + number) == 1)


def pl(number: str) -> CheckDigit:
    """Poland (NIP): weights 6, 5, 7, 2, 3, 4, 5, 6, 7; check = sum mod 11 (10 never issued)."""
    return _result(weighted_sum(number, (6, 5, 7, 2, 3, 4, 5, 6, 7, -1)) % 11 == 0)


def pt(number: str) -> CheckDigit:
    """Portugal (NIF): weights 9 … 2, check = (11 − sum mod 11) mod 11 mod 10."""
    total = weighted_sum(number[:8], (9, 8, 7, 6, 5, 4, 3, 2))
    return _result((11 - total) % 11 % 10 == int(number[8]))


def ro(number: str) -> CheckDigit:
    """Romania (CUI/CIF): weights 7, 5, 3, 2, 1, 7, 5, 3, 2 right-aligned, ×10 mod 11 mod 10."""
    body = number[:-1].zfill(9)
    check = 10 * weighted_sum(body, (7, 5, 3, 2, 1, 7, 5, 3, 2)) % 11 % 10
    return _result(check == int(number[-1]))


def se(number: str) -> CheckDigit:
    """Sweden: Luhn over the ten-digit organisation or personal number (then ``01``)."""
    return _result(luhn_ok(number[:10]))


def si(number: str) -> CheckDigit:
    """Slovenia: weights 8 … 2, check = 11 − sum mod 11, 10 → 0, 11 not issued."""
    check = 11 - weighted_sum(number[:7], (8, 7, 6, 5, 4, 3, 2)) % 11
    return _result(check != 11 and check % 10 == int(number[7]))
