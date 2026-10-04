"""Versionierte, bewusst unvollständige Tabelle der Kürzungsgründe."""

from __future__ import annotations

import pytest

from auditcore_tyfindings import (
    EingabeFehler,
    ProfilFehler,
    kennziffer_aus_kuerzungsgrund,
    kuerzungsgrund,
    load_kuerzungsgruende,
)
from auditcore_tyfindings.kuerzungsgrund import STANDARDTABELLE, tabelle_aus_dict

FINGERPRINT = "6e8b0cc9ead71dc215e138039d134912498dca4e11644e8373407be4612ddf14"


def test_tabelle_versioniert_mit_fingerprint() -> None:
    tabelle = load_kuerzungsgruende(*STANDARDTABELLE)
    assert (tabelle.id, tabelle.version) == STANDARDTABELLE
    assert tabelle.fingerprint == FINGERPRINT
    assert tabelle.status == "INCOMPLETE_DOMAIN_INPUT_REQUIRED"


def test_null_heisst_kein_kuerzungsgrund() -> None:
    eintrag = kuerzungsgrund("0")
    assert eintrag is not None and eintrag.status == "kein_kuerzungsgrund"
    assert kennziffer_aus_kuerzungsgrund("0") is None


@pytest.mark.parametrize(
    ("schluessel", "kennziffer"),
    [("830", "8.3"), ("810", "8.10"), ("890", "8.90"), (" 810 ", "8.10")],
)
def test_fachlich_zugeordnete_schluessel(schluessel: str, kennziffer: str) -> None:
    eintrag = kuerzungsgrund(schluessel)
    assert eintrag is not None and eintrag.status == "zugeordnet"
    assert kennziffer_aus_kuerzungsgrund(schluessel) == kennziffer


@pytest.mark.parametrize("schluessel", ["8100", "00", "811", ""])
def test_unbekannte_schluessel(schluessel: str) -> None:
    assert kuerzungsgrund(schluessel) is None
    assert kennziffer_aus_kuerzungsgrund(schluessel) is None


def test_schluessel_als_text() -> None:
    with pytest.raises(EingabeFehler):
        kennziffer_aus_kuerzungsgrund(810)  # type: ignore[arg-type]


def _tabelle(*eintraege: dict[str, object]) -> dict[str, object]:
    return {
        "schema": "auditcore_tyfindings.kuerzungsgrund/1",
        "id": "test.synthetisch",
        "version": "1",
        "status": "TEST",
        "eintraege": list(eintraege),
    }


def test_zugeordneter_eintrag_liefert_kennziffer() -> None:
    tabelle = tabelle_aus_dict(
        _tabelle({"schluessel": "X1", "status": "zugeordnet", "kennziffer": "8.1"})
    )
    assert kennziffer_aus_kuerzungsgrund("X1", tabelle) == "8.1"


@pytest.mark.parametrize(
    "eintraege",
    [
        [{"schluessel": "X1", "status": "zugeordnet", "kennziffer": None}],
        [{"schluessel": "X1", "status": "offen", "kennziffer": "8.1"}],
        [{"schluessel": "X1", "status": "unbekannt", "kennziffer": None}],
        [{"schluessel": 1, "status": "offen", "kennziffer": None}],
        [{"schluessel": "X1", "status": "offen"}, {"schluessel": "X1", "status": "offen"}],
        ["X1"],
    ],
)
def test_fehlerhafte_tabelle(eintraege: list[dict[str, object]]) -> None:
    with pytest.raises(ProfilFehler):
        tabelle_aus_dict(_tabelle(*eintraege))


def test_falsches_schema() -> None:
    with pytest.raises(ProfilFehler):
        tabelle_aus_dict({"schema": "x", "eintraege": []})
    with pytest.raises(ProfilFehler):
        load_kuerzungsgruende("efre.kuerzungsgrund_zs", "1999.1.1")
