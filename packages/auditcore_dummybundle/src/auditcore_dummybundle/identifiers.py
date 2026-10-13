"""Synthetic IBAN, BIC and VAT identifiers that fail every check by construction.

The correct check digit is computed with ``auditcore_identifiers`` and then
missed on purpose: an identifier built here with ``valid=False`` can neither
pass a checksum test nor denote an existing account or taxable person.
``valid=True`` is an explicit choice for testing check routines.

Additional precautions, which are conventions and not guarantees: the bank
code starts with ``0`` and the BIC carries ``0`` as last character of the
location code (the SWIFT convention for test addresses).
"""

from __future__ import annotations

from random import Random

from auditcore_identifiers import at_uid_check_digit, de_vat_check_digit, iban_check_digits

#: (bank code length, account number length) of the BBAN.
_BBAN = {"DE": (8, 10), "AT": (5, 11)}
#: Bank part of every BIC built here.
BIC_BANK = "SYNT"


def _digits(rng: Random, count: int) -> str:
    return "".join(str(rng.randrange(10)) for _ in range(count))


def _missed(correct: int, modulus: int) -> int:
    """A check value next to ``correct`` that is never congruent to it."""
    return correct + 1 if correct + 1 < modulus else correct - 1


def iban(rng: Random, country: str, *, valid: bool = False) -> str:
    """IBAN-shaped text for ``DE`` or ``AT`` with a missed (default) check number."""
    bank_length, account_length = _BBAN[country]
    bban = "0" + _digits(rng, bank_length - 1) + _digits(rng, account_length)
    check = int(iban_check_digits(country, bban))
    if not valid:
        check = _missed(check, 99)
    return f"{country}{check:02d}{bban}"


def vat_id(rng: Random, country: str, *, valid: bool = False) -> str:
    """VAT identifier for ``DE`` or ``AT`` with a missed (default) check digit."""
    if country == "AT":
        body = _digits(rng, 7)
        check = at_uid_check_digit(body)
        prefix = "ATU"
    else:
        body = str(rng.randrange(1, 10)) + _digits(rng, 7)
        check = de_vat_check_digit(body)
        prefix = "DE"
    if not valid:
        check = (check + 1) % 10
    return f"{prefix}{body}{check}"


def bic(country: str) -> str:
    """Fixed, recognisably synthetic BIC: bank part ``SYNT``, test location ``X0``."""
    return f"{BIC_BANK}{country}X0"
