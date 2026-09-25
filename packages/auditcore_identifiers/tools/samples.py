"""Deterministic input samples for characterisation and cross-checks (seeded, no network).

Valid IBANs/LEIs/VAT IDs are computed here with independent arithmetic (not the
library) and then mutated: altered check digits, substituted and transposed
characters, wrong lengths, case, separators and non-ASCII look-alikes.
"""

from __future__ import annotations

import random
import re
import string

SEED = 20260925
#: SWIFT IBAN Registry: example IBAN per country (Release 101); see docs/test-vectors.md.
IBAN_EXAMPLES = (
    "DE89370400440532013000", "AT611904300234573201", "CH9300762011623852957",
    "FR1420041010050500013M02606", "GB29NWBK60161331926819", "NL91ABNA0417164300",
    "BE68539007547034", "IT60X0542811101000000123456", "ES9121000418450200051332",
    "PL61109010140000071219812874", "LU280019400644750000", "IE29AIBK93115212345678",
    "DK5000400440116243", "FI2112345600000785", "SE4550000000058398257466",
    "NO9386011117947", "PT50000201231234567890154", "GR1601101250000000012300695",
    "CZ6508000000192000145399", "SK3112000000198742637541", "HU42117730161111101800000000",
    "SI56263300012039086", "HR1210010051863000160", "EE382200221020145685",
    "LT121000011101001000", "LV80BANK0000435195001", "MT84MALT011000012345MTLCAST001S",
    "CY17002001280000001200527600", "BG80BNBG96611020345678", "RO49AAAA1B31007593840000",
    "LI21088100002324013AA", "IS140159260076545510730339", "MC5811222000010123456789030",
    "SM86U0322509800000000270100", "GI75NWBK000000007099453", "SA0380000000608010167519",
)
#: GLEIF LEI records, confirmed via api.gleif.org on 2026-09-25 (docs/test-vectors.md).
LEI_EXAMPLES = (
    "7LTWFZYICNSX8D621K86", "529900T8BM49AURSDO55",
    "5493001KJTIIGC8Y1R12", "529900W18LQJJN6SJ336",
)
BIC_EXAMPLES = (
    "DEUTDEFF", "DEUTDEFF500", "COBADEFFXXX", "NWBKGB2L", "BNPAFRPP", "MARKDEF1100",
    "SYNTDEH1XXX", "RZOOAT2L", "UBSWCHZH80A", "DEUTDE00", "1234DEFF", "DEUTXXFF",
    "DEUTDEF", "DEUTDEFF5", "DEUTDEFF50", "DEUTDEFF5000", "DEUT DE FF", "deutdeff",
    "DEUTDEFF-500", "DEÜTDEFF", "D3UTDEFF", "DEUTKXFF", "DEUTXKFF", "DEUTUKFF",
)
_NON_ASCII = ("٣", "²", "Ä", "ß", " ", " ", "Ｄ", "@", ";", "-", "/", ".", "\n")


def mod97_digits(body: str) -> str:
    """Check digits (ISO 7064 MOD 97-10) computed independently of the library."""
    number = int("".join(str(int(c, 36)) for c in body + "00"))
    return f"{98 - number % 97:02d}"


def _random_bban(rng: random.Random, structure: str) -> str:
    kinds = {"n": string.digits, "a": string.ascii_uppercase,
             "c": string.digits + string.ascii_uppercase}
    return "".join(
        "".join(rng.choice(kinds[kind]) for _ in range(int(length)))
        for length, kind in re.findall(r"(\d+)!([nac])", structure)
    )


def valid_ibans(rng: random.Random, structures: dict[str, str], per_country: int) -> list[str]:
    result = []
    for country, structure in sorted(structures.items()):
        for _ in range(per_country):
            bban = _random_bban(rng, structure)
            result.append(country + mod97_digits(bban + country) + bban)
    return result


def mutations(rng: random.Random, text: str, check: int = 2) -> list[str]:
    """Typical input errors and spellings of one valid identifier.

    ``check`` is the index of the two check digits (IBAN 2, LEI 18).
    """
    altered = f"{(int(text[check : check + 2]) + 1) % 100:02d}"
    position = rng.randrange(4, len(text))
    replaced = str((int(text[position], 36) + 1) % 10) if text[position].isdigit() else "7"
    swap = rng.randrange(4, len(text) - 1)
    return [
        text,
        text.lower(),
        " ".join(text[i : i + 4] for i in range(0, len(text), 4)),
        "-".join(text[i : i + 4] for i in range(0, len(text), 4)),
        f"  {text}  ",
        text + "\n",
        "IBAN " + text,
        text[:check] + altered + text[check + 2 :],
        text[:position] + replaced + text[position + 1 :],
        text[:swap] + text[swap + 1] + text[swap] + text[swap + 2 :],
        text[:-1],
        text + "0",
        text[:position] + rng.choice(_NON_ASCII) + text[position + 1 :],
    ]


def iban_samples(structures: dict[str, str]) -> list[str | None]:
    rng = random.Random(SEED)
    samples: list[str | None] = [None, "", " ", "DE", "DE89", "IBAN", "XX89370400440532013000"]
    for iban in list(IBAN_EXAMPLES) + valid_ibans(rng, structures, 2):
        samples.extend(mutations(rng, iban))
    for _ in range(150):
        length = rng.randrange(5, 36)
        samples.append("".join(rng.choice(string.ascii_uppercase[:6] + string.digits)
                               for _ in range(length)))
    samples.extend(["DE89370400440532013@00", "DE8937040044053201300;", "-E89370400440532013000"])
    return list(dict.fromkeys(samples))


