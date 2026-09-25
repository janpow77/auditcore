"""Allocation and reproducible selection for the REST contract (framework-free).

Randomness comes from ``random.Random(seed)`` only. Without a supplied seed
a fresh one is generated with :mod:`secrets` and returned, so every draw can
be repeated exactly from the response. Strata are processed in the order of
their first appearance in ``items`` and consume one shared generator.
"""

from __future__ import annotations

import hashlib
import json
import random
import secrets
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from ..selection import draw_start, simple_random, stratified_allocation, systematic_mus
from ..sizes import SamplingInputError
from ._validate import (
    MAX_ITEMS,
    MAX_SEED,
    ContractError,
    as_object,
    choice,
    integer,
    number,
    optional_seed,
    require,
)
from .profiles import LIBRARY

ALLOCATIONS = ("proportional", "equal")


@dataclass(frozen=True)
class Item:
    """One element of the population as supplied by the caller."""

    position: int
    id: str
    value: float | None
    stratum: str | None


def _item(position: int, raw: object) -> Item:
    entry = as_object(raw, f"items[{position}]")
    identifier = entry.get("id", str(position + 1))
    if not isinstance(identifier, (str, int)) or isinstance(identifier, bool):
        raise ContractError(f"'items[{position}].id' muss Text oder ganze Zahl sein.")
    value = entry.get("value")
    stratum = entry.get("stratum")
    if stratum is not None and not isinstance(stratum, str):
        raise ContractError(f"'items[{position}].stratum' muss Text sein.")
    parsed = None if value is None else number(value, f"items[{position}].value")
    return Item(position, str(identifier), parsed, stratum)


def parse_items(raw: object) -> list[Item]:
    """Validated population, at most :data:`MAX_ITEMS` elements."""
    if not isinstance(raw, list) or not raw:
        raise ContractError("'items' muss eine nicht leere Liste sein.")
    if len(raw) > MAX_ITEMS:
        raise ContractError(f"Höchstens {MAX_ITEMS} Elemente je Anfrage.", status=413)
    return [_item(i, entry) for i, entry in enumerate(raw)]


def items_digest(items: Sequence[Item]) -> str:
    """SHA-256 over the canonical population; binds a draw to its input."""
    canonical = [[i.id, i.value, i.stratum] for i in items]
    data = json.dumps(canonical, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def allocate(payload: object) -> dict[str, Any]:
    """``POST /allocation``: sample size per stratum."""
    body = as_object(payload)
    total = integer(require(body, "total_sample_size"), "total_sample_size")
    method = choice(require(body, "method"), "method", ALLOCATIONS)
    raw = as_object(require(body, "strata"), "strata")
    strata: dict[Hashable, int] = {
        name: integer(size, f"strata.{name}") for name, size in raw.items()
    }
    try:
        allocation = stratified_allocation(total, strata, method)
    except SamplingInputError as exc:
        raise ContractError(str(exc)) from exc
    return {
        "library": LIBRARY,
        "method": method,
        "total_sample_size": total,
        "allocated": sum(allocation.values()),
        "strata": [
            {"stratum": str(k), "population": strata[str(k)], "sample_size": v}
            for k, v in allocation.items()
        ],
    }


def _groups(items: Sequence[Item]) -> dict[str | None, list[Item]]:
    groups: dict[str | None, list[Item]] = {}
    for item in items:
        groups.setdefault(item.stratum, []).append(item)
    return groups


def _sizes(
    body: Mapping[str, object], groups: Mapping[str | None, list[Item]]
) -> dict[str | None, int]:
    total = integer(require(body, "sample_size"), "sample_size")
    if list(groups) == [None]:
        return {None: total}
    if None in groups:
        raise ContractError("Bei Schichtung muss jedes Element eine Schicht ('stratum') haben.")
    method = choice(require(body, "allocation"), "allocation", ALLOCATIONS)
    counts: dict[Hashable, int] = {k: len(v) for k, v in groups.items()}
    try:
        allocation = stratified_allocation(total, counts, method)
    except SamplingInputError as exc:
        raise ContractError(str(exc)) from exc
    return {cast(str, k): v for k, v in allocation.items()}


def _row(item: Item, hits: int, draw_order: int) -> dict[str, Any]:
    return {
        "order": draw_order,
        "position": item.position,
        "id": item.id,
        "value": item.value,
        "stratum": item.stratum,
        "hits": hits,
    }


def _mus_stratum(
    rng: random.Random, members: list[Item], size: int, variant: str
) -> dict[str, Any]:
    positive = sum(i.value for i in members if i.value is not None and i.value > 0)
    base = positive if variant == "portal" else sum(i.value or 0.0 for i in members)
    interval = base / size if size > 0 and base > 0 else 0.0
    start = draw_start(rng, interval)
    drawn = systematic_mus(
        [i.value for i in members], sample_size=size, interval=interval, start=start,
        variant=variant,
    )
    unique = list(dict.fromkeys(drawn.positions))
    return {
        "interval": interval,
        "start": start,
        "rows": [members[p] for p in unique],
        "hits": [drawn.hits.count(p) for p in unique],
        "excluded_negative": [members[p].id for p in drawn.excluded_negative],
        "excluded_zero_or_missing": [members[p].id for p in drawn.excluded_zero_or_missing],
    }


def _srs_stratum(rng: random.Random, members: list[Item], size: int) -> dict[str, Any]:
    chosen = cast(list[int], simple_random(rng, list(range(len(members))), size))
    return {"rows": [members[i] for i in chosen], "hits": [1] * len(chosen)}


def _draw_stratum(
    method: str, rng: random.Random, members: list[Item], size: int, variant: str | None
) -> dict[str, Any]:
    try:
        if method == "mus":
            return _mus_stratum(rng, members, size, str(variant))
        return _srs_stratum(rng, members, size)
    except SamplingInputError as exc:
        raise ContractError(str(exc)) from exc


def select(payload: object) -> dict[str, Any]:
    """``POST /selection``: reproducible MUS or random selection, optionally stratified."""
    body = as_object(payload)
    method = choice(require(body, "method"), "method", ("mus", "srs"))
    variant = choice(require(body, "variant"), "variant", ("portal", "flowstat")) if (
        method == "mus"
    ) else None
    items = parse_items(require(body, "items"))
    supplied = optional_seed(body.get("seed"))
    seed = secrets.randbelow(MAX_SEED + 1) if supplied is None else supplied
    # Reproducible audit draw from a documented seed, not cryptography.
    rng = random.Random(seed)  # nosec B311
    groups = _groups(items)
    sizes = _sizes(body, groups)
    rows: list[dict[str, Any]] = []
    strata: list[dict[str, Any]] = []
    for stratum, members in groups.items():
        drawn = _draw_stratum(method, rng, members, sizes[stratum], variant)
        for item, hits in zip(drawn.pop("rows"), drawn.pop("hits"), strict=True):
            rows.append(_row(item, hits, len(rows) + 1))
        strata.append({"stratum": stratum, "population": len(members),
                       "sample_size": sizes[stratum], **drawn})
    return {
        "library": LIBRARY,
        "method": method,
        "variant": variant,
        "seed": seed,
        "seed_generated": supplied is None,
        "items_sha256": items_digest(items),
        "population": len(items),
        "selected": len(rows),
        "strata": strata,
        "rows": rows,
    }
