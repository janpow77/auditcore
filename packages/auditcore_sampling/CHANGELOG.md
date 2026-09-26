# Changelog auditcore_sampling

## 0.2.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle 61 bestehenden Tests (Replay gegen die
aufgezeichneten Ausgaben von flowstat und audit-portal, Größen, Auswahl,
REST-Vertrag, Reproduzierbarkeit, Architektur) laufen grün. Ein zusätzlicher
Differenzlauf gegen den Rechenkern (4 000 geschichtete MUS-Läufe mit fehlenden,
NaN-, Null- und Negativwerten sowie 40 000 Aufrufe von `mus_size`/`srs_size`
inklusive aller Fehlerpfade) ergab bitgleiche Ergebnisse und identische
Fehlermeldungen.

- `legacy.flowstat_mus_stratified`: Berechnung je Schicht als eigener Schritt
  (`_flowstat_stratum`); Summen-, Rundungs- und Auswahlreihenfolge unverändert.
- Typen: `sizes._number` und `sizes._factor` nehmen `object` statt `Any`;
  interne Schichtzeilen als `dict[str, object]`.
- `web` (seit 0.2.0) erfüllt die Maßstäbe bereits; drei Module nur mit
  `ruff format` einheitlich formatiert, ohne inhaltliche Änderung.

Sichtbare Änderung ist nur die Versionskennung `library` in
`SizePlan.to_dict()` („auditcore_sampling 0.2.1“). Der Test
`test_plans_carry_method_inputs_and_library` prüfte die Kennung als festes
Literal; er vergleicht jetzt mit `__version__` (wie der entsprechende Test in
auditcore_statistics). Die Replay-/Paritätstests sind unverändert.

Messung mit `auditcore-codegate check --package auditcore_sampling`:

| Messung | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 0 | 0 |
| Funktionen > 60 Zeilen | 0 | 0 |
| Module > 400 Zeilen | 0 | 0 |
| `Any`-Verwendungen | 11 | 8 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen. Die verbleibenden `Any` stehen an
öffentlichen Signaturen (Schichtschlüssel `strata`, die pandas-`groupby`
nachbildend sortiert werden, Ergebnis-Dictionaries der Legacy-Adapter,
`SizePlan.inputs` und `to_dict`); eine Verengung würde typisierte Consumer
brechen.

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
