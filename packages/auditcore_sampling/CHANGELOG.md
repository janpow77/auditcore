# Changelog auditcore_sampling

## 0.1.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle 31 bestehenden Tests (Replay gegen die
aufgezeichneten Ausgaben von flowstat und audit-portal, Größen, Auswahl,
Reproduzierbarkeit, Architektur) laufen grün. Ein zusätzlicher Differenzlauf
gegen 0.1.0 (4 000 geschichtete MUS-Läufe mit fehlenden, NaN-, Null- und
Negativwerten sowie 40 000 Aufrufe von `mus_size`/`srs_size` inklusive aller
Fehlerpfade) ergab bitgleiche Ergebnisse und identische Fehlermeldungen.

- `legacy.flowstat_mus_stratified`: Berechnung je Schicht als eigener Schritt
  (`_flowstat_stratum`); Summen-, Rundungs- und Auswahlreihenfolge unverändert.
- Typen: `sizes._number` und `sizes._factor` nehmen `object` statt `Any`;
  interne Schichtzeilen als `dict[str, object]`.

Sichtbare Änderung ist nur die Versionskennung `library` in
`SizePlan.to_dict()` („auditcore_sampling 0.1.1“). Der Test
`test_plans_carry_method_inputs_and_library` prüfte die Kennung als festes
Literal „0.1.0“; er vergleicht jetzt mit `__version__` (wie der entsprechende
Test in auditcore_statistics). Die Replay-/Paritätstests sind unverändert.

Messung mit `auditcore-codegate check --package auditcore_sampling`:

| Messung | 0.1.0 | 0.1.1 |
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
