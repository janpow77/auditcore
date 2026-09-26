"""German labels of the ``identifiers_ui/1`` catalogue (kinds, reasons, detail fields)."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from ..result import IdentifierKind, Reason

#: Label, description and country hint per identifier kind.
KIND_LABELS: Mapping[IdentifierKind, tuple[str, str, bool]] = MappingProxyType(
    {
        IdentifierKind.IBAN: (
            "IBAN",
            "Internationale Kontonummer (ISO 13616): Register, Länge, BBAN-Aufbau, "
            "Prüfziffer MOD 97-10; nationale Kontoprüfziffern werden nicht geprüft.",
            False,
        ),
        IdentifierKind.BIC: (
            "BIC",
            "Geschäftskennung von Instituten (ISO 9362): 8 oder 11 Zeichen, Länderkennzeichen.",
            False,
        ),
        IdentifierKind.VAT_ID: (
            "USt-IdNr.",
            "Umsatzsteuer-Identifikationsnummer: Formate aller EU-Staaten, Prüfziffer "
            "für DE und AT; ohne Länderpräfix nur mit angegebenem Land.",
            True,
        ),
        IdentifierKind.TAX_ID: (
            "Steuer-ID",
            "Steuerliche Identifikationsnummer (§ 139b AO): 11 Ziffern, "
            "Ziffernverteilung, Prüfziffer.",
            False,
        ),
        IdentifierKind.TAX_NUMBER: (
            "Steuernummer",
            "Steuernummer: Landesformat (10/11 Ziffern) oder 13-stelliges "
            "Bundesformat; nur grobe Formatprüfung ohne Prüfziffer.",
            False,
        ),
        IdentifierKind.LEI: (
            "LEI",
            "Legal Entity Identifier (ISO 17442): 20 Zeichen, Prüfziffer MOD 97-10.",
            False,
        ),
        IdentifierKind.REGISTER_NUMBER: (
            "Handelsregisternummer",
            "Registerart (HRA, HRB, GnR, PR, VR) und Nummer; nur Format.",
            False,
        ),
    }
)

REASON_LABELS: Mapping[Reason, str] = MappingProxyType(
    {
        Reason.MISSING: "Wert fehlt",
        Reason.INVALID_TYPE: "Kein Text",
        Reason.INVALID_CHARACTERS: "Unzulässige Zeichen",
        Reason.INVALID_LENGTH: "Falsche Länge",
        Reason.INVALID_FORMAT: "Falsches Format",
        Reason.UNKNOWN_COUNTRY: "Unbekanntes Land",
        Reason.COUNTRY_MISMATCH: "Land passt nicht",
        Reason.INVALID_CHECKSUM: "Prüfziffer falsch",
    }
)

#: Labels of the keys in ``CheckResult.details``; unknown keys are shown as they are.
DETAIL_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "bban": "BBAN",
        "check_digits": "Prüfziffern",
        "registry": "Register",
        "expected_length": "Erwartete Länge",
        "length": "Länge",
        "institution": "Institut",
        "location": "Ort",
        "branch": "Filiale",
        "test_bic": "Test-BIC",
        "eu": "EU-Mitgliedstaat",
        "checksum": "Prüfziffer",
        "format": "Format",
        "land": "Land",
        "lou_prefix": "LOU-Präfix",
        "register": "Registerart",
        "number": "Nummer",
        "suffix": "Zusatz",
        "outcome": "Ergebnis (Legacy)",
        "severity": "Schwere (Legacy)",
    }
)

#: Labels of detail values that are codes rather than data.
VALUE_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "verified": "geprüft",
        "not_checked": "nicht geprüft",
        "land": "Landesformat",
        "federal": "Bundesformat",
    }
)
