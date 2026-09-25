"""Execute the original identifier checks and record their outputs (characterisation).

The original functions are read from pinned Git blobs (hash verified), only the
needed top-level definitions or methods are compiled and executed with the
standard library. No application is imported, no database or network is used.

    python tools/capture_originals.py --repos /home/janpow/Projekte \
        --auditcore /path/to/auditcore-checkout tests/fixtures
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import platform
import re
import subprocess
import sys
import types
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import samples  # noqa: E402

from auditcore_identifiers.registry import IBAN_BBAN_STRUCTURE  # noqa: E402  (inputs only)

FLOWINVOICE = "fb2d18568d2eaf64574d131ceae51a936b9aac02"
PORTAL = "d8eefa426826bdecb67036774f3128ae05e7d0d0"
FLOWWORKSHOP = "a05bb2143bd96d5e981f9462f05b965e1658be36"
AUDITCORE = "99788a18c28bf683ada62bb3ab9d4aeb36f2c5b2"
_DOCS = "packages/auditcore_documents/src/auditcore_documents/pipeline/stages/"
#: key -> (local directory, repository, commit, path, git blob)
SOURCES: dict[str, tuple[str, str, str, str, str]] = {
    "flowinvoice.validators": ("flowinvoice", "janpow77/flowinvoice", FLOWINVOICE,
                               "backend/app/services/validators.py",
                               "d3c09fbd9182c74ff6855b7a84f4672322f3f025"),
    "flowinvoice.pipeline": ("flowinvoice", "janpow77/flowinvoice", FLOWINVOICE,
                             "backend/app/pipeline/stages/validation.py",
                             "679954a2396984ad4ae05a4244f5e38e11dda2c6"),
    "flowinvoice.risk_checker": ("flowinvoice", "janpow77/flowinvoice", FLOWINVOICE,
                                 "backend/app/services/risk_checker.py",
                                 "b799e855c382760d0a84762b2949462692f7be01"),
    "audit_portal.validators": ("audit-portal", "janpow77/audit-portal", PORTAL,
                                "backend/app/services/validators.py",
                                "d3c09fbd9182c74ff6855b7a84f4672322f3f025"),
    "audit_portal.pipeline": ("audit-portal", "janpow77/audit-portal", PORTAL,
                              "backend/app/pipeline/stages/validation.py",
                              "a485cb0a73789cb94264fed22bc7186a5ab13e19"),
    "audit_portal.risk_checker": ("audit-portal", "janpow77/audit-portal", PORTAL,
                                  "backend/app/services/risk_checker.py",
                                  "5e93b2b8c99ace75ccd8592410906e38d77f224f"),
    "flowworkshop.entity_resolution": ("flowworkshop", "janpow77/flowworkshop", FLOWWORKSHOP,
                                       "auditworkshop/backend/services/entity_resolution.py",
                                       "d7a799b65e0444e8be8e606b35bd2cc1ecbdfac0"),
    "auditcore.invoicesynth": ("auditcore", "janpow77/auditcore", AUDITCORE,
                               "packages/auditcore_invoicesynth/src/auditcore_invoicesynth/"
                               "identifiers.py", "7b0529b32d17d6fd7fba5b4fc5cd91f4d28f39d4"),
    "auditcore.documents_base": ("auditcore", "janpow77/auditcore", AUDITCORE,
                                 _DOCS + "validation_base.py",
                                 "391865454cea422771e990dbb615de837bcc0ef7"),
    "auditcore.documents_donut": ("auditcore", "janpow77/auditcore", AUDITCORE,
                                  _DOCS + "donut_values.py",
                                  "9200477cad216cb6d187f126e6da2e100361c9d4"),
    "auditcore.entity_matching_lei": ("auditcore", "janpow77/auditcore", AUDITCORE,
                                      "packages/auditcore_entity_matching/src/"
                                      "auditcore_entity_matching/lei.py",
                                      "d897b2876f7487e3c5ec261f07d8217e191bd0a0"),
}


def read_blob(repos: Path, auditcore: Path, key: str) -> str:
    local, _repository, commit, path, blob = SOURCES[key]
    directory = auditcore if local == "auditcore" else repos / local
    data = subprocess.run(["git", "-C", str(directory), "cat-file", "blob", f"{commit}:{path}"],
                          check=True, capture_output=True).stdout
    digest = hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()
    if digest != blob:
        raise SystemExit(f"{key}: blob {digest} != pinned {blob}")
    return data.decode("utf-8")


def _named(node: ast.stmt) -> str | None:
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return node.name
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def extract(source: str, names: Iterable[str], namespace: dict[str, Any]) -> dict[str, Any]:
    """Compile the named top-level definitions or ``Class.method`` functions."""
    tree = ast.parse(source)
    wanted = set(names)
    body: list[ast.stmt] = []
    for node in tree.body:
        if _named(node) in wanted:
            body.append(node)
        if isinstance(node, ast.ClassDef):
            body += [m for m in node.body if f"{node.name}.{_named(m)}" in wanted]
    module = ast.Module(body=body, type_ignores=[])
    exec(compile(module, "<pinned>", "exec"), namespace)  # noqa: S102  (pinned blob)
    return namespace


def load_module(name: str, source: str) -> types.ModuleType:
    module = types.ModuleType(name)
    sys.modules[name] = module
    exec(compile(source, name, "exec"), module.__dict__)  # noqa: S102  (pinned blob)
    return module


def record(function: str, inputs: dict[str, Any], call: Callable[[], Any]) -> dict[str, Any]:
    try:
        return {"function": function, "inputs": inputs, "output": call(), "exception": None}
    except Exception as error:  # noqa: BLE001  (the exception is the observation)
        return {"function": function, "inputs": inputs, "output": None,
                "exception": type(error).__name__}


def _plain(result: Any) -> dict[str, Any]:
    value = result.value
    return {"status": str(result.status.value), "value": value if value is None else str(value),
            "message": result.message, "details": result.details}


def capture_validators(module: types.ModuleType) -> list[dict[str, Any]]:
    cases = []
    single = {"validate_iban": samples.iban_samples(dict(IBAN_BBAN_STRUCTURE)),
              "validate_bic": samples.bic_samples(),
              "validate_german_tax_id": samples.tax_number_samples()}
    vat = samples.vat_samples()
    single["validate_german_vat_id"] = list(dict.fromkeys(v for v, _ in vat))
    single["validate_uk_vat_id"] = single["validate_german_vat_id"]
    for name, values in single.items():
        function = getattr(module, name)
        cases += [record(name, {"value": v}, lambda f=function, v=v: _plain(f(v)))
                  for v in values]
    eu = module.validate_eu_vat_id
    cases += [record("validate_eu_vat_id", {"value": v, "country_code": c},
                     lambda v=v, c=c: _plain(eu(v, c))) for v, c in vat]
    return cases


class _Result:
    def __init__(self, **fields: Any) -> None:
        self.fields = fields


def capture_pipeline(source: str) -> list[dict[str, Any]]:
    names = ["IbanChecksumRule._validate_iban", "VatIdFormatRule.evaluate"]
    space = extract(source, names, {"ValidationResult": _Result})
    rule = types.SimpleNamespace(rule_id="VAL_VAT_ID_FORMAT", name="vat_id_format",
                                 severity="WARN")

    def evaluate(value: Any) -> dict[str, Any]:
        context = types.SimpleNamespace(artifacts=types.SimpleNamespace(
            normalized_json={"vat_id": value}))
        fields = asyncio.run(space["evaluate"](rule, context)).fields
        return {k: fields.get(k) for k in ("outcome", "message", "severity", "evidence")}

    ibans = samples.iban_samples(dict(IBAN_BBAN_STRUCTURE))
    vats = list(dict.fromkeys(v for v, _ in samples.vat_samples()))
    iban = space["_validate_iban"]
    return ([record("_validate_iban", {"value": v}, lambda v=v: list(iban(None, v)))
             for v in ibans]
            + [record("VatIdFormatRule.evaluate", {"value": v}, lambda v=v: evaluate(v))
               for v in vats])


def capture_normalize(source: str) -> list[dict[str, Any]]:
    function = extract(source, ["RiskChecker._normalize_vat_id"], {})["_normalize_vat_id"]
    values = list(dict.fromkeys(v for v, _ in samples.vat_samples()))
    return [record("_normalize_vat_id", {"value": v}, lambda v=v: function(None, v))
            for v in values]


def capture_flowworkshop(source: str) -> list[dict[str, Any]]:
    space = extract(source, ["_LEI_RE", "is_valid_lei", "extract_lei_from_text"], {"re": re})
    values = samples.lei_samples()
    return ([record("is_valid_lei", {"value": v}, lambda v=v: space["is_valid_lei"](v))
             for v in values]
            + [record("extract_lei_from_text", {"value": v},
                      lambda v=v: space["extract_lei_from_text"](v)) for v in values])


def capture_internal(sources: dict[str, str]) -> list[dict[str, Any]]:
    synth = load_module("_pinned_invoicesynth", sources["auditcore.invoicesynth"])
    base = extract(sources["auditcore.documents_base"],
                   ["IBAN_COUNTRY_LENGTHS", "VAT_ID_PATTERNS", "validate_iban"], {})
    donut = extract(sources["auditcore.documents_donut"],
                    ["compact", "de_vat_check_digit", "at_uid_check_digit", "vat_id_check"],
                    {"re": re, "VAT_ID_PATTERNS": base["VAT_ID_PATTERNS"]})
    lei = load_module("_pinned_entity_lei", sources["auditcore.entity_matching_lei"])
    ibans = samples.iban_samples(dict(IBAN_BBAN_STRUCTURE))
    vats = list(dict.fromkeys(v for v, _ in samples.vat_samples()))
    leis = samples.lei_samples()
    cases = [record("invoicesynth.iban_valid", {"value": v}, lambda v=v: synth.iban_valid(v))
             for v in ibans]
    cases += [record("invoicesynth.vat_id_valid", {"value": v},
                     lambda v=v: synth.vat_id_valid(v)) for v in vats]
    cases += [record("documents.validate_iban", {"value": v},
                     lambda v=v: list(base["validate_iban"](v))) for v in ibans]
    cases += [record("documents.donut_iban", {"value": v},
                     lambda v=v: list(base["validate_iban"](donut["compact"](v)))) for v in ibans]
    cases += [record("documents.donut_vat_id_check", {"value": v},
                     lambda v=v: donut["vat_id_check"](donut["compact"](v))) for v in vats]
    cases += [record("entity_matching.check_lei", {"value": v},
                     lambda v=v: lei.check_lei(v).valid) for v in leis]
    cases += [record("entity_matching.extract_lei", {"value": v},
                     lambda v=v: lei.extract_lei(v)) for v in leis]
    return cases


def _source_entries(keys: Iterable[str]) -> list[dict[str, str]]:
    return [{"key": k, "repository": SOURCES[k][1], "commit": SOURCES[k][2],
             "path": SOURCES[k][3], "git_blob": SOURCES[k][4]} for k in keys]


def write(target: Path, keys: list[str], cases: list[dict[str, Any]]) -> None:
    header = {"status": "OBSERVED", "scope": "LOCAL_ORIGINAL_EXECUTION",
              "sources": _source_entries(keys),
              "environment": {"python": platform.python_version()},
              "tool": "tools/capture_originals.py", "count": len(cases)}
    lines = [json.dumps(case, ensure_ascii=False, sort_keys=True) for case in cases]
    text = json.dumps(header, ensure_ascii=False, indent=1)[:-2]
    text += ',\n "cases": [\n' + ",\n".join(lines) + "\n ]\n}\n"
    target.write_text(text, encoding="utf-8")


def _app(prefix: str, sources: dict[str, str]) -> list[dict[str, Any]]:
    validators = load_module(f"_pinned_{prefix}_validators", sources[f"{prefix}.validators"])
    cases = capture_validators(validators)
    cases += capture_pipeline(sources[f"{prefix}.pipeline"])
    return cases + capture_normalize(sources[f"{prefix}.risk_checker"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos", type=Path, required=True)
    parser.add_argument("--auditcore", type=Path, required=True)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    sources = {key: read_blob(args.repos, args.auditcore, key) for key in SOURCES}
    for prefix in ("flowinvoice", "audit_portal"):
        keys = [k for k in SOURCES if k.startswith(prefix + ".")]
        write(args.output / f"{prefix}_observed.json", keys, _app(prefix, sources))
    keys = [k for k in SOURCES if k.startswith(("auditcore.", "flowworkshop."))]
    cases = capture_internal(sources)
    cases += capture_flowworkshop(sources["flowworkshop.entity_resolution"])
    write(args.output / "internal_observed.json", keys, cases)


if __name__ == "__main__":
    main()
