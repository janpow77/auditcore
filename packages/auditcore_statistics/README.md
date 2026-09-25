# auditcore_statistics

Beschreibende Prüfstatistik mit benannten, quellengebundenen Methodenprofilen.
Nur Standardbibliothek; keine Abhängigkeit von `auditcore`, NumPy oder SciPy.

```python
from auditcore_statistics import benford_test

ergebnis = benford_test([123, 187, 2450, 31, 4.2, 0, None], digits=1)
ergebnis.analysed, ergebnis.zero, ergebnis.missing  # 5, 1, 1
ergebnis.p_value  # Chi-Quadrat, 8 Freiheitsgrade
ergebnis.deviates_at_level  # None: kein α angegeben
```

`benford_test` liefert Verteilung, Ausschlüsse und Chi-Quadrat-Statistik. Es
stellt keine Auffälligkeiten fest; eine Signifikanzaussage erfolgt nur mit
ausdrücklichem `significance_level`. Für zwei Ziffern ist
`short_values="exclude"|"pad"` anzugeben.

`legacy_run_benford` reproduziert `flowstat@d665ac2 run_benford` exakt (für
bestehende Consumer). Seit 0.2.0 reproduziert `legacy_flowinvoice_benford` die
Betrugsprüfung `flowinvoice@fb2d185 BenfordsLawAnalyzer.analyze` (Profil
`flowinvoice.fraud_benford`, identisch in audit-portal): gerundete
Erwartungswerte, fester kritischer Wert 15,507, Stufen-p-Wert, Mindestumfang 50.
Empfohlen (Entscheidung 23.09.2026): `recommended_flowinvoice_benford`, also
`benford_test` mit `digits=1` und `significance_level=0.05`. Unterschiede und offene Entscheidungen:
[docs/behavior-changes.md](docs/behavior-changes.md). Herkunft und
MIT-Freigabe: `NOTICE`, `provenance.json`. Debian: `python3-auditcore-statistics`.

**Konformität und Oberflächen (ab 0.3.0):** `auditcore_statistics.conformity.assess`
liefert MAD-Band, z-Werte je Ziffer und den Zweitziffertest unter dem
benannten Profil `nigrini.2012`. `auditcore_statistics.web` stellt den
REST-Vertrag für `<flowaudit-benford>` bereit (Extra `web`); Vertrag:
`docs/ui/benford-rest.md` im Repository.
