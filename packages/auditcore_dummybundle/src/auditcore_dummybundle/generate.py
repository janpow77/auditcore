"""Entry points: tables for templates of one bundle, or for a free recipe."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from auditcore_dummybundle.anomalies import plant_anomalies
from auditcore_dummybundle.bundle import build_bundle
from auditcore_dummybundle.config import BundleConfig
from auditcore_dummybundle.errors import BundleError
from auditcore_dummybundle.model import MARKING, Budget, Column, Result, Table
from auditcore_dummybundle.recipe import Recipe
from auditcore_dummybundle.table import generate_table, recipe_document
from auditcore_dummybundle.templates import (
    Positions,
    Template,
    get_template,
    located,
    project,
)

PACKAGE = "auditcore_dummybundle"
VERSION = "0.1.0"
MARKING_COLUMN = "synthetisch"
_NOTICE = "Synthetische Testdaten ohne Bezug zu echten Vorhaben, Personen oder Unternehmen."
_INVALID_NOTE = (
    "IBAN und USt-IdNr. tragen eine gezielt verfehlte Prüfziffer und bestehen keine "
    "formale Prüfung."
)
_VALID_NOTE = (
    "IBAN und USt-IdNr. sind auf ausdrückliche Wahl formal gültig; sie können zufällig "
    "einer vergebenen Kennung entsprechen."
)


@dataclass(frozen=True)
class Options:
    """Output choices that do not change the generated values."""

    solution: bool = False
    marking_column: bool = False
    include_private: bool = False
    max_tables: int = 200


def _marked(table: Table) -> Table:
    columns = (*table.columns, Column(MARKING_COLUMN, "text"))
    rows = tuple((*row, MARKING) for row in table.rows)
    return Table(table.name, table.title, columns, rows, table.source)


def _meta(seed: int, base_date: str) -> dict[str, object]:
    return {
        "marking": MARKING,
        "notice": _NOTICE,
        "package": PACKAGE,
        "version": VERSION,
        "seed": seed,
        "base_date": base_date,
        "max_workers": 1,
    }


def _finish(tables: list[Table], options: Options) -> tuple[Table, ...]:
    if len(tables) > options.max_tables:
        raise BundleError(
            f"Die Auswahl ergäbe {len(tables)} Tabellen; zulässig sind {options.max_tables}. "
            "Bitte weniger Vorhaben oder Mittelabrufe wählen.",
            code="too_large",
            path="params.operations",
        )
    names = [table.name for table in tables]
    if len(set(names)) != len(names):
        raise BundleError("Tabellennamen sind nicht eindeutig.", code="duplicate", path="templates")
    return tuple(_marked(table) if options.marking_column else table for table in tables)


def _chosen(template_ids: Sequence[str], options: Options) -> list[Template]:
    if not template_ids:
        raise BundleError(
            "Mindestens eine Vorlage ist zu wählen.", code="missing", path="templates"
        )
    unique = list(dict.fromkeys(template_ids))
    return [get_template(item, include_private=options.include_private) for item in unique]


def generate_templates(
    config: BundleConfig,
    template_ids: Sequence[str],
    options: Options | None = None,
    budget: Budget | None = None,
) -> Result:
    """Build one bundle for ``config`` and project it into the chosen templates."""
    options = options or Options()
    chosen = _chosen(template_ids, options)
    bundle = build_bundle(config, budget)
    sources = frozenset(table.source for template in chosen for table in template.tables)
    plant_anomalies(bundle, sources)
    tables: list[Table] = []
    positions: Positions = {}
    for template in chosen:
        projected, found = project(bundle, template)
        tables.extend(projected)
        for key, value in found.items():
            positions.setdefault(key, []).extend(value)
    meta = _meta(config.seed, config.base_date.isoformat())
    meta.update(
        {
            "mode": "templates",
            "templates": [
                {
                    "id": t.id,
                    "title": t.title,
                    "version": t.version,
                    "status": t.status,
                    "content_hash": t.content_hash,
                }
                for t in chosen
            ],
            "params": config.as_dict(),
            "identifiers": _VALID_NOTE if config.identifiers_valid else _INVALID_NOTE,
            "anomalies": {
                "selected": list(config.anomalies),
                "planted": len(bundle.solution),
                "not_applicable": list(bundle.skipped_anomalies),
            },
        }
    )
    solution = located(bundle, positions) if options.solution else None
    return Result(_finish(tables, options), meta, solution)


def generate_recipe(
    recipe: Recipe, options: Options | None = None, budget: Budget | None = None
) -> Result:
    """Generate the free table of ``recipe``."""
    options = options or Options()
    table = generate_table(recipe, budget)
    meta = _meta(recipe.seed, recipe.base_date.isoformat())
    valid = any(spec.params.get("valid") is True for spec in recipe.fields)
    meta.update(
        {
            "mode": "recipe",
            "title": recipe.title,
            "derived_from": recipe.derived_from,
            "recipe": recipe_document(recipe, VERSION),
            "identifiers": _VALID_NOTE if valid else _INVALID_NOTE,
        }
    )
    return Result(_finish([table], options), meta, None)
