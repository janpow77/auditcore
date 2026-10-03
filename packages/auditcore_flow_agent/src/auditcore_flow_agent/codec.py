"""Versionierbare JSON-Ablage; keine ausführbaren Python-Objekte in der Warteschlange."""

from __future__ import annotations

import json
from dataclasses import fields
from typing import cast

from auditcore_common.json_values import JsonValue, decode_json, jsonable

from .models import JobSpec, ResourceRequest, RetryPolicy
from .resources import Gpu, Node


def record(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
        raise ValueError("JSON-Objekt erforderlich.")
    return cast(dict[str, object], value)


def sequence(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("Liste von Kennungen erforderlich.")
    return tuple(value)


def decode(text: str) -> dict[str, object]:
    return record(decode_json(text, lambda error: ValueError(f"Ungültiges JSON: {error}")))


def encode(value: JobSpec | Node) -> str:
    data = {f.name: jsonable(getattr(value, f.name), dataclasses=True) for f in fields(value)}
    return json.dumps(data, sort_keys=True, allow_nan=False, ensure_ascii=False)


def read_job(text: str) -> JobSpec:
    data = decode(text)
    resource = record(data["resources"])
    retry = record(data["retry"])
    return JobSpec(
        job_id=cast(str, data["job_id"]),
        scope=cast(str, data["scope"]),
        capability=cast(str, data["capability"]),
        resources=ResourceRequest(
            cpus=cast(int, resource["cpus"]),
            memory_mb=cast(int, resource["memory_mb"]),
            gpu_count=cast(int, resource["gpu_count"]),
            min_vram_mb=cast(int, resource["min_vram_mb"]),
        ),
        payload=cast(dict[str, JsonValue], record(data["payload"])),
        dependencies=sequence(data["dependencies"]),
        priority=cast(int, data["priority"]),
        not_before=cast(float, data["not_before"]),
        timeout_s=cast(float, data["timeout_s"]),
        lease_s=cast(float, data["lease_s"]),
        stall_timeout_s=cast(float | None, data["stall_timeout_s"]),
        retry=RetryPolicy(
            max_attempts=cast(int, retry["max_attempts"]),
            initial_delay_s=cast(float, retry["initial_delay_s"]),
            max_delay_s=cast(float, retry["max_delay_s"]),
        ),
        model=cast(str | None, data["model"]),
        allowed_nodes=sequence(data["allowed_nodes"]),
        preferred_nodes=sequence(data["preferred_nodes"]),
    )


def _gpu(value: object) -> Gpu:
    data = record(value)
    return Gpu(
        gpu_id=cast(str, data["gpu_id"]),
        free_vram_mb=cast(int, data["free_vram_mb"]),
        loaded_models=sequence(data["loaded_models"]),
        blocked=cast(bool, data["blocked"]),
        speed=cast(float, data["speed"]),
    )


def read_node(text: str) -> Node:
    data = decode(text)
    cards = data["gpus"]
    if not isinstance(cards, list):
        raise ValueError("GPU-Liste erforderlich.")
    return Node(
        node_id=cast(str, data["node_id"]),
        observed_at=cast(float, data["observed_at"]),
        cpus=cast(int, data["cpus"]),
        memory_mb=cast(int, data["memory_mb"]),
        capabilities=sequence(data["capabilities"]),
        gpus=tuple(_gpu(g) for g in cards),
        models=sequence(data["models"]),
        accepting=cast(bool, data["accepting"]),
        speed=cast(float, data["speed"]),
    )
