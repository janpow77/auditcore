# Verhaltensänderungen gegenüber der Quelle (FlowStat, HIS-Bericht)

Die Bibliothek übernimmt die Zahlerkennung und die Rundungstoleranz, korrigiert
aber sechs bekannte Fehler. Eine Anwendung, die umstellt, sieht deshalb mehr
Befunde und mehr `not_run` als bisher. Das ist gewollt.

| Nr. | Quelle (FlowStat) | auditcore_reportgates |
|---|---|---|
| 1 | `%`, `Prozent` und `Prozentpunkte` mit denselben Faktoren (1 und 0,01) | eigene Dimensionen `share` und `points`; nie ineinander umgerechnet |
| 2 | Textzahl mehr als 10 % neben jedem Objektwert → `nicht_im_objekt`, Gate bleibt `passed` | Zahl ohne Treffer ist `unbound` und ein Befund; nur `match` besteht |
| 3 | nicht prüfbar (`_nicht_pruefbar`) → `passed: True` | `not_run`; die Freigabe (`release`) bleibt dann `not_run` |
| 4 | Mio./Tsd.-Faktor durch Ausprobieren mehrerer Faktoren | Faktor aus der Spalteneinheit (`unit_of(header)`); ohne Einheit kein Faktor |
| 5 | Zählzeilen und Zeilen ohne Einheit fielen teils aus dem Wertevergleich | jede Zeile mit Zahl oder Fehlwert wird verglichen, auch `Anzahl` und Summen |
| 6 | Fehlwert und Null nicht unterschieden (`0,00` gegen `k. A.`) | `MISSING` ist kein Wert; `fehlend_vs_wert` bzw. `wert_fehlt` als Befund, `format_de(0)` = `0,00`, `format_de(None)` = `k. A.` |

Weitere Abweichungen:

- Zeilenanker nur über die normalisierte Beschriftung (keine unscharfe
  Ähnlichkeit 0,82); doppelte Beschriftungen werden in Reihenfolge gezählt.
- Datenstand: undeklariert oder abweichend → `not_run` mit Grund, die
  Abweichungen bleiben als Befunde sichtbar.
- Bewusst nicht im Objekt stehende Kontextzahlen gibt der Aufrufer als
  `BoundValue` mit eigener `source` an; sie werden nicht stillschweigend übergangen.
