"""Source references and the derivation step shared by all estimators.

Every formula of this package is taken from the Commission guidance on
sampling for audit authorities; each :class:`Step` names the section it comes
from so that an auditor can retrace a result line by line.
"""

from __future__ import annotations

from dataclasses import dataclass

GUIDANCE = (
    "Europäische Kommission, Guidance on sampling methods for audit authorities, "
    "EGESIF_16-0014-01 vom 20.01.2017"
)
GUIDANCE_ID = "EGESIF_16-0014-01"
RER_TEMPLATE = (
    "Europäische Kommission, CPRE_23-0013-01, Methodological note ACR/AO, "
    "Annex 3 (RER calculation template)"
)
RER_TEMPLATE_ID = "CPRE_23-0013-01 Annex 3"
CPR = "Verordnung (EU) 2021/1060"


def guidance(section: str) -> str:
    """Reference to one section or appendix of the sampling guidance."""
    prefix = "" if section.startswith("Anhang") else "Abschn. "
    return f"{GUIDANCE_ID}, {prefix}{section}"


def cpr(article: str) -> str:
    """Reference to one provision of Regulation (EU) 2021/1060."""
    return f"Art. {article} {CPR}"


@dataclass(frozen=True)
class Step:
    """One retraceable line of a derivation: formula, value and source."""

    label: str
    formula: str
    value: float
    source: str

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible step."""
        return {
            "label": self.label,
            "formula": self.formula,
            "value": self.value,
            "source": self.source,
        }
