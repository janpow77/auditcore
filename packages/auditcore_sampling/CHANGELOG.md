# Changelog auditcore_sampling

## 0.2.0 – REST-Vertrag für Oberflächen (Extra `web`)

Keine Änderung an Methoden oder Ergebnissen; alle bestehenden Replay- und
Reproduzierbarkeitstests laufen unverändert.

- Neues Unterpaket `auditcore_sampling.web`: framework-freier REST-Vertrag
  (`catalogue`, `calculate_size` mit schrittweiser Herleitung, `allocate`,
  `select` mit sichtbarem, reproduzierbarem Seed und Eingabe-Fingerabdruck,
  `export_selection` als CSV/JSON) sowie Starlette-Routen und optionaler
  FastAPI-Router. Vertrag: `docs/ui/sampling-rest.md`.
- Extra `web` (`starlette>=0.26`, Debian `python3-starlette`); die Laufzeit ohne
  Extra bleibt reine Standardbibliothek.
