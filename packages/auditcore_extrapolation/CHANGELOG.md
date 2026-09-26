# Changelog auditcore_extrapolation

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
