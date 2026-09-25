"""Isolated runner for Python helpers (executed as a script in a separate process).

Reads a JSON request from stdin and writes the result to the file named in
``AUDITCORE_HELPERS_OUTPUT`` (stdout stays free for the app's own output):

``{"mode": "contracts", "python_path": [...], "module": "a.b" | "x.py", "export": "f",
"calls": [...]}``
``{"mode": "probe", "functions": [{"id", "name", "source", "prelude"}], "calls": [...]}``

Only the standard library is used, so any application interpreter can run it.
"""

from __future__ import annotations

import datetime as _dt
import decimal
import importlib
import importlib.util
import json
import math
import os
import re
import sys
import time
from collections.abc import Callable
from types import ModuleType

MAX_MESSAGE = 160
#: Validation errors (pydantic settings) echo input values such as secrets from .env.
SECRET_ECHO = re.compile(r"(input_value|input)\s*=\s*('[^']*'|\"[^\"]*\"|\S+)")

PROBE_PRELUDE = (
    "from __future__ import annotations\n"
    "import re, math, decimal\n"
    "from decimal import Decimal, InvalidOperation\n"
)


def describe_error(error: BaseException) -> str:
    """Error type plus the first line of its message, shortened and without echoed inputs."""
    first = (str(error).strip().splitlines() or [""])[0]
    text = SECRET_ECHO.sub(r"\1=***", f"{type(error).__name__}: {first}")
    return text if len(text) <= MAX_MESSAGE else text[: MAX_MESSAGE - 1] + "…"


def decode(value: object) -> object:
    """Turn encoded special values into Python objects."""
    if isinstance(value, list):
        return [decode(item) for item in value]
    if not isinstance(value, dict):
        return value
    if value.get("$nan"):
        return float("nan")
    if isinstance(value.get("$date"), str):
        return _dt.datetime.fromisoformat(str(value["$date"]).replace("Z", "+00:00"))
    if isinstance(value.get("$error"), str):
        return Exception(value["$error"])
    return {str(key): decode(item) for key, item in value.items()}


def encode(value: object, depth: int = 0) -> object:
    """Encode a return value as JSON-compatible data."""
    if isinstance(value, float) and math.isnan(value):
        return {"$nan": True}
    if isinstance(value, decimal.Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, (_dt.datetime, _dt.date)):
        return {"$date": value.isoformat()}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if depth < 6 and isinstance(value, (list, tuple)):
        return [encode(item, depth + 1) for item in value]
    if depth < 6 and isinstance(value, dict):
        return {str(key): encode(item, depth + 1) for key, item in value.items()}
    return str(value)


def call_all(function: Callable[..., object], calls: list[dict[str, object]]) -> dict[str, object]:
    """Call ``function`` with every argument list and collect results or errors."""
    results: dict[str, object] = {}
    for call in calls:
        args = decode(call.get("args", []))
        try:
            value = function(*(args if isinstance(args, list) else []))
            results[str(call["id"])] = {"value": encode(value)}
        except Exception as error:  # noqa: BLE001 - every failure is a case result
            results[str(call["id"])] = {"error": describe_error(error)}
    return results


def load_module(target: str) -> ModuleType:
    """Import a dotted module name or a ``.py`` file path."""
    if not target.endswith(".py"):
        return importlib.import_module(target)
    spec = importlib.util.spec_from_file_location("auditcore_helper_target", target)
    if spec is None or spec.loader is None:
        raise ImportError(target)
    module = importlib.util.module_from_spec(spec)
    # Dataclasses and typing look the module up while it is being executed.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def pick(module: object, name: str) -> object:
    """Resolve a dotted attribute path."""
    current = module
    for part in name.split("."):
        current = getattr(current, part)
    return current


def run_contracts(request: dict[str, object]) -> dict[str, object]:
    """Import the helper and run all calls."""
    paths = request.get("python_path", [])
    for path in reversed(paths if isinstance(paths, list) else []):
        sys.path.insert(0, str(path))
    try:
        function = pick(load_module(str(request["module"])), str(request["export"]))
    except Exception as error:  # noqa: BLE001 - reported as load error
        return {"load_error": f"Modul nicht ladbar: {describe_error(error)}"}
    if not callable(function):
        return {"load_error": f"Export „{request['export']}“ ist keine Funktion"}
    calls = request.get("calls", [])
    return {"results": call_all(function, calls if isinstance(calls, list) else [])}


def probe_one(entry: dict[str, object], calls: list[dict[str, object]]) -> dict[str, object]:
    """Execute one extracted function standalone; unknown names mean 'not isolated'."""
    prelude = entry.get("prelude", [])
    code = PROBE_PRELUDE + "\n".join(str(p) for p in (prelude if isinstance(prelude, list) else []))
    code += "\n" + str(entry["source"])
    namespace: dict[str, object] = {"__name__": "auditcore_helper_probe"}
    try:
        exec(compile(code, "<probe>", "exec"), namespace)  # nosec B102
    except Exception as error:  # noqa: BLE001 - not executable standalone
        return {"isolated": False, "reason": describe_error(error)}
    function = namespace.get(str(entry["name"]))
    if not callable(function):
        return {"isolated": False, "reason": "keine Funktion"}
    results = call_all(function, calls)
    for result in results.values():
        message = result.get("error", "") if isinstance(result, dict) else ""
        if isinstance(message, str) and message.startswith("NameError"):
            return {"isolated": False, "reason": message}
    return {"isolated": True, "results": results}


def run_probe(request: dict[str, object]) -> dict[str, object]:
    """Probe every function of the request."""
    functions = request.get("functions", [])
    calls = request.get("calls", [])
    call_list = calls if isinstance(calls, list) else []
    results = {
        str(entry["id"]): probe_one(entry, call_list)
        for entry in (functions if isinstance(functions, list) else [])
        if isinstance(entry, dict)
    }
    return {"results": results}


def main() -> None:
    """Entry point of the runner process."""
    if hasattr(time, "tzset"):
        time.tzset()
    request = json.loads(sys.stdin.read())
    response = run_probe(request) if request.get("mode") == "probe" else run_contracts(request)
    with open(os.environ["AUDITCORE_HELPERS_OUTPUT"], "w", encoding="utf-8") as handle:
        json.dump(response, handle, ensure_ascii=False)


if __name__ == "__main__":
    main()
