"""Prüfziffer-gültige, aber fiktive Kennungen (Entscheidung E5 vom 24.09.2026).

IBAN (ISO 13616, Modulo 97), deutsche USt-IdNr. (ISO 7064 MOD 11,10) und
österreichische UID (ATU, Prüfziffer nach BMF-Verfahren) werden mit gültiger
Prüfziffer erzeugt, damit ein Modell die realistische Struktur lernt. Die
Bankleitzahlen stammen aus einer fiktiven Liste: deutsche Bankleitzahlen mit
führender 9 sind keinem Clearinggebiet zugeordnet (Clearinggebiete 1–8). Eine
Übereinstimmung mit realen Nummern ist dennoch möglich; jede gerenderte Seite
trägt deshalb sichtbar die Kennzeichnung ``SYNTHETISCH``.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

#: Fiktive Banken (Name, BLZ, BIC). BIC-Institutskennung ``SYNT`` = synthetisch.
FICTIONAL_BANKS_DE: tuple[tuple[str, str, str], ...] = (
    ("Synthetische Testbank Nord", "90010010", "SYNTDEH1XXX"),
    ("Synthetische Testbank Süd", "90020020", "SYNTDEM2XXX"),
    ("Beispiel-Sparkasse Musterstadt", "90030030", "SYNTDEF3XXX"),
    ("Musterbank Rhein-Main (fiktiv)", "90040040", "SYNTDEF4XXX"),
    ("Testgenossenschaftsbank (fiktiv)", "90050050", "SYNTDEB5XXX"),
)
FICTIONAL_BANKS_AT: tuple[tuple[str, str, str], ...] = (
    ("Synthetische Testbank Wien", "99010", "SYNTATW1XXX"),
    ("Beispielkasse Tirol (fiktiv)", "99020", "SYNTATI2XXX"),
    ("Musterbank Steiermark (fiktiv)", "99030", "SYNTATG3XXX"),
)
IBAN_LENGTHS = {"DE": 22, "AT": 20}


def _iban_numeric(text: str) -> int:
    return int("".join(str(int(char, 36)) for char in text))


def iban_check_digits(country: str, bban: str) -> str:
    """Prüfziffern nach ISO 13616: 98 − (BBAN + Land + 00) mod 97."""
    if not (len(country) == 2 and country.isalpha() and country.isupper()):
        raise ValueError("Ländercode aus zwei Großbuchstaben erwartet")
    if not bban.isalnum() or bban.upper() != bban:
        raise ValueError("BBAN aus Ziffern und Großbuchstaben erwartet")
    return f"{98 - _iban_numeric(bban + country + '00') % 97:02d}"


def iban_valid(iban: str) -> bool:
    """Länge (DE/AT bekannt, sonst 15–34) und Modulo-97-Prüfung."""
    text = iban.replace(" ", "").upper()
    if not 15 <= len(text) <= 34 or not text.isalnum() or not text[:2].isalpha():
        return False
    expected = IBAN_LENGTHS.get(text[:2])
    if expected is not None and len(text) != expected:
        return False
    if not text[2:4].isdigit():
        return False
    return _iban_numeric(text[4:] + text[:4]) % 97 == 1


def format_iban(iban: str, *, grouped: bool) -> str:
    """Vierergruppen (Papierform) oder am Stück."""
    text = iban.replace(" ", "")
    return " ".join(text[i : i + 4] for i in range(0, len(text), 4)) if grouped else text


def de_vat_check_digit(first_eight: str) -> int:
    """Prüfziffer der deutschen USt-IdNr. (ISO 7064, MOD 11,10)."""
    if len(first_eight) != 8 or not first_eight.isdigit() or first_eight[0] == "0":
        raise ValueError("Acht Ziffern ohne führende Null erwartet")
    product = 10
    for char in first_eight:
        total = (int(char) + product) % 10
        if total == 0:
            total = 10
        product = (2 * total) % 11
    check = 11 - product
    return 0 if check == 10 else check


def _digit_sum(value: int) -> int:
    return value // 10 + value % 10


def at_uid_check_digit(first_seven: str) -> int:
    """Prüfziffer der österreichischen UID (ATU + 8 Ziffern)."""
    if len(first_seven) != 7 or not first_seven.isdigit():
        raise ValueError("Sieben Ziffern erwartet")
    digits = [int(char) for char in first_seven]
    total = sum(d if i % 2 == 0 else _digit_sum(2 * d) for i, d in enumerate(digits))
    return (10 - (total + 4) % 10) % 10


def vat_id_valid(vat_id: str) -> bool:
    """Format und Prüfziffer für DE und AT; andere Länder sind hier nicht prüfbar."""
    text = vat_id.replace(" ", "").upper()
    if text.startswith("DE") and len(text) == 11 and text[2:].isdigit() and text[2] != "0":
        return de_vat_check_digit(text[2:10]) == int(text[10])
    if text.startswith("ATU") and len(text) == 11 and text[3:].isdigit():
        return at_uid_check_digit(text[3:10]) == int(text[10])
    return False


@dataclass(frozen=True)
class BankAccount:
    """Fiktive Bankverbindung mit gültiger IBAN-Prüfziffer."""

    iban: str
    bic: str
    bank_name: str


def fictional_bank_account(rng: Random, country: str) -> BankAccount:
    """IBAN aus fiktiver BLZ-Liste und zufälliger Kontonummer."""
    if country == "DE":
        name, blz, bic = rng.choice(FICTIONAL_BANKS_DE)
        bban = blz + f"{rng.randrange(10**10):010d}"
    elif country == "AT":
        name, blz, bic = rng.choice(FICTIONAL_BANKS_AT)
        bban = blz + f"{rng.randrange(10**11):011d}"
    else:
        raise ValueError("Nur DE und AT werden unterstützt")
    return BankAccount(country + iban_check_digits(country, bban) + bban, bic, name)


def fictional_vat_id(rng: Random, country: str) -> str:
    """USt-IdNr. (DE) bzw. UID (AT) mit gültiger Prüfziffer."""
    if country == "DE":
        body = str(rng.randint(1, 9)) + f"{rng.randrange(10**7):07d}"
        return f"DE{body}{de_vat_check_digit(body)}"
    if country == "AT":
        body = f"{rng.randrange(10**7):07d}"
        return f"ATU{body}{at_uid_check_digit(body)}"
    raise ValueError("Nur DE und AT werden unterstützt")


def fictional_tax_number(rng: Random, country: str) -> str:
    """Steuernummer ohne Prüfziffernanspruch (nur Layoutvielfalt)."""
    if country == "DE":
        return f"{rng.randint(10, 99)}/{rng.randint(100, 999)}/{rng.randint(10000, 99999)}"
    return f"{rng.randint(10, 99)} {rng.randint(100, 999)}/{rng.randint(1000, 9999)}"
