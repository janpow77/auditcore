# Changelog auditcore_statistics

## 0.3.0 – Konformitätskennzahlen und REST-Vertrag (Extra `web`)

`benford_test`, die Legacy-Adapter und ihre Ergebnisse bleiben unverändert.

- Neues Modul `auditcore_statistics.conformity`: MAD mit Bewertungsbändern,
  z-Wert je Ziffer (mit Stetigkeitskorrektur) und Zweitziffertest, abgeleitet
  aus einem `BenfordResult`. Stufen und kritische Werte nur aus dem
  ausdrücklich benannten Profil `nigrini.2012`; eine Stufe ist keine
  Feststellung.
- Neues Unterpaket `auditcore_statistics.web`: REST-Vertrag (`catalogue`,
  `analyse`; JSON-Zahlen exakt als `Decimal`), Starlette-Routen und optionaler
  FastAPI-Router. Vertrag: `docs/ui/benford-rest.md`.
- Extra `web` (`starlette>=0.26`, Debian `python3-starlette`).
