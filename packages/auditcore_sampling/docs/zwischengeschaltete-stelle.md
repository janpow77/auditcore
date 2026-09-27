# Belegziehung einer Zwischengeschalteten Stelle (`auditcore_sampling.intermediate_body`)

Verfahren einer Zwischengeschalteten Stelle im Sinne von Art. 71 Abs. 3
VO (EU) 2021/1060, die Verwaltungsüberprüfungen (Art. 74) für die
Verwaltungsbehörde durchführt. Übernommen aus flowinvoice
(`backend/app/verwk/pipeline/pruefplan.py`, Commit `fb2d18568d2e`,
Blob `08155dae…`), als versioniertes, parametrisiertes Profil formuliert.

## Profil `zs.value_share_escalation`, Version 1

| Parameter | Wert | Bedeutung |
|---|---|---|
| `start_share` | 0,25 | Zufällig gezogen wird, bis die Belege 25 % der **Ausgaben** des Mittelabrufs erreichen (nicht der Belegzahl). |
| `step`, `max_share` | 0,15, 0,85 | Leiter 25 → 40 → 55 → 70 → 85 %; aus dem Startanteil fortgeschrieben. |
| `escalate` | wahr | Die nächste Stufe folgt, solange **neu hinzugekommene** Belege einen finanziellen Fehler tragen (Auslegung der Quelle, fachlich zu bestätigen); gezogene Belege bleiben enthalten. |
| `quality_every` | 20 | Qualitätsstichprobe: jeder 20. als „keine Prüfung“ eingestufte Mittelabruf (`quality_sample`). |

Parameter lassen sich je Anwendung setzen (`with_parameters`); das Profil
bindet keine Institution. Die Risikoeinstufung, die über „keine Prüfung /
Teilprüfung / Vollprüfung“ entscheidet, gehört nicht zur Ziehung und ist
nicht Teil dieses Moduls.

## Zufall

Die Bibliothek zieht keinen Zufall selbst: `value_share_draw` bekommt die
Ziehreihenfolge. Diese kommt aus `draw_order(random.Random(seed), n)` oder –
für Anwendungen mit NumPy – aus
`numpy.random.default_rng(derived_seed(seed, mittelabruf)).permutation(n)`;
`derived_seed` leitet je Mittelabruf einen eigenen Startwert ab wie die Quelle.

## Paritätsnachweis

`tools/capture_intermediate_body.py` hat die Ziehung von flowinvoice
tatsächlich ausgeführt (numpy 2.4.3, pandas 3.0.1, Python 3.12.3):
240 synthetische Mittelabrufe mit 0 bis 250 Belegen, festen Seeds, Startanteilen
0 bis 1 und Erweiterung an/aus (`tests/fixtures/intermediate_body_observed.json.gz`).
`tests/test_intermediate_body_parity.py` prüft je Fall abgeleiteten Seed,
NumPy-Reihenfolge, gezogene Positionen und Stufe jedes Belegs sowie die Leiter
für neun Startanteile: alle 240 Ziehungen (5.701 Belege) und alle Leitern
stimmen überein.
