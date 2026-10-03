"""Deterministische Platzierung nach Inventar, Reservierungen und Leistungshinweisen."""

from __future__ import annotations

from dataclasses import dataclass

from .models import JobSpec
from .validation import identifier, integer, names, number, positive


@dataclass(frozen=True)
class Gpu:
    gpu_id: str
    free_vram_mb: int
    loaded_models: tuple[str, ...] = ()
    blocked: bool = False
    speed: float = 1

    def __post_init__(self) -> None:
        identifier(self.gpu_id)
        integer(self.free_vram_mb, "free_vram_mb")
        names(self.loaded_models)
        positive(self.speed, "speed")
        if not isinstance(self.blocked, bool):
            raise ValueError("blocked muss ein Wahrheitswert sein.")


@dataclass(frozen=True)
class Node:
    node_id: str
    observed_at: float
    cpus: int
    memory_mb: int
    capabilities: tuple[str, ...]
    gpus: tuple[Gpu, ...] = ()
    models: tuple[str, ...] = ()
    accepting: bool = True
    speed: float = 1

    def __post_init__(self) -> None:
        identifier(self.node_id)
        number(self.observed_at, "observed_at")
        integer(self.cpus, "cpus")
        integer(self.memory_mb, "memory_mb")
        names(self.capabilities)
        names(self.models)
        names(tuple(gpu.gpu_id for gpu in self.gpus))
        positive(self.speed, "speed")
        if not isinstance(self.accepting, bool) or not isinstance(self.gpus, tuple):
            raise ValueError("Ungültige Rechnerfreigabe oder GPU-Liste.")


@dataclass(frozen=True)
class SchedulerPolicy:
    node_max_age_s: float = 60
    aging_interval_s: float = 60
    max_active_per_scope: int = 2

    def __post_init__(self) -> None:
        positive(self.node_max_age_s, "node_max_age_s")
        positive(self.aging_interval_s, "aging_interval_s")
        integer(self.max_active_per_scope, "max_active_per_scope", minimum=1)


@dataclass(frozen=True)
class Allocation:
    node_id: str
    gpu_ids: tuple[str, ...]
    cpus: int
    memory_mb: int


def fits_node(job: JobSpec, node: Node, now: float, policy: SchedulerPolicy) -> bool:
    """Nur frische, freigegebene und zum Auftrag passende Inventare zulassen."""
    if not node.accepting or not 0 <= now - node.observed_at <= policy.node_max_age_s:
        return False
    if job.allowed_nodes and node.node_id not in job.allowed_nodes:
        return False
    if job.capability not in node.capabilities:
        return False
    return job.model is None or job.model in node.models


def candidates(
    job: JobSpec, node: Node, occupied: tuple[Allocation, ...]
) -> tuple[tuple[Gpu, ...], ...]:
    """Ganze GPUs exklusiv vergeben; CPU-/RAM-Budgets zählen auch für GPU-Aufträge."""
    active = [allocation for allocation in occupied if allocation.node_id == node.node_id]
    request = job.resources
    if sum(a.cpus for a in active) + request.cpus > node.cpus:
        return ()
    if sum(a.memory_mb for a in active) + request.memory_mb > node.memory_mb:
        return ()
    busy = {gpu_id for a in active for gpu_id in a.gpu_ids}
    cards = tuple(
        g
        for g in node.gpus
        if g.gpu_id not in busy and not g.blocked and g.free_vram_mb >= request.min_vram_mb
    )
    if len(cards) < request.gpu_count:
        return ()
    ordered = sorted(
        cards, key=lambda g: (job.model in g.loaded_models, g.speed, g.gpu_id), reverse=True
    )
    return (tuple(ordered[: request.gpu_count]),)


def choose_node(
    job: JobSpec,
    nodes: tuple[Node, ...],
    occupied: tuple[Allocation, ...],
    now: float,
    policy: SchedulerPolicy,
) -> Allocation | None:
    """Weicher Rechnerwunsch, geladene Modelle, Leistung; stabile Kennungen lösen Gleichstand."""
    ranked: list[tuple[tuple[int, int, float, str, tuple[str, ...]], Allocation]] = []
    for node in nodes:
        if not fits_node(job, node, now, policy):
            continue
        for cards in candidates(job, node, occupied):
            ids = tuple(g.gpu_id for g in cards)
            rank = (
                int(node.node_id in job.preferred_nodes),
                sum(job.model in g.loaded_models for g in cards),
                node.speed * (sum(g.speed for g in cards) if cards else 1),
                node.node_id,
                ids,
            )
            ranked.append(
                (rank, Allocation(node.node_id, ids, job.resources.cpus, job.resources.memory_mb))
            )
    return max(ranked, key=lambda item: item[0])[1] if ranked else None
