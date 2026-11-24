"""German labels of the ``identifiers_ui/1`` catalogue (kinds, reasons, detail fields)."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from ..result import CheckDigit, IdentifierKind, Reason, Verdict

#: Label, description and country hint per identifier kind.
KIND_LABELS: Mapping[IdentifierKind, tuple[str, str, bool]] = MappingProxyType(
    {
        IdentifierKind.IBAN: (
            "IBAN",
            "Internationale Kontonummer (ISO 13616): Register, Länge, BBAN-Aufbau, "
            "Prüfziffer MOD 97-10 (nur 02–98 möglich); nationale Kontoprüfziffern werden "
            "nicht geprüft.",
            False,
        ),
        IdentifierKind.BIC: (
            "BIC",
            "Geschäftskennung von Instituten (ISO 9362): 8 oder 11 Zeichen, Länderkennzeichen; "
            "keine Prüfziffer, Eintrag im SWIFT-Verzeichnis nicht geprüft.",
            False,
        ),
        IdentifierKind.VAT_ID: (
            "USt-IdNr.",
            "Umsatzsteuer-Identifikationsnummer: Formate und Prüfziffern aller "
            "EU-Staaten; für GB/XI und ältere französische Nummern mit Buchstabenschlüssel "
            "ist die Prüfziffer nicht prüfbar; ohne Länderpräfix nur mit angegebenem Land.",
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
            "Legal Entity Identifier (ISO 17442): 20 Zeichen, Prüfziffer MOD 97-10 "
            "(nur 02–98 möglich).",
            False,
        ),
        IdentifierKind.REGISTER_NUMBER: (
            "Handelsregisternummer",
            "Registerart (HRA, HRB, GnR, GsR, PR, VR) und Nummer ab 1; ein angegebenes "
            "Registergericht wird abgetrennt und ausgewiesen; nur Format, keine Prüfziffer.",
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
        "court": "Registergericht",
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

#: Labels of :class:`~auditcore_identifiers.result.CheckDigit` (``check_digit``).
CHECK_DIGIT_LABELS: Mapping[CheckDigit, str] = MappingProxyType(
    {
        CheckDigit.VERIFIED: "geprüft, richtig",
        CheckDigit.FAILED: "falsch",
        CheckDigit.NOT_CHECKED: "nicht prüfbar",
        CheckDigit.NONE: "keine Prüfziffer",
    }
)

#: Labels of :class:`~auditcore_identifiers.result.Verdict` (``verdict``).
VERDICT_LABELS: Mapping[Verdict, str] = MappingProxyType(
    {
        Verdict.VALID: "formal gültig",
        Verdict.FORMAT_VALID: "Format gültig, Prüfziffer nicht geprüft",
        Verdict.INVALID: "ungültig",
        Verdict.MISSING: "Wert fehlt",
    }
)
