"""Packaged source catalogue: completeness of H0 families, verified origins, validation."""

from __future__ import annotations

import copy
import json
import re
from importlib import resources
from typing import Any

import pytest

from auditcore_harvest.catalog import load_catalog, summary, validate_catalog
from auditcore_harvest.errors import ConfigError


def document() -> dict[str, Any]:
    text = resources.files("auditcore_harvest.catalogs").joinpath("sources.json").read_text()
    return json.loads(text)


def test_catalog_covers_every_h0_family_and_is_honest() -> None:
    entries = load_catalog()
    stats = summary(entries)
    assert len(entries) == 62
    assert stats["implementation"] == {"PLANNED": 53, "SUPPORTED": 7, "LEGACY_ONLY": 2}
    assert set(stats["family"]) == {
        "legal",
        "procurement",
        "funding",
        "registry",
        "price",
        "geo",
        "property",
    }
    ids = {e.source_id for e in entries}
    for required in (
        "legal.dip_bundestag",
        "legal.eurlex",
        "legal.curia",
        "legal.eca",
        "legal.designer_olaf",
        "legal.designer_gesetze_im_internet",
        "legal.designer_hessenrecht",
        "procurement.ted_awards",
        "procurement.had_search",
        "funding.state_aid",
        "funding.de_minimis_eaid",
        "funding.eu_beneficiaries",
        "price.tankerkoenig",
        "price.mtsk",
        "geo.overpass",
        "property.zvg",
    ):
        assert required in ids
    supported = {e.source_id for e in entries if e.implementation == "SUPPORTED"}
    assert supported == {
        "legal.dip_bundestag",
        "legal.eurlex",
        "legal.bafin",
        "legal.curia",
        "legal.eca",
        "procurement.ted_awards",
        "procurement.had_search",
    }
    for entry in entries:
        assert entry.live_test in ("NOT_EXECUTED", "NOT_CONFIGURED")
        assert entry.data["licence_access"]["status"] != "REVIEWED"
        for origin in entry.data["origins"]:
            assert origin["verified"] and re.fullmatch(r"[0-9a-f]{40}", origin["commit"])


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d["sources"].append(copy.deepcopy(d["sources"][0])), "doppelt"),
        (lambda d: d["sources"][0].__setitem__("auth", "magic"), "auth"),
        (
            lambda d: d["sources"][0]["implementation"].__setitem__("status", "SUPPORTED"),
            "Fixtures",
        ),
        (lambda d: d["sources"][0]["live_test"].__setitem__("status", "PASS"), "Datum"),
        (
            lambda d: d["sources"][0]["config_schema"]["properties"].__setitem__(
                "api_key", {"type": "string", "default": "x"}
            ),
            "Geheimnis",
        ),
        (lambda d: d["sources"][0]["origins"][0].__setitem__("commit", "abc"), "SHA"),
        (lambda d: d.__setitem__("schema", "x"), "Katalogschema"),
        (lambda d: d["sources"][0].pop("consumers"), "Pflichtfeld"),
    ],
)
def test_validation_rejects_inconsistent_entries(mutate: Any, message: str) -> None:
    data = document()
    mutate(data)
    with pytest.raises(ConfigError, match=message):
        validate_catalog(data)


def test_loader_rejects_paths() -> None:
    with pytest.raises(ConfigError):
        load_catalog("../pyproject.toml")
