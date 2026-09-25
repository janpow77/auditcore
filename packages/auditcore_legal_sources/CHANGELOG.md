# Changelog – auditcore_legal_sources

## 0.1.1 – Refaktorierung ohne Verhaltensänderung

- `legacy` ist ein Unterpaket nach Quelle: `legacy.common` (Datumsparser,
  Erkennungsregeln, Dokumentform), `legacy.dip`, `legacy.eurlex`,
  `legacy.feeds`. Alle bisherigen Namen bleiben unter
  `auditcore_legal_sources.legacy` importierbar.
- `legacy_dip_normalize` in kurze Hilfsfunktionen zerlegt (PDF-URL,
  Förderperiode, Fonds); die Ausnahmebehandlung der Quelle bleibt gleich.
- `funding_period_designer` liest seine Regeln aus deklarativen Tabellen
  in unveränderter Reihenfolge.
- Gemeinsame Adapterhilfen (Profilwahl, JSON, Datensätze, Seiten) liegen in
  `_adapter_support`; `adapters` enthält nur noch die Adapterklassen.
- Typen: Konfigurationen als `Mapping[str, object]`, Antwortkörper als
  `object` mit Strukturprüfung; `Any` bleibt nur an Roh-JSON-Grenzen.
- Keine Umbenennung öffentlicher Namen, keine Aliase nötig.

| Messung | 0.1.0 | 0.1.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 1 | 0 |
| Module > 400 Zeilen | 2 | 0 |
| `Any`-Vorkommen | 69 | 59 |
| mypy --strict | sauber | sauber |
| Tests / Abdeckung | 244 / 96,7 % | 254 / 96,9 % |
