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

from .profiles import RegistryProfile


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
    visited: set[Any] = field(default_factory=set)

    @property
    def self_references(self) -> list[str]:
        """Node ids whose parent is the node itself."""
        return [n.id for n in self.graph.values() if n.parent_id == n.id]


def traverse(
    company: Mapping[str, Any],
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


def network(graph: OwnershipGraph) -> dict[str, list[dict[str, Any]]]:
    """Cytoscape-compatible nodes and edges (as the source)."""
    nodes, edges = [], []
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

    is_sme: bool
    category: str
    employees: Any
    turnover: Any
    balance_sheet: Any
    status: str
    profile: Mapping[str, str]
    decisions: tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
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
        }


def sme_status(company: Mapping[str, Any], profile: RegistryProfile) -> SmeAssessment:
    """``calculate_kmu_status``: thresholds of the profile, no aggregation (see decisions)."""
    profile.require_kind("sme")
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
