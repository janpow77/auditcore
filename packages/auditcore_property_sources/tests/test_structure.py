"""Structure of the 0.1.1 refactoring: ``adapters`` became a subpackage."""

from __future__ import annotations

import importlib

import auditcore_property_sources.adapters as adapters

OLD_PUBLIC_NAMES = (
    "ADAPTER_VERSION",
    "DEFAULT_ROBOTS_POLICY",
    "ROBOTS_POLICIES",
    "AccessNotPermittedError",
    "BieniciAdapter",
    "CityaAdapter",
    "ImmobilienDeAdapter",
    "InBerlinWohnenAdapter",
    "KleinanzeigenAdapter",
    "ParuvenduAdapter",
    "ZvgDetailAdapter",
    "ZvgListingAdapter",
)


def test_public_names_of_the_former_module_stay_importable() -> None:
    for name in OLD_PUBLIC_NAMES:
        assert name in adapters.__all__
        assert getattr(adapters, name) is not None
    assert adapters.ADAPTER_VERSION == "1.1.0"
    assert adapters.ROBOTS_POLICIES == ("ignore", "respect")
    assert adapters.DEFAULT_ROBOTS_POLICY == "ignore"


def test_only_the_harvest_bridge_imports_auditcore_harvest() -> None:
    for module in ("_base", "berlin", "france", "zvg"):
        source = importlib.import_module(f"auditcore_property_sources.adapters.{module}")
        text = open(source.__file__, encoding="utf-8").read()  # noqa: SIM115
        assert "import auditcore_harvest" not in text
        assert "from auditcore_harvest" not in text
