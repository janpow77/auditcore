# Legacyverhalten und bewusst korrigiertes Verhalten

Quellen, tatsächlich ausgeführt mit `tools/capture_legacy.py` (290 Fälle,
Python 3.12.3; Referenzen pyproj 3.8.0/PROJ 9.8.1 und shapely 2.1.2 nur zum
Vergleich, keine Abhängigkeit):

| Repository | Commit | Datei (Blob) | Symbole |
|---|---|---|---|
| osint | `d361ddb` | `ortsdienst/dienst.py` (`d9e0651`) | `ERDRADIUS_KM`, `haversine_km`, `Bestand.umkreis` |
| osint | `d361ddb` | `werkzeuge/bundeslaender_holen.py` (`4df5560`) | `utm_nach_wgs84`, `wkb_polygone`, `douglas_peucker`, `ring_vereinfachen` |
| osint | `d361ddb` | `werkzeuge/betroffenheit.py` (`2b7a1f6`) | `_achsen_drehen`, `_im_ring` |
| osint | `d361ddb` | `werkzeuge/vorhaben_verorten.py` (`1b6057a`) | `adresse_aufbereiten`, `abfragen` |
| audit_designer | `1254591` | `backend/app/api/vpai_notebook/gis/_common.py` (`54b4f41`) | `_point_in_geometry`, `_geometry_centroid`, `_haversine_distance_m`, `_point_segment_distance_m`, `_geometry_edge_distance_m`, `_geocode_address` |
| audit_designer | `1254591` | `backend/app/core/shared/research/register/geocoding.py` (`12056f3`) | `_entfernung_km`, `_punkt_in_ring`, `_punkt_in_gebiet`, `naechste_nuts3` |
| audit_designer | `1254591` | `backend/app/modules/vp_ai/services/company/company_records.py` (`874901d`) | `_NaturaClient._haversine_m`, `_NaturaClient._distance_to_geometry_m` |
| flowsearch | `10cb2a3` | `backend/app/api/eu_beneficiaries.py` (`b45c679`) | `calculate_distance` |
| flowsearch | `10cb2a3` | `backend/app/services/natura2000_service.py` (`33f83f6`) | `_calculate_distance`, `_get_geometry_center` |
| flowworkshop | `3d1cb40` | `auditworkshop/backend/services/geocoding_service.py` (`3c6ac68`) | `geocode_single` (Netzpfad) |

Das Modul `auditcore_geo.legacy` reproduziert **alle** Fälle exakt
(`tests/test_legacy_replay.py`); `utm_nach_wgs84` sogar bitgleich über den
parametrisierten Bibliothekscode. Der Bibliotheksvertrag weicht nur hier ab:

