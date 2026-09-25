"""Reference tables: IBAN registry structures and ISO 3166-1 country codes.

Sources (facts, not code):

* IBAN BBAN structures: SWIFT IBAN Registry, Release 101, as transcribed in
  ``stdnum/iban.dat`` of python-stdnum 2.2 ("generated from iban-registry-v101.txt").
  Notation ``<length>!<type>`` with ``n`` = digits, ``a`` = capital letters,
  ``c`` = alphanumeric. The IBAN length is 4 + the BBAN length.
* ISO 3166-1 alpha-2: Debian ``iso-codes`` 4.16.0 (249 codes) plus ``XK``
  (Kosovo, user-assigned code used by the IBAN registry and SWIFT).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType

IBAN_REGISTRY_RELEASE = "SWIFT IBAN Registry Release 101"

#: BBAN structure per IBAN country (89 countries).
IBAN_BBAN_STRUCTURE: Mapping[str, str] = MappingProxyType({
    "AD": "4!n4!n12!c", "AE": "3!n16!n", "AL": "8!n16!c", "AT": "5!n11!n", "AZ": "4!a20!c",
    "BA": "3!n3!n8!n2!n", "BE": "3!n7!n2!n", "BG": "4!a4!n2!n8!c", "BH": "4!a14!c",
    "BI": "5!n5!n11!n2!n", "BR": "8!n5!n10!n1!a1!c", "BY": "4!c4!n16!c", "CH": "5!n12!c",
    "CR": "4!n14!n", "CY": "3!n5!n16!c", "CZ": "4!n16!n", "DE": "8!n10!n", "DJ": "5!n5!n11!n2!n",
    "DK": "4!n9!n1!n", "DO": "4!c20!n", "EE": "2!n14!n", "EG": "4!n4!n17!n",
    "ES": "4!n4!n1!n1!n10!n", "FI": "3!n11!n", "FK": "2!a12!n", "FO": "4!n9!n1!n",
    "FR": "5!n5!n11!c2!n", "GB": "4!a6!n8!n", "GE": "2!a16!n", "GI": "4!a15!c", "GL": "4!n9!n1!n",
    "GR": "3!n4!n16!c", "GT": "4!c20!c", "HN": "4!a20!n", "HR": "7!n10!n",
    "HU": "3!n4!n1!n15!n1!n", "IE": "4!a6!n8!n", "IL": "3!n3!n13!n", "IQ": "4!a3!n12!n",
    "IS": "4!n2!n6!n10!n", "IT": "1!a5!n5!n12!c", "JO": "4!a4!n18!c", "KW": "4!a22!c",
    "KZ": "3!n13!c", "LB": "4!n20!c", "LC": "4!a24!c", "LI": "5!n12!c", "LT": "5!n11!n",
    "LU": "3!n13!c", "LV": "4!a13!c", "LY": "3!n3!n15!n", "MC": "5!n5!n11!c2!n", "MD": "2!c18!c",
    "ME": "3!n13!n2!n", "MK": "3!n10!c2!n", "MN": "4!n12!n", "MR": "5!n5!n11!n2!n",
    "MT": "4!a5!n18!c", "MU": "4!a2!n2!n12!n3!n3!a", "NI": "4!a20!n", "NL": "4!a10!n",
    "NO": "4!n6!n1!n", "OM": "3!n16!c", "PK": "4!a16!c", "PL": "8!n16!n", "PS": "4!a21!c",
    "PT": "4!n4!n11!n2!n", "QA": "4!a21!c", "RO": "4!a16!c", "RS": "3!n13!n2!n",
    "RU": "9!n5!n15!c", "SA": "2!n18!c", "SC": "4!a2!n2!n16!n3!a", "SD": "2!n12!n",
    "SE": "3!n16!n1!n", "SI": "5!n8!n2!n", "SK": "4!n6!n10!n", "SM": "1!a5!n5!n12!c",
    "SO": "4!n3!n12!n", "ST": "4!n4!n11!n2!n", "SV": "4!a20!n", "TL": "3!n14!n2!n",
    "TN": "2!n3!n13!n2!n", "TR": "5!n1!n16!c", "UA": "6!n19!c", "VA": "3!n15!n", "VG": "4!a16!n",
    "XK": "4!n10!n2!n", "YE": "4!a4!n18!c",
})

_ISO_3166_ALPHA2 = """
AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO
BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ
DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP
GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG
KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML
MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE
PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL
SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM
US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW
"""
#: ISO 3166-1 alpha-2 codes plus XK.
COUNTRY_CODES: frozenset[str] = frozenset(_ISO_3166_ALPHA2.split()) | {"XK"}

_TYPES = {"n": "[0-9]", "a": "[A-Z]", "c": "[A-Z0-9]"}
_PART = re.compile(r"(\d+)!([nac])")


def _bban_pattern(structure: str) -> re.Pattern[str]:
    parts = (f"{_TYPES[kind]}{{{length}}}" for length, kind in _PART.findall(structure))
    return re.compile("".join(parts), re.ASCII)


def _bban_length(structure: str) -> int:
    return sum(int(length) for length, _ in _PART.findall(structure))


#: Compiled BBAN pattern per IBAN country (use with ``fullmatch``).
BBAN_PATTERNS: Mapping[str, re.Pattern[str]] = MappingProxyType(
    {country: _bban_pattern(s) for country, s in IBAN_BBAN_STRUCTURE.items()}
)
#: Total IBAN length per country (country code + check digits + BBAN).
IBAN_LENGTHS: Mapping[str, int] = MappingProxyType(
    {country: 4 + _bban_length(s) for country, s in IBAN_BBAN_STRUCTURE.items()}
)
