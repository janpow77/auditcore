"""Feststellungsliste und Vorschlag der Funktionsfähigkeitskategorie je Kernanforderung."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from ..extensions import AuditFinding, AuditReference, AuditStep
from ..model import BpmnDocument, as_document
from ..profiles import Profile, ProfileRegistry
from ..vocabulary import FUNCTIONING_CATEGORIES, label

Row = dict[str, str]


def _finding_row(element_id: str, name: str, finding: AuditFinding) -> Row:
    return {
        "id": finding.id or "",
        "kennung": finding.reference or "",
        "element": name,
        "element_id": element_id,
        "art": finding.finding_type or "",
        "einstufung": finding.severity or "",
        "ka": finding.key_requirement or "",
        "bk": finding.assessment_criterion or "",
        "beschreibung": finding.description or "",
        "empfehlung": finding.recommendation or "",
        "frist": finding.deadline or "",
        "status": finding.status or "",
    }


def finding_list(source: str | bytes | BpmnDocument) -> list[Row]:
    """Alle Prüffeststellungen an Elementen und am Diagramm."""
    document = as_document(source)
    rows = [_finding_row(e.id, e.label, f) for e in document for f in e.extensions.findings]
    if document.diagram_info is not None:
        owner = document.diagram_info_owner or ""
        rows += [_finding_row(owner, "Diagramm", f) for f in document.diagram_info.findings]
    return rows


@dataclass(frozen=True)
class CategoryProposal:
    """Vorschlag der Funktionsfähigkeitskategorie einer KA (keine Entscheidung)."""

    key_requirement: int
    title: str
    proposal: int | None
    reason: str
    findings: tuple[str, ...]
    note: str = "Vorschlag – die Einstufung entscheidet der Prüfer."

    def to_dict(self) -> dict[str, object]:
        """JSON-fähige Darstellung."""
        text = label(FUNCTIONING_CATEGORIES[str(self.proposal)]) if self.proposal else None
        return {
            "key_requirement": self.key_requirement,
            "title": self.title,
            "proposal": self.proposal,
            "category_text": text,
            "reason": self.reason,
            "findings": list(self.findings),
            "note": self.note,
        }


@dataclass
class _Evidence:
    references: dict[int, int]
    failed_steps: dict[int, int]
    findings: dict[int, list[AuditFinding]]

    def add_holder(
        self, references: Sequence[AuditReference], findings: Sequence[AuditFinding], steps: Sequence[AuditStep]
    ) -> None:
        """Nimmt Prüfbezüge, Feststellungen und Prüfschritte eines Trägers auf."""
        for number in {r.key_requirement_number for r in references if r.key_requirement_number is not None}:
            self.references[number] = self.references.get(number, 0) + 1
            self.failed_steps[number] = self.failed_steps.get(number, 0) + sum(
                s.result == "nicht_erfuellt" for s in steps
            )
        for finding in findings:
            ka = AuditReference(key_requirement=finding.key_requirement).key_requirement_number
            if finding.status != "entfallen" and ka is not None:
                self.findings.setdefault(ka, []).append(finding)
                self.references[ka] = self.references.get(ka, 0) + 1


def _collect(documents: list[BpmnDocument]) -> _Evidence:
    evidence = _Evidence({}, {}, {})
    for document in documents:
        for element in document:
            ext = element.extensions
            evidence.add_holder(ext.audit_references, ext.findings, ext.audit_steps)
        info = document.diagram_info
        if info is not None:
            evidence.add_holder(info.audit_references, info.findings, ())
    return evidence


def _category(findings: list[AuditFinding], failed: int) -> tuple[int, str]:
    if any(f.severity == "schwerwiegend" for f in findings):
        return 4, "Mindestens eine schwerwiegende Feststellung."
    if any(f.finding_type == "finanziell" or f.severity == "mittel" for f in findings):
        return 3, "Finanzielle oder mittlere Feststellung(en)."
    if findings or failed:
        return 2, "Nur formelle, geringe Feststellung(en) oder nicht erfüllte Prüfschritte."
    return 1, "Prüfbezüge ohne Feststellung."


def category_proposals(
    documents: Iterable[str | bytes | BpmnDocument], *, profile: Profile | None = None
) -> list[CategoryProposal]:
    """Vorschlag je KA aus Feststellungen und Prüfschritten (ausdrücklich nur Vorschlag).

    Keine Grundlage → kein Vorschlag; Belege ohne Feststellung → 1; nur
    formelle, geringe Feststellungen oder nicht erfüllte Prüfschritte → 2;
    finanzielle oder mittlere → 3; schwerwiegende → 4. Entfallene
    Feststellungen zählen nicht.
    """
    docs = [as_document(d) for d in documents]
    if profile is None:
        profile = ProfileRegistry().for_diagram(docs[0].diagram_info if docs else None)[0]
    evidence = _collect(docs)
    proposals = []
    for requirement in profile.key_requirements:
        number, title = requirement.number, label(requirement.title)
        items = evidence.findings.get(number, [])
        names = tuple(f.reference or f.id or "Feststellung" for f in items)
        if not evidence.references.get(number):
            proposals.append(
                CategoryProposal(number, title, None, "Keine Prüfbezüge oder Feststellungen zu dieser KA.", ())
            )
            continue
        category, reason = _category(items, evidence.failed_steps.get(number, 0))
        proposals.append(CategoryProposal(number, title, category, reason, names))
    return proposals
