"""The recipe of a free table: strict reading, defaults and dependency order.

A recipe is the downloadable and reloadable column definition: fields with
type, parameters, share of empty values and an optional rule, plus the run
(seed, base date, rows, country) and the package version that wrote it.
Loading is strict: unknown keys, types, parameters or column references are
rejected with the path of the offending entry.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from auditcore_dummybundle import parsing
from auditcore_dummybundle.config import COUNTRY_CHOICES
from auditcore_dummybundle.errors import BundleError
from auditcore_dummybundle.fieldtypes import RULES_BY_ID, TYPES_BY_ID, FieldType, Param
from auditcore_dummybundle.model import MARKING

FORMAT = "auditcore.dummybundle.recipe"
FORMAT_VERSION = 1
_FIELD_KEYS = ("name", "type", "params", "empty_share", "rule")
_RECIPE_KEYS = (
    "format",
    "format_version",
    "title",
    "derived_from",
    "marking",
    "run",
    "generator",
    "fields",
)
_RUN_KEYS = ("seed", "base_date", "rows", "country")


@dataclass(frozen=True)
class RecipeLimits:
    """Upper bounds a host may tighten for a public endpoint."""

    max_rows: int = 100_000
    max_fields: int = 60


@dataclass(frozen=True)
class FieldSpec:
    """One column: validated parameters with defaults filled in."""

    name: str
    type: str
    params: dict[str, object]
    empty_share: Decimal
    rule: str | None
    rule_params: dict[str, object]

    @property
    def references(self) -> tuple[str, ...]:
        """Names of the columns this column is derived from."""
        found: list[str] = []
        for value in (self.params.get("field"), self.params.get("date_field"),
                      self.rule_params.get("field"), self.rule_params.get("group_by")):  # fmt: skip
            if isinstance(value, str):
                found.append(value)
        many = self.params.get("fields")
        if isinstance(many, tuple):
            found.extend(str(name) for name in many)
        return tuple(found)


@dataclass(frozen=True)
class Recipe:
    """A validated free table definition."""

    title: str
    derived_from: str | None
    seed: int
    base_date: date
    rows: int
    country: str
    fields: tuple[FieldSpec, ...]
    written_by: str = ""

    def order(self) -> tuple[FieldSpec, ...]:
        """Fields in an order in which every reference is generated first."""
        return _dependency_order(self.fields)


def _values(value: object, path: str, param: Param) -> tuple[tuple[str, int], ...]:
    items = parsing.as_list(value, path, param.high, minimum=param.low)
    result = []
    for index, item in enumerate(items):
        entry = parsing.as_object(item, f"{path}[{index}]", ("value", "weight"))
        text = parsing.as_text(entry.get("value"), f"{path}[{index}].value", empty=True)
        weight = parsing.as_int(entry.get("weight", 1), f"{path}[{index}].weight", 1, 1_000_000)
        result.append((text, weight))
    return tuple(result)


def _names(value: object, path: str, param: Param) -> tuple[str, ...]:
    items = parsing.as_list(value, path, param.high, minimum=param.low)
    return tuple(
        parsing.as_text(item, f"{path}[{i}]", max_length=80) for i, item in enumerate(items)
    )


def _param(value: object, path: str, param: Param) -> object:
    if param.kind == "int":
        return parsing.as_int(value, path, param.low, param.high)
    if param.kind == "decimal":
        return parsing.as_decimal(value, path, Decimal(param.low), Decimal(param.high))
    if param.kind == "bool":
        return parsing.as_bool(value, path)
    if param.kind == "date":
        return parsing.as_date(value, path)
    if param.kind == "choice":
        return parsing.as_choice(value, path, param.options)
    if param.kind == "values":
        return _values(value, path, param)
    if param.kind == "fields":
        return _names(value, path, param)
    limit = 80 if param.kind == "field" else max(param.high, 1)
    return parsing.as_text(value, path, max_length=limit, empty=param.kind == "text")


def _default(param: Param) -> object:
    if param.kind == "decimal" and param.default is not None:
        return Decimal(str(param.default))
    return param.default


def _params(raw: object, path: str, kind: FieldType) -> dict[str, object]:
    allowed = {param.name: param for param in kind.params}
    given = parsing.as_object({} if raw is None else raw, path, allowed)
    values: dict[str, object] = {}
    for name, param in allowed.items():
        if given.get(name) is None:
            if param.required:
                raise BundleError(f"'{path}.{name}' fehlt.", code="missing", path=f"{path}.{name}")
            values[name] = _default(param)
        else:
            values[name] = _param(given[name], f"{path}.{name}", param)
    return values


def _rule(raw: object, path: str) -> tuple[str | None, dict[str, object]]:
    if raw is None:
        return None, {}
    if not isinstance(raw, Mapping):
        raise BundleError(f"'{path}' muss ein Objekt sein.", path=path)
    kind = parsing.as_choice(raw.get("kind"), f"{path}.kind", RULES_BY_ID)
    rest = {key: value for key, value in raw.items() if key != "kind"}
    return kind, _params(rest, path, RULES_BY_ID[kind])


def _field(raw: object, index: int) -> FieldSpec:
    path = f"fields[{index}]"
    data = parsing.as_object(raw, path, _FIELD_KEYS)
    kind = parsing.as_choice(data.get("type"), f"{path}.type", TYPES_BY_ID)
    rule, rule_params = _rule(data.get("rule"), f"{path}.rule")
    return FieldSpec(
        name=parsing.as_text(data.get("name"), f"{path}.name", max_length=80).strip(),
        type=kind,
        params=_params(data.get("params"), f"{path}.params", TYPES_BY_ID[kind]),
        empty_share=parsing.as_decimal(
            data.get("empty_share", 0), f"{path}.empty_share", Decimal(0), Decimal(1)
        ),
        rule=rule,
        rule_params=rule_params,
    )


def _dependency_order(fields: tuple[FieldSpec, ...]) -> tuple[FieldSpec, ...]:
    by_name = {field.name: field for field in fields}
    done: list[FieldSpec] = []
    state: dict[str, int] = {}

    def visit(field: FieldSpec) -> None:
        if state.get(field.name) == 2:
            return
        if state.get(field.name) == 1:
            raise BundleError(
                f"Die Spalte '{field.name}' hängt im Kreis von sich selbst ab.",
                code="cycle",
                path=field.name,
            )
        state[field.name] = 1
        for name in field.references:
            visit(by_name[name])
        state[field.name] = 2
        done.append(field)

    for field in fields:
        visit(field)
    return tuple(done)


def _check_fields(fields: tuple[FieldSpec, ...]) -> None:
    names = [field.name for field in fields]
    for index, field in enumerate(fields):
        path = f"fields[{index}]"
        if names.count(field.name) > 1:
            raise BundleError(
                f"Der Spaltenname '{field.name}' kommt mehrfach vor.", code="duplicate", path=path
            )
        for name in field.references:
            if name not in names or name == field.name:
                raise BundleError(
                    f"Die Spalte '{field.name}' verweist auf die unbekannte Spalte '{name}'.",
                    code="unknown_field",
                    path=path,
                )
        if field.rule == "sum_to" and field.type != "amount":
            raise BundleError(
                "Die Summenbindung gilt nur für Spalten des Typs Betrag.",
                code="rule_not_applicable",
                path=f"{path}.rule",
            )
    _dependency_order(fields)


def _run(raw: object, limits: RecipeLimits) -> tuple[int, date, int, str]:
    run = parsing.as_object(raw, "run", _RUN_KEYS)
    for key in ("seed", "base_date", "rows"):
        if key not in run:
            raise BundleError(f"'run.{key}' fehlt.", code="missing", path=f"run.{key}")
    return (
        parsing.as_int(run["seed"], "run.seed", 0, 2**31 - 1),
        parsing.as_date(run["base_date"], "run.base_date"),
        parsing.as_int(run["rows"], "run.rows", 1, limits.max_rows),
        parsing.as_choice(run.get("country", "DE"), "run.country", COUNTRY_CHOICES),
    )


def _written_by(raw: object) -> str:
    if raw is None:
        return ""
    data = parsing.as_object(raw, "generator", ("package", "version"))
    package = parsing.as_text(data.get("package", ""), "generator.package", empty=True)
    version = parsing.as_text(
        data.get("version", ""), "generator.version", max_length=40, empty=True
    )
    return f"{package} {version}".strip()


def parse_recipe(raw: object, limits: RecipeLimits | None = None) -> Recipe:
    """Strictly read a recipe; raises :class:`BundleError` naming the offending path."""
    limits = limits or RecipeLimits()
    data = parsing.as_object(raw, "recipe", _RECIPE_KEYS)
    if data.get("format") != FORMAT or data.get("format_version") != FORMAT_VERSION:
        raise BundleError(
            f"Die Datei ist kein Rezept im Format {FORMAT}, Fassung {FORMAT_VERSION}.",
            code="unknown_format",
            path="format",
        )
    if data.get("marking", MARKING) != MARKING:
        raise BundleError(f"'marking' muss {MARKING} lauten.", path="marking")
    entries = parsing.as_list(data.get("fields"), "fields", limits.max_fields, minimum=1)
    fields = tuple(_field(entry, index) for index, entry in enumerate(entries))
    _check_fields(fields)
    seed, base_date, rows, country = _run(data.get("run"), limits)
    derived = data.get("derived_from")
    return Recipe(
        title=parsing.as_text(data.get("title", "Eigene Tabelle"), "title", max_length=120),
        derived_from=None
        if derived is None
        else parsing.as_text(derived, "derived_from", max_length=20),
        seed=seed,
        base_date=base_date,
        rows=rows,
        country=country,
        fields=fields,
        written_by=_written_by(data.get("generator")),
    )
