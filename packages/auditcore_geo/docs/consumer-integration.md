# Consumer-Umstellung

Status: audit_designer nutzt 0.1.0 (PR janpow77/audit_designer#382, Release
v0.3.0); osint, flowsearch und flowworkshop sind **geplant**. Für 0.2.0 gilt wie
zuvor: keine Requirements-Änderung und kein Push in Consumer-Repositories aus
diesem Repository; die Umstellung ist unten beschrieben und getestet.

## audit_designer: Workaround `geo_flaeche.py` entfällt mit 0.2.0

Stand: audit_designer `main@7226382` (PR #382, gemergt) nutzt `auditcore_geo`
0.1.0 und liest Flächen über den eigenen Workaround
`backend/app/core/shared/geo_flaeche.py` (`GeoFlaeche`, `lies_flaeche`), weil
0.1.0 Geometrien mit zu Punkt/Linie zusammengefallenen Ringen als Ganzes
verwarf (15 von 1 051 hessischen Natura-2000-Gebieten betroffen, 10 davon
vollständig). 0.2.0 behandelt diese Ringe selbst (GEO-C16) mit derselben
Semantik: echte Teilflächen bleiben Fläche, zusammengefallene Außenringe
zählen als Punkt/Linie mit Abstand, zusammengefallene Löcher entfallen – und
nennt jeden Fall in `Flaeche.hinweise`. **Nach dem Umstieg auf 0.2.0 kann
`geo_flaeche.py` ersatzlos gelöscht werden.**

Getestet in einer Wegwerf-Kopie (`git archive` von `audit_designer@7226382`,
isolierte venv, kein Push, keine Datenbank) mit dem gebauten Wheel
`auditcore_geo-0.2.0-py3-none-any.whl`:

| Lauf | `tests/test_geo_auditcore.py` + `tests/test_vpai_gis_helpers.py` |
|---|---|
| designer unverändert, Wheel 0.1.0 (Release v0.3.0) | 53 passed |
| designer unverändert, Wheel 0.2.0 (Workaround aktiv) | 53 passed |
| designer umgestellt (Patch unten, `geo_flaeche.py` gelöscht), Wheel 0.2.0 | 53 passed |

`tests/test_flowstat_geo_handler.py` braucht PostgreSQL: NOT_EXECUTED.
Vergleich Workaround gegen Umstellung auf den 12 Geometrien × 14 Punkten von
`tests/fixtures/entartet_observed.json` (`_point_in_geometry`,
`_geometry_edge_distance_m`, `_NaturaClient._distance_to_geometry_m`,
`_geometry_centroid`): alle Abstände identisch. Zwei bewusste Unterschiede:

- Ein Punkt **genau auf** einem zusammengefallenen Außenring liegt jetzt auf
  dem Rand und zählt nach D2 als innen (`_point_in_geometry` → `True`,
  vorher `False`; Abstand in beiden Fällen 0). 11 von 168 Punkten; so
  verhielt sich der Workaround bereits bei kollinearen Ringen mit drei
  verschiedenen Punkten.
- Schwerpunkt eines Gebiets **ohne** echte Teilfläche: Linien
  längengewichtet, sonst Punktmittel (wie shapely), statt Mittel aller
  verschiedenen Punkte (1 von 12 Geometrien: `multi_nur_entartet`).

Umstellung (nach Anhebung der Requirements auf `auditcore_geo[geocoder]==0.2.0`,
Debian `python3-auditcore-geo (>= 0.2.0)`) – `backend/app/core/shared/geo_flaeche.py`
löschen und:

```diff
diff --git a/backend/app/api/vpai_notebook/gis/_common.py b/backend/app/api/vpai_notebook/gis/_common.py
index ea02be1..e04da62 100644
--- a/backend/app/api/vpai_notebook/gis/_common.py
+++ b/backend/app/api/vpai_notebook/gis/_common.py
@@ -19,14 +19,25 @@ from datetime import datetime
 from decimal import Decimal
 from typing import Any
 
-from auditcore_geo import KUGEL_MITTLERER_RADIUS, KoordinatenFehler, Punkt, grosskreis_m
+from auditcore_geo import (
+    EMPFOHLEN_RAND_GILT_ALS_INNEN,
+    KUGEL_MITTLERER_RADIUS,
+    Flaeche,
+    GeometrieFehler,
+    KoordinatenFehler,
+    Punkt,
+    enthaelt,
+    flaeche_aus_geojson,
+    flaechenschwerpunkt,
+    grosskreis_m,
+    randabstand_m,
+)
 from fastapi import HTTPException
 from pydantic import BaseModel, Field
 from sqlalchemy.orm import Session
 
 from app.core.config import settings
 from app.core.shared import nominatim
-from app.core.shared.geo_flaeche import GeoFlaeche, lies_flaeche
 from app.models.vpai_notebook import (
     VpaiGisFeature,
     VpaiGisLayer,
@@ -228,17 +239,23 @@ def _iter_ring_coordinates(geometry: dict[str, Any]) -> list[list[tuple[float, f
 # ``auditcore_geo`` rechnet je Teilfläche mit eigenem Außenring und eigenen
 # Löchern; Randpunkte zählen als innen (D2). Schwerpunkte sind
 # flächengewichtet (GEO-C09) statt Mittel aller Stützpunkte. Erdmodell:
-# Mittelradius R1 = 6 371 008,8 m wie bisher.
+# Mittelradius R1 = 6 371 008,8 m wie bisher. Zu Punkt oder Linie
+# zusammengefallene Ringe (gerundete Kleinstgebiete) behandelt auditcore_geo
+# ab 0.2.0 selbst (GEO-C16): Objekt ohne Fläche mit Abstand, Hinweis in
+# ``Flaeche.hinweise``.
 # ---------------------------------------------------------------------------
 
 
-def _geo_flaeche(geometry: dict[str, Any] | GeoFlaeche) -> GeoFlaeche | None:
-    """GeoJSON-Polygon/-MultiPolygon als Fläche; unbrauchbar → ``None``.
-
-    Zu Punkt oder Linie zusammengefallene Ringe bleiben als solche erhalten,
-    siehe :mod:`app.core.shared.geo_flaeche`.
-    """
-    return lies_flaeche(geometry)
+def _geo_flaeche(geometry: dict[str, Any] | Flaeche) -> Flaeche | None:
+    """GeoJSON-Polygon/-MultiPolygon als Fläche; unbrauchbar → ``None`` (GEO-C06)."""
+    if isinstance(geometry, Flaeche):
+        return geometry
+    if not isinstance(geometry, dict):
+        return None
+    try:
+        return flaeche_aus_geojson(geometry)
+    except GeometrieFehler:
+        return None
 
 
 def _geo_punkt(lon: float, lat: float) -> Punkt | None:
@@ -249,24 +266,24 @@ def _geo_punkt(lon: float, lat: float) -> Punkt | None:
 
 
 def _point_in_geometry(
-    lon: float, lat: float, geometry: dict[str, Any] | GeoFlaeche
+    lon: float, lat: float, geometry: dict[str, Any] | Flaeche
 ) -> bool:
     """Punkt in der Fläche (Randpunkte zählen als innen, D2)."""
     flaeche = _geo_flaeche(geometry)
     punkt = _geo_punkt(lon, lat)
     if flaeche is None or punkt is None:
         return False
-    return flaeche.enthaelt(punkt)
+    return enthaelt(flaeche, punkt, rand_gilt_als_innen=EMPFOHLEN_RAND_GILT_ALS_INNEN)
 
 
 def _geometry_centroid(
-    geometry: dict[str, Any] | GeoFlaeche,
+    geometry: dict[str, Any] | Flaeche,
 ) -> tuple[float, float] | None:
     """Flächengewichteter Schwerpunkt als ``(lon, lat)``; unbrauchbar → ``None``."""
     flaeche = _geo_flaeche(geometry)
     if flaeche is None:
         return None
-    schwerpunkt = flaeche.schwerpunkt()
+    schwerpunkt = flaechenschwerpunkt(flaeche)
     return schwerpunkt.lon, schwerpunkt.lat
 
 
@@ -281,14 +298,14 @@ def _haversine_distance_m(
 
 
 def _geometry_edge_distance_m(
-    lon: float, lat: float, geometry: dict[str, Any] | GeoFlaeche
+    lon: float, lat: float, geometry: dict[str, Any] | Flaeche
 ) -> float | None:
     """Abstand zum nächsten Rand in Metern; 0 innen/auf dem Rand, ``None`` ohne Fläche."""
     flaeche = _geo_flaeche(geometry)
     punkt = _geo_punkt(lon, lat)
     if flaeche is None or punkt is None:
         return None
-    return flaeche.randabstand_m(punkt, KUGEL_MITTLERER_RADIUS)
+    return randabstand_m(punkt, flaeche, KUGEL_MITTLERER_RADIUS)
 
 
 def _natura_props(feature: dict[str, Any]) -> tuple[str, str, str]:
diff --git a/backend/app/modules/vp_ai/services/company/company_records.py b/backend/app/modules/vp_ai/services/company/company_records.py
index 037fcc0..de0f5ab 100644
--- a/backend/app/modules/vp_ai/services/company/company_records.py
+++ b/backend/app/modules/vp_ai/services/company/company_records.py
@@ -1244,18 +1244,26 @@ class _NaturaClient:
         unbrauchbare Geometrie ergibt ``None`` statt 0,0 („im Gebiet“,
         GEO-C06). Erdmodell 6 371 000 m wie bisher.
         """
-        from auditcore_geo import KUGEL_6371_KM, KoordinatenFehler, Punkt
-
-        from app.core.shared.geo_flaeche import lies_flaeche
+        from auditcore_geo import (
+            KUGEL_6371_KM,
+            GeometrieFehler,
+            KoordinatenFehler,
+            Punkt,
+            flaeche_aus_geojson,
+            randabstand_m,
+        )
 
-        flaeche = lies_flaeche(geometry)
+        try:
+            flaeche = flaeche_aus_geojson(geometry) if isinstance(geometry, dict) else None
+        except GeometrieFehler:
+            flaeche = None
         try:
             punkt = Punkt(float(lat), float(lng))
         except (KoordinatenFehler, TypeError, ValueError):
             return None
         if flaeche is None:
             return None
-        return round(flaeche.randabstand_m(punkt, KUGEL_6371_KM), 1)
+        return round(randabstand_m(punkt, flaeche, KUGEL_6371_KM), 1)
 
     def check(self, location: str) -> tuple[float, float, list[dict], list[dict]]:
         """Prüft FFH- und Vogelschutzgebiete für einen Standort."""
diff --git a/backend/tests/test_geo_auditcore.py b/backend/tests/test_geo_auditcore.py
index 0ee15ef..fb14fd7 100644
--- a/backend/tests/test_geo_auditcore.py
+++ b/backend/tests/test_geo_auditcore.py
@@ -6,6 +6,7 @@ import json
 from datetime import datetime
 
 import pytest
+from auditcore_geo import flaeche_aus_geojson
 from auditcore_harvest import Response, TransportError
 
 from app.api.vpai_notebook.gis._common import (
@@ -14,7 +15,6 @@ from app.api.vpai_notebook.gis._common import (
     _point_in_geometry,
 )
 from app.core.shared import nominatim
-from app.core.shared.geo_flaeche import lies_flaeche
 from app.modules.vp_ai.services.company.company_records import _NaturaClient
 
 
@@ -74,8 +74,9 @@ def test_zusammengefallenes_gebiet_bleibt_in_der_pruefung() -> None:
         "type": "MultiPolygon",
         "coordinates": [[[[9.212, 50.2062]] * 5]],
     }
-    flaeche = lies_flaeche(punktgebiet)
-    assert flaeche is not None and flaeche.flaeche is None
+    flaeche = flaeche_aus_geojson(punktgebiet)
+    assert flaeche.polygone == () and len(flaeche.objekte_ohne_flaeche) == 1
+    assert "GEO-C16" in flaeche.hinweise[0]  # sichtbar, nicht still
     abstand = _geometry_edge_distance_m(9.213, 50.2062, punktgebiet)
     assert abstand == pytest.approx(71.3, abs=0.5)
     assert _point_in_geometry(9.213, 50.2062, punktgebiet) is False
```

Empfehlung (nicht Teil des Patches): `natura.py` kann `flaeche.hinweise` in die
Ergebniszeilen übernehmen, damit Prüfende sehen, dass ein Abstand auf ein zu
einem Punkt gerundetes Gebiet zurückgeht; `randbefund(...)` liefert dazu den
maßgeblichen `EntarteterRing`. Wer lieber scheitert, liest mit `strikt=True`.

## Getestete Integrationsvariante: osint `ortsdienst/dienst.py`

Geprüft in einer Wegwerf-Kopie von `osint@d361ddb` (Worktree im Scratch-Verzeichnis)
mit einer isolierten venv, in die nur das gebaute Wheel
`auditcore_geo-0.1.0-py3-none-any.whl` installiert wurde:

- `tests/test_ortsdienst.py`: 13 Tests vorher und nachher **PASS**
  (`python -m unittest tests.test_ortsdienst`).
- Vergleich Original gegen umgestellte Fassung auf 5 000 synthetischen
  Vorhaben, 60 Abfragen (Radien 1–150 km und ohne Radius, mit/ohne Fondsfilter):
  **60/60** identische Antworten (Reihenfolge, Summen, Gesamtzahl,
  `entfernung_km`).
- `tests/test_ort_foerderung.py`, `test_ort_hessen.py`, `test_ort_vermerk.py`
  benötigen Playwright/Browser: NOT_EXECUTED (unabhängig von der Umstellung).

Umstellung (exakter Patch):

```diff
diff --git a/ortsdienst/dienst.py b/ortsdienst/dienst.py
index d9e0651..915bdaa 100644
--- a/ortsdienst/dienst.py
+++ b/ortsdienst/dienst.py
@@ -22,6 +22,9 @@ import os
 import unicodedata
 from urllib.parse import parse_qs, urlparse
 
+from auditcore_geo import KUGEL_MITTLERER_RADIUS, KoordinatenFehler, Punkt, grosskreis_km
+from auditcore_geo import umkreis as geo_umkreis
+
 #: Die vier Fonds des Begünstigtenregisters und ihre Kennung, wie sie die
 #: Karte in „fonds" führt (web/beguenstigte.js). Die Vorhaben Hessen sind
 #: kein Fonds, sondern der Prüfbestand des audit_designer — sie laufen als
@@ -53,11 +56,8 @@ HESSEN_BETRAG_MAX = 100_000_000.0
 
 
 def haversine_km(lat1, lon1, lat2, lon2):
-    """Großkreisentfernung in Kilometern."""
-    p = math.pi / 180
-    a = (math.sin((lat2 - lat1) * p / 2) ** 2
-         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
-    return 2 * ERDRADIUS_KM * math.asin(math.sqrt(min(1.0, a)))
+    """Großkreisentfernung in Kilometern (auditcore_geo, Profil R1 = 6371,0088 km)."""
+    return grosskreis_km(Punkt(lat1, lon1), Punkt(lat2, lon2), KUGEL_MITTLERER_RADIUS)
 
 
 def normalisieren(text):
@@ -94,6 +94,7 @@ class Bestand:
         self.fonds = []          # parallel: Kennung der Gruppe (EFRE, ESF, JTF, SONST, HESSEN)
         self.suchform = []       # parallel: normalisierter Name + Titel
         self.az_form = []        # parallel: normalisiertes Aktenzeichen oder ''
+        self.punkte = []         # parallel: auditcore_geo.Punkt
         self.betroffenheit = {'treffer': {}, 'bezeichnungen': {}}
         self.stand = None
 
@@ -105,6 +106,10 @@ class Bestand:
         lon, lat = _zahl(koord[0]), _zahl(koord[1])
         if lon is None or lat is None:
             return
+        try:
+            ort = Punkt(lat, lon)
+        except KoordinatenFehler:
+            return                 # außerhalb des Wertebereichs: nicht verortbar
         p = dict(feature.get('properties') or {})
         p['fonds'] = fonds_kennung
         p['lon'], p['lat'] = lon, lat
@@ -112,6 +117,7 @@ class Bestand:
         self.lat.append(lat)
         self.lon.append(lon)
         self.fonds.append(fonds_kennung)
+        self.punkte.append(ort)
         self.suchform.append(normalisieren(f"{p.get('name', '')} {p.get('vorhaben', '')}"))
         self.az_form.append(normalisieren(str(p.get('az') or '')))
 
@@ -200,28 +206,11 @@ class Bestand:
         sonst stünde jedes zweimal. Liefert alle Treffer [(entfernung, i)];
         gekürzt wird erst in ort_antwort, weil die Summen über alle laufen.
         """
-        alle = []
-        # Eine Ja/Nein-Liste je Vorhaben statt einer Mengenprüfung in der
-        # Schleife — bei 100.000 Sätzen zählt das.
-        passt = None if fonds is None else [f in fonds for f in self.fonds]
-        if km is None:
-            for i, (la, lo) in enumerate(zip(self.lat, self.lon)):
-                if passt is not None and not passt[i]:
-                    continue
-                alle.append((haversine_km(lat, lon, la, lo), i))
-        else:
-            dlat = km / 111.0 + 1e-9
-            dlon = km / (111.0 * max(0.05, math.cos(lat * math.pi / 180))) + 1e-9
-            for i, (la, lo) in enumerate(zip(self.lat, self.lon)):
-                if passt is not None and not passt[i]:
-                    continue
-                if abs(la - lat) > dlat or abs(lo - lon) > dlon:
-                    continue
-                e = haversine_km(lat, lon, la, lo)
-                if e <= km:
-                    alle.append((e, i))
-        alle.sort()
-        return alle
+        auswahl = [i for i, f in enumerate(self.fonds) if fonds is None or f in fonds]
+        treffer = geo_umkreis(
+            Punkt(lat, lon), [self.punkte[i] for i in auswahl],
+            None if km is None else km * 1000.0, KUGEL_MITTLERER_RADIUS)
+        return [(t.abstand_m / 1000.0, auswahl[t.index]) for t in treffer]
 
     def summen(self, indizes):
         """Summen über alle Treffer: Gesamtkosten, EU-Betrag, je Fonds, Lagegüte.
```

Dazu in osint `requirements` (nach Release): `auditcore_geo==0.1.0`
(Debian: `python3-auditcore-geo`). Verhaltensänderungen durch die Umstellung:
GEO-C02 (keine verlorenen Treffer an Datumsgrenze/hoher Breite; in Hessen ohne
Wirkung) und Koordinaten außerhalb des Wertebereichs werden beim Laden
übersprungen statt gerechnet. `ERDRADIUS_KM` bleibt als Konstante stehen.

## Weitere Consumer-Stellen (Anleitung, nicht ausgeführt)

| Repository | Stelle | Umstellung | Achtung |
|---|---|---|---|
| osint | `werkzeuge/bundeslaender_holen.py`: `utm_nach_wgs84`, `wkb_polygone`, `douglas_peucker`, `ring_vereinfachen` | `utm_nach_geographisch_lonlat(x, y, ETRS89_UTM32N)`, `lies_gpkg_polygone(blob).polygone`, `douglas_peucker`, `ring_vereinfachen(r, t, stellen=4)` | Ergebnisgleich; `lies_gpkg_polygone` weist fehlerhafte Blobs ab (GEO-C07). |
| osint | `werkzeuge/betroffenheit.py`: `_achsen_drehen`, `_im_ring` | `achsenfolge_erkennen(ringe, BEREICH_DEUTSCHLAND_OSINT)`; `lage()` je Gebiet | `UNBEKANNT` behandeln (GEO-C08); Randpunkte als innen (D2). |
| osint | `werkzeuge/vorhaben_verorten.py`: `abfragen` | `NominatimAdapter` + `empfohlene_laufparameter` + eigener Transport und Zwischenspeicher als Senke | User-Agent enthält heute „privat“; Kontakt ergänzen. |
| audit_designer | `core/shared/research/register/geocoding.py`: `_entfernung_km`, `_punkt_in_gebiet`, `naechste_nuts3` | `grosskreis_km(..., KUGEL_6371_KM)`, `lage()`, `naechster_stuetzpunkt_m(..., nur_aussenringe=True)` | Bestehender Register-Bestand: Profil 6371 km beibehalten (GEO-C01); neue gemeinsame Bestände `EMPFOHLENES_ERDMODELL` (D1). |
| audit_designer | `api/vpai_notebook/gis/_common.py`: `_point_in_geometry`, `_geometry_edge_distance_m`, `_geometry_centroid`, `_geocode_address` | `lage`, `randabstand_m(..., KUGEL_MITTLERER_RADIUS)`, `flaechenschwerpunkt`, Nominatim-Adapter | **Entschieden (D3): umstellen.** Punkte in weiteren Teilflächen erhalten 0 m (bewusste Korrektur GEO-C04/C05); Randpunkte als innen (D2); erfundene Konfidenz entfällt (GEO-C12). |
| audit_designer | `modules/vp_ai/services/company/company_records.py`: `_NaturaClient._distance_to_geometry_m` | **Entschieden (D4):** `randabstand_m(punkt, flaeche_aus_geojson(geometrie), KUGEL_6371_KM)` statt Stützpunktabstand | Gemeldete Abstände werden kleiner (bewusste Korrektur GEO-C09); 0,0 m bei ungültiger Geometrie entfällt (GEO-C06). |
| flowsearch | `api/eu_beneficiaries.py:calculate_distance`, `services/natura2000_service.py:_calculate_distance/_get_geometry_center` | `grosskreis_km/_m(..., KUGEL_6371_KM)`, `flaechenschwerpunkt` | `(0, 0)` bei unbekannter Geometrie entfällt (GEO-C06). |
| flowworkshop | `services/geocoding_service.py:geocode_single` (Netzpfad) | Nominatim-Adapter; Offline-PLZ/Stadt/NUTS bleiben | Netzfehler ≠ kein Treffer (GEO-C10); `format=json` → `jsonv2` (GEO-C11). |

Nominatim im Consumer: Transport (z. B. httpx oder
`auditcore_harvest/docs/examples/urllib_transport.py`) und eine Senke, die als
Zwischenspeicher dient, stellt die Anwendung. Vor jedem Lauf
`empfohlene_laufparameter(konfig, run_id, heute_bereits_gesendet=n)` bzw.
`pruefe_laufparameter(..., heute_bereits_gesendet=n)` aufrufen (`n` = Anfragen
dieses Consumers am öffentlichen Endpunkt am laufenden Tag, vom Consumer
gezählt) und das `RateLimit` an den `HarvestEngine` übergeben. Am öffentlichen
Endpunkt höchstens 1 000 Anfragen je Tag und Consumer (D5); darüber eine eigene
Nominatim-Instanz (`basis_url`) oder einen Import verwenden. Keine parallelen
Läufe gegen den öffentlichen Endpunkt; Namensnennung anzeigen.