| ID | Original (beobachtet) | Bibliothek | Begründung |
|---|---|---|---|
| GEO-C01 | Sechs Haversine-Varianten: Radius 6371,0088 km (osint) bzw. 6 371 008,8 m (designer gis) gegenüber 6371 km/6 371 000 m (designer register, company, flowsearch ×2); Einheiten km/m; Achsenfolge (lat, lon) außer designer gis (lon, lat); Formeln asin/atan2, teils ohne Klemmung. Frankfurt–Berlin: 423,5505 km gegenüber 423,5499 km. | Zwei benannte `Kugelprofil`e (`kugel.r1_6371008_8m`, `kugel.6371000m`) ohne Standardwert; Ergebnis stets in m (`grosskreis_m`) bzw. ausdrücklich km; `Punkt` mit benannten Feldern. Abweichung zu jedem Original ≤ 1e-7 relativ. | Varianten nicht still vereinheitlichen; Achsenfolgefehler ausschließen. |
| GEO-C02 | `Bestand.umkreis`: Rechteckvorfilter `km/111`, `km/(111·cos φ)`. Verliert Treffer im Umkreis: bei 60° N/1000 km ein Punkt in 995,1 km; an der Datumsgrenze (0°, 179,9°) ein Punkt in 16,7 km bei 50 km Radius. | `umkreis`: exakter Kugel-Vorfilter (`asin(sin θ/cos φ)`), Pole und Datumsgrenze; gegen Vollsuche geprüft (40 Zufallsläufe). Grenze inklusive wie im Original. | Für Hessen-Radien ohne Wirkung, für allgemeine Nutzung falsch-negativ. |
| GEO-C03 | Strahlverfahren (alle drei Quellen): Punkte auf linker/unterer Kante gelten als innen, auf rechter/oberer als außen; auf Lochkanten umgekehrt; Ecken uneinheitlich. | `lage()` liefert `INNEN`/`AUSSEN`/`RAND` (Rand exakt oder mit Meter-Toleranz); `enthaelt(..., rand_gilt_als_innen=...)` verlangt eine ausdrückliche Entscheidung. Gegen shapely in allen 125 Fällen gleich. | Randpunkte fachlich entschieden: innen (D2). |
| GEO-C04 | designer gis `_point_in_geometry`: bei MultiPolygon gilt nur der erste Außenring, alle weiteren Ringe (auch Außenringe weiterer Teile) als Löcher. Punkt im zweiten Teil → außen. designer register rechnet dagegen korrekt je Teilfläche. | Je Polygon Außenring und eigene Löcher (Semantik von designer register). | Schutzgebiete sind häufig Multipolygone. |
| GEO-C05 | Folge von C04 in `_geometry_edge_distance_m`: Punkt innerhalb des zweiten Teils erhält 277,99 m Randabstand statt 0. | `randabstand_m` = 0 innen/auf dem Rand; sonst Minimum über alle Kanten aller Ringe (gleiche lokale Näherung, Abweichung zu PROJ/shapely ≤ 0,5 %). | Natura-Nähe würde unterschätzt bzw. „nicht im Gebiet“ gemeldet. |
| GEO-C06 | Ungültige/fehlende Geometrie: company `_distance_to_geometry_m` → **0,0 m** (liest sich als „im Gebiet“), designer gis → `None`, flowsearch `_get_geometry_center` → **(0, 0)** (Golf von Guinea, Abstand ≈ 5 600 km = „weit weg“). | `flaeche_aus_geojson` wirft `GeometrieFehler`; nie ein Ersatzwert. | Fehlende Daten dürfen weder Betroffenheit noch Nichtbetroffenheit erzeugen. |
| GEO-C07 | `wkb_polygone`: EWKB-Z-Typ wird als 2D gelesen (vertauschte Werte), MultiPolygon mit Punktteil liefert `[[]]`, Leerflag und Restbytes werden ignoriert, Hüllrechteck 5 → `KeyError`, abgeschnitten → `struct.error`, `srs_id` wird verworfen. | `lies_gpkg_polygone`: nur 2D-Polygon/MultiPolygon; alle Abweichungen `GeometrieFehler`; `srs_id` wird zurückgegeben. Gültige Blobs ergebnisgleich. | Stille Fehllesungen verfälschen Grenzen. |
| GEO-C08 | `_achsen_drehen`: erstes passendes Paar entscheidet; nichts passt oder Paare widersprechen sich → `False` („nicht drehen“). | `achsenfolge_erkennen` → `UNBEKANNT`, wenn nichts passt oder Widerspruch. | Unbekannt bleibt unbekannt. |
| GEO-C09 | Schwerpunkte als Stützpunktmittel: designer gis über alle Ringe inkl. Schlusspunkt und Löcher, flowsearch nur erster Ring des ersten Teils; Quadrat (0..10) → (4, 4) statt (5, 5). Company misst Abstand zum nächsten **Stützpunkt** (264,2 m statt 143 m Kantenabstand). | `flaechenschwerpunkt` (flächengewichtet, Löcher abgezogen; = shapely); Kanten- und Stützpunktabstand als getrennte, ehrlich benannte Maße (`randabstand_m`, `naechster_stuetzpunkt_m`). | Distanzmaß muss benannt sein. |
| GEO-C10 | flowworkshop `geocode_single`: Netzfehler → `None`, dasselbe Ergebnis wie „kein Treffer“; beides als `None` im Zwischenspeicher. | Adapter: Transportfehler → Lauf `failed` mit strukturiertem Fehler; `kein_treffer` nur bei leerer Antwort. | Ausfall ≠ Nichtvorhandensein. |
| GEO-C11 | Anfragen: osint `jsonv2`, 1,1 s Pause; flowworkshop `format=json`, 1,1 s (Fernabfrage standardmäßig aus); designer ohne Pause und ohne Zwischenspeicher. | Adapter fragt `jsonv2` ab; `pruefe_laufparameter` erzwingt am öffentlichen Endpunkt ≥ 1 s, bei regelmäßigen Läufen ≥ 15 s (4/min), Budget ≥ Anfragezahl, identifizierenden User-Agent, https. Suchparameter von osint/designer werden gleich gebildet. | OSMF-Nutzungsbedingungen. |
| GEO-C12 | designer `_geocode_address` erfindet Konfidenz 0,85/0,95 aus dem Feld `class`, das `jsonv2` nicht liefert (dort `category`) – praktisch immer 0,85; wählt stets den ersten Treffer. | Keine Konfidenz; alle Treffer mit Rang, Kategorie, `place_rank`, `importance`, Rahmen; Auswahl bleibt beim Consumer. | Keine unbelegte Bewertung. |
| GEO-C13 | `douglas_peucker` rekursiv; negative Toleranz behält alle Punkte. | Iterativ (keine Rekursionsgrenze), ergebnisgleich; negative/unendliche Toleranz und nicht endliche Punkte → `GeometrieFehler`; `ring_vereinfachen` verlangt `stellen` ausdrücklich. | Eingabeprüfung. |
| GEO-C14 | `utm_nach_wgs84` heißt WGS 84, rechnet aber GRS80/ETRS89 ohne Datumsübergang; nur Zone 32N. Abweichung zu PROJ ≤ 0,71 mm. | `utm_nach_geographisch(…, UtmZone)` bitgleich für Zone 32N/GRS80, dazu Zonen 1–60, Südhalbkugel, Hinrechnung (Rundlauf ≤ 1 mm). Keine Datumstransformation; der Name sagt das. | Bezugssystem ehrlich benennen. |

