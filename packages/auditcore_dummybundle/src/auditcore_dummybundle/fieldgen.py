"""Value generators of the free table, one per field type, working column by column.

Every column draws from its own random stream (seed plus column name), so
adding or changing one column never shifts the values of another.
"""

from __future__ import annotations

import re
import string
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from random import Random
from typing import cast

from auditcore_dummybundle import catalogs as cat
from auditcore_dummybundle import identifiers
from auditcore_dummybundle.amounts import CENT, quantize
from auditcore_dummybundle.errors import BundleError
from auditcore_dummybundle.model import Cell
from auditcore_dummybundle.recipe import FieldSpec, Recipe
from auditcore_dummybundle.seeds import pick_cents

_PLACEHOLDER = re.compile(r"\{([^{}]*)\}")
_KNOWN = re.compile(r"JJJJ|JJ|MM|N{1,12}|Z{1,12}|A{1,12}")
_BOOLEAN = {"ja_nein": ("Ja", "Nein"), "true_false": ("wahr", "falsch"), "one_zero": ("1", "0")}


@dataclass
class Context:
    """Rows shared by all columns: country and coherent location per row."""

    recipe: Recipe
    countries: list[str]
    locations: list[tuple[str, str, str]]
    columns: dict[str, list[Cell]] = field(default_factory=dict)

    @property
    def rows(self) -> int:
        """Number of rows of the table."""
        return self.recipe.rows


Generator = Callable[[Context, FieldSpec, Random], list[Cell]]


def _fail(spec: FieldSpec, message: str, code: str = "invalid_input") -> BundleError:
    return BundleError(f"Spalte '{spec.name}': {message}", code=code, path=spec.name)


def _numbers(ctx: Context, spec: FieldSpec, name: str) -> list[Decimal | None]:
    values: list[Decimal | None] = []
    for cell in ctx.columns[name]:
        if cell is None:
            values.append(None)
        elif isinstance(cell, (Decimal, int)) and not isinstance(cell, bool):
            values.append(Decimal(cell))
        else:
            raise _fail(spec, f"Die Bezugsspalte '{name}' enthält keine Zahlen.", "not_numeric")
    return values


def _dates(ctx: Context, spec: FieldSpec, name: str) -> list[date | None]:
    values: list[date | None] = []
    for cell in ctx.columns[name]:
        if cell is not None and not isinstance(cell, date):
            raise _fail(spec, f"Die Bezugsspalte '{name}' enthält kein Datum.", "not_a_date")
        values.append(cell)
    return values


def _sequence(ctx: Context, spec: FieldSpec, _: Random) -> list[Cell]:
    start, step = cast(int, spec.params["start"]), cast(int, spec.params["step"])
    return [start + index * step for index in range(ctx.rows)]


def _fill(token: str, rng: Random, when: date, index: int) -> str:
    if token == "JJJJ":
        return f"{when.year:04d}"
    if token == "JJ":
        return f"{when.year % 100:02d}"
    if token == "MM":
        return f"{when.month:02d}"
    if token[0] == "N":
        return f"{index + 1:0{len(token)}d}"
    alphabet = string.digits if token[0] == "Z" else string.ascii_uppercase
    return "".join(alphabet[rng.randrange(len(alphabet))] for _ in token)


