# Regelwerk `efre.uebersicht_vue` – Abgleich der Übersicht über die Verwaltungsüberprüfungen

Die Prüfbehörde gleicht die Übersicht der Zwischengeschalteten Stelle über die
Verwaltungsüberprüfungen (Anlage zur Verwaltungserklärung nach Artikel 74
Absatz 1 Buchstabe f und Anhang XVIII VO (EU) 2021/1060) mit den Berichten des
EFRE-Infoportals ab. Das Regelwerk legt fest, wie Beschreibungen und Angaben
dabei eingeordnet werden. Es löst Hinweise aus, keine Feststellungen; die
Einstufung als Einzelfall oder systembedingt bleibt Prüferentscheidung.

## Bereiche

| Bereich | Zweck |
|---|---|
| `FALLGRUPPE` | Fallgruppe einer Kürzungsbeschreibung; `bewertung` „Fehler“ oder „kein Fehler“ (Kappung, Herausnahme auf Wunsch). Fallgruppen „kein Fehler“ gehören nicht in die Fehlerquote. |
| `UR` | Kürzung als Unregelmäßigkeit gekennzeichnet |
| `BETRUG` | Merkmale einer Doppelabrechnung, nicht gezahlter Ausgaben oder einer Manipulation (auch über die Kennziffern 8.2 und 8.8) |
| `VERGABE` | Vergabemangel in der Beschreibung außerhalb der Kategorie 1 |
| `NF_FINANZIELL` | nichtfinanzielle Feststellung mit finanziellem Wortlaut |
| `ABHILFE_KUENFTIG` | Abhilfe erst angekündigt („wird geheilt“, „mit dem FB“) |
| `NF_THEMA` | Themen nichtfinanzieller Feststellungen, die die Formalregeln des Profils `efre.tof_2021_2027` nicht abdecken (Vergabe, Personal) |
| `ZGS_OFFEN` | Angabe der Zwischengeschalteten Stelle offen oder verschoben („zur gvRL“) |
| `SCHWELLE` | Schwellen; Merkmale nach Artikel 2 Nr. 33: mehr als fünf Vorhaben, ab drei Förderprogrammgruppen, ab 10 % des Korrekturbetrags |

## Abgleich

Eine Regel trifft, wenn die Kennziffer passt (falls angegeben), eines der
Stichwörter im kleingeschriebenen Text vorkommt (falls angegeben), eines der
Zusatzwörter vorkommt (falls angegeben) und keines der Ausschlusswörter.
`[wort]` verlangt das ganze Wort, Kennziffern werden exakt verglichen, `1.*`
steht für alle Kennziffern der Kategorie 1. Die erste zutreffende Regel eines
Bereichs gewinnt; die Reihenfolge ist fachlich festgelegt.

## Herkunft und Pflege

Quelle ist `RegelnStandard` in `modAKB_Regeln.bas` der AKB-Auswertung (1.8.1).
`tools/vba_regeln.py <modAKB_Regeln.bas> --check` prüft die Parität,
`--write` erzeugt die Regeln neu. Eine geänderte Regel ist eine neue
Regelwerksversion; veröffentlichte Versionen bleiben unverändert.
