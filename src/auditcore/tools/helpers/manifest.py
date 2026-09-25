"""The application manifest ``.auditcore/helpers.json``.

It names which app function fulfils which contract, which paths the scanner
ignores and which rules are switched off (always with a reason)::

    {
      "schema_version": 1,
      "app": "regulierung",
      "python": "backend/.venv/bin/python",
      "scan": {"exclude": ["frontend/src/generated/**"]},
      "lint": {"disable": {"HC-CSV-02": "Export nur für interne Weiterverarbeitung"}},
      "bindings": [
        {"contract": "parse-number", "language": "ts",
         "module": "frontend/src/lib/numberFormat.ts", "export": "parseNumberDe",
         "args": ["text"], "select": {"mode": "de"}}
      ]
    }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from auditcore.tools.helpers.model import (
    PYTHON,
    TYPESCRIPT,
    HelperToolError,
    as_dict,
    as_list,
    as_str,
    read_json,
    str_list,
)

DEFAULT_MANIFEST = Path(".auditcore") / "helpers.json"
DEFAULT_BASELINE = Path(".auditcore") / "helpers-baseline.json"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Binding:
    """One app function bound to a contract."""

    id: str
    contract: str
    language: str
    module: str
    export: str
    args: tuple[object, ...] = ()
    select: dict[str, object] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    exclude_tags: tuple[str, ...] = ()
    skip: dict[str, str] = field(default_factory=dict)
    result_path: str = ""
    python_path: tuple[str, ...] = ()
    python: str = ""
    cwd: str = ""


@dataclass(frozen=True)
class Manifest:
    """Parsed manifest (an absent file yields the empty manifest)."""

    app: str = ""
    python: str = ""
    excludes: tuple[str, ...] = ()
    disabled_rules: dict[str, str] = field(default_factory=dict)
    bindings: tuple[Binding, ...] = ()
    path: Path | None = None


def _binding(entry: dict[str, object], index: int) -> Binding:
    contract = as_str(entry.get("contract"))
    language = as_str(entry.get("language"))
    export = as_str(entry.get("export"))
    if language not in (PYTHON, TYPESCRIPT):
        raise HelperToolError(f"Bindung {index}: language muss 'ts' oder 'python' sein")
    if not (contract and export and as_str(entry.get("module"))):
        raise HelperToolError(f"Bindung {index}: contract, module und export sind Pflicht")
    skip = {str(k): as_str(v) for k, v in as_dict(entry.get("skip")).items()}
    if any(not reason.strip() for reason in skip.values()):
        raise HelperToolError(f"Bindung {index}: jeder übersprungene Fall braucht eine Begründung")
    return Binding(
        id=as_str(entry.get("id")) or f"{contract}:{export}",
        contract=contract,
        language=language,
        module=as_str(entry.get("module")),
        export=export,
        args=tuple(as_list(entry.get("args"))),
        select=as_dict(entry.get("select")),
        tags=tuple(str_list(entry.get("tags"))),
        exclude_tags=tuple(str_list(entry.get("exclude_tags"))),
        skip=skip,
        result_path=as_str(entry.get("result_path")),
        python_path=tuple(str_list(entry.get("python_path"))),
        python=as_str(entry.get("python")),
        cwd=as_str(entry.get("cwd")),
    )


def load_manifest(path: Path) -> Manifest:
    """Read and validate a manifest; a missing file is the empty manifest."""
    if not path.is_file():
        return Manifest()
    data = as_dict(read_json(path))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise HelperToolError(f"{path}: schema_version {SCHEMA_VERSION} erwartet")
    disabled = {
        str(k): as_str(v) for k, v in as_dict(as_dict(data.get("lint")).get("disable")).items()
    }
    if any(not reason.strip() for reason in disabled.values()):
        raise HelperToolError(f"{path}: abgeschaltete Regeln brauchen eine Begründung")
    bindings = tuple(
        _binding(as_dict(item), i) for i, item in enumerate(as_list(data.get("bindings")))
    )
    ids = [binding.id for binding in bindings]
    if len(ids) != len(set(ids)):
        raise HelperToolError(f"{path}: doppelte Bindungs-IDs (Feld id setzen)")
    return Manifest(
        app=as_str(data.get("app")),
        python=as_str(data.get("python")),
        excludes=tuple(str_list(as_dict(data.get("scan")).get("exclude"))),
        disabled_rules=disabled,
        bindings=bindings,
        path=path,
    )
