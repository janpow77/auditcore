"""Derive the packaged rule profiles from the recorded legacy catalog snapshot.

The snapshot was produced by ``capture_regulierung_legacy.py`` from the
executed original. This tool only restructures it; wording, thresholds and
legal references are copied unchanged. ``tests/test_profiles.py`` verifies
the packaged JSON against the fixture again, so a manual edit is detected.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROFILE_VERSION = "2026.09.1"
REGIMES = {"dsgvo": "regulierung.dsgvo", "hdsig_ji": "regulierung.hdsig_ji"}


def reference(question: dict[str, Any], regime: str) -> str:
    """Mirror of ``katalog.fundstelle``; checked against observed outputs in tests."""
    if regime != "hdsig_ji":
        return str(question["rechtsgrundlage"])
    if question.get("rechtsgrundlage_ji"):
        return (
            f"{question['rechtsgrundlage']}; im Dritten Teil HDSIG {question['rechtsgrundlage_ji']}"
        )
    if question["block"] in ("art35_abs3", "dsk_muss_liste"):
        return f"{question['rechtsgrundlage']}; im Dritten Teil HDSIG § 62 Abs. 1 HDSIG"
    return str(question["rechtsgrundlage"])


def build(snapshot: dict[str, Any], source: dict[str, Any], regime: str) -> dict[str, Any]:
    catalog = snapshot["catalog"]
    texts = catalog["vorschlag_text_ji"] if regime == "hdsig_ji" else catalog["vorschlag_text"]
    return {
        "schema": "auditcore_dataprotection.profile/1",
        "id": REGIMES[regime],
        "version": PROFILE_VERSION,
        "status": "SOURCE_CHARACTERIZED",
        "legal_status": (
            "Aus der Quellanwendung übernommenes, charakterisiertes Softwareprofil. "
            "Keine rechtliche Prüfung oder Bestätigung der Auslegung, Schwellen oder "
            "Gewichtungen durch diese Bibliothek."
        ),
        "source": source,
        "regime": {
            "key": regime,
            "title": catalog["regime_titel"][regime],
            "explanation": catalog["regime_erlaeuterung"][regime],
            "notice": catalog["regime_hinweis_ji"] if regime == "hdsig_ji" else "",
            "norms": catalog["normen"][regime],
        },
        "screening": {
            "blocks": [{"key": k, "title": v} for k, v in catalog["block_titel"].items()],
            "points_threshold": catalog["schwelle_punkte"],
            "questions": [
                {
                    "key": q["schluessel"],
                    "block": q["block"],
                    "text": q["text"],
                    "legal_basis": q["rechtsgrundlage"],
                    "legal_basis_ji": q["rechtsgrundlage_ji"],
                    "reference": reference(q, regime),
                    "effect": q["wirkung"],
                    "explanation": q["erlaeuterung"],
                    "prefill": q["vorbelegung"],
                }
                for q in catalog["fragen"]
            ],
        },
        "risk": {
            "scale": {"min": 1, "max": 4},
            "severity": catalog["schwere"],
            "likelihood": catalog["wahrscheinlichkeit"],
            "dimensions": [{"key": k, "title": v} for k, v in catalog["dimensionen"].items()],
            "sdm_dimensions": catalog["sdm_dimensionen"],
            "bands": [
                {"up_to": 0, "label": "offen"},
                {"up_to": 4, "label": "gering"},
                {"up_to": 9, "label": "mittel"},
                {"up_to": None, "label": "hoch"},
            ],
            "mitigation": {"cap_per_axis": 2, "floor": 1},
            "measures": [
                {
                    "key": m["schluessel"],
                    "title": m["bezeichnung"],
                    "legal_basis": m["rechtsgrundlage"],
                    "reduces_likelihood": m["senkt_wahrscheinlichkeit"],
                    "reduces_severity": m["senkt_schwere"],
                    "explanation": m["erlaeuterung"],
                }
                for m in catalog["massnahmen"]
            ],
        },
        "recommendation": {
            "consult_from": 10,
            "conditions_from": 5,
            "texts": texts,
            "maximum_product": 16,
        },
        "prefill": {"large_scale_threshold": catalog["umfang_schwelle"]},
        "workflow": {
            "min_justification_length": catalog["mindestlaenge_begruendung"],
            "dpo_votes": ["zugestimmt", "zugestimmt_mit_auflagen", "abgelehnt"],
            "significant_fields": [
                {"key": k, "title": v} for k, v in catalog["wesentliche_felder"].items()
            ],
            "status_texts": catalog["status_text"],
            "vote_texts": catalog["votum_text"],
            "data_subject_view_templates": catalog["standpunkt_begruendungen"],
        },
        "register": {
            "columns": [{"key": k, "title": t} for k, t in catalog["verzeichnis_spalten"]],
            "legal_references": catalog["verzeichnis_fundstellen"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("output", type=Path, help="package profiles directory")
    args = parser.parse_args()
    snapshot = json.loads(args.fixture.read_text())
    source = {
        "repository": snapshot["source"]["repository"],
        "commit": snapshot["source"]["commit"],
        "files": [
            f for f in snapshot["source"]["files"] if "dsfa/" in f["path"] or "dsgvo" in f["path"]
        ],
        "rights": "USER_AUTHORIZED_MIT",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    for regime, profile_id in REGIMES.items():
        path = args.output / f"{profile_id}-{PROFILE_VERSION}.json"
        profile = build(snapshot, source, regime)
        path.write_text(json.dumps(profile, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
        print(path)


if __name__ == "__main__":
    main()
