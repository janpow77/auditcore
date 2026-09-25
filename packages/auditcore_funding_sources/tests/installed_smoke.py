"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

import warnings
from datetime import date
from importlib.metadata import distribution
from importlib.util import find_spec


def main() -> None:
    """Parse a transparency row, compute its identity, cumulate, run a harvest adapter."""
    package = distribution("auditcore_funding_sources")
    assert package.version == "0.1.3"
    runtime = [r for r in package.requires or [] if "extra ==" not in r]
    assert runtime == ["auditcore_common==0.1.0", "auditcore_harvest==0.1.0"], runtime
    assert find_spec("auditcore") is None
    from auditcore_funding_sources import cumulation, snapshot, workshop

    content = "Name des Begünstigten;Gesamtkosten;PLZ\nBeispiel GmbH;1.234,56;01067\n".encode()
    rows = workshop.parse_file(content, "liste.csv")
    assert rows[0]["cost_total_raw"] == "1.234,56" and rows[0]["plz"] == "1067"
    assert workshop.parse_file(content, "liste.csv", typing="text")[0]["plz"] == "01067"
    assert workshop.compute_record_hash(rows[0], "quelle") == workshop.compute_record_hash(
        dict(rows[0]), "quelle"
    )
    context = workshop.SnapshotContext("quelle", "Hessen", "EFRE", "2021-2027", "DE")
    plan = snapshot.plan_snapshot(rows, context, mode="snapshot", stored_identities=["alt"])
    assert plan.delete_all_first and plan.records_inserted == 1
    result = cumulation.calculate(
        [{"grantingDate": "2025-01-01", "amountEur": 1000, "deMinimisType": "GENERAL"}],
        reference_date=date(2026, 9, 1),
    )
    assert str(result.arithmetic_difference_eur) == "299000" and result.decision is None
    from auditcore_funding_sources import designer

    assert str(designer.parse_amount("1.234.567")) == "1234567"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert designer.parse_betrag is designer.parse_amount
    assert [w.category for w in caught] == [DeprecationWarning]
    from auditcore_harvest import AdapterRegistry

    from auditcore_funding_sources import adapters

    registry = AdapterRegistry()
    adapters.register(registry)
    assert "funding.de_minimis_eaid" in registry.sources()
    print("PASS: installed auditcore_funding_sources parsers, snapshot plan, cumulation, adapters")


if __name__ == "__main__":
    main()
