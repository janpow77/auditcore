# REST-Vertrag Planung nach Leitfaden (`auditcore_sampling.guidance/1`)

Stand: auditcore_sampling (Unreleased). Oberfläche: `<flowaudit-sample-size-planner>`
(`SampleSizePlanner`, React `FlowauditSampleSizePlanner`). Die Routen hängen
an denselben Adaptern wie der Stichproben-Vertrag ([sampling-rest.md](sampling-rest.md)):
`create_app`, `routes`, `create_router` aus `auditcore_sampling.web`
(Extra `web`). Framework-frei: `guidance_catalogue`, `guidance_size`,
`guidance_draw`. Jede Antwort trägt `contract: "auditcore_sampling.guidance/1"`;
eine inkompatible Änderung erhält `/2`.

## Grundsätze

- Methode, Faktorprofil (`kom_2017_tables` | `exact`) und Konfidenzniveau sind
  Pflicht; einzig `materiality_rate` hat den Vorgabewert 0,02 (Höchstwert
  nach Leitfaden 5.3), sichtbar in `inputs`.
- Anteile als Werte zwischen 0 und 1, Beträge als JSON-Zahlen.
- Ergebnis und Herleitung stammen unverändert aus `auditcore_sampling.guidance`;
  jeder Schritt nennt die Fundstelle.
- Fehler: `{"error": {"code": "invalid_input" | "invalid_json" | "too_large", "message": "…"}}`
  mit 422, 400 oder 413.

## `GET /guidance/profiles`

`methods` (Kennung, Bezeichnung, Abschnitt, Formel, Felder, Fundstelle,
`confidence_table` = `z` | `reliability` | `null`), `factor_profiles`,
`tables` (z, reliability, expansion), `nonstatistical_rules`,
`assurance_levels`, `procedures` (Belegziehung der Zwischengeschalteten
Stelle mit Leiter), `status` (`GUIDANCE_EGESIF_16_0014_01`), `status_label`
(„nach Leitfaden“), `materiality_rate`.

## `POST /guidance/size`

| `method` | Felder |
|---|---|
| `guidance.srs`, `guidance.difference` | `factor_profile`, `confidence_level`, `book_value`, `anticipated_error_rate`, `materiality_rate`?, `population_size`, `error_sd`, `finite_population_correction`? |
| `guidance.srs_stratified`, `guidance.difference_stratified` | wie oben ohne `population_size`/`error_sd`, dazu `strata`: `[{name, population_size, sd, exhaustive}]` |
| `guidance.mus_standard` | `factor_profile`, `confidence_level`, `book_value`, `anticipated_error_rate`, `materiality_rate`?, `error_rate_sd`, `book_values`? (Hochwertschicht) |
| `guidance.mus_stratified` | `factor_profile`, `confidence_level`, `anticipated_error_rate`, `materiality_rate`?, `strata`: `[{name, book_value, sd}]` |
| `guidance.mus_conservative` | `factor_profile`, `confidence_level`, `book_value`, `anticipated_error_rate`, `materiality_rate`? |
| `guidance.nonstatistical` | `rule` (`cpr_2021_art79_2` \| `cpr_2013_art127_1`), `population_size`, `book_value` (bei `cpr_2013_art127_1`), `assurance_level`? |

```json
{"method": "guidance.mus_conservative", "factor_profile": "kom_2017_tables",
 "confidence_level": 0.9, "book_value": 4199882024, "anticipated_error_rate": 0.002}
```

Antwort (gekürzt):

```json
{"contract": "auditcore_sampling.guidance/1", "status": "GUIDANCE_EGESIF_16_0014_01",
 "status_label": "nach Leitfaden", "method": "guidance.mus_conservative",
 "sample_size": 136, "raw_size": 135.88, "interval": 30881485.47,
 "inputs": {"reliability_factor": 2.31, "expansion_factor": 1.5, "…": "…"},
 "strata": [], "derivation": [{"label": "Zuverlässigkeitsfaktor", "formula": "RF",
 "value": 2.31, "source": "EGESIF_16-0014-01, Tabelle 4"}, "…"], "warnings": ["…"]}
```

`strata` enthält bei geschichteten Verfahren und bei MUS mit `book_values`
je Schicht `name`, `sample_size`, `exhaustive`, `population_size`,
`book_value`, `share` und `cut_off`.

## `POST /guidance/draw`

Belegziehung einer Zwischengeschalteten Stelle:
`{"procedure": "zs.value_share_escalation", "amounts": [...], "errors": [...], "seed": 7, "parameters": {"start_share": 0.25}}`.
Ohne `seed` erzeugt der Server einen (kleiner als 2⁵³) und meldet
`seed_generated: true`. Antwort: `profile`, `ladder`, `positions`
(Ziehreihenfolge), `stages` (Stufe je Beleg), `final_stage`,
`population_value`, `drawn_value`.
