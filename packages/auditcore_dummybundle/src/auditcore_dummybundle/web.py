"""REST contract ``dummybundle_ui/1`` (framework-free): catalogue, generation, recipes.

Hosts wrap these functions in their own routes. A request carries only a
column definition and run parameters, never data of the caller. Nothing is
stored; equal requests give equal replies.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, fields
from importlib.resources import files
from typing import TypeVar, cast

from auditcore_common import rest

from auditcore_dummybundle import parsing
from auditcore_dummybundle.anomalies import ANOMALIES, anomaly_codes
from auditcore_dummybundle.checks import CHECK_TITLES
from auditcore_dummybundle.config import (
    COUNTRY_CHOICES,
    FUNDS,
    PERSON_MODES,
    VAT_MODES,
    BundleConfig,
    BundleLimits,
    parse_config,
)
from auditcore_dummybundle.errors import BundleError
from auditcore_dummybundle.export import document
from auditcore_dummybundle.fieldtypes import FIELD_TYPES, RULES, FieldType
from auditcore_dummybundle.generate import (
    MARKING_COLUMN,
    PACKAGE,
    VERSION,
    Options,
    generate_recipe,
    generate_templates,
)
from auditcore_dummybundle.model import MARKING, Budget
from auditcore_dummybundle.recipe import RecipeLimits, parse_recipe
from auditcore_dummybundle.table import recipe_document
from auditcore_dummybundle.templates import Template, get_template, template_recipe, templates

CONTRACT = "dummybundle_ui/1"
LIBRARY = f"{PACKAGE} {VERSION}"
Json = dict[str, object]
T = TypeVar("T")


@dataclass(frozen=True)
class Limits:
    """Request limits of the contract (reported in the catalogue)."""

    max_operations: int = 50
    max_claims: int = 6
    max_receipts: int = 30
    max_corrections: int = 30
    max_rows: int = 5_000
    max_fields: int = 60
    max_tables: int = 60
    preview_rows: int = 20
    max_seconds: float = 20.0
    max_body_bytes: int = 256 * 1024
    include_private: bool = False

    @property
    def bundle(self) -> BundleLimits:
        """Limits of the bundle parameters."""
        return BundleLimits(
            self.max_operations, self.max_claims, self.max_receipts, self.max_corrections
        )

    @property
    def recipe(self) -> RecipeLimits:
        """Limits of a free table."""
        return RecipeLimits(self.max_rows, self.max_fields)


class ContractError(rest.ContractError):
    """Request does not satisfy the ``dummybundle_ui/1`` contract."""

    def __init__(
        self, message: str, *, status: int = 422, code: str = "invalid_input", path: str = ""
    ) -> None:
        super().__init__(message, status=status, code=code)
        self.path = path

    def to_dict(self) -> dict[str, object]:
        """JSON error body with the path of the offending entry."""
        return {"error": {"code": self.code, "message": str(self), "path": self.path}}


def _guard(action: Callable[[], T]) -> T:
    try:
        return action()
    except BundleError as exc:
        status = {"timeout": 503, "too_large": 413}.get(exc.code, 422)
        raise ContractError(str(exc), status=status, code=exc.code, path=exc.path) from exc


def _type_entry(kind: FieldType) -> Json:
    return {
        "id": kind.id,
        "label": kind.label,
        "cell": kind.cell,
        "note": kind.note,
        "params": [
            {
                "name": p.name, "kind": p.kind, "label": p.label, "default": p.default,
                "min": p.low, "max": p.high, "options": list(p.options), "required": p.required,
            }
            for p in kind.params
        ],
    }  # fmt: skip


def _template_entry(template: Template) -> Json:
    return {
        "id": template.id,
        "title": template.title,
        "purpose": template.purpose,
        "legal_basis": template.legal_basis,
        "version": template.version,
        "status": template.status,
        "content_hash": template.content_hash,
        "release": dict(template.release),
        "public": template.public,
        "column_count": sum(len(table.columns) for table in template.tables),
        "tables": [
            {
                "name": table.name,
                "title": table.title,
                "source": table.source,
                "per_claim": table.split_by is not None,
                "columns": [
                    {"header": c.header, "kind": c.kind, "note": c.note} for c in table.columns
                ],
            }
            for table in template.tables
        ],
        "free_start": template.free_table is not None,
        "sources": list(template.sources),
        "open_points": list(template.open_points),
    }


def _bundles(visible: set[str]) -> list[Json]:
    raw = json.loads(
        files("auditcore_dummybundle").joinpath("data/bundles.json").read_text(encoding="utf-8")
    )
    entries = cast(list[Json], raw["bundles"])
    return [b for b in entries if set(cast(list[str], b["templates"])) <= visible]


def _parameters(limits: Limits) -> list[Json]:
    defaults = BundleConfig(seed=0, base_date=parsing.as_date("2026-01-01", "base_date")).as_dict()
    ranges: dict[str, tuple[object, object]] = {
        "operations": (1, limits.max_operations),
        "claims_min": (1, limits.max_claims),
        "claims_max": (1, limits.max_claims),
        "receipts_min": (1, limits.max_receipts),
        "receipts_max": (1, limits.max_receipts),
        "priorities": (1, 6),
        "payment_applications": (1, 6),
        "corrections": (0, limits.max_corrections),
        "prior_year_withdrawals": (0, 5),
        "seed": (0, 2**31 - 1),
    }
    options: dict[str, tuple[str, ...]] = {
        "country": COUNTRY_CHOICES,
        "fund": FUNDS,
        "vat_deduction": VAT_MODES,
        "person_names": PERSON_MODES,
        "anomalies": anomaly_codes(),
    }
    result: list[Json] = []
    for item in fields(BundleConfig):
        low, high = ranges.get(item.name, (None, None))
        result.append(
            {
                "name": item.name,
                "default": None if item.name in ("seed", "base_date") else defaults[item.name],
                "min": low,
                "max": high,
                "options": list(options.get(item.name, ())),
                "required": item.name in ("seed", "base_date"),
            }
        )
    return result


def catalogue(limits: Limits | None = None) -> Json:
    """``GET /catalogue``: templates, bundles, field types, rules, anomalies, limits."""
    limits = limits or Limits()
    shown = [t for t in templates().values() if t.public or limits.include_private]
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "marking": MARKING,
        "marking_column": MARKING_COLUMN,
        "templates": [_template_entry(template) for template in shown],
        "bundles": _bundles({template.id for template in shown}),
        "parameters": _parameters(limits),
        "field_types": [_type_entry(kind) for kind in FIELD_TYPES],
        "rules": [_type_entry(kind) for kind in RULES],
        "anomalies": [
            {
                "code": kind.code,
                "title": kind.title,
                "description": kind.description,
                "table": kind.table,
                "affected_checks": list(kind.checks),
            }
            for kind in ANOMALIES
        ],  # fmt: skip
        "checks": [{"number": n, "title": title} for n, title in CHECK_TITLES.items()],
        "limits": {k: v for k, v in asdict(limits).items() if k != "include_private"},
    }


def _options(raw: object, limits: Limits) -> tuple[Options, int | None]:
    data = parsing.as_object(
        {} if raw is None else raw, "options", ("solution", "marking_column", "preview")
    )
    options = Options(
        solution=parsing.as_bool(data.get("solution", False), "options.solution"),
        marking_column=parsing.as_bool(data.get("marking_column", False), "options.marking_column"),
        include_private=limits.include_private,
        max_tables=limits.max_tables,
    )
    preview = parsing.as_bool(data.get("preview", False), "options.preview")
    return options, limits.preview_rows if preview else None


def _body(payload: object, allowed: tuple[str, ...]) -> Mapping[str, object]:
    return parsing.as_object(payload, "Anfrage", allowed)


def generate(payload: object, limits: Limits | None = None) -> Json:
    """``POST /generate``: tables for templates of one bundle or for a recipe."""
    limits = limits or Limits()

    def action() -> Json:
        body = _body(payload, ("mode", "templates", "params", "recipe", "options"))
        mode = parsing.as_choice(body.get("mode"), "mode", ("templates", "recipe"))
        options, preview = _options(body.get("options"), limits)
        budget = Budget(limits.max_seconds)
        if mode == "recipe":
            recipe = parse_recipe(body.get("recipe"), limits.recipe)
            return document(generate_recipe(recipe, options, budget), preview)
        ids = parsing.as_list(body.get("templates"), "templates", 20, minimum=1)
        names = [parsing.as_text(item, "templates", max_length=20) for item in ids]
        config = parse_config(
            body.get("params"), anomaly_codes=anomaly_codes(), limits=limits.bundle
        )
        return document(generate_templates(config, names, options, budget), preview)

    return _guard(action)


def recipe_from_template(payload: object, limits: Limits | None = None) -> Json:
    """``POST /recipe/from-template``: a template's list as recipe to adapt."""
    limits = limits or Limits()

    def action() -> Json:
        body = _body(payload, ("template", "run"))
        template = get_template(
            parsing.as_text(body.get("template"), "template", max_length=20),
            include_private=limits.include_private,
        )
        run = parsing.as_object(body.get("run"), "run", ("seed", "base_date", "rows", "country"))
        raw = template_recipe(
            template,
            seed=parsing.as_int(run.get("seed"), "run.seed", 0, 2**31 - 1),
            base_date=parsing.as_date(run.get("base_date"), "run.base_date"),
            rows=parsing.as_int(run.get("rows", 50), "run.rows", 1, limits.max_rows),
            country=parsing.as_choice(run.get("country", "DE"), "run.country", COUNTRY_CHOICES),
            version=VERSION,
        )
        return {"recipe": recipe_document(parse_recipe(raw, limits.recipe), VERSION)}

    return _guard(action)


def check_recipe(payload: object, limits: Limits | None = None) -> Json:
    """``POST /recipe/check``: strict check, normalised recipe, notices and a preview."""
    limits = limits or Limits()

    def action() -> Json:
        body = _body(payload, ("recipe",))
        recipe = parse_recipe(body.get("recipe"), limits.recipe)
        notices = []
        if recipe.written_by and recipe.written_by != LIBRARY:
            notices.append(
                f"Das Rezept stammt von {recipe.written_by}; diese Fassung ist {LIBRARY}. "
                "Gleiche Daten sind nur mit derselben Paketversion zugesagt."
            )
        result = generate_recipe(recipe, Options(), Budget(limits.max_seconds))
        return {
            "recipe": recipe_document(recipe, VERSION),
            "notices": notices,
            "preview": document(result, limits.preview_rows),
        }

    return _guard(action)
