"""Mandatory functional smoke tests after every production deployment.

A green deployment workflow or a health endpoint answering 200 does not prove
that the changed functions work. Every deployment outside ``internal_test``
therefore declares functional smoke cases, and ``auditcore-deploy smoke`` runs
them against the deployed application. A deployment counts as verified only
when all functional cases pass (rule of the rights holder, 2026-09-24:
„das soll pflicht sein“).

Cases call real application endpoints with synthetic, clearly marked test
data. Health or readiness endpoints never count as a functional case.
Credentials come from environment variables named in the case; values are
never written to the result. Response bodies are not stored, only the outcome
of each assertion.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

SMOKE_SCHEMA = "auditcore.functional_smoke/1"
SMOKE_MARKER = "AUDITCORE-SMOKE"
_HEALTH_PATH = re.compile(r"(^|/)(health|healthz|ready|readyz|live|livez|ping|status)/?$", re.I)
_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

Transport = Callable[[str, str, Mapping[str, str], bytes | None, float], tuple[int, bytes]]


@dataclass(frozen=True)
class FunctionalSmokeCase:
    """One functional call against the deployed application."""

    name: str
    changed_feature: str
    path: str
    method: str = "GET"
    expected_status: int = 200
    json_body: Any = None
    json_expect: dict[str, Any] = field(default_factory=dict)
    body_contains: list[str] = field(default_factory=list)
    headers_from_env: dict[str, str] = field(default_factory=dict)
    timeout: float = 60.0


@dataclass
class FunctionalSmokeResult:
    """Outcome per case; no response bodies and no credential values."""

    status: str
    schema: str
    base_url: str
    executed_at: str
    cases: dict[str, dict[str, Any]]
    blockers: list[str]


def is_health_path(path: str) -> bool:
    """Health, readiness and liveness endpoints are not functional tests."""
    return bool(_HEALTH_PATH.search(urllib.parse.urlsplit(path).path))


def load_cases(raw: Any) -> list[FunctionalSmokeCase]:
    """Validate declared cases; reject empty, health-only or ambiguous definitions."""
    if not isinstance(raw, list) or not raw:
        raise ValueError("Fachlicher Rauchtest fehlt: mindestens ein Fall ist Pflicht")
    cases: list[FunctionalSmokeCase] = []
    names: set[str] = set()
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("Rauchtest-Fall muss ein Objekt sein")
        case = FunctionalSmokeCase(**dict(item))
        if not case.name or case.name in names:
            raise ValueError("Rauchtest-Fälle brauchen eindeutige Namen")
        names.add(case.name)
        if not case.changed_feature.strip():
            raise ValueError(f"{case.name}: changed_feature (geprüfte Funktion) ist Pflicht")
        if case.method.upper() not in _METHODS:
            raise ValueError(f"{case.name}: ungültige HTTP-Methode")
        if not case.path.startswith("/") or "://" in case.path:
            raise ValueError(f"{case.name}: path muss ein relativer Pfad sein")
        if is_health_path(case.path):
            raise ValueError(
                f"{case.name}: Health-/Readiness-Endpunkte sind kein fachlicher Rauchtest"
            )
        if not (case.json_expect or case.body_contains):
            raise ValueError(f"{case.name}: fachliche Erwartung (json_expect/body_contains) fehlt")
        for header, variable in case.headers_from_env.items():
            if not re.fullmatch(r"[A-Za-z0-9-]+", header) or not re.fullmatch(
                r"[A-Z][A-Z0-9_]*", variable
            ):
                raise ValueError(f"{case.name}: ungültige Header-Zuordnung")
        if case.method.upper() in {"POST", "PUT", "PATCH"} and SMOKE_MARKER not in json.dumps(
            case.json_body, ensure_ascii=False
        ):
            raise ValueError(
                f"{case.name}: schreibende Fälle müssen Testdaten mit „{SMOKE_MARKER}“ markieren"
            )
        cases.append(case)
    return cases


def _lookup(document: Any, dotted: str) -> Any:
    current = document
    for part in dotted.split("."):
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                raise KeyError(dotted)
            current = current[index]
        elif isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            raise KeyError(dotted)
    return current


def _matches(actual: Any, expected: Any) -> bool:
    if isinstance(expected, Mapping) and set(expected) <= {"exists", "min", "max", "contains"}:
        if "exists" in expected:
            return bool(expected["exists"])
        if "contains" in expected:
            return str(expected["contains"]) in str(actual)
        try:
            value = float(actual)
        except (TypeError, ValueError):
            return False
        return value >= float(expected.get("min", value)) and value <= float(
            expected.get("max", value)
        )
    return bool(actual == expected)


def urllib_transport(
    method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout: float
) -> tuple[int, bytes]:
    """HTTPS-only standard-library transport."""
    if urllib.parse.urlsplit(url).scheme != "https":
        raise ValueError("Rauchtests laufen nur über https")
    request = urllib.request.Request(url, data=body, method=method, headers=dict(headers))  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:  # noqa: S310  # nosec B310
            return int(reply.status), reply.read(5_000_000)
    except urllib.error.HTTPError as error:
        return int(error.code), error.read(100_000)


def run_functional_smoke(
    base_url: str,
    raw_cases: Any,
    *,
    transport: Transport = urllib_transport,
    environ: Mapping[str, str] | None = None,
) -> FunctionalSmokeResult:
    """Run every case; the deployment is verified only if all pass."""
    environ = os.environ if environ is None else environ
    started = datetime.now(UTC).isoformat(timespec="seconds")
    try:
        cases = load_cases(raw_cases)
    except (TypeError, ValueError) as exc:
        return FunctionalSmokeResult("BLOCKED", SMOKE_SCHEMA, base_url, started, {}, [str(exc)])
    results: dict[str, dict[str, Any]] = {}
    for case in cases:
        outcome: dict[str, Any] = {"changed_feature": case.changed_feature, "path": case.path}
        missing = [v for v in case.headers_from_env.values() if not environ.get(v)]
        if missing:
            outcome |= {"status": "NOT_CONFIGURED", "missing_environment": sorted(missing)}
            results[case.name] = outcome
            continue
        headers = {h: environ[v] for h, v in case.headers_from_env.items()}
        body = None
        if case.json_body is not None:
            body = json.dumps(case.json_body, ensure_ascii=False).encode()
            headers["Content-Type"] = "application/json"
        try:
            status, raw = transport(
                case.method.upper(), base_url.rstrip("/") + case.path, headers, body, case.timeout
            )
        except (OSError, ValueError) as exc:
            outcome |= {"status": "FAIL", "reason": f"Transport: {type(exc).__name__}"}
            results[case.name] = outcome
            continue
        failures: list[str] = []
        if status != case.expected_status:
            failures.append(f"HTTP {status} statt {case.expected_status}")
        text = raw.decode("utf-8", errors="replace")
        failures += [f"Text fehlt: {s}" for s in case.body_contains if s not in text]
        if case.json_expect:
            try:
                document = json.loads(text)
            except ValueError:
                failures.append("Antwort ist kein JSON")
            else:
                for key, expected in case.json_expect.items():
                    try:
                        actual = _lookup(document, key)
                    except KeyError:
                        failures.append(f"Feld fehlt: {key}")
                        continue
                    if not _matches(actual, expected):
                        failures.append(f"Erwartung verfehlt: {key}")
        outcome |= {"http_status": status, "status": "FAIL" if failures else "PASS"}
        if failures:
            outcome["failures"] = failures
        results[case.name] = outcome
    statuses = {r["status"] for r in results.values()}
    overall = "PASS" if statuses == {"PASS"} else "FAIL"
    blockers = [f"{n}: {r['status']}" for n, r in results.items() if r["status"] != "PASS"]
    return FunctionalSmokeResult(overall, SMOKE_SCHEMA, base_url, started, results, blockers)


def smoke_required(deployment_target: str) -> bool:
    """Every target except the internal test environment requires functional smoke."""
    return deployment_target != "internal_test"
