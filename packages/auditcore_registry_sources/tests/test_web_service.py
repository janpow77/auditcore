"""Review service: runs, breakdown, freshness, filters (contract screening_review/1)."""

from __future__ import annotations

from typing import Any

import pytest
from web_support import ALICE, make_service, pep_body, sanctions_body

from auditcore_registry_sources.web import CONTRACT, ReviewError


def _hits(run: dict[str, Any], subject: int = 0) -> list[dict[str, Any]]:
    return list(run["subjects"][subject]["hits"])


def test_sanctions_run_has_findings_per_list_and_explained_hits() -> None:
    service = make_service()
    run = service.create_run(sanctions_body(), ALICE)
    assert run["contract"] == CONTRACT
    assert run["run_id"] == "run-1"
    assert run["created_by"] == {"id": "pruefer-a", "display_name": "Prüferin A"}
    first, second = run["subjects"]
    assert first["status"] == "HITS"
    assert [(f["list_key"], f["searched"]) for f in first["findings"]] == [
        ("eu_fsf", True),
        ("un_sc", True),
        ("us_ofac_sdn", False),
    ]
    assert "nicht abgefragt" in first["findings"][2]["note"]
    assert second["status"] == "INCOMPLETE"
    assert any("keine Unbedenklichkeit" in text for text in second["limitations"])
    best = _hits(run)[0]
    assert best["entry"]["entry_id"] == "eu-001"
    assert best["entry"]["addresses"] == "Musterstraße 1, 12345 Musterstadt"
    assert best["review"]["status"] == "open"
    breakdown = best["breakdown"]
    assert breakdown["consistent"] is True
    kinds = [step["step"] for step in breakdown["steps"]]
    assert kinds[:3] == ["normalization", "normalization", "base"]
    assert "adjustment" in kinds and kinds[-1] == "result"
    assert breakdown["scale"] == {"min": 0.0, "max": 100.0}
    assert [c["class"] for c in breakdown["classes"]] == ["exact", "high", "medium"]


def test_conflicting_birth_year_is_visible_in_breakdown() -> None:
    run = make_service().create_run(sanctions_body(), ALICE)
    un_hit = next(h for h in _hits(run) if h["list_key"] == "un_sc")
    assert un_hit["dob_conflict"] and un_hit["country_conflict"]
    points = [s["points"] for s in un_hit["breakdown"]["steps"] if s["step"] == "adjustment"]
    assert points == [-18.0, -10.0]
    assert un_hit["breakdown"]["consistent"] is True


def test_run_records_source_state_at_run_time() -> None:
    run = make_service(stale_after_days=30).create_run(sanctions_body(), ALICE)
    states = {s["list"]["key"]: s for s in run["sources"]}
    assert states["eu_fsf"]["freshness"]["status"] == "current"
    assert states["un_sc"]["freshness"]["status"] == "stale"
    assert states["us_ofac_sdn"]["freshness"]["status"] == "unknown"
    assert states["us_ofac_sdn"]["searchable"] is False


def test_sources_without_threshold_are_not_judged() -> None:
    sources = make_service().sources()["sources"]
    eu = next(s for s in sources if s["list"]["key"] == "eu_fsf")
    assert eu["freshness"] == {
        "status": "not_judged",
        "label": "nicht bewertet",
        "age_days": 2.8,
        "stale_after_days": None,
    }
    assert {s["kind"] for s in sources} == {"sanctions", "pep"}


def test_pep_run_uses_token_profile_and_consistent_breakdown() -> None:
    run = make_service().create_run(pep_body(), ALICE)
    hit = _hits(run)[0]
    assert hit["entry"]["entry_id"] == "pep-001"
    assert hit["score"] == 1.0 and hit["confidence"] == "exact"
    assert hit["breakdown"]["scale"] == {"min": 0.0, "max": 1.0}
    assert hit["breakdown"]["consistent"] is True
    partial = make_service().create_run(
        pep_body(subjects=[{"name": "Petra Musterfrau Beispiel", "country": "de"}], min_score=0.5),
        ALICE,
    )
    steps = _hits(partial)[0]["breakdown"]["steps"]
    assert [s["step"] for s in steps] == [
        "normalization",
        "normalization",
        "base",
        "adjustment",
        "adjustment",
        "result",
    ]
    assert _hits(partial)[0]["breakdown"]["consistent"] is True


def test_pep_threshold_range_is_checked() -> None:
    with pytest.raises(ReviewError) as caught:
        make_service().create_run(pep_body(min_score=80), ALICE)
    assert caught.value.status == 422


@pytest.mark.parametrize(
    ("body", "fragment"),
    [
        (sanctions_body(lists=["gibt_es_nicht"]), "Unbekannte oder unpassende"),
        (sanctions_body(lists=["peps"]), "Unbekannte oder unpassende"),
        (sanctions_body(profile={"id": "flowinvoice.pep_bulk", "version": "2026.09.2"}), "passt"),
        (sanctions_body(profile={"id": "fehlt", "version": "1"}), "nicht vorhanden"),
        (sanctions_body(subjects=[{"name": "Ab"}]), "mindestens 3 Zeichen"),
        (sanctions_body(min_score=10), "Mindestwert"),
    ],
)
def test_invalid_runs_are_rejected_with_reason(body: dict[str, Any], fragment: str) -> None:
    with pytest.raises(ReviewError) as caught:
        make_service().create_run(body, ALICE)
    assert caught.value.status == 422
    assert fragment in caught.value.message


def test_settings_list_screening_profiles_with_recommendation() -> None:
    settings = make_service(four_eyes_outcomes=["confirmed"]).settings()
    profiles = {(p["id"], p["version"]): p for p in settings["profiles"]}
    assert profiles[("audit_designer.sanctions_screening", "2026.09.2")]["recommended"]
    assert profiles[("flowinvoice.pep_bulk", "2026.09.2")]["kind"] == "pep"
    assert not any(p["id"] == "flowinvoice.sanctions_local" for p in settings["profiles"])
    assert settings["four_eyes_outcomes"] == ["confirmed"]


def test_filters_select_hits_but_keep_counts() -> None:
    service = make_service()
    run = service.create_run(sanctions_body(), ALICE)
    view = service.get_run(run["run_id"], {"list": "un_sc"})
    assert {h["list_key"] for h in _hits(view)} == {"un_sc"}
    assert view["subjects"][0]["hits_before_filter"] == len(_hits(run))
    assert view["hit_count"] == run["hit_count"]
    strong = _hits(service.get_run(run["run_id"], {"min_score": "95"}))
    assert strong and all(h["score"] >= 95 for h in strong)
    assert len(strong) < len(_hits(run))
    with pytest.raises(ReviewError):
        service.get_run(run["run_id"], {"status": "kaputt"})
    with pytest.raises(ReviewError):
        service.get_run(run["run_id"], {"min_score": "viel"})


def test_unknown_run_is_404() -> None:
    with pytest.raises(ReviewError) as caught:
        make_service().get_run("gibt-es-nicht")
    assert caught.value.status == 404


def test_runs_are_listed_newest_first_with_counts() -> None:
    service = make_service()
    service.create_run(sanctions_body(), ALICE)
    service.create_run(pep_body(), ALICE)
    runs = service.list_runs()["runs"]
    assert {r["kind"] for r in runs} == {"sanctions", "pep"}
    sanctions = next(r for r in runs if r["kind"] == "sanctions")
    assert sanctions["subjects_with_hits"] == 1 and sanctions["subjects_incomplete"] == 1
    assert sanctions["review_counts"]["open"] == sanctions["hit_count"]
    assert sanctions["review_complete"] is False
