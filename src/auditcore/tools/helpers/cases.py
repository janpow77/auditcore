"""Load the shared contract cases (``contracts/common-cases``) and their decisions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from auditcore.tools.helpers.model import (
    HelperToolError,
    as_dict,
    as_list,
    as_str,
    read_json,
    str_list,
)

CASES_ENV = "AUDITCORE_HELPER_CASES"
CASES_RELATIVE = Path("contracts") / "common-cases"
DECISIONS_FILE = "decisions.json"
NON_CONTRACT_FILES = frozenset({DECISIONS_FILE, "schema.json"})
RESULT_KINDS = frozenset({"decimal", "text", "boolean", "text-contains", "csv"})


@dataclass(frozen=True)
class Case:
    """One contract case with decisions already resolved."""

    id: str
    input: dict[str, object]
    expect: dict[str, object]
    tags: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    note: str = ""

    def selected(self, select: dict[str, object], tags: list[str], exclude_tags: list[str]) -> bool:
        """True when the case matches the input filter and tag filters of a binding."""
        if any(self.input.get(key) != value for key, value in select.items()):
            return False
        if tags and not set(tags) & set(self.tags):
            return False
        return not set(exclude_tags) & set(self.tags)


@dataclass(frozen=True)
class Contract:
    """A versioned contract with its cases."""

    id: str
    version: str
    status: str
    title: str
    languages: tuple[str, ...]
    params: tuple[str, ...]
    result: str
    cases: tuple[Case, ...]


def resolve(value: object, decisions: dict[str, object]) -> object:
    """Replace ``{"$decision": key}`` markers by the central decision values."""
    if isinstance(value, list):
        return [resolve(item, decisions) for item in value]
    if isinstance(value, dict):
        key = value.get("$decision")
        if isinstance(key, str) and len(value) == 1:
            if key not in decisions:
                raise HelperToolError(f"Unbekannte Festlegung: {key}")
            return decisions[key]
        return {str(k): resolve(item, decisions) for k, item in value.items()}
    return value


def _case(entry: dict[str, object], decisions: dict[str, object]) -> Case:
    return Case(
        id=as_str(entry.get("id")),
        input=as_dict(resolve(entry.get("input"), decisions)),
        expect=as_dict(resolve(entry.get("expect"), decisions)),
        tags=tuple(str_list(entry.get("tags"))),
        languages=tuple(str_list(entry.get("languages"))),
        note=as_str(entry.get("note")),
    )


def _contract(path: Path, decisions: dict[str, object]) -> Contract:
    data = as_dict(read_json(path))
    result = as_str(data.get("result"))
    if result not in RESULT_KINDS:
        raise HelperToolError(f"{path.name}: unbekannte Ergebnisart {result!r}")
    cases = tuple(_case(as_dict(item), decisions) for item in as_list(data.get("cases")))
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise HelperToolError(f"{path.name}: doppelte Fall-IDs")
    return Contract(
        id=as_str(data.get("contract")),
        version=as_str(data.get("version")),
        status=as_str(data.get("status")),
        title=as_str(data.get("title")),
        languages=tuple(str_list(data.get("languages"))),
        params=tuple(str_list(data.get("params"))),
        result=result,
        cases=cases,
    )


@dataclass(frozen=True)
class CaseLibrary:
    """All contracts of a cases directory plus the decisions they use."""

    directory: Path
    decisions: dict[str, object]
    contracts: dict[str, Contract]

    def contract(self, name: str) -> Contract:
        """Return a contract by id (raises for unknown ids)."""
        if name not in self.contracts:
            raise HelperToolError(f"Unbekannter Vertrag: {name}")
        return self.contracts[name]

    @property
    def probe_timezone(self) -> str:
        """Process time zone for executing helpers (reveals missing ``timeZone``)."""
        return as_str(self.decisions.get("probe_timezone"), "America/New_York")


def find_cases_dir(explicit: Path | None = None) -> Path:
    """Locate the cases directory: argument, environment, or a surrounding checkout."""
    if explicit is not None:
        return explicit
    configured = os.environ.get(CASES_ENV)
    if configured:
        return Path(configured)
    for parent in Path(__file__).resolve().parents:
        candidate = parent / CASES_RELATIVE
        if (candidate / DECISIONS_FILE).is_file():
            return candidate
    raise HelperToolError(
        "Vertragsfälle nicht gefunden: --cases <auditcore>/contracts/common-cases angeben "
        f"oder {CASES_ENV} setzen"
    )


def load_cases(directory: Path) -> CaseLibrary:
    """Load every contract file of ``directory``."""
    decisions_path = directory / DECISIONS_FILE
    if not decisions_path.is_file():
        raise HelperToolError(f"{decisions_path} fehlt")
    decisions = as_dict(as_dict(read_json(decisions_path)).get("decisions"))
    contracts = {}
    for path in sorted(directory.glob("*.json")):
        if path.name not in NON_CONTRACT_FILES:
            contract = _contract(path, decisions)
            contracts[contract.id] = contract
    return CaseLibrary(directory, decisions, contracts)
