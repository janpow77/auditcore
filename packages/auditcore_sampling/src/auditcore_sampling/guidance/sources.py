"""Source references and the derivation step of the guidance-based planning.

Every formula of :mod:`auditcore_sampling.guidance` names the section of the
Commission guidance or the provision of the regulation it comes from.
"""

from __future__ import annotations

from dataclasses import dataclass

GUIDANCE_ID = "EGESIF_16-0014-01"
GUIDANCE = (
    "Europäische Kommission, Guidance on sampling methods for audit authorities, "
    f"{GUIDANCE_ID} vom 20.01.2017"
)
CPR_2021 = "Verordnung (EU) 2021/1060"
CPR_2013 = "Verordnung (EU) Nr. 1303/2013"
#: Status of every method of this subpackage (distinct from the characterized legacy methods).
GUIDANCE_STATUS = "GUIDANCE_EGESIF_16_0014_01"
GUIDANCE_STATUS_LABEL = "nach Leitfaden"


def guidance(section: str) -> str:
    """Reference to one section, table or appendix of the sampling guidance."""
    prefix = "" if section.startswith(("Anhang", "Tabelle")) else "Abschn. "
    return f"{GUIDANCE_ID}, {prefix}{section}"


def regulation(article: str, act: str = CPR_2021) -> str:
    """Reference to one provision of a regulation."""
    return f"Art. {article} {act}"


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
