"""Gate rules GATE-01 to GATE-08, evaluated in the backend.

A gate names the reason, the responsible role and the next step. Gates
concern the documentation and the introduction of one specific version; they
never switch off a running procedure. A greyed-out button is no control: the
services call :func:`refuse_if_gated` before every positive step.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .errors import ConflictError
from .status import (
    ConsultationStatus,
    DpiaWorkStatus,
    NecessityStatus,
    StatusAxes,
    TransferStatus,
)

ACTION_CONFIRM_DOCUMENTATION = "dokumentation_bestaetigen"
ACTION_COMPLETE_DPIA = "dsfa_abschliessen"
ACTION_DECIDE_OPERATION = "betrieb_entscheiden"
ACTION_REPORT_INTEGRATION = "registerintegration_ausweisen"

#: Which gates prevent which positive step (catalogue 9.3).
ACTION_GATES: Mapping[str, frozenset[str]] = {
    ACTION_CONFIRM_DOCUMENTATION: frozenset({"GATE-01", "GATE-02"}),
    ACTION_COMPLETE_DPIA: frozenset({"GATE-01", "GATE-02", "GATE-04"}),
    ACTION_DECIDE_OPERATION: frozenset(
        {"GATE-01", "GATE-02", "GATE-03", "GATE-04", "GATE-05", "GATE-06", "GATE-07"}
    ),
    ACTION_REPORT_INTEGRATION: frozenset({"GATE-08"}),
}


@dataclass(frozen=True)
class GateFinding:
    """A gate that applies, with role and next step."""

    id: str
    reason: str
    role: str
    next_step: str

    def to_dict(self) -> dict[str, str]:
        """JSON form."""
        return {
            "id": self.id,
            "reason": self.reason,
            "role": self.role,
            "next_step": self.next_step,
        }


@dataclass(frozen=True)
class GateInput:
    """Everything the gates look at for one activity version."""

    activity: Mapping[str, object]
    axes: StatusAxes
    blocking_issues: Sequence[str]
    open_tasks: Sequence[str]
    planned_effect_only: bool
    unproven_measures: Sequence[str]
    changed_since_confirmation: bool
    dpo_statement: bool


def _blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _gate_01(data: GateInput) -> GateFinding | None:
    activity = data.activity
    missing = [
        title
        for field, title in (
            ("rechtsregime", "Rechtsregime"),
            ("verantwortliche_stelle", "verantwortliche Stelle"),
            ("ermaechtigungsgrundlage", "Befugnisgrundlage"),
        )
        if _blank(activity.get(field))
    ]
    if activity.get("rechtsregime") == "unklar":
        missing.append("Rechtsregime (als unklar gekennzeichnet)")
    if not missing:
        return None
    return GateFinding(
        "GATE-01",
        f"Ungeklärt: {', '.join(missing)}. Kein positiver rechtlicher Abschluss.",
        "fachverantwortung",
        "Rechtsregime, Verantwortlichkeit und Befugnisgrundlage klären und begründen.",
    )


def _gate_02(data: GateInput) -> GateFinding | None:
    reasons = [*data.blocking_issues, *data.open_tasks]
    if not reasons:
        return None
    shown = "; ".join(reasons[:5]) + (" …" if len(reasons) > 5 else "")
    return GateFinding(
        "GATE-02",
        f"Pflichtangaben fehlen, sind unklar, unbestätigt oder widersprüchlich: {shown}",
        "erfassung",
        "Fehlende Angaben ergänzen; Entwurfsexport bleibt gekennzeichnet möglich.",
    )


def _gate_03(data: GateInput) -> GateFinding | None:
    axes = data.axes
    if axes.necessity is NecessityStatus.UNDECIDED:
        return GateFinding(
            "GATE-03",
            "Die DSFA-Erforderlichkeit ist ungeklärt.",
            "fachverantwortung",
            "Schwellwertanalyse vollständig beantworten und begründet entscheiden.",
        )
    if (
        axes.necessity is NecessityStatus.REQUIRED
        and axes.dpia_work is not DpiaWorkStatus.COMPLETED
    ):
        return GateFinding(
            "GATE-03",
            "Eine DSFA ist erforderlich, aber nicht inhaltlich abgeschlossen.",
            "fachverantwortung",
            "Notwendigkeit, Verhältnismäßigkeit, Risiken und Maßnahmen bearbeiten.",
        )
    return None


def _gate_04(data: GateInput) -> GateFinding | None:
    if data.axes.necessity is not NecessityStatus.REQUIRED or data.dpo_statement:
        return None
    return GateFinding(
        "GATE-04",
        "Die erforderliche Beteiligung der oder des Datenschutzbeauftragten fehlt.",
        "dsb",
        "Stellungnahme einholen und den Umgang damit dokumentieren.",
    )


def _gate_05(data: GateInput) -> GateFinding | None:
    status = data.axes.consultation
    if data.axes.necessity is NecessityStatus.REQUIRED and status is ConsultationStatus.UNCHECKED:
        reason = "Die Konsultationspflicht ist noch nicht geprüft."
    elif status in (ConsultationStatus.REQUIRED, ConsultationStatus.INITIATED):
        reason = "Eine erforderliche Konsultation ist nicht abgeschlossen."
    else:
        return None
    return GateFinding(
        "GATE-05",
        f"{reason} Der reguläre Entscheidungsprozess ist angehalten.",
        "fachverantwortung",
        "Konsultation durchführen und Ergebnis dokumentieren; nur rechtlich zulässige "
        "Sonderwege gesondert behandeln.",
    )


def _gate_06(data: GateInput) -> GateFinding | None:
    if not data.planned_effect_only:
        return None
    return GateFinding(
        "GATE-06",
        "Die Risikominderung beruht auf nicht nachgewiesenen Maßnahmen: "
        f"{', '.join(data.unproven_measures)}.",
        "it_betrieb",
        "Umsetzung und Wirksamkeit mit Nachweis belegen, bevor der Betrieb beginnt.",
    )


def _gate_07(data: GateInput) -> GateFinding | None:
    if not data.changed_since_confirmation:
        return None
    return GateFinding(
        "GATE-07",
        "Seit der bestätigten Fassung wurde Relevantes geändert.",
        "fachverantwortung",
        "Neue Fassung prüfen; die alte Entscheidung gilt nicht automatisch weiter.",
    )


def _gate_08(data: GateInput) -> GateFinding | None:
    if data.axes.transfer is TransferStatus.TAKEN_OVER:
        return None
    return GateFinding(
        "GATE-08",
        f"Zentrale Übernahme nicht nachgewiesen (Stand: {data.axes.transfer.value}).",
        "zentrale_vvt_stelle",
        "Bestätigte Fassung übertragen und Übernahme mit zentraler Kennung bestätigen lassen.",
    )


_GATES = (_gate_01, _gate_02, _gate_03, _gate_04, _gate_05, _gate_06, _gate_07, _gate_08)


def evaluate_gates(data: GateInput) -> tuple[GateFinding, ...]:
    """All gates that currently apply, in order."""
    return tuple(f for gate in _GATES if (f := gate(data)) is not None)


def blocking_for(findings: Sequence[GateFinding], action: str) -> tuple[GateFinding, ...]:
    """Findings that prevent one positive step."""
    gates = ACTION_GATES[action]
    return tuple(f for f in findings if f.id in gates)


def refuse_if_gated(findings: Sequence[GateFinding], action: str) -> None:
    """Raise with reason, role and next step if a gate prevents the action."""
    blocking = blocking_for(findings, action)
    if blocking:
        details = " | ".join(
            f"{f.id}: {f.reason} Zuständig: {f.role}. Nächster Schritt: {f.next_step}"
            for f in blocking
        )
        raise ConflictError(f"Gesperrt ({action}): {details}")
