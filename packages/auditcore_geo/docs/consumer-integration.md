# Consumer-Umstellung

Status: **geplant**. Nutzerentscheidung vom 23.09.2026: auditcore_geo wird gebaut,
auch ohne bereits umgestellten Consumer – „der mehrfache Nutzen kommt noch“.
Umgestellt wird erst nach dem zentralen Release (v0.3.0); bis dahin keine
Requirements-Änderung und kein Push in Consumer-Repositories.

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
