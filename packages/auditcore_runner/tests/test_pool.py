from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

import jsonschema
import pytest

from auditcore_runner import pool


def test_roundtrip_and_schema(tmp_path: Path) -> None:
    path = pool.save(
        pool.Pool({"cpu-gross": 2, "gpu-16gb": 0}, source="flow-agent", reasons={"gpu-16gb": ["Spiel"]}),
        tmp_path / "runner-pool.json",
    )
    document = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(
        files("auditcore_runner").joinpath("data", "schemas", "runner-pool.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(document, schema)
    loaded = pool.load(path)
    assert loaded is not None and loaded.targets == {"cpu-gross": 2, "gpu-16gb": 0}
    assert loaded.reasons == {"gpu-16gb": ["Spiel"]} and loaded.updated


def test_missing_file_means_no_regulator(tmp_path: Path) -> None:
    assert pool.load(tmp_path / "fehlt.json") is None
    assert pool.load(None) is None


@pytest.mark.parametrize(
    "document",
    [
        {"schema": "falsch", "klassen": {}},
        {"schema": pool.POOL_SCHEMA, "klassen": {"Ungültig Name": {"soll": 1}}},
        {"schema": pool.POOL_SCHEMA, "klassen": {"cpu": {"soll": -1}}},
        {"schema": pool.POOL_SCHEMA, "klassen": {"cpu": {"soll": True}}},
    ],
)
def test_invalid(document: object) -> None:
    with pytest.raises(pool.PoolFormatError):
        pool.parse(document)


def test_legacy_schema_and_assignments() -> None:
    assert pool.parse({"schema": "auditcore-pruefbank/runner-pool/1", "klassen": {"cpu": {"soll": 1}}}).targets == {
        "cpu": 1
    }
    assert pool.parse_assignments(["cpu-gross=2", "gpu-16gb=0"]) == {"cpu-gross": 2, "gpu-16gb": 0}
    with pytest.raises(pool.PoolFormatError):
        pool.parse_assignments(["cpu=zwei"])
