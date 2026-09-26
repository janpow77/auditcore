"""Mit python -I gegen ein installiertes Wheel oder Debian-Paket ausführen; pytest nicht nötig."""

from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_geo import (
    ETRS89_UTM32N,
    KUGEL_6371_KM,
    KUGEL_MITTLERER_RADIUS,
    Lage,
    Punkt,
    douglas_peucker,
    flaeche_aus_geojson,
    grosskreis_km,
    lage,
    legacy,
    randabstand_m,
    umkreis,
    utm_nach_geographisch,
)


def main() -> None:
    """Profile, Umkreis, Fläche mit Rand, UTM und die optionale Adaptergrenze aufrufen."""
    paket = distribution("auditcore_geo")
    assert paket.version == "0.3.0"
    laufzeit = [r for r in paket.requires or [] if "extra ==" not in r]
    assert laufzeit == ["auditcore_common==0.1.1"], laufzeit
    assert find_spec("auditcore") is None
    frankfurt, berlin = Punkt(50.1106, 8.6821), Punkt(52.52, 13.405)
    assert round(grosskreis_km(frankfurt, berlin, KUGEL_MITTLERER_RADIUS), 6) == round(
        legacy.osint_haversine_km(50.1106, 8.6821, 52.52, 13.405), 6
    )
    assert grosskreis_km(frankfurt, berlin, KUGEL_6371_KM) < grosskreis_km(
        frankfurt, berlin, KUGEL_MITTLERER_RADIUS
    )
    datumsgrenze = umkreis(Punkt(0.0, 179.9), [Punkt(0.0, -179.95)], 50_000, KUGEL_MITTLERER_RADIUS)
    assert [t.index for t in datumsgrenze] == [0]
    quadrat = flaeche_aus_geojson(
        {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]}
    )
    assert lage(Punkt(5, 10), quadrat) is Lage.RAND
    assert lage(Punkt(5, 5), quadrat) is Lage.INNEN
    # GEO-C16: zusammengefallene Teilfläche bleibt als Punkt mit Abstand erhalten.
    mit_punkt = flaeche_aus_geojson(
        {
            "type": "MultiPolygon",
            "coordinates": [
                [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                [[[20, 5], [20, 5], [20, 5], [20, 5]]],
            ],
        }
    )
    assert len(mit_punkt.polygone) == 1 and "GEO-C16" in mit_punkt.hinweise[0]
    assert lage(Punkt(5, 20), mit_punkt) is Lage.RAND
    assert 0 < randabstand_m(Punkt(5, 20.001), mit_punkt, KUGEL_MITTLERER_RADIUS) < 200
    punkt = utm_nach_geographisch(477000.0, 5550000.0, ETRS89_UTM32N)
    assert (punkt.lon, punkt.lat) == legacy.osint_utm_nach_wgs84(477000.0, 5550000.0)
    assert len(douglas_peucker([(0, 0), (1, 0.001), (2, 0)], 0.01)) == 2
    # 0.3.0: framework-freier REST-Vertrag ohne Starlette/FastAPI/harvest.
    from auditcore_geo.web import Settings, radius_search

    vertrag = radius_search(
        {
            "zentrum": {"lat": 50.1106, "lon": 8.6821},
            "punkte": [{"id": "b", "lat": 52.52, "lon": 13.405}],
            "radius_m": 500_000,
            "erdmodell": KUGEL_MITTLERER_RADIUS.profil_id,
        },
        Settings(),
    )
    assert vertrag["treffer"] == [
        {"index": 0, "id": "b", "abstand_m": vertrag["treffer"][0]["abstand_m"]}
    ]
    if find_spec("auditcore_harvest") is None:
        try:
            import auditcore_geo.nominatim  # noqa: F401
        except ImportError:
            pass
        else:
            raise AssertionError("Der Nominatim-Adapter muss das Extra [geocoder] verlangen")
    else:
        from auditcore_geo.nominatim import NominatimAdapter

        assert NominatimAdapter.source.source_id == "geo.nominatim_search"
    print(
        "PASS: installed auditcore_geo profiles, radius, boundary, degenerate rings, UTM, "
        "web contract and extra boundary"
    )


if __name__ == "__main__":
    main()
