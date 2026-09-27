# Changelog – auditcore_bpmn

## Unreleased

Keine Verhaltensänderung. Fachliche Spezifikation `docs/spezifikation.md`
(Zweck, Verträge, neun Invarianten, Fehlerfälle, Abgrenzung, Abweichungen vom
Altverhalten) mit Hypothesis-Eigenschaftstests `tests/test_spezifikation.py`;
Legacy-Varianten benannt (`validate_bpmn_bva`, `BpmnAnalyzer`, `analyze_bpmn`,
`export_bpmn_to_excel`, `export_bpmn_to_pdf`). Befunde ohne Codeänderung
festgehalten: B1 gebeugte Normnamen („der Delegierten Verordnung“) sind im
Zitat-Rundlauf nicht stabil (`xfail(strict=True)`), B2 Richtlinien in der
Altform „2014/24/EU“ werden nicht erkannt. `specification`-Block in
`provenance.json`, Katalogstatus „spezifiziert“. `hypothesis` im Extra `dev`.

## 0.1.2 – 2026-09-26 – Paketstand für Release v0.4.2

Keine Verhaltensänderung. README mit den Installationsangaben aus Release v0.4.1. Pins: `auditcore_legal_sources==0.1.5`.

## 0.1.1 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Codeänderung. Extra `legal` pinnt `auditcore_legal_sources==0.1.4`.

## 0.1.0 – Erste Fassung

- BPMN 2.0 sicher lesen (defusedxml oder gehärteter Expat) und rundlauftreu
  schreiben; Elementmodell für alle BPMN-2.0-Elemente.
- FlowAudit-Erweiterung Schema 1.0 und 1.1 (verbindlich in
  `docs/bpmn/flowaudit-schema-1.1.md`, XSD im Paket).
- Profile je Förderperiode (KA aus Anhang XI VO (EU) 2021/1060 und Anhang IV
  Delegierte VO (EU) Nr. 480/2014), Prüfregeln mit stabilen IDs (de/en).
- Diagrammsammlung mit Speicher-Port, Freigaben mit SHA-256, Versions- und
  Soll/Ist-Vergleich, Neutralisieren, Anreichern von Altbeständen, Berichte.
- Legacy-treue Übernahme von `bpmn_analyzer.py`, `validate_bpmn_bva` und
  `bpmn_export.py` aus audit_designer (95 charakterisierte Fälle, eine
  dokumentierte Abweichung).
