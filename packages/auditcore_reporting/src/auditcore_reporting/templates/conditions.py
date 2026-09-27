"""Conditions of text blocks and sections as JSON data – never evaluated as code.

A condition is either a name (a named condition of the template or, failing
that, a data path: a boolean counts as itself, anything else as "filled") or
an object with exactly one operator::

    {"filled": "feststellungen"}            {"empty": "bemerkung"}
    {"equals": ["ergebnis", "ohne"]}        {"not_equals": ["ergebnis", "ohne"]}
    {"in": ["fonds", ["EFRE", "ESF+"]]}     {"greater": ["betrag", 0]}
    {"less": [...]}  {"at_least": [...]}    {"at_most": [...]}
    {"all": [c1, c2]}  {"any": [c1, c2]}    {"not": c}
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence

from .errors import TemplateError
from .values import is_filled, lookup, valid_path

Condition = str | Mapping[str, object]
_UNARY = ("filled", "empty")
_COMPARE = ("equals", "not_equals", "in", "greater", "less", "at_least", "at_most")
_GROUP = ("all", "any")
OPERATORS = (*_UNARY, *_COMPARE, *_GROUP, "not")
MAX_DEPTH = 16


def _operator(spec: Mapping[str, object], where: str) -> tuple[str, object]:
    if len(spec) != 1:
        raise TemplateError(f"{where}: Bedingung braucht genau einen Operator ({spec!r}).")
    name, argument = next(iter(spec.items()))
    if name not in OPERATORS:
        raise TemplateError(f"{where}: unbekannter Operator {name!r}; erlaubt: {OPERATORS}.")
    return name, argument


def _comparison(name: str, argument: object, where: str) -> tuple[str, object]:
    if (
        not isinstance(argument, (list, tuple))
        or len(argument) != 2
        or not isinstance(argument[0], str)
    ):
        raise TemplateError(f"{where}: {name!r} erwartet [Datenpfad, Wert].")
    path, value = argument
    if name == "in" and not isinstance(value, (list, tuple)):
        raise TemplateError(f"{where}: 'in' erwartet eine Werteliste.")
    numeric = name in ("greater", "less", "at_least", "at_most")
    if numeric and (isinstance(value, bool) or not isinstance(value, (int, float))):
        raise TemplateError(f"{where}: {name!r} vergleicht nur mit Zahlen.")
    return path, value


def _named_paths(
    spec: str, named: Mapping[str, Condition], where: str, depth: int
) -> Iterator[str]:
    if spec in named:
        yield from condition_paths(named[spec], named, f"{where} → {spec}", depth + 1)
    elif valid_path(spec):
        yield spec
    else:
        raise TemplateError(f"{where}: {spec!r} ist weder benannte Bedingung noch Datenpfad.")


def _operator_paths(
    name: str, argument: object, named: Mapping[str, Condition], where: str, depth: int
) -> Iterator[str]:
    if name in _UNARY:
        if not isinstance(argument, str) or not valid_path(argument):
            raise TemplateError(f"{where}: {name!r} erwartet einen Datenpfad.")
        yield argument
    elif name in _COMPARE:
        yield _comparison(name, argument, where)[0]
    elif name == "not":
        yield from condition_paths(_child(argument, where), named, where, depth + 1)
    else:
        if not isinstance(argument, (list, tuple)) or not argument:
            raise TemplateError(f"{where}: {name!r} erwartet eine nicht leere Liste.")
        for child in argument:
            yield from condition_paths(_child(child, where), named, where, depth + 1)


def condition_paths(
    spec: Condition, named: Mapping[str, Condition], where: str, depth: int = 0
) -> Iterator[str]:
    """Data paths a condition reads; raises :class:`TemplateError` for malformed ones."""
    if depth > MAX_DEPTH:
        raise TemplateError(f"{where}: Bedingungen zu tief verschachtelt oder zyklisch.")
    if isinstance(spec, str):
        yield from _named_paths(spec, named, where, depth)
        return
    if not isinstance(spec, Mapping):
        raise TemplateError(f"{where}: Bedingung muss Name oder Objekt sein.")
    name, argument = _operator(spec, where)
    yield from _operator_paths(name, argument, named, where, depth)


def _child(value: object, where: str) -> Condition:
    if isinstance(value, (str, Mapping)):
        return value
    raise TemplateError(f"{where}: Bedingung muss Name oder Objekt sein.")


def _items(value: object) -> list[object]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _compare(name: str, left: object, right: object) -> bool:
    if name == "equals":
        return left == right
    if name == "not_equals":
        return left != right
    if name == "in":
        return isinstance(right, Sequence) and left in right
    if isinstance(left, bool) or not isinstance(left, (int, float)):
        return False
    number = float(right) if isinstance(right, (int, float)) else 0.0
    checks: dict[str, Callable[[float], bool]] = {
        "greater": lambda value: value > number,
        "less": lambda value: value < number,
        "at_least": lambda value: value >= number,
        "at_most": lambda value: value <= number,
    }
    return checks[name](float(left))


def evaluate(spec: Condition, values: Mapping[str, object], named: Mapping[str, Condition]) -> bool:
    """Truth of a (validated) condition for ``values``."""
    if isinstance(spec, str):
        if spec in named:
            return evaluate(named[spec], values, named)
        value = lookup(values, spec)
        return value if isinstance(value, bool) else is_filled(value)
    name, argument = next(iter(spec.items()))
    if name in _UNARY:
        filled = is_filled(lookup(values, str(argument)))
        return filled if name == "filled" else not filled
    if name == "not":
        return not evaluate(_child(argument, "Bedingung"), values, named)
    if name in _GROUP:
        children = [_child(child, "Bedingung") for child in _items(argument)]
        results = (evaluate(child, values, named) for child in children)
        return all(results) if name == "all" else any(results)
    path, expected = _comparison(name, argument, "Bedingung")
    return _compare(name, lookup(values, path), expected)
