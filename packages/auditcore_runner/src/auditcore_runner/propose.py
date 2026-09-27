"""Suggest runner classes and limits from measured hardware."""

from __future__ import annotations

from .auth_setup import detect_auth
from .hardware import Gpu, HostFacts
from .profile import (
    BASE_LABELS,
    TEMPLATE_GPU_CLASSES,
    Auth,
    GpuPolicy,
    Network,
    Profile,
    RunnerClass,
    Target,
)

LARGE_CPUS = 24
LARGE_MEMORY_GB = 48


def gpu_class_for(vram_mb: int) -> str:
    return "gpu-16gb" if vram_mb >= 12000 else "gpu-8gb"


def _gpu_classes(facts: HostFacts, project_label: str) -> dict[str, RunnerClass]:
    classes: dict[str, RunnerClass] = {}
    for name in TEMPLATE_GPU_CLASSES:
        count = sum(1 for g in facts.gpus if gpu_class_for(g.vram_mb) == name)
        if count:
            labels = (*BASE_LABELS, project_label, facts.hostname, "gpu", name)
            classes[name] = RunnerClass(True, 2, 8, count, labels, 128, 19, 10, quiet_max=0, kind="gpu")
    return classes


def _gpu_policies(gpus: tuple[Gpu, ...]) -> tuple[GpuPolicy, ...]:
    return tuple(GpuPolicy(g.uuid, g.name, g.vram_mb, True, gpu_class_for(g.vram_mb), g.index) for g in gpus)


def _budget(facts: HostFacts, reserve: tuple[int, int], gpu: dict[str, RunnerClass]) -> tuple[int, int]:
    used_cpus = sum(c.cpus * c.max_instances for c in gpu.values())
    used_memory = sum(c.memory_gb * c.max_instances for c in gpu.values())
    return (
        facts.cpu_count - reserve[0] - used_cpus,
        facts.memory_mb // 1024 - reserve[1] - used_memory,
    )


def propose(facts: HostFacts, target: str = "", project_label: str = "auditcore", auth: Auth | None = None) -> Profile:
    """A safe starting profile: large machines share cores at low priority; credentials per RUN-022."""
    large = facts.cpu_count >= LARGE_CPUS and facts.memory_mb >= LARGE_MEMORY_GB * 1024
    name = "cpu-gross" if large else "cpu"
    cpus, memory = (8, 12) if large else (2, 5)
    reserve = (4, 12) if large else (6, 24)
    gpu_classes = _gpu_classes(facts, project_label)
    budget_cpus, budget_memory = _budget(facts, reserve, gpu_classes)
    instances = max(0, min(budget_cpus // cpus, budget_memory // memory, 6))
    shares, nice, io = (128, 19, 10) if large else (512, 10, 100)
    labels = (*BASE_LABELS, project_label, facts.hostname, name)
    classes = {name: RunnerClass(True, cpus, memory, instances, labels, shares, nice, io)}
    classes.update(gpu_classes)
    return Profile(
        host=facts.hostname,
        target=Target(scope="repo", name=target),
        auth=auth if auth is not None else detect_auth()[0],
        reserve_cpus=reserve[0],
        reserve_memory_gb=reserve[1],
        network=Network(enabled=True, firewall_required=True),
        classes=classes,
        gpus=_gpu_policies(facts.gpus),
    )