def _pattern(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    pattern = str(spec.params["pattern"])
    for token in _PLACEHOLDER.findall(pattern):
        if not _KNOWN.fullmatch(token):
            raise _fail(
                spec, f"Unbekannter Platzhalter {{{token}}} im Muster.", "unknown_placeholder"
            )
    source = spec.params["date_field"]
    dates = _dates(ctx, spec, source) if isinstance(source, str) else [None] * ctx.rows
    return [
        _render(pattern, rng, dates[index] or ctx.recipe.base_date, index)
        for index in range(ctx.rows)
    ]


def _render(pattern: str, rng: Random, when: date, index: int) -> str:
    def fill(match: re.Match[str]) -> str:
        return _fill(match.group(1), rng, when, index)

    return _PLACEHOLDER.sub(fill, pattern)


def _person(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    if spec.params["source"] == "role":
        return [cat.role_name(rng) for _ in range(ctx.rows)]
    part = {"first": 0, "last": 1}.get(str(spec.params["part"]))
    names = [cat.person_name(rng, country) for country in ctx.countries]
    return [name if part is None else name.split(" ")[part] for name in names]


def _company(ctx: Context, _: FieldSpec, rng: Random) -> list[Cell]:
    return [cat.company_name(rng) for _ in range(ctx.rows)]


def _address(ctx: Context, spec: FieldSpec, _: Random) -> list[Cell]:
    part = str(spec.params["part"])
    names = cat.catalogs().country_names
    cells: list[Cell] = []
    for country, (street, postal_code, city) in zip(ctx.countries, ctx.locations, strict=True):
        parts = {
            "full": f"{street}, {postal_code} {city}",
            "street": street,
            "postal_code": postal_code,
            "city": city,
            "country": names[country],
        }
        cells.append(parts[part])
    return cells


def _nuts(ctx: Context, _: FieldSpec, __: Random) -> list[Cell]:
    return [cat.catalogs().nuts3[city] for _, _, city in ctx.locations]


def _email(ctx: Context, _: FieldSpec, rng: Random) -> list[Cell]:
    return [f"stelle{rng.randrange(10_000):04d}@example.org" for _ in range(ctx.rows)]


def _date(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    end = cast(date | None, spec.params["end"]) or ctx.recipe.base_date
    start = cast(date | None, spec.params["start"]) or end - timedelta(days=365)
    if start > end:
        raise _fail(spec, "Der Beginn liegt nach dem Ende.", "invalid_range")
    span = (end - start).days + 1
    return [start + timedelta(days=rng.randrange(span)) for _ in range(ctx.rows)]


def _date_offset(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    low, high = cast(int, spec.params["min_days"]), cast(int, spec.params["max_days"])
    if low > high:
        raise _fail(spec, "Der Mindestabstand übersteigt den Höchstabstand.", "invalid_range")
    cells: list[Cell] = []
    for reference in _dates(ctx, spec, str(spec.params["field"])):
        days = rng.randrange(low, high + 1)
        cells.append(None if reference is None else reference + timedelta(days=days))
    return cells


def _amount(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    low, high = cast(Decimal, spec.params["min"]), cast(Decimal, spec.params["max"])
    if low > high:
        raise _fail(spec, "Das Minimum übersteigt das Maximum.", "invalid_range")
    quantum = Decimal(1).scaleb(-cast(int, spec.params["decimals"]))
    skew = 3 if spec.params["distribution"] == "skewed" else 1
    low_units, high_units = int(low / quantum), int(high / quantum)
    return [
        Decimal(pick_cents(rng, low_units, max(low_units, high_units), skew=skew)) * quantum
        for _ in range(ctx.rows)
    ]


def _amount_factor(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    low = int(cast(Decimal, spec.params["min_factor"]) * 10_000)
    high = int(cast(Decimal, spec.params["max_factor"]) * 10_000)
    if low > high:
        raise _fail(spec, "Der kleinste Faktor übersteigt den größten.", "invalid_range")
    cells: list[Cell] = []
    for reference in _numbers(ctx, spec, str(spec.params["field"])):
        factor = Decimal(rng.randrange(low, high + 1)) / 10_000
        cells.append(None if reference is None else quantize(reference * factor))
    return cells


def _computed(ctx: Context, spec: FieldSpec, _: Random) -> list[Cell]:
    operation = str(spec.params["operation"])
    names = cast(tuple[str, ...], spec.params["fields"])
    if len(names) != (1 if operation == "rate" else 2):
        raise _fail(spec, "Die Rechenart passt nicht zur Zahl der Spalten.", "invalid_fields")
    left = _numbers(ctx, spec, names[0])
    rate = cast(Decimal, spec.params["rate"])
    right = [rate] * ctx.rows if operation == "rate" else _numbers(ctx, spec, names[1])
    cells: list[Cell] = []
    for a, b in zip(left, right, strict=True):
        if a is None or b is None:
            cells.append(None)
        elif operation == "sum":
            cells.append(quantize(a + b))
        elif operation == "difference":
            cells.append(quantize(a - b))
        else:
            cells.append(quantize(a * b))
    return cells


def _integer(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    low, high = cast(int, spec.params["min"]), cast(int, spec.params["max"])
    if low > high:
        raise _fail(spec, "Das Minimum übersteigt das Maximum.", "invalid_range")
    return [rng.randrange(low, high + 1) for _ in range(ctx.rows)]


def _decimal(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    quantum = Decimal(1).scaleb(-cast(int, spec.params["decimals"]))
    low = int(cast(Decimal, spec.params["min"]) / quantum)
    high = int(cast(Decimal, spec.params["max"]) / quantum)
    if low > high:
        raise _fail(spec, "Das Minimum übersteigt das Maximum.", "invalid_range")
    return [Decimal(rng.randrange(low, high + 1)) * quantum for _ in range(ctx.rows)]


def _choice(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    values = cast(tuple[tuple[str, int], ...], spec.params["values"])
    return [cat.weighted_pick(rng, values) for _ in range(ctx.rows)]


def _boolean(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    yes, no = _BOOLEAN[str(spec.params["style"])]
    threshold = int(cast(Decimal, spec.params["probability"]) * 1_000_000)
    return [yes if rng.randrange(1_000_000) < threshold else no for _ in range(ctx.rows)]


def _text(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    low, high = cast(int, spec.params["min_parts"]), cast(int, spec.params["max_parts"])
    if low > high:
        raise _fail(spec, "Das Minimum übersteigt das Maximum.", "invalid_range")
    return [cat.purpose_text(rng, low, high) for _ in range(ctx.rows)]


def _iban(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    valid = bool(spec.params["valid"])
    return [identifiers.iban(rng, country, valid=valid) for country in ctx.countries]


def _vat_id(ctx: Context, spec: FieldSpec, rng: Random) -> list[Cell]:
    valid = bool(spec.params["valid"])
    return [identifiers.vat_id(rng, country, valid=valid) for country in ctx.countries]


def _bic(ctx: Context, _: FieldSpec, __: Random) -> list[Cell]:
    return [identifiers.bic(country) for country in ctx.countries]


def _constant(ctx: Context, spec: FieldSpec, _: Random) -> list[Cell]:
    return [str(spec.params["value"]) or None] * ctx.rows


GENERATORS: dict[str, Generator] = {
    "sequence": _sequence,
    "pattern": _pattern,
    "person": _person,
    "company": _company,
    "address": _address,
    "nuts": _nuts,
    "email": _email,
    "date": _date,
    "date_offset": _date_offset,
    "amount": _amount,
    "amount_factor": _amount_factor,
    "computed": _computed,
    "integer": _integer,
    "decimal": _decimal,
    "choice": _choice,
    "boolean": _boolean,
    "text": _text,
    "iban": _iban,
    "bic": _bic,
    "vat_id": _vat_id,
    "constant": _constant,
}

#: Smallest unit the sum binding distributes.
SUM_QUANTUM = CENT
