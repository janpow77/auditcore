"""Canonical procurement notice record contract shared by online harvest and file import."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

RECORD_CONTRACT = "auditcore_procurement.notice/1"

#: Coverage labels. Award-only results must not be presented as full coverage.
COVERAGE_AWARDS_WITH_WINNER = "award_notices_with_winner"
COVERAGE_ALL_NOTICES = "all_notice_types"
COVERAGE_TENDER_SEARCH = "tender_search_results"

NOTICE_FIELDS: tuple[str, ...] = (
    "notice_id",
    "contract_id",
    "document_number",
    "contracting_authority_name",
    "contracting_authority_country",
    "contracting_authority_address",
    "contractor_name",
    "contractor_country",
    "contractor_address",
    "contractor_vat_id",
    "title",
    "description",
    "cpv_codes",
    "nuts_codes",
    "contract_value",
    "contract_value_currency",
    "estimated_value",
    "publication_date",
    "contract_award_date",
    "contract_start_date",
    "contract_end_date",
    "procedure_type",
    "contract_type",
)
NUMERIC_FIELDS = frozenset({"contract_value", "estimated_value"})
DATE_FIELDS = frozenset(
    {"publication_date", "contract_award_date", "contract_start_date", "contract_end_date"}
)


@dataclass(frozen=True)
class Issue:
    """Validation or plausibility note; ``blocking`` means the value is unreliable."""

    code: str
    message: str
    blocking: bool
    field: str = ""

    def to_dict(self) -> dict[str, Any]:
        """JSON representation."""
        return {
            "code": self.code,
            "message": self.message,
            "blocking": self.blocking,
            "field": self.field,
        }


def validate_record(record: Mapping[str, Any], *, require_contractor: bool = True) -> list[Issue]:
    """Check a canonical record: known fields, value types, ISO dates, required contractor."""
    issues: list[Issue] = []
    for key, value in record.items():
        if key not in NOTICE_FIELDS:
            issues.append(Issue("unknown_field", f"Unbekanntes Feld '{key}'.", True, key))
        elif key in NUMERIC_FIELDS:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                issues.append(Issue("not_numeric", f"'{key}' muss eine Zahl sein.", True, key))
        elif not isinstance(value, str) or not value.strip():
            issues.append(Issue("not_text", f"'{key}' muss nichtleerer Text sein.", True, key))
        elif key in DATE_FIELDS and not _is_iso_date(value):
            issues.append(Issue("not_iso_date", f"'{key}' ist kein ISO-Datum.", True, key))
    if require_contractor and not record.get("contractor_name"):
        issues.append(Issue("missing_contractor", "Auftragnehmer fehlt.", True, "contractor_name"))
    return issues


def _is_iso_date(value: str) -> bool:
    return (
        len(value) == 10
        and value[4] == "-"
        and value[7] == "-"
        and value.replace("-", "").isdigit()
    )