## Nur gelesen, nicht übernommen

- flowworkshop `lookup_nuts` (`geocoding_service.py`): nächster NUTS-Mittelpunkt
  nach **quadrierter Gradentfernung** mit Schwelle 0,5 Grad², kommentiert als
  „~50km“. Die Schwelle entspricht bei 50° N rund 78 km Nord–Süd und 51 km
  Ost–West (statisch gelesen, nicht ausgeführt: benötigt Referenzdaten).
  Die Punkt-in-Fläche-Zuordnung von designer register ist dafür die belastbare
  Mechanik; die Referenzdaten (PLZ, NUTS) bleiben bei den Anwendungen.
- Offline-Verortung über PLZ-/Ortsverzeichnisse (designer register,
  flowworkshop, flowsearch) bleibt datengebunden in den Anwendungen.
- PostGIS-Abfragen (flowsearch `ST_DWithin`) bleiben Consumer.

## Entscheidungen (DECIDED, 23.09.2026, vom Nutzer delegiert)

Der Nutzer hat die fünf offenen Fragen am 23.09.2026 delegiert („entscheide du
bitte“); entschieden hat der koordinierende Agent:

| Nr. | Frage | Entscheidung | Umsetzung |
|---|---|---|---|
| D1 | Erdradius eines gemeinsamen Bestands | IUGG-Mittelradius R1 = 6 371 008,8 m (`kugel.r1_6371008_8m`) ist **empfohlen** für neue gemeinsame Bestände; `kugel.6371000m` bleibt für Replay und Altbestände. | Konstante `EMPFOHLENES_ERDMODELL`; weiterhin kein stiller Standardwert, das Profil wird ausdrücklich übergeben. |
| D2 | Randpunkte | Randpunkte zählen als **innen** (konservativ: ein möglicher Schutzgebietsbezug wird eher gemeldet als übersehen). | Konstante `EMPFOHLEN_RAND_GILT_ALS_INNEN = True`; `enthaelt(..., rand_gilt_als_innen=)` bleibt ausdrücklich. |
| D3 | Natura-Analyse in audit_designer | **Umstellen** auf korrekte Multipolygone; das bisherige Verhalten (weitere Teilflächen als Löcher) ist ein Fehler. | Bewusste Korrektur GEO-C04/GEO-C05: `lage`/`randabstand_m`; Punkte in weiteren Teilflächen erhalten 0 m. Legacy-Replay bleibt (`legacy.designer_gis_*`). |
| D4 | Abstandsmaß in company `_NaturaClient` | **Kantenabstand** statt Stützpunktabstand. | Bewusste Korrektur GEO-C09: `randabstand_m` statt `naechster_stuetzpunkt_m`; gemeldete Abstände werden kleiner (Beispiel 264,2 m → 143 m). Legacy bleibt reproduzierbar. |
| D5 | Öffentliches Nominatim | Höchstens 1 Anfrage/s (Läufe nach Zeitplan 15 s), **höchstens 1 000 Anfragen je Tag und Consumer**, Ergebnisse zwischenspeichern; darüber eigene Nominatim-Instanz oder Import. | GEO-C15: `OEFFENTLICH_TAGESGRENZE = 1000`; `validate_config` weist `budget > 1000` am öffentlichen Endpunkt ab; `pruefe_laufparameter`/`empfohlene_laufparameter` verlangen `heute_bereits_gesendet` (Tageszählung des Consumers) und weisen Läufe über der Grenze ab. Eigene Instanzen sind nicht begrenzt. |

| ID | Original | Bibliothek | Begründung |
|---|---|---|---|
| GEO-C15 | Keine Tagesgrenze; designer ohne Takt, flowworkshop/osint 1,1 s ohne Obergrenze. | Tagesgrenze 1 000 Anfragen je Consumer am öffentlichen Endpunkt, vor dem Lauf geprüft. | Entscheidung D5; OSMF: keine intensive Nutzung. |

Keine offenen HUMAN_DECISION_REQUIRED für dieses Paket.
