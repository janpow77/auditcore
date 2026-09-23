"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from decimal import Decimal
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_procurement import (
    build_ted_query,
    inspect_notice,
    load_profile,
    normalize_notice,
    parse_ted_file,
    run_prechecks,
    ted_company_result,
    validate_record,
)
from auditcore_procurement.ted import dump_records


def main() -> None:
    """Normalise, import, check and precheck with the installed pure core."""
    package = distribution("auditcore_procurement")
    assert package.version == "0.1.0"
    assert not [r for r in package.requires or [] if "extra ==" not in r]
    assert find_spec("auditcore") is None
    notice = {
        "publication-number": "1-2024",
        "winner-name": {"deu": ["Beispiel GmbH"]},
        "result-value-notice": "150000.00",
        "publication-date": "2024-01-15+01:00",
    }
    record = normalize_notice(notice)
    assert record == {
        "notice_id": "1-2024",
        "document_number": "1-2024",
        "contractor_name": "Beispiel GmbH",
        "publication_date": "2024-01-15",
        "contract_value": 150000.0,
    }
    assert validate_record(record) == []
    assert parse_ted_file(dump_records([record]), "x.json")[0] == [record]
    assert build_ted_query(country="DEU").endswith("notice-type=can-standard AND winner-name=*")
    assert [i.code for i in inspect_notice({**notice, "result-value-notice": "1.234,56"})] == [
        "ambiguous_amount"
    ]
    profile = load_profile("procurement.hvtg-legacy", "2026.09.1")
    report = run_prechecks(
        profile,
        Decimal("800"),
        None,
        None,
        "Liefer-/Dienstleistungen",
        "Direktvergabe",
        "BELOW_1K",
        [{"procurement_doc_type": "VERGABEVERMERK"}],
    )
    assert report["overall_status"] == "FAIL"  # min_bids for BELOW_1K is 1 and no ANGEBOT
    hvtg = load_profile("procurement.hvtg", "2026.09.2")
    yearly = run_prechecks(
        hvtg,
        Decimal("218000"),
        None,
        None,
        "Liefer-/Dienstleistungen",
        None,
        None,
        [],
        mode="strict",
        year=2026,
        authority_type="sub_central",
    )
    assert yearly["checks"][0]["calculated_tier"] == "ABOVE_EU"
    assert yearly["checks"][0]["eu_threshold"]["value"] == 216000
    missing = run_prechecks(
        hvtg, Decimal("1"), None, None, "Bauleistungen", None, None, [], mode="strict", year=2023
    )
    assert missing["overall_status"] == "REVIEW_REQUIRED"
    assert ted_company_result(500, None, "DE", "designer").status == "failed"
    if find_spec("auditcore_harvest") is not None:
        from auditcore_procurement.sources import TedAwardsAdapter

        TedAwardsAdapter().validate_config(
            {"api_url": "https://api.ted.europa.eu/v3/notices/search"}
        )
        print("PASS: installed sources extra (auditcore_harvest) importable")
    print("PASS: installed auditcore_procurement core behavior and independent runtime")


if __name__ == "__main__":
    main()
