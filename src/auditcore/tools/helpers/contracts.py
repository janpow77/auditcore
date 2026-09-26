"""``contracts``: run the shared contract cases against the helpers an app names."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from auditcore.tools.helpers.cases import Case, CaseLibrary, Contract
from auditcore.tools.helpers.compare import Outcome, compare, show
from auditcore.tools.helpers.execute import RunResult, package_root, run_python, run_typescript
from auditcore.tools.helpers.manifest import Binding, Manifest
from auditcore.tools.helpers.model import PYTHON, as_dict, as_str

PASS, FAIL, SKIP = "bestanden", "verletzt", "übersprungen"
LOAD_CASE = "laden"


@dataclass(frozen=True)
class CaseResult:
    """Result of one case for one binding."""

    case: str
    status: str
    detail: str


@dataclass
class BindingRun:
    """All case results of one binding."""

    binding: Binding
    contract: Contract | None
    results: list[CaseResult] = field(default_factory=list)
    load_error: str = ""

    @property
    def violations(self) -> list[CaseResult]:
        """Failed cases (a load error counts as one violation)."""
        failed = [result for result in self.results if result.status == FAIL]
        if self.load_error:
            failed.insert(0, CaseResult(LOAD_CASE, FAIL, self.load_error))
        return failed

    def keys(self) -> list[str]:
        """Ratchet keys of all violations."""
        return [f"contract|{self.binding.id}|{result.case}" for result in self.violations]

    def to_dict(self) -> dict[str, object]:
        """Serialize for the JSON report."""
        counts = {
            status: sum(r.status == status for r in self.results) for status in (PASS, FAIL, SKIP)
        }
        return {
            "binding": self.binding.id,
            "contract": self.binding.contract,
            "version": self.contract.version if self.contract else "",
            "language": self.binding.language,
            "function": f"{self.binding.module}:{self.binding.export}",
            "counts": counts,
            "load_error": self.load_error,
            "violations": [{"case": r.case, "detail": r.detail} for r in self.violations],
            "skipped": [
                {"case": r.case, "detail": r.detail} for r in self.results if r.status == SKIP
            ],
        }


def lookup(data: object, path: str) -> object:
    """Follow a dotted path through nested JSON objects."""
    current = data
    for part in path.split("."):
        current = as_dict(current).get(part)
    return current


def build_args(spec: tuple[object, ...], params: tuple[str, ...], case: Case) -> list[object]:
    """Map case input to positional arguments according to the binding's ``args``."""
    if not spec:
        return [case.input.get(name) for name in params]
    args: list[object] = []
    for item in spec:
        entry = as_dict(item)
        if isinstance(item, str):
            args.append(case.input.get(item))
        elif "path" in entry:
            args.append(lookup(case.input, as_str(entry["path"])))
        elif "literal" in entry:
            args.append(entry["literal"])
        else:
            mapping = as_dict(entry.get("object"))
            args.append({key: case.input.get(as_str(name)) for key, name in mapping.items()})
    return args


def describe_input(case: Case) -> str:
    """Compact rendering of a case input for reports."""
    return ", ".join(f"{key}={show(value)}" for key, value in case.input.items())


def applicable(binding: Binding, contract: Contract) -> tuple[list[Case], list[CaseResult]]:
    """Cases to run and cases skipped (by language or with the manifest's reason)."""
    run: list[Case] = []
    skipped: list[CaseResult] = []
    for case in contract.cases:
        if not case.selected(binding.select, list(binding.tags), list(binding.exclude_tags)):
            continue
        if case.languages and binding.language not in case.languages:
            skipped.append(CaseResult(case.id, SKIP, f"nur für {', '.join(case.languages)}"))
        elif case.id in binding.skip:
            skipped.append(CaseResult(case.id, SKIP, binding.skip[case.id]))
        else:
            run.append(case)
    return run, skipped


def _execute(
    binding: Binding, calls: list[dict[str, object]], root: Path, manifest: Manifest, tz: str
) -> RunResult:
    if binding.language == PYTHON:
        request = {
            "mode": "contracts",
            "python_path": [str(root / path) for path in binding.python_path] or [str(root)],
            "module": str(root / binding.module)
            if binding.module.endswith(".py")
            else binding.module,
            "export": binding.export,
            "calls": calls,
        }
        interpreter = binding.python or manifest.python
        python = str(root / interpreter) if "/" in interpreter else interpreter or None
        workdir = root / (binding.cwd or (binding.python_path[0] if binding.python_path else ""))
        return run_python(request, interpreter=python, cwd=workdir, timezone=tz)
    module = root / binding.module
    request = {"mode": "contracts", "module": str(module), "export": binding.export, "calls": calls}
    return run_typescript(request, cwd=package_root(module, root), timezone=tz)


def run_binding(
    binding: Binding, library: CaseLibrary, root: Path, manifest: Manifest
) -> BindingRun:
    """Execute one binding against its contract."""
    if binding.contract not in library.contracts:
        return BindingRun(binding, None, load_error=f"Unbekannter Vertrag {binding.contract}")
    contract = library.contract(binding.contract)
    cases, skipped = applicable(binding, contract)
    run = BindingRun(binding, contract, list(skipped))
    if not cases:
        return run
    calls: list[dict[str, object]] = [
        {"id": case.id, "args": build_args(binding.args, contract.params, case)} for case in cases
    ]
    raw = _execute(binding, calls, root, manifest, library.probe_timezone)
    run.load_error = raw.load_error
    for case in cases if not raw.load_error else []:
        outcome = Outcome.from_json(raw.results.get(case.id))
        if binding.result_path and outcome.error is None:
            outcome = Outcome(value=lookup(outcome.value, binding.result_path))
        passed, detail = compare(contract.result, case.expect, outcome)
        text = f"{describe_input(case)} → {detail}" if not passed else detail
        run.results.append(CaseResult(case.id, PASS if passed else FAIL, text))
    return run


def run_contracts(manifest: Manifest, library: CaseLibrary, root: Path) -> list[BindingRun]:
    """Run every binding of the manifest."""
    return [run_binding(binding, library, root, manifest) for binding in manifest.bindings]
