# Changelog auditcore_reporting

## 0.2.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle 88 bestehenden Tests (Flowlib-Goldens für
Zahlenformate und Arbeitsmappen, Profil-Fingerprints, Ressourcengrenzen) laufen
unverändert grün. Die Profile `flowlib-legacy-v1` und `plain-v1` sind
bytegleich; `formats.py`, `profiles.py` und `profile-registry.json` wurden
nicht berührt, damit die Implementierungs-Fingerprints gültig bleiben.

- `_excel._table_columns` in Einzelprüfungen zerlegt (Blattname, Spalten,
  Startzeile, Formate); Reihenfolge, Ausnahmetypen und Meldungen bleiben gleich.
- `_excel._body` in Zellformat, Zellschreiben und Blattabschluss
  (Spaltenbreiten, Fixierung, Autofilter) zerlegt.
- Neue Charakterisierungstests `tests/test_validation_messages.py` (19 Fälle)
  halten jeden Prüfzweig mit Typ, Meldung und Vorrang fest; sie liefen vor der
  Zerlegung gegen den unveränderten Code grün.

Messung mit `auditcore-codegate check --package auditcore_reporting`:

| Messung | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 2 | 0 |
| Funktionen > 60 Zeilen | 0 | 0 |
| Module > 400 Zeilen | 0 | 0 |
| `Any`-Verwendungen | 4 | 4 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen. Die `Any` stehen ausschließlich
in `formats.py` und `profiles.py`; beide Dateien sind per SHA-256 im
Profilregister verankert. Eine Verengung auf `object` würde die Fingerprints und
damit die Profilmetadaten ändern und ist deshalb bewusst unterblieben.
