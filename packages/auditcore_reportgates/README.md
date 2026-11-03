# auditcore_reportgates

Fail-closed-Zahlengates für erzeugte Berichte: Zahlen im Fließtext gegen die
Berichtsobjekte, Tabellen gegen Referenzwerte und die Freigabeentscheidung
über alle Pflicht-Gates. Nicht Prüfbares ist `not_run`, nie `passed`.

```python
from auditcore_reportgates import (
    BoundValue,
    Table,
    check_paragraph,
    compare_tables,
    exact,
    release,
    unit_of,
)

werte = [BoundValue(exact(15_782_365), unit_of("Zuwendung (Euro)"), "Tabelle 7")]
prosa = check_paragraph("Bewilligt wurden 15,8 Mio. Euro.", werte, location="S. 12")

ist = Table(("Bereich", "Anzahl", "Mio. Euro"), (("A", 3, 1.25),), vintage="2025-05-14")
soll = Table(("Bereich", "Anzahl", "Mio. Euro"), (("A", "3", "1,3"),), vintage="2025-05-14")
werte_gate = compare_tables(ist, soll)

freigabe = release([prosa, werte_gate], required=["prose_numbers", "reference_values"])
assert freigabe.released
```

Abhängigkeit: nur `auditcore_common`. Verhaltensänderungen gegenüber der
Quelle: `docs/behavior-changes.md`.
