# REST-Vertrag Benford (`auditcore_statistics.web`)

Stand: auditcore_statistics 0.3.0. Oberfläche: `<flowaudit-benford>` aus `@flowaudit/ui`.

`analyse` und `catalogue` sind framework-frei. `create_app`/`routes` benötigen das Extra
`web` (Starlette, Debian `python3-starlette`), `create_router` zusätzlich FastAPI.
Authentisierung und Mandantentrennung bleiben in der einbindenden Anwendung.

```python
from auditcore_statistics.web import create_app, create_router
app = create_app("/api/benford")
fastapi_app.include_router(create_router("/api/benford"))
```

## Grundsätze

- Verteilung und Ausschlüsse kommen aus `benford_test`, Kennzahlen aus
  `auditcore_statistics.conformity.assess`. Bewertungsstufen und kritische Werte stammen nur
  aus dem ausdrücklich gewählten Profil (`profile`); es gibt keine Voreinstellung.
- Eine Bewertungsstufe beschreibt die Nähe der Verteilung zum Benford-Gesetz. Sie ist
  **keine Feststellung** zu einzelnen Belegen oder zum Datenbestand.
- JSON-Zahlen werden als `Decimal` gelesen: analysiert werden genau die gesendeten Ziffern
  (`0.1` bleibt 1, nicht 1000000000000000055…).
- Fehlerform wie beim Stichprobenvertrag (`invalid_input` 422, `invalid_json` 400,
  `too_large` 413). Grenzen: 64 MiB je Anfrage, 1 000 000 Werte.

## `GET /profiles`

```json
{"library": "auditcore_statistics 0.3.0", "method": "auditcore_statistics.benford/1",
 "tests": [{"id": "first", "label": "Erste Ziffer (1–9)", "digits": 1},
           {"id": "first_two", "label": "Erste zwei Ziffern (10–99)", "digits": 2},
           {"id": "second", "label": "Zweite Ziffer (0–9)", "digits": 2}],
 "short_values": [{"id": "exclude", "…": "…"}, {"id": "pad", "…": "…"}],
 "profiles": [{"id": "nigrini.2012", "mad_bounds": {"first": [0.006, 0.012, 0.015],
   "first_two": [0.0012, 0.0018, 0.0022], "second": [0.008, 0.010, 0.012]},
   "level_labels": ["Enge Übereinstimmung", "Akzeptable Übereinstimmung",
                    "Grenzwertig akzeptable Übereinstimmung", "Keine Übereinstimmung"],
   "z_critical": 1.96, "continuity_correction": true, "significance_level": 0.05,
   "source": "…", "note": "…"}],
 "limits": {"max_values": 1000000}}
```

## `POST /analyze`

```json
{"test": "first", "profile": "nigrini.2012", "values": [123.45, 18, null, 0, -12.5]}
```

`short_values` (`exclude` | `pad`) ist für `first_two` und `second` Pflicht und für `first`
unzulässig. `null` zählt als fehlend, 0 wird ausgeschlossen, negative Werte gehen mit ihrem
Betrag ein und werden gezählt. Texte und Wahrheitswerte werden abgewiesen – das Einlesen von
Dateien (Dezimalkomma, Tausenderpunkte) übernimmt die Oberfläche und zeigt verworfene Zeilen an.

Antwort:

- `distribution`: `benford_test(...).to_dict()` – `analysed`, `excluded`
  (`missing`, `zero`, `short`), `negative_absolute`, `rows[]` je Zifferngruppe
  (`observed_count`, `observed_share`, `expected_share`, `deviation`), Chi² der Gruppen.
- `conformity`: `profile`, `test`, `analysed`, `mad`, `mad_level` (0–3), `mad_label`,
  `chi2_statistic`, `degrees_of_freedom`, `p_value`, `significance_level`, `chi2_exceeds`,
  `z_critical`, `exceeding_digits` und `rows[]` mit `z` und `exceeds` (|z| > kritischer Wert).

Beim Test `second` werden die Gruppen 10–99 nach ihrer zweiten Ziffer zusammengefasst; die
Chi²-Werte in `conformity` beziehen sich dann auf 10 Klassen (9 Freiheitsgrade), die in
`distribution` auf 90 Gruppen.

## Formeln (Profil `nigrini.2012`)

- MAD = Σ|p_i − p₀_i| / k (k = 9, 90 oder 10), Stufe = erstes Band mit MAD < Grenze.
- z_i = (|p_i − p₀_i| − 1/(2n)) / √(p₀_i(1 − p₀_i)/n); die Stetigkeitskorrektur entfällt,
  wenn sie größer als |p_i − p₀_i| ist.
- Chi² = Σ(O_i − E_i)²/E_i, p-Wert aus der Chi²-Verteilung mit k − 1 Freiheitsgraden.