def valid_leis(rng: random.Random, count: int) -> list[str]:
    alphabet = string.digits + string.ascii_uppercase
    result = []
    for _ in range(count):
        prefix = "".join(rng.choice(alphabet) for _ in range(18))
        result.append(prefix + mod97_digits(prefix))
    return result


def lei_samples() -> list[str | None]:
    rng = random.Random(SEED + 1)
    samples: list[str | None] = [None, "", "   ", "LEI", "1234567890123456789"]
    for lei in list(LEI_EXAMPLES) + valid_leis(rng, 40):
        samples.extend(mutations(rng, lei, check=18)[:12])
        samples.append(f"LEI: {lei}")
    return list(dict.fromkeys(samples))


def bic_samples() -> list[str | None]:
    rng = random.Random(SEED + 2)
    samples: list[str | None] = [None, "", " ", *BIC_EXAMPLES]
    for _ in range(80):
        length = rng.choice((7, 8, 9, 11, 12))
        samples.append("".join(rng.choice(string.ascii_uppercase + string.digits)
                               for _ in range(length)))
    return list(dict.fromkeys(samples))


def _mod_11_10(digits: str) -> int:
    product = 10
    for char in digits:
        total = (int(char) + product) % 10 or 10
        product = (2 * total) % 11
    return (11 - product) % 10


def _at_digit(seven: str) -> int:
    values = [int(c) if i % 2 == 0 else sum(divmod(2 * int(c), 10)) for i, c in enumerate(seven)]
    return (10 - (sum(values) + 4) % 10) % 10


def _digits(rng: random.Random, count: int) -> str:
    return "".join(rng.choice(string.digits) for _ in range(count))


def _vat_bodies(rng: random.Random) -> list[str]:
    bodies = []
    for _ in range(12):
        first = str(rng.randint(1, 9)) + _digits(rng, 7)
        bodies += ["DE" + first + str(_mod_11_10(first)),
                   "DE" + first + str((_mod_11_10(first) + 1) % 10)]
        seven = _digits(rng, 7)
        bodies += ["ATU" + seven + str(_at_digit(seven)),
                   "ATU" + seven + str((_at_digit(seven) + 3) % 10)]
    return bodies


_VAT_PREFIXES = (
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU", "IE",
    "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "XI", "GB", "GR",
    "US", "CH", "NO",
)
_VAT_SHAPES = (
    ("n7",), ("n8",), ("n9",), ("n10",), ("n11",), ("n12",), ("n13",), ("=U", "n8"),
    ("n8", "a1"), ("a1", "n7", "a1"), ("n7", "a2"), ("a2", "n9"), ("n9", "=B", "n2"),
    ("n10", "=01"), ("=GD", "n3"), ("=HA", "n3"), ("=0", "n9"), ("=1", "n8"),
    ("n1", "=+", "n5", "a1"), ("a1", "n8"),
)


def _shape(rng: random.Random, shape: tuple[str, ...]) -> str:
    """``n<k>`` = k random digits, ``a<k>`` = k random letters, ``=<text>`` = literal."""
    out = ""
    for token in shape:
        if token.startswith("="):
            out += token[1:]
        elif token.startswith("n"):
            out += _digits(rng, int(token[1:]))
        else:
            out += "".join(rng.choice(string.ascii_uppercase) for _ in range(int(token[1:])))
    return out


def vat_samples() -> list[tuple[str | None, str | None]]:
    """(value, country) pairs; country is the optional restriction of the check."""
    rng = random.Random(SEED + 3)
    values: list[str | None] = [None, "", " ", "DE", "de136695976", "DE 136 695 976",
                                "DE136.695.976", "DE-136-695-976", "DE136695976\n",
                                "DE١٣٦٦٩٥٩٧٦", "ＤＥ136695976", "DE13669597", "GB123456789",
                                "GBGD001", "GBHA599", "ATU13585627", "NL004495445B01"]
    values += _vat_bodies(rng)
    for prefix in _VAT_PREFIXES:
        for shape in _VAT_SHAPES:
            values.append(prefix + _shape(rng, shape))
    values = list(dict.fromkeys(values))
    pairs: list[tuple[str | None, str | None]] = [(value, None) for value in values]
    for value in values[::4]:
        pairs += [(value, "DE"), (value, "AT"), (value, "FR")]
    pairs += [("136695976", "DE"), ("U13585627", "AT"), ("DE136695976", "de")]
    return pairs


def tax_number_samples() -> list[str | None]:
    rng = random.Random(SEED + 4)
    values: list[str | None] = [None, "", " ", "12/345/67890", "123/456/78901", "123/4567/8901",
                                "12 345 67890", "1234567890", "12345678901", "2893081508152",
                                "181/815/08155", "9181081508155", "5133081508159", "123456789",
                                "12/345/6789", "12-345-67890", "12.345.67890", "1234567890123",
                                "12/345/67890\n", "١٢/٣٤٥/٦٧٨٩٠", "12/345/6789A", "12  345 67890"]
    for _ in range(60):
        digits = _digits(rng, rng.choice((9, 10, 11, 12, 13, 14)))
        values += [digits, f"{digits[:2]}/{digits[2:5]}/{digits[5:]}"]
    return list(dict.fromkeys(values))


def tax_id_samples() -> list[str | None]:
    rng = random.Random(SEED + 5)
    values: list[str | None] = [None, "", "36574261809", "36 574 261 809", "36574261890",
                                "36554266806", "06574261809", "3657426180", "365742618091"]
    while len(values) < 160:
        first = _digits(rng, 10)
        values += [first + str(_mod_11_10(first)), first + str((_mod_11_10(first) + 1) % 10)]
    for triple in ("1112345678", "1121345678", "1213145678"):
        values.append(triple + str(_mod_11_10(triple)))
    return list(dict.fromkeys(values))
