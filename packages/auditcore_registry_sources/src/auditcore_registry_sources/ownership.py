"""Ownership traversal, beneficial-owner (UBO) and SME judgements as explicit profiles.

Source: flowsearch ``UBOEngine``. The rules are professional settings with
open decisions (``HUMAN_DECISION_REQUIRED`` in ``flowsearch.ubo`` and
``flowsearch.kmu``): the voting-rights threshold (source 50 %, § 3 Abs. 2 GwG
25 %), the multiplication of shares along a chain, the treatment of owners
without type and the SME categories without balance-sheet alternative and
without partner/linked enterprise aggregation. Every result carries these
decisions; nothing here is a legal assessment.

Corrected: the source's ``build_ownership_chain`` does not terminate on a
self-referencing node (observed memory growth); :func:`ownership_chain`
stops at a repeated node and reports the cycle.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ._types import JsonObject, JsonValue
from .profiles import RegistryProfile

#: Company data as passed by the caller (source field names, values unchecked).
CompanyData = Mapping[str, Any]


@dataclass
class OwnershipNode:
    """A company or person in the ownership graph (field names as in the source)."""

    id: str
    name: str
    type: str
    direct_share: float
    effective_share: float
    voting_rights: float | None = None
    level: int = 0
    parent_id: str | None = None


@dataclass
class OwnershipGraph:
    """Nodes in discovery order, the graph by node id and detected self-references."""

    nodes: list[OwnershipNode] = field(default_factory=list)
    graph: dict[str, OwnershipNode] = field(default_factory=dict)
    visited: set[object] = field(default_factory=set)

    @property
    def self_references(self) -> list[str]:
        """Node ids whose parent is the node itself."""
        return [n.id for n in self.graph.values() if n.parent_id == n.id]


def traverse(
    company: CompanyData,
    profile: RegistryProfile,
    *,
    graph: OwnershipGraph | None = None,
    level: int = 0,
    parent_share: float = 100.0,
) -> OwnershipGraph:
    """Depth-first traversal with effective shares (``share / 100 * parent share``)."""
    profile.require_kind("ownership")
    graph = graph if graph is not None else OwnershipGraph()
    if level >= int(profile.setting("max_depth")):
        return graph
    company_id = company.get("id", company.get("name"))
    if company_id in graph.visited:
        return graph
    graph.visited.add(company_id)
    missing_type = str(profile.setting("missing_type"))
    for holder in company.get("shareholders", []):
        share = holder.get("share", 0.0)
        effective = (share / 100.0) * parent_share
        node = OwnershipNode(
            id=holder.get("id", holder["name"]),
            name=holder["name"],
            type=holder.get("type", missing_type),
            direct_share=share,
            effective_share=effective,
            voting_rights=holder.get("voting_rights"),
            level=level + 1,
            parent_id=company_id,
        )
        graph.nodes.append(node)
        graph.graph[node.id] = node
        if node.type == "company" and holder.get("has_details"):
            traverse(holder, profile, graph=graph, level=level + 1, parent_share=effective)
    return graph


def _above(value: float, threshold: float, comparison: str) -> bool:
    return value > threshold if comparison == "greater_than" else value >= threshold


def beneficial_owners(
    nodes: Sequence[OwnershipNode], profile: RegistryProfile
) -> list[OwnershipNode]:
    """Natural persons above the share threshold or with voting control, by share descending."""
    profile.require_kind("ownership")
    share_threshold = float(profile.setting("share_threshold"))
    voting_threshold = float(profile.setting("voting_threshold"))
    share_cmp = str(profile.setting("share_comparison"))
    voting_cmp = str(profile.setting("voting_comparison"))
    owners = [
        n
        for n in nodes
        if n.type == "person"
        and (
            _above(n.effective_share, share_threshold, share_cmp)
            or bool(n.voting_rights and _above(n.voting_rights, voting_threshold, voting_cmp))
        )
    ]
    owners.sort(key=lambda n: n.effective_share, reverse=True)
    return owners


def unclassified_holders(
    nodes: Sequence[OwnershipNode], profile: RegistryProfile
) -> list[OwnershipNode]:
    """Holders of unknown type above a threshold: to be clarified, never silently a person."""
    profile.require_kind("ownership")
    share_threshold = float(profile.setting("share_threshold"))
    voting_threshold = float(profile.setting("voting_threshold"))
    share_cmp = str(profile.setting("share_comparison"))
    voting_cmp = str(profile.setting("voting_comparison"))
    return [
        n
        for n in nodes
        if n.type not in ("person", "company")
        and (
            _above(n.effective_share, share_threshold, share_cmp)
            or bool(n.voting_rights and _above(n.voting_rights, voting_threshold, voting_cmp))
        )
    ]


@dataclass(frozen=True)
class Chain:
    """Chain from the root to a node; ``cycle`` names the node that repeated."""

    nodes: tuple[OwnershipNode, ...]
    cycle: str | None = None


def ownership_chain(graph: OwnershipGraph, node_id: str) -> Chain:
    """Walk parent links to the root; stops at the first repeated node."""
    chain: list[OwnershipNode] = []
    seen: set[str] = set()
    current: str | None = node_id
    while current and current in graph.graph:
        if current in seen:
            return Chain(tuple(reversed(chain)), cycle=current)
        seen.add(current)
        node = graph.graph[current]
        chain.append(node)
        current = node.parent_id
    return Chain(tuple(reversed(chain)))


def network(graph: OwnershipGraph) -> dict[str, list[JsonObject]]:
    """Cytoscape-compatible nodes and edges (as the source)."""
    nodes: list[JsonObject] = []
    edges: list[JsonObject] = []
    for node_id, node in graph.graph.items():
        nodes.append(
            {
                "data": {
                    "id": node.id,
                    "label": node.name,
                    "type": node.type,
                    "effective_share": node.effective_share,
                    "level": node.level,
                }
            }
        )
        if node.parent_id:
            edges.append(
                {"data": {"source": node.parent_id, "target": node_id, "share": node.direct_share}}
            )
    return {"nodes": nodes, "edges": edges}


@dataclass(frozen=True)
class SmeAssessment:
    """SME category of the legacy profile, always with its open decisions."""

    is_sme: bool | None
    category: str
    employees: Any
    turnover: Any
    balance_sheet: Any
    status: str
    profile: Mapping[str, str]
    decisions: tuple[Mapping[str, JsonValue], ...]
    notes: tuple[str, ...] = ()

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "is_sme": self.is_sme,
            "category": self.category,
            "employees": self.employees,
            "turnover": self.turnover,
            "balance_sheet": self.balance_sheet,
            "status": self.status,
            "profile": dict(self.profile),
            "decisions": [dict(d) for d in self.decisions],
            "notes": list(self.notes),
        }


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _aggregated(company: CompanyData, key: str) -> float | None:
    """Own value plus linked (full) and partner (by share) values; any gap → ``None``."""
    total = _number(company.get(key))
    for linked in company.get("linked", []) or []:
        value = _number(linked.get(key))
        total = None if total is None or value is None else total + value
    for partner in company.get("partners", []) or []:
        value, share = _number(partner.get(key)), _number(partner.get("share"))
        total = (
            None
            if total is None or value is None or share is None
            else total + value * share / 100.0
        )
    return total


def _agvo_category(
    employees: float,
    turnover: float | None,
    balance: float | None,
    profile: RegistryProfile,
    notes: list[str],
) -> tuple[str, bool | None]:
    """Size class by headcount and (turnover or balance sheet); appends open points."""
    for key, label in (
        ("micro", "Kleinstunternehmen"),
        ("small", "Kleinunternehmen"),
        ("medium", "Mittleres Unternehmen"),
    ):
        rule = profile.setting(key)
        financial = (turnover is not None and turnover <= rule["turnover_max"]) or (
            balance is not None and balance <= rule["balance_sheet_max"]
        )
        if employees < rule["employees_below"] and financial:
            return label, True
    if turnover is None or balance is None:
        notes.append("Ein Finanzwert fehlt; die Alternative Umsatz/Bilanzsumme ist offen.")
        return "Nicht bestimmbar", None
    return "Großunternehmen", False


def _agvo(company: CompanyData, profile: RegistryProfile) -> SmeAssessment:
    """Anhang I AGVO: headcount and (turnover or balance sheet), linked/partner aggregated."""
    notes = [str(n) + " – nicht ausgewertet." for n in profile.setting("not_evaluated")]
    employees = _aggregated(company, "employees")
    turnover = _aggregated(company, "revenue")
    balance = _aggregated(company, "balance_sheet_total")
    if not company.get("linked") and not company.get("partners"):
        notes.append(
            "Keine verbundenen oder Partnerunternehmen angegeben; eigenständiges Unternehmen "
            "angenommen, vom Nutzer zu bestätigen."
        )
    category = "Nicht bestimmbar"
    is_sme: bool | None = None
    if employees is not None and (turnover is not None or balance is not None):
        category, is_sme = _agvo_category(employees, turnover, balance, profile, notes)
    else:
        notes.append(
            "Mitarbeiterzahl oder beide Finanzwerte fehlen (auch bei Partnern/Verbundenen)."
        )
    return SmeAssessment(
        is_sme=is_sme,
        category=category,
        employees=employees,
        turnover=turnover,
        balance_sheet=balance,
        status=profile.status,
        profile=profile.reference,
        decisions=profile.decisions,
        notes=tuple(notes),
    )


def sme_status(company: CompanyData, profile: RegistryProfile) -> SmeAssessment:
    """``calculate_kmu_status``: thresholds of the profile, no aggregation (see decisions)."""
    profile.require_kind("sme")
    if profile.settings.get("method") == "agvo_annex_i":
        return _agvo(company, profile)
    sme, micro, small = profile.setting("sme"), profile.setting("micro"), profile.setting("small")
    employees = company.get("employees", 0)
    turnover = company.get("revenue", 0)
    balance = company.get("balance_sheet_total", 0)
    is_sme = employees < sme["employees_below"] and (
        turnover <= sme["turnover_max"] or balance <= sme["balance_sheet_max"]
    )
    if employees < micro["employees_below"] and turnover <= micro["turnover_max"]:
        category = "Kleinstunternehmen"
    elif employees < small["employees_below"] and turnover <= small["turnover_max"]:
        category = "Kleinunternehmen"
    else:
        category = "Mittleres Unternehmen"
    return SmeAssessment(
        is_sme=is_sme,
        category=category if is_sme else "Großunternehmen",
        employees=employees,
        turnover=turnover,
        balance_sheet=balance,
        status=profile.status,
        profile=profile.reference,
        decisions=profile.decisions,
    )
