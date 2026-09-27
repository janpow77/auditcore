# Changelog auditcore_extrapolation

## Unreleased

- Stichprobe in mehreren Zeiträumen (Leitfaden 6.1.3, 6.2.3, 6.3.3, 6.3.4,
  6.4.9, 7.3, Anhang 2): `Period`, `project_periods`, `assess_periods`,
  `combined_precision`.
- Zwei- und dreistufige Stichprobe, ETC mit Lead-Partner und Partner-Stichprobe
  (7.6, 6.4.10, 6.5.3): `SubSample`, `project_subsample`, `unit_from_subsample`.
- Neuberechnung des Konfidenzniveaus (7.7) mit Tabelle 1 aus 3.2.1:
  `recalculate_confidence`, `system_confidence_level`.
- Gruppen von Programmen (7.8): `assess_groups`.
- Merkmalsstichprobe für Systemprüfungen (7.9.3–7.9.5): `evaluate_attributes`
  (mit Wurzel in der Präzision; Formelfehler des Leitfadens dokumentiert).
- REST `evaluation/1` abwärtskompatibel erweitert (`periods`, `group`,
  `subsample`, `system_assessment`, `required_confidence_level`,
  `population_units`; Antwort `design`, `subsamples`, `groups`,
  `confidence_recalculation`), neuer Endpunkt `POST /attributes`.
- Fehlerbehebung: Der konservative MUS-Ansatz scheiterte an Konfidenzniveaus aus
  Tabelle 4 ohne z-Wert in Tabelle 3 (50 %, 75 %, 85 %, 99 %).
- Referenzfälle 6.1.3.6, 6.2.3.6, 6.3.3.7, 6.3.4.7, 6.4.9.1, 6.4.9.2,
  6.5.3.3.2, 7.3.2.2, 7.6.5, 7.7, 7.8.2, 7.9.5; Abdeckungsliste in
  `docs/abgrenzung.md`.

Keine Verhaltensänderung: `web._contract.Reader` prüft das JSON-Objekt über
`auditcore_common.rest.json_object` (Meldung und Status unverändert).

## 0.1.0 – 2026-09-26 – Paketstand für Release v0.4.2 (erste Veröffentlichung)

Erste Fassung (Neuimplementierung nach EGESIF_16-0014-01 und CPRE_23-0013-01 Annex 3).

- Hochrechnung und Präzision: einfache Zufallsstichprobe (Mittelwert- und
  Verhältnisschätzung, geschichtet), Differenzenschätzung (mit korrigiertem
  Buchwert und Untergrenze), MUS-Standardansatz (geschichtet, Hochwertschicht),
  MUS-Verhältnisschätzung bei systemischen Fehlern, konservativer MUS-Ansatz
  (Basispräzision und Zuschläge), nicht-statistische Stichproben (gleiche
  Wahrscheinlichkeit, wertproportional) mit Prüfung nach Art. 79 Abs. 2 CPR.
- Trennung der Hochwertschicht (`split_top_stratum`, iterativ nach 6.3.1.3),
  auch mit einem Stichprobenplan aus `auditcore_sampling`.
- Fehlerklassen: zufällig, systemisch (abgegrenzt), anomal (nur mit
  Begründung; korrigiert nicht in der TER).
- Gesamtfehlerquote mit Wesentlichkeitsschwelle, Fehlerobergrenze und Ergebnis
  nach 4.12/6.4.6; Restfehlerquote getrennt nach Annex 3 (Decimal, ROUND(K; 4)).
- Faktorprofile `kom_2017_tables` und `exact`; jede Formel mit Fundstelle.
- REST-Vertrag `auditcore_extrapolation.evaluation/1` (`[web]`): `/profiles`,
  `/evaluate`, `/evaluate/export` (CSV/JSON), `/residual`; REST-Grundlage aus
  `auditcore_common.rest` (Pflichtabhängigkeit `auditcore_common==0.1.1`).
