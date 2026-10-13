"""The free table: columns from a recipe, rules between columns, sum binding."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import cast

from auditcore_dummybundle import catalogs as cat
from auditcore_dummybundle.amounts import allocate
from auditcore_dummybundle.errors import BundleError
from auditcore_dummybundle.fieldgen import GENERATORS, SUM_QUANTUM, Context
from auditcore_dummybundle.fieldtypes import TYPES_BY_ID
from auditcore_dummybundle.model import MARKING, Budget, Cell, Column, Table
from auditcore_dummybundle.recipe import FORMAT, FORMAT_VERSION, FieldSpec, Recipe
from auditcore_dummybundle.seeds import stream

_NUMERIC = ("amount", "decimal", "int")


def _context(recipe: Recipe) -> Context:
    rng = stream(recipe.seed, "row-context")
    countries = [cat.country_of(rng, recipe.country) for _ in range(recipe.rows)]
    locations = [cat.address(rng, country) for country in countries]
    return Context(recipe, countries, locations)


def _coerce(spec: FieldSpec, value: object) -> Cell:
    """Rule value in the cell type of the column; empty text means an empty cell."""
    if value is None or value == "":
        return None
    kind = TYPES_BY_ID[spec.type].cell
    if kind not in _NUMERIC:
        return str(value)
    try:
        number = Decimal(str(value).replace(",", "."))
    except InvalidOperation as exc:
        raise BundleError(
            f"Spalte '{spec.name}': Der Regelwert '{value}' ist keine Zahl.",
            code="not_numeric",
            path=spec.name,
        ) from exc
    return int(number) if kind == "int" else number


def _apply_when(ctx: Context, spec: FieldSpec, cells: list[Cell]) -> list[Cell]:
    watched = ctx.columns[str(spec.rule_params["field"])]
    expected = str(spec.rule_params["equals"])
    hit = _coerce(spec, spec.rule_params["value"])
    otherwise = spec.rule_params["otherwise"]
    miss = _coerce(spec, otherwise)
    result: list[Cell] = []
    for seen, cell in zip(watched, cells, strict=True):
        if seen is not None and str(seen) == expected:
            result.append(hit)
        else:
            result.append(cell if otherwise is None else miss)
    return result


def _apply_empty(recipe: Recipe, spec: FieldSpec, cells: list[Cell]) -> list[Cell]:
    if spec.empty_share <= 0:
        return cells
    rng = stream(recipe.seed, "empty", spec.name)
    threshold = int(spec.empty_share * 1_000_000)
    return [None if rng.randrange(1_000_000) < threshold else cell for cell in cells]


def _apply_sum(ctx: Context, spec: FieldSpec, cells: list[Cell]) -> list[Cell]:
    total = cast(Decimal, spec.rule_params["total"]).quantize(SUM_QUANTUM)
    group_field = spec.rule_params["group_by"]
    keys = ctx.columns[group_field] if isinstance(group_field, str) else [None] * len(cells)
    result = list(cells)
    for key in dict.fromkeys(keys):
        members = [i for i, k in enumerate(keys) if k == key and cells[i] is not None]
        if not members:
            continue
        weights = [cast(Decimal, cells[i]) for i in members]
        if not any(weights):
            weights = [Decimal(1)] * len(members)
        for i, part in zip(members, allocate(total, weights, SUM_QUANTUM), strict=True):
            result[i] = part
    return result


def _column(ctx: Context, spec: FieldSpec) -> list[Cell]:
    rng = stream(ctx.recipe.seed, "column", spec.name)
    cells = GENERATORS[spec.type](ctx, spec, rng)
    if spec.rule == "when":
        cells = _apply_when(ctx, spec, cells)
    cells = _apply_empty(ctx.recipe, spec, cells)
    if spec.rule == "sum_to":
        cells = _apply_sum(ctx, spec, cells)
    return cells


def generate_table(recipe: Recipe, budget: Budget | None = None) -> Table:
    """Generate the table of ``recipe``; equal recipes give equal tables."""
    budget = budget or Budget()
    ctx = _context(recipe)
    for spec in recipe.order():
        budget.tick()
        ctx.columns[spec.name] = _column(ctx, spec)
    columns = tuple(Column(spec.name, TYPES_BY_ID[spec.type].cell) for spec in recipe.fields)
    rows = tuple(
        tuple(ctx.columns[spec.name][index] for spec in recipe.fields)
        for index in range(recipe.rows)
    )
    return Table("Tabelle", recipe.title, columns, rows, "recipe")


def _plain(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        if value and isinstance(value[0], tuple):
            return [{"value": name, "weight": weight} for name, weight in value]
        return list(value)
    return value if value is None or isinstance(value, (str, int, bool)) else str(value)


def _field_document(spec: FieldSpec) -> dict[str, object]:
    document: dict[str, object] = {
        "name": spec.name,
        "type": spec.type,
        "params": {key: _plain(value) for key, value in spec.params.items() if value is not None},
        "empty_share": str(spec.empty_share),
    }
    if spec.rule is not None:
        rule: dict[str, object] = {"kind": spec.rule}
        rule.update({k: _plain(v) for k, v in spec.rule_params.items() if v is not None})
        document["rule"] = rule
    return document


def recipe_document(recipe: Recipe, version: str) -> dict[str, object]:
    """Recipe as a JSON-ready document that :func:`recipe.parse_recipe` reads back unchanged."""
    return {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "title": recipe.title,
        "derived_from": recipe.derived_from,
        "marking": MARKING,
        "run": {
            "seed": recipe.seed,
            "base_date": recipe.base_date.isoformat(),
            "rows": recipe.rows,
            "country": recipe.country,
        },
        "generator": {"package": "auditcore_dummybundle", "version": version},
        "fields": [_field_document(spec) for spec in recipe.fields],
    }
