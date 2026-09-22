"""Derive packaged data profiles from the recorded legacy constants (no manual edits).

``tests/test_profiles.py`` compares the packaged JSON with the fixtures again.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "tests"))
from conftest import load, revive  # noqa: E402

VERSION = "2026.09.1"


def source(variant: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "repository": data["source"]["repository"],
        "commit": data["source"]["commit"],
        "files": [{"path": f["path"], "git_blob": f["git_blob"]} for f in data["source"]["files"]],
        "variant": variant,
    }


def main() -> None:
    target = HERE / "src/auditcore_funding_sources/data"
    workshop = load("flowworkshop")
    constants = revive(workshop["constants"])
    profile = {
        "schema": "auditcore_funding_sources.beneficiary_profile/1",
        "id": "flowworkshop.beneficiaries",
        "version": VERSION,
        "status": "SOURCE_CHARACTERIZED",
        "source": source("flowworkshop", workshop),
        "column_patterns": [
            [role, list(patterns)] for role, patterns in constants["column_patterns"].items()
        ],
        "canonical_aliases": constants["canonical_aliases"],
        "hash_fields": constants["hash_fields"],
        "nameless": constants["nameless"],
        "fund_columns": constants["fund_columns"],
        "default_mode": constants["default_mode"],
        "modes": constants["modes"],
        "legal_suffixes": constants["legal_suffixes"],
        "filler_words": constants["filler_words"],
    }
    (target / f"flowworkshop.beneficiaries-{VERSION}.json").write_text(
        json.dumps(profile, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    )
    designer = load("designer")
    dconst = revive(designer["constants"])
    authority = {
        "schema": "auditcore_funding_sources.authority_levels/1",
        "id": "designer.deminimis.authority_levels",
        "version": VERSION,
        "status": "SOURCE_CHARACTERIZED",
        "source": source("designer", designer),
        "rules": dconst["authority_rules"],
        "levels": dconst["authority_levels"],
        "federal": "Bund",
        "undetermined": "unbestimmt",
    }
    (target / f"designer.deminimis.authority_levels-{VERSION}.json").write_text(
        json.dumps(authority, indent=1, ensure_ascii=False) + "\n"
    )
    cumulation = {
        "schema": "auditcore_funding_sources.cumulation_profile/1",
        "id": "designer.deminimis.cumulation",
        "version": VERSION,
        "status": "REVIEW_REQUIRED",
        "legacy_method_version": dconst["method_version"],
        "legal_basis": "Artikel 3 Absatz 2 und Artikel 6 der Verordnung (EU) 2023/2831",
        "valid_from": None,
        "valid_to": None,
        "validity_note": (
            "Gültigkeitszeitraum der Regel nicht fachlich festgelegt; aus der Quellanwendung "
            "übernommen, keine bestätigte aktuelle Rechtslage."
        ),
        "ceiling_eur": dconst["ceiling_general"],
        "ceiling_applies_to_type": "GENERAL",
        "types_without_ceiling": dconst["types_without_ceiling"],
        "window": {"years": 3, "rule": "calendar-years-inclusive-endpoints"},
        "notices": dconst["notices"],
        "source": source("designer", designer),
    }
    (target / f"designer.deminimis.cumulation-{VERSION}.json").write_text(
        json.dumps(cumulation, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    )
    state_aid = {
        "schema": "auditcore_funding_sources.name_profile/1",
        "id": "designer.state_aid",
        "version": VERSION,
        "status": "SOURCE_CHARACTERIZED",
        "source": source("designer", designer),
        "legal_suffixes": dconst["sa_legal_suffixes"],
        "filler_words": dconst["sa_filler_words"],
        "transliteration": dconst["sa_transliteration"],
    }
    (target / f"designer.state_aid-{VERSION}.json").write_text(
        json.dumps(state_aid, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    )
    print("profiles written")


if __name__ == "__main__":
    main()
