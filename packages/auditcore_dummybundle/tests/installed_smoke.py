"""Smoke check executed after installing the wheel: bundle, checks, recipe, contract."""

from __future__ import annotations

from datetime import date
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_dummybundle import (
    BundleConfig,
    build_bundle,
    generate_templates,
    run_checks,
    templates,
    web,
)


def main() -> None:
    """Sum checks, template projection and the REST contract on the installed package."""
    package = distribution("auditcore_dummybundle")
    assert package.version == "0.1.0"
    assert sorted(r for r in package.requires or [] if "extra ==" not in r) == [
        "auditcore_common==0.2.1",
        "auditcore_dummygenerator==0.1.4",
        "auditcore_identifiers==0.2.1",
    ]
    assert find_spec("auditcore") is None
    config = BundleConfig(seed=42, base_date=date(2026, 1, 1))
    assert all(outcome.passed for outcome in run_checks(build_bundle(config)))
    public = [key for key, template in templates().items() if template.public]
    assert public == ["V0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "N1"]
    assert {template.status for template in templates().values()} == {"Freigegeben"}
    result = generate_templates(config, public)
    assert result.meta["marking"] == "SYNTHETISCH" and len(result.tables) > 20
    assert web.catalogue()["contract"] == "dummybundle_ui/1"
    print("PASS: installed auditcore_dummybundle")


if __name__ == "__main__":
    main()
