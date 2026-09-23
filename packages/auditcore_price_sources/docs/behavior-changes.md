# Beobachtete Connectoren und bewusste Abweichungen

Quelle: `janpow77/regulierung@853676d2`, `backend/app/services/external_apis/`
(Blobs in `provenance.json`). `tools/capture_regulierung_connectors.py` hat die
Original-Connectoren **tatsächlich ausgeführt** – 30 Szenarien mit
In-Prozess-`httpx.MockTransport`, synthetischen Antworten
(`tests/fixtures/payloads`), In-Memory-SQLite und einer aufzeichnenden
Sitzung. Festgehalten sind Anfragen (ohne Geheimniswerte), Client-Timeouts,
`HarvestResult`, die gespeicherten ORM-Zeilen, Commits und Rollbacks
(`tests/fixtures/regulierung_connectors_observed.json`).

`tests/test_characterization.py` spielt dieselben Antworten durch die neuen
Adapter und vergleicht Anfragen, gelesene Werte, gespeicherte Zeilen und
Paket-Hashes. Der migrierte Consumer (siehe `consumer-migration.md`) wurde mit
demselben Werkzeug erfasst (`regulierung_migrated_observed.json`): **Die
gespeicherten Fachzeilen (Wechselkurs, Rohstoffpreis, Tankstelle) sind in allen
30 Szenarien identisch**; Unterschiede betreffen nur Status, Zähler und
Fehlertexte bei fehlerhaften Antworten (unten).

## Übernommen

| Quelle | Übernommenes Verhalten |
|---|---|
| Bundesbank | `GET {url}/data/BBEX3/D.USD.EUR.BB.AC.000?format=json&lastNObservations=30`, `Accept: application/json`; Tageswerte; Bestand wird nie überschrieben (`append_only`); Paket-Hash über `json.dumps(payload, sort_keys=True)` |
| Destatis | Adapter unverändert verschoben (Tabellen, Parameter, Seitenfolge, HTTP≠200 als Hinweis ohne Wiederholung, Binärantwort als Parserfehler, Paket-Hash, Zähler) |
| EIA | Parameter, Produkt `EPCBRENT`, 30-Tage-Fenster, absteigende Sortierung, `api_key` nur als Geheimnis; gespeicherte `Rohstoffpreis`-Zeilen |
| Overpass | Overpass-QL bytegleich (`fuel_query("DE-HE")`), `POST` Formularfeld `data`, 180 s; Zuordnung `osm-{typ}-{id}`, Koordinaten aus Element oder `center`, Platzhalter und Kürzungen über `legacy_station_fields` |
| Tankerkönig | Health-Semantik (`check_list_response`): HTTP-Status, `ok`, Quellmeldung; `harvest()` bleibt im Consumer deaktiviert (ADR-005) |
| EU Oil Bulletin | Nur Seiten-Snapshot mit SHA-256, keine Preisauswertung |
| MTS-K, VID-Sekundärdienste | kein Abrufvertrag (Push bzw. Stub) – nicht übernommen, im Katalog begründet |

## Abweichungen (PS-C)

| Nr. | Original | Neu |
|---|---|---|
| PS-C01 | Bundesbank: Beobachtung `null` wird still übersprungen | Datensatz mit `wert: null`, `status: fehlwert`, Quellstatus (`OBS_STATUS`) |
| PS-C02 | Unlesbarer Wert, fehlendes Datum, Index ohne Zeitangabe still übersprungen; Status `erfolg` | Hinweis je Beobachtung, Lauf `partial` → Consumer `teilweise` |
| PS-C03 | Antwort ohne Beobachtungen: `erfolg` mit 0 | Hinweis „keine Beobachtungen“, `teilweise` |
| PS-C04 | EIA: eine Seite (`length=5000`), Fenster aus `date.today()` | Seiten über `offset`/`total`; Fenster aus Anfragefilter oder `window_days` zur Engine-Uhr (Consumer: lokale Zeitzone wie bisher) |
| PS-C05 | EIA: leere Werte still übersprungen, Einheit fest `USD/Barrel`; `anzahl` zählte alle Rohzeilen | Leere Werte als `fehlwert`, unlesbare Zeile als Hinweis; Einheit aus `units` (`$/BBL` → `USD/Barrel`, Herkunft `quelle`), Profil-Einheit nur markiert als Rückfall |
| PS-C06 | Overpass: Elemente ohne Typ/ID oder ohne Koordinaten still übersprungen; Platzhalter schon beim Lesen | Ohne Typ/ID: Hinweis; ohne Koordinaten: Datensatz mit `koordinaten_herkunft: fehlt` (Consumer-Zuordnung überspringt ihn wie bisher); normalisierte Werte ohne Platzhalter |
| PS-C07 | Overpass-`remark` (z. B. Server-Timeout mit Teilergebnis) gilt als vollständiger Erfolg | Hinweis, `teilweise` |
| PS-C08 | Tankerkönig: nur Health-Check | Adapter liefert Stationen mit Preisen in EUR/Liter; `false`/`null` → kein Preis; PLZ als Zahl wird fünfstellig aufgefüllt und markiert; Zeitbezug `abrufzeitpunkt` (kein Änderungszeitpunkt), `zweck: vorpruefung`, `beweismittel: false`; `ok:false` mit API-Key-Meldung → `auth_error` |
| PS-C09 | EU-Seite: jede HTTP-200-Antwort wird gehasht | Nur Textseiten bis `max_bytes`; Binär-/NUL-Inhalte sind Parserfehler |
| PS-C10 | Keine Wiederholung (Docstring behauptet Retry) | Begrenzte Wiederholung des Kerns; Consumer-Konfiguration: 2 Versuche, `Retry-After` höchstens 30 s |
| PS-C11 | Fehlertext enthielt Antworttext (`HTTP 500: <300 Zeichen>`) bzw. Parser-Ausnahmetext | Strukturierte Fehlertexte des Kerns ohne Antwortinhalt (`Serverfehler HTTP 500.`) |
| PS-C12 | Destatis-Datensatz nur mit Tabelle und Zeilenzahl | Adapter 1.1.0 ergänzt `inhalt` (Zeitangaben, Periodencodes, Einheiten, Werte/Fehlwerte); Paging-Profil 2026.09.1 unverändert |
| PS-C13 | Overpass-Consumer: doppelte Elemente einer Antwort hätten zweimal angelegt werden können | Consumer führt den Bestand während des Laufs fort |

## HUMAN_DECISION_REQUIRED

- **PS-H01** Anzeige `teilweise` statt `erfolg` bei Antworten mit Hinweisen
  (PS-C02, PS-C03, PS-C07) ändert die Admin-Übersicht; fachliche Abnahme nötig.
- **PS-H02** Soll `list.php` von Tankerkönig künftig als Vorprüfungsquelle
  gespeichert werden? Die Bibliothek kennzeichnet Zeitbezug und Zweck; die
  Entscheidung (ADR-005, § 7 MTSKraftV) bleibt beim Consumer. Bis dahin
  unverändert deaktiviert.
- **Datenrechte** aller Dienste: `REVIEW_REQUIRED` (Katalog `licence_access`).
