# REST-Vertrag Stichprobe (`auditcore_sampling.web`)

Stand: auditcore_sampling 0.2.0. Oberfläche: `<flowaudit-sampling>` aus `@flowaudit/ui`.

Der Vertrag ist framework-frei implementiert (`calculate_size`, `allocate`, `select`,
`export_selection`, `catalogue`). Die Starlette-Routen (`create_app`, `routes`) benötigen das
Extra `web` (`pip install auditcore_sampling[web]`, Debian: `python3-starlette`), der
FastAPI-Router (`create_router`) zusätzlich FastAPI. Alle Adapter liefern byte-gleiche Antworten.
Authentisierung, Mandantentrennung, CORS und Protokollierung bleiben in der einbindenden Anwendung.

```python
from auditcore_sampling.web import create_app, create_router, routes

app = create_app("/api/sampling")                      # eigenständige ASGI-App
starlette_app.routes.extend(routes("/api/sampling"))   # in bestehende Starlette-App
fastapi_app.include_router(create_router("/api/sampling"))
```

## Grundsätze

- Jede Methode ist ausdrücklich benannt (`method`). Es gibt keine stille Voreinstellung;
  fehlende Pflichtfelder werden mit 422 abgewiesen, nicht ersetzt.
- Der Stichprobenumfang stammt immer aus `mus_size`/`srs_size`. Die Herleitung wiederholt die
  dokumentierte Formel mit eingesetzten Werten; weicht sie vom Bibliotheksergebnis ab, ist das
  ein Programmfehler (500).
- Zufall kommt nur aus `random.Random(seed)`. Ohne `seed` erzeugt der Server einen mit
  `secrets` (kleiner als 2⁵³, damit JavaScript ihn exakt zurücksenden kann) und gibt ihn
  zurück (`seed_generated: true`). Übergebene Seeds dürfen bis 2⁶³ − 1 reichen. Gleiche Anfrage + gleicher Seed =
  gleiche Auswahl, gebunden an `items_sha256`.
- Beträge sind JSON-Zahlen, Anteile Werte zwischen 0 und 1 (0,95 statt 95 %).
- Fehler: `{"error": {"code": "invalid_input" | "invalid_json" | "too_large", "message": "…"}}`
  mit Status 422, 400 oder 413. Standardgrenze 32 MiB je Anfrage, 200 000 Elemente.

## `GET /profiles`

Methodenprofile aus `METHODS` mit Bezeichnung, Status (`RECOMMENDED`, `SUPERSEDED`,
`LEGACY_CHARACTERIZED`), Quelle, Formel, zulässigen Konfidenzniveaus samt Faktor und
Parameterbeschreibung. Dazu `recommended.mus` (`portal.mus_poisson`), die
Nutzerentscheidung vom 23.09.2026 (`decision`), die Auswahlvarianten `portal`/`flowstat` und
die Aufteilungen `proportional`/`equal`.

## `POST /size`

MUS:

```json
{"method": "portal.mus_poisson", "population_value": 475478.94, "materiality": 50000,
 "expected_error_rate": 0.005, "confidence_level": 0.95}
```

Einfache Zufallsstichprobe: `population_size` (ganze Zahl ≥ 1), `confidence_level`,
`margin_of_error` ∈ (0, 1), `expected_proportion` ∈ [0, 1] (Pflicht; die Oberfläche schlägt
0,5 sichtbar vor).

Antwort (gekürzt):

```json
{"library": "auditcore_sampling 0.2.0", "method": "portal.mus_poisson", "kind": "mus",
 "status": "RECOMMENDED", "sample_size": 30, "interval": 15849.298,
 "inputs": {"population_value": 475478.94, "factor": 3.0, "…": "…"},
 "warnings": [],
 "derivation": [
   {"label": "Zuverlässigkeitsfaktor bei 95% Konfidenz", "formula": "RF", "value": 3.0},
   {"label": "Erwarteter Fehler", "formula": "E = V · r", "value": 2377.3947},
   {"label": "Präzision", "formula": "P = max(M − E, M / 2)", "value": 47622.6053},
   {"label": "Stichprobenumfang", "formula": "n = ⌈RF · V / P⌉", "value": 30},
   {"label": "Stichprobenintervall", "formula": "J = V / n", "value": 15849.298}]}
```

Bei einer Grundgesamtheit ohne Wert ist `sample_size` 0, `derivation` leer und `warnings`
nennt den Grund.

## `POST /allocation`

`{"total_sample_size": 10, "method": "proportional" | "equal", "strata": {"A": 70, "B": 30}}`
→ `strata: [{"stratum", "population", "sample_size"}]`, `allocated` (Summe; durch Aufrunden
kann sie `total_sample_size` übersteigen). Formeln: proportional `min(⌈n·N_h/N⌉, N_h)`,
gleich `min(⌈n/H⌉, N_h)` (FlowStat).

## `POST /selection`

```json
{"method": "mus", "variant": "portal", "sample_size": 30, "seed": 42,
 "allocation": "proportional",
 "items": [{"id": "B-1", "value": 1234.5, "stratum": "Los 1"}, "…"]}
```

- `method`: `mus` (systematisch, Variante `portal` oder `flowstat` ist Pflicht) oder `srs`.
- `items[].id` optional (sonst laufende Nummer ab 1), `value` Zahl oder `null`,
  `stratum` optional. Haben Elemente eine Schicht, müssen alle eine haben und `allocation` ist
  Pflicht; `sample_size` wird dann nach Schicht aufgeteilt.
- MUS je Schicht: Intervall = Summe der positiven Werte (Variante `portal`) bzw. Summe aller
  Werte (`flowstat`) geteilt durch den Schichtumfang; Start aus dem gemeinsamen Generator.
- Schichten werden in der Reihenfolge ihres ersten Auftretens gezogen.

Antwort: `seed`, `seed_generated`, `items_sha256`, `population`, `selected`,
`strata[]` (`stratum`, `population`, `sample_size`, bei MUS `interval`, `start`,
`excluded_negative`, `excluded_zero_or_missing` als Kennungen) und `rows[]` (`order`,
`position` 0-basiert in `items`, `id`, `value`, `stratum`, `hits` = Anzahl Geldeinheiten-
Treffer; bei `portal` einmal gelistet, Treffer gezählt).

## `POST /selection/export`

Gleicher Körper wie `/selection` plus `"format": "csv" | "json"`; `seed` ist Pflicht, weil die
Auswahl serverseitig wiederholt wird. CSV: UTF-8 mit BOM, Semikolon, Dezimalkomma, Spalten
`Lfd. Nr.;Position;Kennung;Wert;Schicht;Treffer`. Zellen, die mit `= + - @` beginnen, erhalten
ein führendes Apostroph (Formelinjektion). Dateiname `stichprobe-<methode>-seed-<seed>.csv`
im Header `Content-Disposition`.

## Nicht Teil des Vertrags

Auswertung der Stichprobe (Fehlerprojektion, Differenz-/Verhältnisschätzung, obere
Fehlergrenze) – die Bibliothek enthält dafür noch keine charakterisierten Methoden; siehe
[Paritätsinventur](sampling-benford-paritaet.md).
