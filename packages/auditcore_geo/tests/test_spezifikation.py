"""Eigenschaftstests der Invarianten aus ``docs/spezifikation.md`` (Hypothesis).

Synthetische Koordinaten, kein Netz. Jede Testfunktion nennt ihre Invariante.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from auditcore_geo import (
    ETRS89_UTM32N,
    GRS80,
    KUGEL_6371_KM,
    KUGEL_MITTLERER_RADIUS,
    KoordinatenFehler,
    Lage,
    Punkt,
    UtmZone,
    douglas_peucker,
    enthaelt,
    flaeche_aus_ringen,
    flaechenschwerpunkt,
    geographisch_nach_utm,
    grosskreis_km,
    grosskreis_m,
    lage,
    randabstand_m,
    umkreis,
    utm_nach_geographisch,
)

LAT = st.floats(min_value=-90, max_value=90, allow_nan=False)
LON = st.floats(min_value=-180, max_value=180, allow_nan=False)
PUNKT = st.builds(Punkt, lat=LAT, lon=LON)
PROFIL = st.sampled_from([KUGEL_MITTLERER_RADIUS, KUGEL_6371_KM])
EINSTELLUNG = settings(max_examples=200, deadline=None)
# Viertelgrad-Raster: Rand- und Eckpunkte sind exakt darstellbar.
RASTER = st.integers(min_value=-40, max_value=40).map(lambda n: n / 4)


@EINSTELLUNG
@given(PUNKT, PUNKT, PROFIL)
def test_i1_entfernung_symmetrisch_nichtnegativ_beschraenkt(a: Punkt, b: Punkt, profil) -> None:
    """I1: symmetrisch, ≥ 0, 0 für gleiche Punkte, höchstens halber Erdumfang."""
    d = grosskreis_m(a, b, profil)
    assert d == grosskreis_m(b, a, profil)
    assert 0.0 <= d <= math.pi * profil.radius_m * (1 + 1e-12)
    assert grosskreis_m(a, a, profil) == 0.0


@EINSTELLUNG
@given(PUNKT, PUNKT, PUNKT, PROFIL)
def test_i2_dreiecksungleichung(a: Punkt, b: Punkt, c: Punkt, profil) -> None:
    """I2: d(a, c) ≤ d(a, b) + d(b, c) (Rundungsspielraum 1 mm)."""
    assert (
        grosskreis_m(a, c, profil) <= grosskreis_m(a, b, profil) + grosskreis_m(b, c, profil) + 1e-3
    )


@EINSTELLUNG
@given(PUNKT, PUNKT)
def test_i3_einheit_und_profil_skalieren_linear(a: Punkt, b: Punkt) -> None:
    """I3: km = m / 1000; Profile unterscheiden sich nur um den Radiusfaktor."""
    m = grosskreis_m(a, b, KUGEL_MITTLERER_RADIUS)
    assert grosskreis_km(a, b, KUGEL_MITTLERER_RADIUS) == m / 1000.0
    faktor = KUGEL_6371_KM.radius_m / KUGEL_MITTLERER_RADIUS.radius_m
    assert grosskreis_m(a, b, KUGEL_6371_KM) == pytest.approx(m * faktor, rel=1e-12, abs=1e-9)


@EINSTELLUNG
@given(PUNKT, st.lists(PUNKT, max_size=25), st.floats(0, 3e6, allow_nan=False), PROFIL)
def test_i4_umkreis_vollstaendig_und_sortiert(
    zentrum: Punkt, punkte, radius: float, profil
) -> None:
    """I4: genau die Punkte mit Entfernung ≤ Radius, sortiert nach (Entfernung, Index)."""
    erwartet = sorted(
        (grosskreis_m(zentrum, p, profil), i)
        for i, p in enumerate(punkte)
        if grosskreis_m(zentrum, p, profil) <= radius
    )
    treffer = umkreis(zentrum, punkte, radius, profil)
    assert [(t.abstand_m, t.index) for t in treffer] == erwartet


@EINSTELLUNG
@given(
    st.floats(min_value=-80, max_value=84, allow_nan=False),
    st.floats(min_value=-3, max_value=3, allow_nan=False),
    st.integers(min_value=1, max_value=60),
)
def test_i5_utm_rundlauf_unter_einem_millimeter(lat: float, dlon: float, zone: int) -> None:
    """I5: geographisch → UTM → geographisch innerhalb der Zone (±3°) ≤ 1 mm."""
    utm = UtmZone(zone, lat >= 0, GRS80)
    lon = utm.mittelmeridian_grad + dlon
    assume(-180 <= lon <= 180)
    start = Punkt(lat=lat, lon=lon)
    zurueck = utm_nach_geographisch(*geographisch_nach_utm(start, utm), utm)
    assert grosskreis_m(start, zurueck, KUGEL_MITTLERER_RADIUS) <= 1e-3


@EINSTELLUNG
@given(
    st.lists(st.tuples(RASTER, RASTER), min_size=0, max_size=40, unique=True),
    st.floats(min_value=0, max_value=3, allow_nan=False),
)
def test_i6_douglas_peucker_teilfolge_mit_endpunkten_und_toleranz(punkte, toleranz: float) -> None:
    """I6: Teilfolge der Eingabe, Endpunkte bleiben, jeder weggelassene Punkt liegt
    höchstens ``toleranz`` von der Geraden seines Abschnitts entfernt."""
    ergebnis = douglas_peucker(punkte, toleranz)
    if len(punkte) < 3:
        assert ergebnis == [(float(x), float(y)) for x, y in punkte]
        return
    assert ergebnis[0] == punkte[0] and ergebnis[-1] == punkte[-1]
    indizes = [punkte.index(p) for p in ergebnis]
    assert indizes == sorted(set(indizes))
    for a, b in zip(indizes, indizes[1:], strict=False):
        (x1, y1), (x2, y2) = punkte[a], punkte[b]
        laenge = math.hypot(x2 - x1, y2 - y1)
        for x, y in punkte[a + 1 : b]:
            d = (
                abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / laenge
                if laenge
                else math.hypot(x - x1, y - y1)
            )
            assert d <= toleranz + 1e-9


def _rechteck(w: float, s: float, o: float, n: float) -> list[tuple[float, float]]:
    return [(w, s), (o, s), (o, n), (w, n), (w, s)]


RECHTECK = (
    st.tuples(RASTER, RASTER, RASTER, RASTER)
    .filter(lambda r: r[0] < r[2] and r[1] < r[3])
    .map(lambda r: (r[0], r[1], r[2], r[3]))
)


@EINSTELLUNG
@given(RECHTECK, RASTER, RASTER, st.integers(0, 3), st.booleans())
def test_i7_lage_dreiwertig_unabhaengig_von_umlaufsinn_und_start(
    rechteck, lon: float, lat: float, drehung: int, umkehren: bool
) -> None:
    """I7: INNEN/RAND/AUSSEN wie am Rechteck abgelesen; Umlaufsinn und Startpunkt
    des Rings ändern nichts."""
    w, s, o, n = rechteck
    ring = _rechteck(w, s, o, n)[:-1]
    ring = ring[drehung:] + ring[:drehung]
    if umkehren:
        ring.reverse()
    flaeche = flaeche_aus_ringen([[ring]])
    punkt = Punkt(lat=lat, lon=lon)
    if w < lon < o and s < lat < n:
        erwartet = Lage.INNEN
    elif w <= lon <= o and s <= lat <= n:
        erwartet = Lage.RAND
    else:
        erwartet = Lage.AUSSEN
    assert lage(punkt, flaeche) is erwartet


@EINSTELLUNG
@given(RECHTECK, RASTER, RASTER, PROFIL)
def test_i8_randregel_ausdruecklich_und_randabstand_null_genau_bei_nicht_aussen(
    rechteck, lon: float, lat: float, profil
) -> None:
    """I8: ``enthaelt`` folgt ``lage`` und der ausdrücklichen Randregel;
    ``randabstand_m`` ist 0 genau für Punkte innen oder auf dem Rand, sonst > 0."""
    flaeche = flaeche_aus_ringen([[_rechteck(*rechteck)]])
    punkt = Punkt(lat=lat, lon=lon)
    ort = lage(punkt, flaeche)
    assert enthaelt(flaeche, punkt, rand_gilt_als_innen=True) is (ort is not Lage.AUSSEN)
    assert enthaelt(flaeche, punkt, rand_gilt_als_innen=False) is (ort is Lage.INNEN)
    abstand = randabstand_m(punkt, flaeche, profil)
    assert (abstand == 0.0) is (ort is not Lage.AUSSEN)
    assert abstand >= 0.0


@EINSTELLUNG
@given(RECHTECK)
def test_i9_schwerpunkt_rechteck_ist_mitte(rechteck) -> None:
    """I9: Flächenschwerpunkt (flächengewichtet) eines Rechtecks ist seine Mitte."""
    w, s, o, n = rechteck
    mitte = flaechenschwerpunkt(flaeche_aus_ringen([[_rechteck(w, s, o, n)]]))
    assert mitte.lon == pytest.approx((w + o) / 2, abs=1e-9)
    assert mitte.lat == pytest.approx((s + n) / 2, abs=1e-9)


@EINSTELLUNG
@given(LAT, LON, st.floats(allow_nan=True, allow_infinity=True))
def test_i10_achsenfolge_benannt_ungueltiges_wird_abgewiesen(
    lat: float, lon: float, x: float
) -> None:
    """I10: ``aus_lonlat`` und ``aus_latlon`` sind spiegelbildlich; Werte außerhalb
    des Wertebereichs oder nicht endlich werden abgewiesen, nie geklemmt."""
    assert Punkt.aus_lonlat([lon, lat]) == Punkt.aus_latlon([lat, lon]) == Punkt(lat, lon)
    if not (math.isfinite(x) and -90 <= x <= 90):
        with pytest.raises(KoordinatenFehler):
            Punkt(lat=x, lon=0.0)
    else:
        assert Punkt(lat=x, lon=0.0).lat == x


def test_i5_zone_32n_ist_grs80() -> None:
    """I5: das vordefinierte ETRS89/UTM32N rechnet auf GRS80 (keine Datumstransformation)."""
    assert ETRS89_UTM32N.ellipsoid is GRS80 and ETRS89_UTM32N.zone == 32
