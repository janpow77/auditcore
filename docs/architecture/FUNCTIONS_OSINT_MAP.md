# Funktionsübersicht OSINT / map.flowaudit.de

Stand: 22.09.2026. Untersuchte GitHub-Quelle: `janpow77/osint`, Commit
`d361ddb9a502bb899065e799d50104f306cfdc89`.
[Unveränderlicher Quellstand](https://github.com/janpow77/osint/tree/d361ddb9a502bb899065e799d50104f306cfdc89).
Alle nachfolgenden relativen Quellpfade beziehen sich auf dieses Repository und diesen Commit.

## Umfang und Belegqualität

Der gesamte versionierte Dateibaum wurde erfasst: 252 Dateien, darunter 125 Graphify-Artefakte,
58 Dateien unter `web/` (40 JavaScript-Dateien), zehn Python-Werkzeuge, vier Python-Dienste,
17 Testdateien unter `tests/` und `kartendienst/test_dienst.py`. Python-Symbole und Testmethoden
wurden mit AST erfasst; UI-Einstiege, Quellenaufrufe, HTTP-Routen und Deploymentkonfiguration
wurden zusätzlich gelesen. Die Funktionsgruppen unten decken alle Dienste, Werkzeuge und
JavaScript-Module ab. Das ist eine statische Funktionsübersicht, kein vollständiges Codeaudit.

Wichtig: Der lokale Inventurcheckout ist sparse. `rg --files` allein findet nicht README,
HTML, Caddy-Konfiguration und Graphify-Daten. Diese wurden mit `git ls-tree` / `git show`
aus dem vollständigen Commit gelesen. Keine privaten Rohdatensätze oder Codeauszüge werden
in diesen Bericht übernommen. Vor einer öffentlichen Codeübernahme bleibt die Rechteprüfung
für OSINT selbst und für jedes Quell-/Bildmaterial erforderlich; eine MIT-Freigabe anderer
Generatoren gilt hier nicht.

Status: Quell-/AST-/Graphartefaktanalyse **EXECUTED**. Anwendung, Browser,
Livequellen, Anmeldung, Lastverhalten und vorhandene Tests **NOT_EXECUTED**.

## Anwendungen und Dienste

| Bestandteil | Belegte Funktionen / Schnittstellen | Aufrufer und Abgrenzung |
|---|---|---|
| Ortsansicht | `web/ort.html`, `ort.js`: Ort/Radius setzen, Länderzuordnung, Suche, URL-Zustand, Kartenansichten, Modulregistrierung über `antwortAnmelden`, abbruchfähige Neuberechnung über `antwortenRechnen` | Caddy-Wurzel leitet auf `/ort.html`; die Fachmodule registrieren eigene Antworten; UI bleibt Anwendung |
| Klassische Karte | `web/karte.html`, `app.js`: Luftbild-, Fach-, Förder-, Lage- und eigene Datenebenen sowie Foto-, Such-, Vergleichs- und Flugbedienung | HTML lädt gemeinsame Skripte; nicht automatisch ein zweites Python-Paket |
| Nachrichtenstartseite | `web/index.html`, `nachrichten.js`, `dashboard.js`, `start-himmel.js`: Meldungsfilter, Lesebereich, Quellenzustand, CSV-Export, Globus, Uhr und Flugspuren | `/dienst/nachrichten/`, `/anmeldung/fluege`; Darstellung bleibt Browsercode |
| Ortsdienst | `ortsdienst/dienst.py`: `Bestand.aufnehmen`, `hessen_aufnehmen`, `umkreis`, `summen`, `ort_antwort`, `suchen`; `GET /gesund`, `/ort`, `/suche` | `ort-foerderung.js` und `ort-hessen.js` rufen `/dienst/ort/ort` bzw. `/suche` auf; Datei-/HTTP-Hülle vom Fachkern trennen |
| Nachrichtendienst | `nachrichten/dienst.py`: `feed_lesen`, `guardian_lesen`, `themen_finden`, `Lesetext`, `bereinigen`, `artikel`, `quelle_holen`, `nachrichten` | Startseite und Ortsnachrichten verwenden denselben Dienst; RSS/Atom, HTML-Bereinigung, Quellenstatus und Zwischenspeicher als Kandidaten |
| Kartendienst | `kartendienst/dienst.py`: `kachelrahmen`, Terrarium-Lesen/-Schreiben, `hoehenkachel`, `historisch`, `sachsen_anhalt`, `punkte_pruefen`, `profil`; `/gesund`, `/katalog`, PNG-Kacheln, `POST /profil` | `ort-karten.js`, `ort-hoehenprofil.js`, `layers.js`; Rasterio/NumPy/Pillow und lokales DGM sind optionale schwere Abhängigkeiten |
| Anmeldung | `anmeldung/anmeldedienst.py`: Passwortprüfung, signierter Nachweis, An-/Abmeldung und Prüfroute; `fluege_holen` liefert begrenzten OpenSky-Auszug | Caddy `forward_auth` schützt die Fachrouten; Authentisierung bleibt Anwendung/Betrieb und darf bei Extraktion nicht entfallen |
| Overpass | `overpass/docker-compose.yml`, Proxywege und bestehende Abfragefunktionen | Eigene Instanz plus öffentliche Ausweichwege; Betrieb ist kein fachlicher Bibliothekskern |

`betrieb/caddy-map.conf` ordnet diese Anwendung ausdrücklich `map.flowaudit.de` zu:
Anmeldung auf Port 8300, Nachrichten 8301, Ortsdienst 8302, Karten 8303; die Fachrouten
stehen hinter `forward_auth`. `docker-compose.yml` definiert Karten-, Nachrichten-, Orts-
und Webdienst; Anmeldung/Overpass haben eigene Compose-Dateien. Das belegt die vorgesehene
Zuordnung, nicht den aktuellen Zustand des laufenden Servers.

## Fachliche Funktionsgruppen und Bibliothekskandidaten

Die Paketnamen sind Zielvorschläge für die Konsolidierungsplanung, keine bereits erzeugten
Pakete. Die Browserdarstellung wird nicht allein wegen ähnlicher Begriffe nach Python portiert.

| Funktion | Konkrete Quellen / Symbole | Zuordnung / wichtige Grenze |
|---|---|---|
| Luftbild-/Grundkartenkatalog, WMS/XYZ, historische Verfügbarkeit | `layers.js` (`wms`, `histQuelle`), `karten-katalog.js`, `ortskarten.js`, `ort-ansichten.js` (`jahrgangAmPunkt`) | `auditcore_geo`: Quellenbeschreibungen/Abdeckung und optional Quellenadapter; transparente WMS-Probe ist kein vollständiger Flächennachweis |
| Geländeraster, DGM-Pilot, Projektion, Höhenprofil | `kartendienst/dienst.py`, `werkzeuge/dgm_pilot_holen.py`; `ort-karten.js`, `ort-hoehenprofil.js` | `auditcore_geo` mit optionalem Raster-Extra; originales Höhenprofil und Darstellungsüberhöhung getrennt lassen |
| Kartenvergleich und Darstellung | `ort-vergleich.js`, `ort-karten-ui.js`, `raum.js`, `fachdaten.js`, `ort-karten.js` | MapLibre-, DOM- und WebGL-Anteile bleiben UI; reine Geometrie-/Katalogregeln separat extrahierbar |
| Orts-/Umkreissuche, Normalisierung, Suchpriorität | `ortsdienst/dienst.py`: `haversine_km`, `normalisieren`, `Bestand.umkreis`, `Bestand.suchen`, `parameter_ort` | `auditcore_geo` für Distanz/Geometrie; fachliche Aktenzeichen-/Begünstigtensuche als Förderdatenfunktion |
| Förderregister und Summen | `Bestand.summen`, `hessen_aufnehmen`; `ort-foerderung.js`, `ort-hessen.js`, `finanzfilter.js`, `beguenstigte.js` | `auditcore_funding_sources` für Datensatznormalisierung und Filter; Gesamtbetrag, EU-Betrag, EU-Satz und hessische Fördersumme sind unterschiedliche Größen |
| Kohesio-Suche, Vorhabendaten | `foerderung.js`: `foerderBedingung`, `foerderungZaehlen`, `foerderungHolen`; `beguenstigte_exportieren.py` | Förderadapter auf `auditcore_harvest`; SQL/SSH-/Dateiexport bleibt austauschbarer Eingangsadapter |
| Räumliche Umweltbetroffenheit | `werkzeuge/betroffenheit.py`: `Gitter`, `_ringe`, `_achsen_drehen`, `_im_ring`, `block_verarbeiten`, `kulisse_pruefen`; `ort-kulissen.js`: `gmlLesen`, `antwortLesen`, `quelleRechnen` | `auditcore_geo`: Geometrie/GML und Abdeckungsstatus; Quelle ausgefallen oder unvollständig darf nicht „nicht betroffen“ werden |
| Träger-/Adressmatching | `traeger_verorten.py`: `normalisiere`, `ohne_rechtsform`, `NutsFlaechen`, `Adressen`, `Zuwendungsempfaenger`, `Zuordner` | `auditcore_entity_matching` und Geo-Komponente; SQL/SSH/DB-Schreibfunktion `einpflegen` gehört in Adapter, keine automatische Bestandsmigration |
| Register-/Kammerquellen | `traeger_quellen.py`: `zer_holen`, `ihk_holen`, `hwk_holen`, `kammern_holen`, `adressen_holen` | `auditcore_registry_sources` + Geo-Quellen; gemeinsamer Abruf über `auditcore_harvest` |
| Standortfelddeutung und Tabellenmapping | `standorte_heben.py`: `zerlegen`, `Aufloeser`; `spalten_zuordnen.py`: `art_des_inhalts`, `rolle` | Fachlich gebundene Importprofile, ggf. `auditcore_documents`; keine pauschale Interpretation beliebiger Spalten |
| Vorhabenverortung | `vorhaben_verorten.py`: `kopfzeile_finden`, `spalte`, `adresse_aufbereiten`, `abfragen`, `zahl`; `orte_sammeln.py` | Förderimport + Geo-Adapter; Nominatim-Abfragebedingungen und Wiederholbarkeit getrennt behandeln |
| Landesgeometrien / Vereinfachung | `bundeslaender_holen.py`: `utm_nach_wgs84`, `wkb_polygone`, `douglas_peucker`, `ring_vereinfachen`, `gpkg_laden` | `auditcore_geo`; vorhandene Standardbibliotheken und Projektionstests prüfen, keine neue allgemeine Geodatenengine erfinden |
| Nachrichtenharvest und sichere Lesetexte | `nachrichten/dienst.py`: Feedparser, Guardian-API, HTML-Parser, Themenregeln; `nachrichten.js` | Gemeinsames Harvest-Framework plus eigener Nachrichten-Quellenbereich als Kandidat; Rechte für Volltexte und Quellenbedingungen separat prüfen |
| Ortsbezug von Nachrichten | `ortsbezug.js`: `schreibweise`, `woerter`, `treffer`, `ortFinden`; `ort-nachrichten.js`: `rechnen` | Ortslexikon/heuristisches Matching; Mehrdeutigkeit und Treffergewichtung erhalten, kein behaupteter sicherer Ereignisort |
| Wetter, Reise, Verkehr, Erdbeben, Fluglage | `warnungen.js`, `lage.js`, `ebenen.js`, `flug.js`; `ort-lage.js`: `wetterwarnungAmOrt`, `reisehinweisAmOrt`, `baustellenImUmkreis`, `erdbebenImUmkreis`, `flugzeugeImUmkreis` | Geo-/Lagequellenadapter auf Harvest; Anbieterlimit und Ausfallstatus erhalten, keine pauschale Risikobewertung ableiten |
| OSM-Merkmalssuche und Kameraobjekte | `suche.js`: `abfrageBauen`, `overpassAbfragen`, `merkmaleSuchen`; `ort-werkzeuge.js`: `merkmaleImUmkreis`; `ebenen.js`: `kamerasHolen` | `auditcore_geo` mit Overpass-Adapter; Kamerastandorte sind keine verfügbaren Kamerabilder |
| Straßenpanoramen | `strasse.js`: `strassenbilderSuchen`, `strassenbildHolen`; `ort-ansichten.js`: `panoramaxUmkreis`, `mapillaryUmkreis`; `panorama.js` | Geo-Quellenadapter; Panoramarenderer bleibt Web/UI, Mapillary-Zugang und Bildrechte separat |
| EXIF und Sonnenstand | `bild.js`: `bildAuswerten`, `sonnenstand`; entsprechende Funktionen in `ort-werkzeuge.js` | Geo-/Dokumentenmetadaten als Kandidat; derzeit browserlokale Bilderverarbeitung nicht still in Serverupload ändern |
| Eigene CSV-/GeoJSON-Daten | `eigene.js`: `csvLesen`, `zahl`, `saetzeZuMerkmalen`, `eigeneDateiLesen` | Importprofile für `auditcore_documents`/Geo; Format-, Zahlen- und Koordinatenregeln charakterisieren; Daten bleiben derzeit lokal |
| Messung und Belegexport | `werkzeuge.js`, `ort-werkzeuge.js`: Messgeometrie; `ort-vermerk.js`: `vermerkBauen`, `quelleStandGuete`, `eigenstaendig`, `speichern`; `dashboard.js`: CSV-Export | `auditcore_geo` für Berechnung; `auditcore_reporting` für strukturiertes Belegmodell/Export, DOM-Kopieren/Druckdialog bleiben UI |
| Kameraflug, Aufzeichnung, Flugzeugmodell | `flugweg.js`: `flugStarten`, `kameraFuehren`, `aufnahmeStarten`; `flugmodell.js`; `ort-flug.js` | UI-/Visualisierungsfunktionen, kein belegter eigenständiger Python-Fachpaketbedarf |
| Bedienung und Dashboard | `spaltenbreite.js`, `dashboard.js`, `start-himmel.js`, `ort.js`, `app.js` | Anwendungen erhalten; Uhr/Globus/Mondanimation ist keine neue Prüfmethodikbibliothek |

## Belegte Quellenfamilien

Die folgenden Quellen stehen in aktuellen Codekonstanten/Abrufstellen; „belegt“ bedeutet
Anbindung im Code, nicht heute erfolgreich abgerufen oder eine aktuelle Lizenzbewertung.

- Nachrichten: Deutschlandfunk, Tagesschau, franceinfo, RFI, Deutsche Welle, netzpolitik.org,
  Guardian (API mit Schlüssel, sonst RSS) und 3sat NANO (`nachrichten/dienst.py`).
- Förderung: Kohesio sowie lokale EFRE-/ESF-/JTF-/sonstige Begünstigten- und hessische
  Vorhabenbestände (`foerderung.js`, `beguenstigte.js`, `ortsdienst/dienst.py`).
- Register und Verortung: BZSt-Zuwendungsempfängerregister, IHK, HWK/ZDH, OpenStreetMap/Overpass,
  Wikidata und Nominatim (`werkzeuge/traeger_quellen.py`, `orte_sammeln.py`, `vorhaben_verorten.py`).
- Geodaten: BKG-Landesgeometrien, Landes-WMS/-Luftbilder, basemap.de, Mapzen/AWS-Terrarium,
  hessisches DGM1, BfN/Hessen-WFS und weitere im Katalog benannte Quellen; EEA als
  Ausweichquelle in `ort-kulissen.js`.
- Lage: DWD, Auswärtiges Amt, Autobahn-API, USGS und OpenSky; OSM-Kamerastandorte.
- Straßenansichten: Panoramax und Mapillary. In UI/Dokumentation genannte Webcams oder
  Videoportallinks sind nicht automatisch implementierte Harvest-Adapter.

TED, HAD, State Aid, De-minimis und Sanktionen werden hier **nicht** als eigenständige
belegte OSINT-Implementierungen behauptet. Ihre Quellen liegen in anderen Anwendungen
und gehören in die übergreifende Funktionsübersicht. Ein Begünstigtenkartenbestand ist
kein Nachweis eines State-Aid- oder De-minimis-Prüfkerns.

## Aufrufketten und Graphify

Das vorhandene `graphify-out/graph.json` wurde tatsächlich eingelesen: 1.283 Knoten,
2.286 Kanten, davon 1.023 `calls`, 702 `contains`, 380 `method`, 104 `rationale_for`,
42 `indirect_call`, 24 `references`, fünf `inherits`, fünf `uses`, ein `imports`.
Der eingebettete `built_at_commit` ist `ba3d33ac722e881673ecaaa54af65b85d1d5bba6` und
stimmt **nicht** mit dem untersuchten HEAD überein. Zudem nennen `GRAPH_REPORT.md` und
`ARCHITEKTUR.md` nur 813 Knoten / 1.234 Kanten. Die Artefakte sind somit kein konsistenter
aktueller Vollständigkeitsnachweis. Build-Excludes schließen u. a. HTML, YAML, Markdown,
PDF und Paketmetadaten aus; Deployment-/UI-Einstiege mussten separat gelesen werden.

Konkrete graphische Aufrufbelege wurden am aktuellen Code gegengeprüft:

1. `ortsdienst/dienst.py:386`: `Handler.do_GET` → `Bestand.ort_antwort` → Umkreis/Summen;
   davor Browseraufruf in `ort-foerderung.js` / `ort-hessen.js`, Proxy in Caddy.
2. `kartendienst/dienst.py:236`: `Handler.do_POST` → `profil`; davor
   `ort-hoehenprofil.js:59` → `POST /dienst/karten/profil`.
3. `web/ort.js:599,647,799`: Modulregistrierung/Schaltung/Neuberechnung →
   `antwortenRechnen`; konkrete Fachmodule registrieren `rechnen` und `zeigen`.
4. Nachrichtenseite und `ort-nachrichten.js` → `/dienst/nachrichten/` →
   `quelle_holen` → Feed-/Guardian-Parser. Diese Browser-HTTP-Kante wird zusätzlich
   über Quelltext und Proxykonfiguration belegt, nicht aus einer einzelnen Graphkante abgeleitet.

Ein neuer Graphify-Lauf wurde für diesen Teilbericht nicht ausgeführt (**NOT_EXECUTED**).
KIRA-/RAG-Ergebnisse werden im übergeordneten Bericht getrennt dokumentiert; dieser Teilbericht
beansprucht keine eigene erfolgreiche KIRA-Suche. Strukturgraphen ersetzen keine Laufzeitspur.

## Tests, Risiken und nächste Extraktionsschritte

18 Python-Testdateien enthalten zusammen **189 statisch gezählte `test_`-Methoden**.
Das ist kein Ergebnis eines Testlaufs. Relevante vorhandene Verträge:

- `test_ortsdienst.py`: Entfernungen, Umkreis/Limit, Gruppenfilter, EU-Betrag gegen EU-Satz,
  hessische unplausible Beträge, Aktenzeichenpriorität und Parameterprüfung.
- `test_verortung.py`: bekannte Orte, Postleitzahlen/Adressen, Reihenfolge und Fehlerfälle.
- `test_nachrichten.py`: HTML/Links, RSS nicht automatisch Volltext, Themen, Cache/Ausfall,
  Guardian-API und Geheimnisbehandlung.
- `kartendienst/test_dienst.py`: Terrarium, Kachelgrenzen, Profilvalidierung, DGM/Weltfallback,
  Reprojektion, feste Sachsen-Anhalt-Quelle.
- Browsertests prüfen Förderfilter, Kulissen/Ausweichketten, Ausfälle/Abbruch, Quellenlimits,
  EXIF/Messung, Kartenschichten/Profile, Ortsansicht/Flug und Vermerk/PDF-Druck.
  Sie benötigen eine laufende Anwendung und Playwright/Chromium; Fremddienste werden teilweise
  durch Testantworten ersetzt. Ein späteres Bestehen wäre kein Livequellennachweis.

Vor Extraktion zuerst bekannte Ein-/Ausgaben dieser Kerne sichern. Finanzsummen und
Plausibilitätsgrenzen brauchen versionierte Fachprofile; Fehlbestände und ungefähre Verortung
müssen sichtbar bleiben. Die Originalimplementierung kann unbekannte Werte in bestimmten
Summen als null behandeln; daraus darf kein ungeprüfter allgemeiner Bibliotheksvertrag werden.

Priorität: (1) reine Geo-/Orts- und Importverträge samt Tests, (2) Förder-/Trägerdatenadapter,
(3) Nachrichten- und Lagequellen auf den gemeinsamen Harvestkern, (4) Reporting-Belegmodell.
Es werden keine Repozusammenlegung, keine öffentliche Übernahme privater Quellen und keine
zusätzlichen Pakete allein anhand dieser Funktionsnamen automatisch vorgenommen.
