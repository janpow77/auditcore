# Changelog auditcore_extrapolation

## 0.3.0 – 2026-11-23

Korrekturen nach der Prüfung vom 23.11.2026. Ergebnisse können sich ändern;
der REST-Vertrag `evaluation/1` ist nur um Felder erweitert.

- **Geschichtete Präzision bei nicht proportionaler Aufteilung:** Die Formel
  N × z × s_w / √n (Anhang II DelVO (EU) 2023/67, Leitfaden 6.1.2.4/6.2.2.4)
  setzt n_h = n × N_h / N voraus. Weicht die Aufteilung ab (`is_proportional`),
  rechnet die Bibliothek mit SE = z × √(Σ N_h² s_h² / n_h)
  (`general_stratified_precision`), nennt den Wert der Anhang-Formel in einer
  Warnung und weist den Schritt „Präzision (nicht proportionale Aufteilung)“
  aus. Beispiel: 285 302 € → 637 955 €, Ergebnis „nicht schlüssig“ statt
  „nicht wesentlich“.
- **Mindestumfang (Art. 5 Abs. 5 DelVO (EU) 2023/67):** Unter 30 geprüften
  Einheiten (über alle Zeiträume) Warnung und Einschränkung, bei einer
  Zufallsschicht zusätzlich der Vergleichswert mit dem t-Quantil
  (`extra.minimum_sample`, `TComparison`); maßgeblich bleibt z. Unter 3
  Einheiten je Zufallsschicht Warnung mit Fundstelle.
- **MUS-Standardansatz ohne Fehler:** Statt SE = 0 gilt die Basispräzision
  SI × RF(0) (Leitfaden 6.3.5.5), ebenso bei MUS-Verhältnisschätzung ohne
  systemische Fehler; Formelwert in `extra.zero_errors`. In allen anderen
  Fällen mit Präzision 0 oder Schichten ohne Streuung wird die Einschränkung
  ausgewiesen.
- Neue Felder `Projection.limitations` und `TotalErrorRate.limitations`; die
  Erläuterung beginnt dann mit „Eingeschränkte Aussagekraft“.
- **Konservativer Ansatz:** Basispräzision und erster Zuschlag verwenden
  dasselbe RF(0) (Tabelle 4, 2,31 bei 90 %; vorher 2,30 aus Anhang 3 für den
  Zuschlag). Wie im Text von 6.3.5.5 (Faktor 0,58).
- Herleitung: „Gesamtfehler / BV“, „ULE = Gesamtfehler + SE“, „CBV = BV −
  Gesamtfehler“ statt „TER“ für den Betrag.
- RER: deutsche Begründung in `not_applicable` („Entfällt: Restfehlerquote nicht
  über der Signifikanzschwelle von 2 %.“), Wortlaut der Vorlage in
  `not_applicable_template`; neues Feld `residual_negative` und Hinweis bei
  negativem J/K (nicht auf null begrenzt).
- Meldung zu leeren Schichten nennt die Schicht: „Schicht 'B': Mindestens eine
  geprüfte Einheit erforderlich.“
- Quellen: DelVO (EU) 2023/67 als Rechtsgrundlage 2021–2027; EGESIF_16-0014-01
  als Fassung für 2007–2013 und 2014–2020 gekennzeichnet.
- MUS-Verhältnisschätzung: Kennzahlen der Schicht auch bei Quote 0.
- Zielwerttests `tests/test_zielwerte_hochrechnung.py` (unabhängig nachgerechnet).

## 0.2.1 – 2026-10-17

- Extra `dev`: Testabhängigkeit `auditcore_sampling==0.2.5`.
- Begriff: Meldungen, Ergebnistexte, Herleitung (`TE = Signifikanzschwelle × BV`), RER-Zeile L und die Excel-/CSV-Zusammenfassung nennen die 2-%-Schwelle „Signifikanzschwelle“ statt „Wesentlichkeitsschwelle“ bzw. „Wesentlichkeit“ (DelVO (EU) 2023/67, Anhang I Nr. 1; VO (EU) 2021/1060, Anhang XX Nr. 5.9). Bezeichner (`materiality_rate`, `MATERIALITY_RATE`), Ergebniscodes (`material`, `not_material`, `inconclusive`) und REST-Vertrag bleiben unverändert; die englische Bezeichnung bleibt „materiality threshold“.

## 0.2.0 – 2026-10-03

- Ausschluss und Ersetzen von Einheiten nach verhältnismäßiger Kontrolle
  (Leitfaden 7.10): `Stratum.excluded_*`, Erweiterung auf die ursprüngliche
  Grundgesamtheit je Schicht, `extension_factor`; Referenzfälle 7.10.3.1 b–7.10.3.4.
- Negative Stichprobeneinheiten (4.6): `split_population`, `review_negative_units`,
  REST `POST /negative-units`.
- Discovery- und Stop-or-go-Stichprobe (7.9.6) mit exakter Binomialgrenze:
  `evaluate_discovery`, `evaluate_stop_or_go`, `upper_deviation_limit`;
  `POST /attributes` mit `approach`.
- Programme über mehrere Zeiträume (6.3.4 + 7.8): `assess_groups_over_periods`;
  REST erlaubt `group` zusammen mit `periods`.
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
