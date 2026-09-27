"""Eigenschaftstests der Invarianten aus ``docs/spezifikation.md`` (Hypothesis).

Synthetische Antworten, Szenarien und Verzeichnisse; keine echten Personen.
Jede Testfunktion nennt ihre Invariante.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_dataprotection import (
    Actor,
    FourEyesViolation,
    Permission,
    RegisterService,
    StaleRevisionError,
    ValidationError,
    finalize_consultation,
    load_profile,
    propose,
    screen,
)
from auditcore_dataprotection.memory import (
    FixedClock,
    InMemoryRegisterRepository,
    ListAuditSink,
    RoleAuthorizer,
    SequentialIds,
)
from auditcore_dataprotection.rules import (
    DECISIONS,
    EFFECT_HARD,
    EFFECT_POINT,
    RECOMMENDATION_CONSULTATION,
    RECOMMENDATION_INCOMPLETE,
    RECOMMENDATION_RELEASE,
    RECOMMENDATION_RELEASE_WITH_CONDITIONS,
    RECOMMENDATION_SCREENING_ONLY,
)

EINSTELLUNG = settings(max_examples=100, deadline=None)
PROFILE = [
    load_profile("auditcore.dsgvo", "2026.10.3"),
    load_profile("auditcore.hdsig_ji", "2026.10.3"),
    load_profile("regulierung.dsgvo", "2026.09.1"),
]
PROFIL = st.sampled_from(PROFILE)
ANTWORT = st.sampled_from([True, False, None, "unbekannt", "ja", "nein"])
RANG = {
    RECOMMENDATION_RELEASE: 0,
    RECOMMENDATION_RELEASE_WITH_CONDITIONS: 1,
    RECOMMENDATION_CONSULTATION: 2,
}


@st.composite
def antworten(draw: st.DrawFn, profil, vollstaendig: bool = False) -> dict[str, object]:
    werte = st.booleans() if vollstaendig else ANTWORT
    result: dict[str, object] = {}
    for key in profil.question_keys:
        if vollstaendig or draw(st.booleans()):
            result[key] = draw(werte)
    return result


@st.composite
def szenario(draw: st.DrawFn, profil) -> dict[str, object]:
    stufen = st.integers(profil.scale_min, profil.scale_max)
    massnahmen = draw(
        st.lists(st.sampled_from([m.key for m in profil.measures]), unique=True, max_size=3)
    )
    return {
        "dimension": draw(st.sampled_from(list(profil.dimensions))),
        "description": "Synthetisches Szenario",
        "severity": draw(stufen),
        "likelihood": draw(stufen),
        "measures": massnahmen,
    }


def _ja(wert: object) -> bool:
    return wert is True or wert == "ja"


@EINSTELLUNG
@given(st.data(), PROFIL)
def test_i1_offene_angaben_gelten_nie_als_nein(data: st.DataObject, profil) -> None:
    """I1: ohne bejahtes Muss-Kriterium und unter der Punktschwelle bleibt eine Erhebung
    mit offenen oder unbekannten Fragen ``unvollstaendig`` – nie ``keine_pflicht``."""
    roh = data.draw(antworten(profil))
    ergebnis = screen(profil, roh)
    offen = [
        k
        for k in profil.question_keys
        if k not in roh or not isinstance(roh[k], bool) and roh[k] not in ("ja", "nein")
    ]
    harte = [q.key for q in profil.questions if q.effect == EFFECT_HARD and _ja(roh.get(q.key))]
    punkte = sum(1 for q in profil.questions if q.effect == EFFECT_POINT and _ja(roh.get(q.key)))
    if harte or punkte >= profil.points_threshold:
        assert ergebnis.outcome == "pflicht"
    elif offen:
        assert ergebnis.outcome == "unvollstaendig"
        assert propose(profil, roh).recommendation == RECOMMENDATION_INCOMPLETE
    else:
        assert ergebnis.outcome == "keine_pflicht"
        assert propose(profil, roh).recommendation == RECOMMENDATION_SCREENING_ONLY


@EINSTELLUNG
@given(st.data(), PROFIL)
def test_i2_schwellwertanalyse_monoton_in_ja_antworten(data: st.DataObject, profil) -> None:
    """I2: ein weiteres „Ja“ macht aus einer Pflicht nie „keine Pflicht“ oder „unvollständig“."""
    roh = data.draw(antworten(profil, vollstaendig=True))
    key = data.draw(st.sampled_from(profil.question_keys))
    vorher = screen(profil, roh).outcome
    nachher = screen(profil, {**roh, key: True}).outcome
    if vorher == "pflicht":
        assert nachher == "pflicht"
    assert nachher in ("pflicht", "keine_pflicht")


@EINSTELLUNG
@given(st.data(), PROFIL)
def test_i3_muss_kriterium_entscheidet_allein(data: st.DataObject, profil) -> None:
    """I3: ein bejahtes Muss-Kriterium ergibt „pflicht“, gleich wie die übrigen Antworten lauten."""
    roh = data.draw(antworten(profil))
    hart = data.draw(st.sampled_from([q.key for q in profil.questions if q.effect == EFFECT_HARD]))
    assert screen(profil, {**roh, hart: True}).outcome == "pflicht"


@EINSTELLUNG
@given(st.data(), PROFIL)
def test_i4_massnahmen_mindern_begrenzt_und_nie_unter_die_untergrenze(
    data: st.DataObject, profil
) -> None:
    """I4: je Achse gilt Untergrenze ≤ netto ≤ brutto; die Minderung je Achse ist durch
    die Obergrenze des Profils beschränkt."""
    szenarien = data.draw(st.lists(szenario(profil), min_size=1, max_size=4))
    hart = next(q.key for q in profil.questions if q.effect == EFFECT_HARD)
    vorschlag = propose(profil, {hart: True}, szenarien)
    assert vorschlag.risk is not None
    for r in vorschlag.risk.scenarios:
        assert profil.mitigation_floor <= r.net_severity <= r.gross_severity
        assert profil.mitigation_floor <= r.net_likelihood <= r.gross_likelihood
        assert 0 <= r.reduction_severity <= profil.mitigation_cap
        assert 0 <= r.reduction_likelihood <= profil.mitigation_cap
        assert r.net <= r.gross


@EINSTELLUNG
@given(st.data(), PROFIL)
def test_i5_zusaetzliches_szenario_senkt_die_empfehlung_nie(data: st.DataObject, profil) -> None:
    """I5: die Empfehlung folgt dem höchsten Risiko; ein weiteres Szenario kann sie nur
    erhöhen oder gleich lassen."""
    hart = next(q.key for q in profil.questions if q.effect == EFFECT_HARD)
    szenarien = data.draw(st.lists(szenario(profil), min_size=1, max_size=3))
    weiteres = data.draw(szenario(profil))
    vorher = propose(profil, {hart: True}, szenarien).recommendation
    nachher = propose(profil, {hart: True}, [*szenarien, weiteres]).recommendation
    assert RANG[nachher] >= RANG[vorher]


@EINSTELLUNG
@given(
    PROFIL,
    st.sampled_from(["false", "true", 0, 1, 1.0, "Ja", [], {"ja": "x"}]),
    st.text(alphabet="abcxyz_", min_size=1, max_size=8),
)
def test_i6_eingaben_werden_geprueft_nicht_umgedeutet(profil, schlecht, fremd: str) -> None:
    """I6: nicht boolesche Antworten, unbekannte Fragen, doppelte Maßnahmen und Werte
    außerhalb der Skala führen zu ``ValidationError``."""
    key = profil.question_keys[0]
    with pytest.raises(ValidationError):
        screen(profil, {key: schlecht})
    if fremd not in profil.question_keys:
        with pytest.raises(ValidationError):
            screen(profil, {fremd: True})
    massnahme = profil.measures[0].key
    basis = {
        "dimension": next(iter(profil.dimensions)),
        "description": "x",
        "severity": 2,
        "likelihood": 2,
    }
    for kaputt in (
        {**basis, "measures": [massnahme, massnahme]},
        {**basis, "severity": profil.scale_max + 1},
        {**basis, "likelihood": profil.scale_min - 1},
        {**basis, "residual_severity": profil.scale_max + 1},
    ):
        with pytest.raises(ValidationError):
            propose(profil, {}, [kaputt])


@EINSTELLUNG
@given(st.data(), PROFIL)
def test_i7_vorschlag_deterministisch_und_profilgebunden(data: st.DataObject, profil) -> None:
    """I7: gleiche Eingabe, gleicher Vorschlag; er nennt Profilkennung, Version und
    Fingerabdruck."""
    roh = data.draw(antworten(profil))
    szenarien = data.draw(st.lists(szenario(profil), max_size=3))
    a, b = propose(profil, roh, szenarien), propose(profil, roh, szenarien)
    assert a == b
    assert a.profile == profil.reference
    assert set(a.profile) >= {"id", "version", "fingerprint"}


@EINSTELLUNG
@given(st.data(), st.sampled_from(PROFILE[:2]), st.sampled_from(DECISIONS))
def test_i8_konsultation_nur_bei_hohem_restrisiko_nach_entscheidung(
    data: st.DataObject, profil, entscheidung: str
) -> None:
    """I8: der endgültige Konsultationshinweis ist genau dann „erforderlich“, wenn die
    Bewertung die Konsultation empfiehlt und die Verarbeitung nicht verworfen wird;
    vor der Entscheidung gibt es höchstens einen vorläufigen Hinweis."""
    hart = next(q.key for q in profil.questions if q.effect == EFFECT_HARD)
    szenarien = data.draw(st.lists(szenario(profil), min_size=1, max_size=3))
    vorschlag = propose(profil, {hart: True}, szenarien)
    assert vorschlag.consultation_required is False
    assert vorschlag.consultation_notice is not None
    assert vorschlag.consultation_notice["final"] is False
    endgueltig = finalize_consultation(profil, vorschlag.to_dict(), entscheidung)
    erwartet = (
        vorschlag.recommendation == RECOMMENDATION_CONSULTATION and entscheidung != "verworfen"
    )
    assert endgueltig["consultation_required"] is erwartet
    assert endgueltig["consultation_notice"]["final"] is True
    with pytest.raises(ValidationError):
        finalize_consultation(profil, {"recommendation": RECOMMENDATION_INCOMPLETE}, entscheidung)


def _dienst() -> RegisterService:
    rollen = RoleAuthorizer({"alle": frozenset(Permission)})
    return RegisterService(
        InMemoryRegisterRepository(),
        rollen,
        ListAuditSink(),
        FixedClock(),
        SequentialIds(),
        PROFILE[0],
    )


def _person(name: str) -> Actor:
    return Actor(name, frozenset({"mandant-a", "mandant-b"}), frozenset({"alle"}))


INHALT = {
    "deckblatt": {"verantwortlicher": {"name": "Behörde"}, "dsb": {"name": "DSB"}},
    "referate": ["Referat I"],
    "taetigkeiten": [
        {
            "id": "t1",
            "name": "Tätigkeit",
            "referat": "Referat I",
            "zweck": "Zweck",
            "ermaechtigungsgrundlage": "Gesetz",
            "kategorien_betroffene": "Antragsteller",
            "kategorien_daten": "Stammdaten",
            "kategorien_empfaenger": "keine",
            "speicherdauer": "10 Jahre",
            "tom": "Rollenkonzept",
            "drittlandtransfer": False,
            "besondere_kategorien": False,
            "daten_art10": False,
            "anzahl_betroffene": 5,
        }
    ],
}
NAME = st.text(alphabet="abcdefghij", min_size=1, max_size=6)


@EINSTELLUNG
@given(st.lists(NAME, min_size=1, max_size=4), NAME)
def test_i9_vier_augen_wer_bearbeitet_hat_gibt_nicht_frei(bearbeiter, freigeber: str) -> None:
    """I9: wer einen Entwurf bearbeitet hat – auch in früheren Revisionen –, darf ihn nicht
    freigeben; jede andere berechtigte Person darf es."""
    dienst = _dienst()
    fassung = None
    for name in bearbeiter:
        revision = None if fassung is None else fassung.revision
        fassung = dienst.save_draft("mandant-a", _person(name), INHALT, expected_revision=revision)
    assert fassung is not None
    if freigeber in bearbeiter:
        with pytest.raises(FourEyesViolation):
            dienst.release("mandant-a", _person(freigeber), expected_revision=fassung.revision)
    else:
        frei = dienst.release("mandant-a", _person(freigeber), expected_revision=fassung.revision)
        assert frei.released_by == freigeber
        assert dienst.released("mandant-b", _person(freigeber)) is None


@EINSTELLUNG
@given(st.integers(min_value=-3, max_value=6))
def test_i10_veraltete_revision_wird_abgewiesen(abweichung: int) -> None:
    """I10: Speichern und Freigeben verlangen die aktuelle Revision (optimistische Sperre)."""
    dienst = _dienst()
    fassung = dienst.save_draft("mandant-a", _person("anna"), INHALT)
    falsch = fassung.revision + abweichung
    if abweichung:
        with pytest.raises(StaleRevisionError):
            dienst.save_draft("mandant-a", _person("anna"), INHALT, expected_revision=falsch)
        with pytest.raises(StaleRevisionError):
            dienst.release("mandant-a", _person("bert"), expected_revision=falsch)
    else:
        neu = dienst.save_draft("mandant-a", _person("anna"), INHALT, expected_revision=falsch)
        assert neu.revision == fassung.revision + 1 and neu.version == fassung.version
