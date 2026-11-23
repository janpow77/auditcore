"""Who applies the threshold for central government authorities in Germany, by date.

Art. 4 Buchst. b RL 2014/24/EU sets a lower threshold for supply and service
contracts of central government authorities. § 106 Abs. 2 Nr. 1 GWB names the
German authorities that apply it; the wording changed on 01.07.2026. The
version is chosen by the reference date of the case (date of the measure or of
the contract notice), never by today's date. Before 18.04.2016 a different
provision applied, which is not recorded here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .precheck_profile import ThresholdUnavailable

PROVISION = "§ 106 Abs. 2 Nr. 1 GWB"
_FIRST = date(2016, 4, 18)


@dataclass(frozen=True)
class CentralGovernmentRule:
    """One version of § 106 Abs. 2 Nr. 1 GWB with its verbatim wording."""

    version: str
    valid_from: date
    valid_to: date | None
    wording: str
    applies_to_de: str
    applies_to_en: str
    reference: str

    def to_dict(self) -> dict[str, str | None]:
        """JSON view (dates ISO 8601; ``valid_to`` ``None`` = in force until amended)."""
        return {
            "provision": PROVISION,
            "version": self.version,
            "valid_from": self.valid_from.isoformat(),
            "valid_to": None if self.valid_to is None else self.valid_to.isoformat(),
            "wording": self.wording,
            "applies_to_de": self.applies_to_de,
            "applies_to_en": self.applies_to_en,
            "reference": self.reference,
        }


_HEAD = (
    "für öffentliche Aufträge und Wettbewerbe, die von öffentlichen Auftraggebern vergeben "
    "werden, aus Artikel 4 der Richtlinie 2014/24/EU in der jeweils geltenden Fassung; der "
    "sich hieraus für zentrale Regierungsbehörden ergebende Schwellenwert ist "
)

#: Versions in force, oldest first (wording: gesetze-im-internet.de and buzer.de, 23.11.2026).
RULES: tuple[CentralGovernmentRule, ...] = (
    CentralGovernmentRule(
        version="Fassung vom 18.04.2016 bis 30.06.2026",
        valid_from=_FIRST,
        valid_to=date(2026, 6, 30),
        wording=_HEAD + "von allen obersten Bundesbehörden sowie allen oberen Bundesbehörden und "
        "vergleichbaren Bundeseinrichtungen anzuwenden",
        applies_to_de=(
            "alle obersten Bundesbehörden sowie alle oberen Bundesbehörden und vergleichbaren "
            "Bundeseinrichtungen"
        ),
        applies_to_en="all supreme and higher federal authorities and comparable federal bodies",
        reference=(
            "Art. 1 Gesetz zur Modernisierung des Vergaberechts (Vergaberechtsmodernisierungs"
            "gesetz – VergRModG) vom 17.02.2016, BGBl. I S. 203"
        ),
    ),
    CentralGovernmentRule(
        version="Fassung ab 01.07.2026",
        valid_from=date(2026, 7, 1),
        valid_to=None,
        wording=_HEAD + "vom Bundeskanzleramt und den Bundesministerien anzuwenden",
        applies_to_de="das Bundeskanzleramt und die Bundesministerien",
        applies_to_en="the Federal Chancellery and the federal ministries",
        reference=(
            "Art. 1 Gesetz zur Beschleunigung der Vergabe öffentlicher Aufträge vom "
            "12.05.2026, BGBl. 2026 I Nr. 137"
        ),
    ),
)


def central_government_rule(on: date) -> CentralGovernmentRule:
    """Version of § 106 Abs. 2 Nr. 1 GWB in force on ``on`` (reference date of the case).

    All other German contracting authorities (Länder, municipalities, other
    federal bodies not named) apply the threshold for sub-central contracting
    authorities in that version.

    Raises:
        ThresholdUnavailable: ``on`` lies before 18.04.2016 (not recorded).
    """
    for rule in RULES:
        if rule.valid_from <= on and (rule.valid_to is None or on <= rule.valid_to):
            return rule
    raise ThresholdUnavailable(
        f"Für den {on:%d.%m.%Y} ist keine Fassung von {PROVISION} hinterlegt "
        "(die Vorschrift gilt in dieser Form erst ab dem 18.04.2016)."
    )
