"""Modular synthetic company names: prefix, business area, name suffix, legal form.

The parts are separate lists and are combined per entity form. Every list is
generic on purpose: no known brands, no person-like trade names. Any
resemblance to existing companies is coincidental and not intended.

Two access paths, both deterministic:

* :func:`draw_company_name` draws one name with exactly one call of the caller's
  :class:`random.Random`.
* :func:`company_name_at` maps a position to a name through a seeded affine
  permutation of all combinations. Different positions below
  :func:`company_name_count` never yield the same name, so a data set that
  numbers its parties gets distinct names without shared state.

The legacy list ``TestDataGenerator.companies`` and the field type ``company``
stay unchanged; seeded rows of earlier versions are reproduced byte for byte.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

__all__ = [
    "ENTITY_FORMS",
    "company_name_at",
    "company_name_count",
    "draw_company_name",
]

#: Sector-style prefixes, generic words without brand reference.
PREFIXES = (
    "Agri", "Alpin", "Aqua", "Bio", "BioTech", "Data", "Eco", "Elektro", "Energie", "Feld",
    "Flex", "Forst", "Geo", "Hanse", "Infra", "Klima", "Logistik", "Medi", "Metall", "Mobil",
    "Nord", "Ost", "Rhein", "Solar", "Süd", "Tal", "Terra", "Vita", "West", "Wald",
)  # fmt: skip

#: Business areas of commercial enterprises.
COMMERCIAL_AREAS = (
    "Anlagenbau", "Bau", "Beratung", "Consulting", "Dienste", "Druck", "Entwicklung",
    "Fertigung", "Handel", "Holzbau", "Kunststofftechnik", "Labor", "Maschinenbau",
    "Montage", "Planung", "Produktion", "Projekte", "Service", "Software", "Systeme",
    "Technik", "Transport", "Vertrieb", "Werkstätten",
)  # fmt: skip

#: Business areas of non-profit bodies (associations, foundations).
CIVIC_AREAS = (
    "Bildung", "Bildungswerk", "Forschung", "Gesundheit", "Integration", "Jugendhilfe",
    "Kultur", "Naturschutz", "Qualifizierung", "Sozialwerk", "Sport", "Wissenstransfer",
)  # fmt: skip

#: Business areas of public-law bodies.
PUBLIC_AREAS = (
    "Abwasser", "Breitband", "Energieversorgung", "Gewerbepark", "Hafen", "Innovationszentrum",
    "Klinikum", "Nahverkehr", "Stadtentwicklung", "Technologiepark", "Wasserversorgung",
    "Wirtschaftsförderung",
)  # fmt: skip

#: Name suffixes of commercial enterprises; the empty entry means none.
COMMERCIAL_SUFFIXES = ("", "& Partner", "Gruppe", "Innovation", "Projektgesellschaft", "Werke")

#: Legal forms as patterns; ``{}`` is the name without legal form.
PRIVATE_FORMS = (
    "{} GmbH", "{} AG", "{} GmbH & Co. KG", "{} UG (haftungsbeschränkt)", "{} KG", "{} eG",
)  # fmt: skip
NONPROFIT_FORMS = ("{} e. V.", "Stiftung {}", "{} gGmbH")
PUBLIC_FORMS = ("{} AöR", "Zweckverband {}", "Eigenbetrieb {}")


@dataclass(frozen=True)
class _Scheme:
    """Name parts of one entity form."""

    areas: tuple[str, ...]
    suffixes: tuple[str, ...]
    forms: tuple[str, ...]

    @property
    def count(self) -> int:
        return len(PREFIXES) * len(self.areas) * len(self.suffixes) * len(self.forms)


_SCHEMES = {
    "private": _Scheme(COMMERCIAL_AREAS, COMMERCIAL_SUFFIXES, PRIVATE_FORMS),
    "nonprofit": _Scheme(CIVIC_AREAS, ("",), NONPROFIT_FORMS),
    "public": _Scheme(PUBLIC_AREAS, ("",), PUBLIC_FORMS),
}

#: Supported entity forms: commercial enterprise, non-profit body, public-law body.
ENTITY_FORMS = tuple(_SCHEMES)


def _scheme(entity_form: str) -> _Scheme:
    try:
        return _SCHEMES[entity_form]
    except KeyError:
        message = f"Unknown entity form {entity_form!r}; use one of {ENTITY_FORMS}"
        raise ValueError(message) from None


def company_name_count(entity_form: str | None = None) -> int:
    """Number of distinct names for one entity form, or for all forms together.

    Raises:
        ValueError: ``entity_form`` is not in :data:`ENTITY_FORMS`.
    """
    if entity_form is None:
        return sum(scheme.count for scheme in _SCHEMES.values())
    return _scheme(entity_form).count


def _compose(scheme: _Scheme, index: int) -> str:
    """Decode a combination index; the prefix varies fastest, the legal form slowest."""
    index, prefix = divmod(index, len(PREFIXES))
    index, area = divmod(index, len(scheme.areas))
    form, suffix = divmod(index, len(scheme.suffixes))
    words = [PREFIXES[prefix], scheme.areas[area], scheme.suffixes[suffix]]
    return scheme.forms[form].format(" ".join(word for word in words if word))


def draw_company_name(rng: random.Random, entity_form: str = "private") -> str:
    """Draw one name with a single ``rng.randrange`` call.

    Raises:
        ValueError: ``entity_form`` is not in :data:`ENTITY_FORMS`.
    """
    scheme = _scheme(entity_form)
    return _compose(scheme, rng.randrange(scheme.count))


def _permutation(seed: int, entity_form: str, count: int) -> tuple[int, int]:
    """Multiplier coprime to ``count`` and offset, both derived from ``seed``."""
    rng = random.Random(f"auditcore_dummygenerator.company:{entity_form}:{seed}")
    offset = rng.randrange(count)
    multiplier = rng.randrange(1, count)
    while math.gcd(multiplier, count) != 1:
        multiplier = multiplier % (count - 1) + 1
    return multiplier, offset


def company_name_at(position: int, *, seed: int, entity_form: str = "private") -> str:
    """Name number ``position`` of a seeded, collision-free sequence.

    Positions ``0 … company_name_count(entity_form) - 1`` give pairwise
    different names; the same ``seed``, form and position always give the same
    name, independently of other calls.

    Raises:
        ValueError: Unknown entity form or position outside the name space.
    """
    scheme = _scheme(entity_form)
    if not 0 <= position < scheme.count:
        raise ValueError(f"position must be between 0 and {scheme.count - 1}")
    multiplier, offset = _permutation(seed, entity_form, scheme.count)
    return _compose(scheme, (multiplier * position + offset) % scheme.count)
