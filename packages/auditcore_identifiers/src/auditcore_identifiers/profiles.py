"""Named profiles: ``strict`` (default) and legacy profiles reproducing each application.

A profile maps identifier kinds to check functions. Legacy profiles exist so that an
application can switch to the library without changing results, and then move to
``strict`` deliberately (see ``docs/profiles.md`` for the reasons of each profile).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from auditcore_identifiers import legacy_flowinvoice as fi
from auditcore_identifiers import legacy_pipeline as lp
from auditcore_identifiers.iban import check_bic, check_iban
from auditcore_identifiers.lei import check_lei
from auditcore_identifiers.result import CheckResult, IdentifierKind
from auditcore_identifiers.tax_de import check_register_number, check_tax_id, check_tax_number
from auditcore_identifiers.vat import check_vat_id

#: A check function: ``(value, country) -> CheckResult``; ``country`` is used for VAT IDs.
Checker = Callable[[object, str | None], CheckResult]
STRICT = "strict"

_FLOWINVOICE_ORIGIN = ("janpow77/flowinvoice@fb2d18568d2eaf64574d131ceae51a936b9aac02:"
                       "backend/app/services/validators.py")
_PORTAL_ORIGIN = ("janpow77/audit-portal@d8eefa426826bdecb67036774f3128ae05e7d0d0:"
                  "backend/app/services/validators.py")
_PIPELINE_ORIGIN = ("janpow77/flowinvoice@fb2d18568d2eaf64574d131ceae51a936b9aac02:"
                    "backend/app/pipeline/stages/validation.py")
_PORTAL_PIPELINE_ORIGIN = ("janpow77/audit-portal@d8eefa426826bdecb67036774f3128ae05e7d0d0:"
                           "backend/app/pipeline/stages/validation.py")


class UnknownProfileError(ValueError):
    """The profile name is not registered (a programming error, not a bad value)."""


class UnsupportedKindError(ValueError):
    """The profile has no check for this identifier kind."""


@dataclass(frozen=True)
class Profile:
    """A named set of check functions with its origin and reason for existence."""

    name: str
    title: str
    rationale: str
    origin: str
    legacy: bool
    checkers: Mapping[IdentifierKind, Checker]

    def check(self, kind: IdentifierKind | str, value: object,
              country: str | None = None) -> CheckResult:
        """Run the check of ``kind``; raises :class:`UnsupportedKindError` if absent."""
        key = IdentifierKind(kind)
        checker = self.checkers.get(key)
        if checker is None:
            raise UnsupportedKindError(f"Profil {self.name} prüft keine {key.value}")
        return checker(value, country)


def _plain(function: Callable[[object], CheckResult]) -> Checker:
    return lambda value, _country: function(value)


def _flowinvoice_vat(profile: str) -> Checker:
    return lambda value, country: fi.validate_eu_vat_id(value, country, profile=profile)


def _flowinvoice_checkers(profile: str) -> Mapping[IdentifierKind, Checker]:
    return MappingProxyType({
        IdentifierKind.IBAN: _plain(lambda v: fi.validate_iban(v, profile=profile)),
        IdentifierKind.BIC: _plain(lambda v: fi.validate_bic(v, profile=profile)),
        IdentifierKind.VAT_ID: _flowinvoice_vat(profile),
        IdentifierKind.TAX_NUMBER: _plain(lambda v: fi.validate_german_tax_id(v, profile=profile)),
    })


def _pipeline_checkers(profile: str) -> Mapping[IdentifierKind, Checker]:
    return MappingProxyType({
        IdentifierKind.IBAN: _plain(lambda v: lp.pipeline_validate_iban(v, profile=profile)),
        IdentifierKind.VAT_ID: _plain(lambda v: lp.pipeline_vat_id_format(v, profile=profile)),
    })


_STRICT_CHECKERS: Mapping[IdentifierKind, Checker] = MappingProxyType({
    IdentifierKind.IBAN: _plain(check_iban),
    IdentifierKind.BIC: _plain(check_bic),
    IdentifierKind.VAT_ID: lambda value, country: check_vat_id(value, country),
    IdentifierKind.TAX_ID: _plain(check_tax_id),
    IdentifierKind.TAX_NUMBER: _plain(check_tax_number),
    IdentifierKind.LEI: _plain(check_lei),
    IdentifierKind.REGISTER_NUMBER: _plain(check_register_number),
})

_PROFILES: tuple[Profile, ...] = (
    Profile(STRICT, "Streng (Standard)",
            "Fachlich vollständige Prüfung: Register-Längen und BBAN-Aufbau, Prüfziffern "
            "(IBAN, LEI, USt-IdNr. DE/AT, Steuer-ID), Formate aller EU-Staaten.",
            "auditcore_identifiers", False, _STRICT_CHECKERS),
    Profile("flowinvoice.legacy", "flowinvoice validators.py",
            "Ergebnisgleiche Umstellung von flowinvoice: IBAN ohne Modulo-97-Prüfung, "
            "USt-IdNr. nur nach Muster, deutsche Meldungen des Originals.",
            _FLOWINVOICE_ORIGIN, True, _flowinvoice_checkers("flowinvoice.legacy")),
    Profile("audit_portal.legacy", "audit-portal validators.py",
            "Fork von flowinvoice; validators.py ist byte-identisch (Blob d3c09fbd), "
            "Verhalten wie flowinvoice.legacy.",
            _PORTAL_ORIGIN, True, _flowinvoice_checkers("audit_portal.legacy")),
    Profile(lp.PIPELINE, "Dokumenten-Pipeline (IbanChecksumRule/VatIdFormatRule)",
            "Ergebnisgleich zur Validierungsstufe der Pipeline (flowinvoice, weitergeführt in "
            "auditcore_documents): Modulo 97, Längen für neun Länder, englische Meldungen.",
            _PIPELINE_ORIGIN, True, _pipeline_checkers(lp.PIPELINE)),
    Profile("audit_portal.pipeline.legacy", "audit-portal Dokumenten-Pipeline",
            "Gleiche Regeln wie flowinvoice.pipeline.legacy (Regelteil der Datei unverändert).",
            _PORTAL_PIPELINE_ORIGIN, True, _pipeline_checkers("audit_portal.pipeline.legacy")),
    Profile(lp.DONUT, "auditcore_documents Donut-Prüfung",
            "Ergebnisgleich zu auditcore_documents (Donut-Stufe): kompaktieren, IBAN wie "
            "Pipeline, USt-IdNr. acht Länder mit Prüfziffer DE/AT.",
            "janpow77/auditcore:packages/auditcore_documents", True,
            MappingProxyType({IdentifierKind.IBAN: _plain(lp.donut_validate_iban),
                              IdentifierKind.VAT_ID: _plain(lp.donut_vat_id_check)})),
    Profile(lp.INVOICESYNTH, "auditcore_invoicesynth identifiers",
            "Ergebnisgleich zu den Prüfhilfen des Synthesegenerators (nur DE/AT).",
            "janpow77/auditcore:packages/auditcore_invoicesynth", True,
            MappingProxyType({IdentifierKind.IBAN: _plain(lp.invoicesynth_iban_valid),
                              IdentifierKind.VAT_ID: _plain(lp.invoicesynth_vat_id_valid)})),
    Profile(lp.FLOWWORKSHOP, "flowworkshop entity_resolution",
            "LEI nur nach Format ohne Prüfziffern, wie is_valid_lei (in "
            "auditcore_entity_matching als Legacy weitergeführt).",
            "janpow77/flowworkshop@a05bb2143bd96d5e981f9462f05b965e1658be36:"
            "auditworkshop/backend/services/entity_resolution.py", True,
            MappingProxyType({IdentifierKind.LEI: _plain(lp.flowworkshop_is_valid_lei)})),
)
PROFILES: Mapping[str, Profile] = MappingProxyType({p.name: p for p in _PROFILES})


def get_profile(name: str | Profile = STRICT) -> Profile:
    """Profile by name; raises :class:`UnknownProfileError` for unknown names."""
    if isinstance(name, Profile):
        return name
    profile = PROFILES.get(name)
    if profile is None:
        raise UnknownProfileError(f"Unbekanntes Profil: {name}")
    return profile


def profile_names() -> tuple[str, ...]:
    """All registered profile names, ``strict`` first."""
    return tuple(PROFILES)
