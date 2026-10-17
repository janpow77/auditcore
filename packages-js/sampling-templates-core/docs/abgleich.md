# Abgleich der Rechenkerne mit der Vorlage

<!-- Erzeugt mit `npm run docs:write -w @auditcore/sampling-templates-core`; nicht von Hand ändern. -->

Je Fall werden die Eingaben in eine Kopie der Excel-Vorlage geschrieben, die Mappe wird in **Microsoft Excel**
(Microsoft 365, Version 16.0.20326, 64 Bit, de-de) neu berechnet, und jede Formelzelle des Blatts wird mit dem
Rechenkern verglichen: Zellen mit Ganzzahlformat genau, übrige Zahlen mit relativer Toleranz 1e-9, Texte wortgleich,
Wahrheits- und Fehlerwerte wie Excel sie zeigt. Die Sollwerte stammen aus der Excel-Gegenprobe vom 17.10.2026
(10.531 Fälle, 728.895 Formelzellen; Ablauf in [abweichungen.md](abweichungen.md), Abschnitt 3).

**Toleranzen und ihr Grund.** Der Rechenkern bildet die Rechensemantik von Excel nach (Vergleich nach Rundung auf
15 geltende Stellen, `AUFRUNDEN` mit Vorrundung auf 15 Stellen, `VERGLEICH` genau, Summen ohne Fehlerausgleich);
die Toleranz deckt nur die Reihenfolge der Gleitkommaoperationen, die in JavaScript und Excel nicht in jeder Formel
gleich ist (relative Unterschiede bis etwa 1e-15). Ganzzahlzellen (Stichprobenumfänge) sind davon ausgenommen und
müssen genau stimmen. Bei Eurobeträgen gilt zusätzlich ein absoluter Unterschied bis 0.000001 € als gleich
(Auslöschung in Abstimmungszellen wie Blatt 02 C30, wo Excel einen Rest bis 4,8e-7 € zeigt). Werte ab 10¹⁵ liegen
außerhalb des geprüften Zahlenbereichs: Dort wird nur die Größenordnung verglichen (relativ 0,001), und die
Webfassung weist das Ergebnis als nicht belastbar aus.

**LibreOffice** ist nur noch Hilfsmittel: Die früheren Sollwerte aus der Neuberechnung mit LibreOffice 24.2
(`scripts/golden_recalc.py`) liegen in der Versionsgeschichte (Stand 0.1.5) und unterscheiden sich in 937 Zellen
von Excel (Vergleichstoleranz, Aufrunden, genaue Suche, Wahrheitswert, `#DIV/0!`).

- **Begründet** sind Zellen, an denen die Webfassung nach der geltenden Richtlinie für fehlende Angaben keinen Wert
  zeigt, während die Vorlage einen zeigt ([abweichungen.md](abweichungen.md)); die Gegenprobe ist bestanden. Seit der
  Regel „bei vollständigen Pflichteingaben immer wie die Vorlage“ entstehen sie nur noch, wo eine Eingabe fehlt.
- **Bewusst anders dargestellt** sind Zellen, die die Webfassung nach einer festen Regel anders zeigt (`adapted`):
  die Kopfzeile von Blatt 20 (A6), die Fehlerquote eines Falls mit Buchwert 0 (Blatt 20 E20–E27: Excel `#DIV/0!`,
  Webfassung kein Wert mit Hinweis) und der Faktor zu einem Konfidenzniveau außerhalb der Stufen der Altvorlagen
  (X1 C5/C6, X2 C6, X3 D10, X4 C11: Excel FALSCH, Webfassung 0 mit Hinweis). Geprüft ist je Zelle, dass die Webfassung
  genau den Wert zeigt, der sich nach dieser Regel aus dem Wert von Excel ergibt.
- **Amtlicher Begriff** sind Texte, in denen die Webfassung statt „Signifikanzschwelle“ der Vorlage den amtlichen
  Begriff „Signifikanzschwelle“ zeigt (Anhang I Nr. 1 DelVO (EU) 2023/67); sonst ist der Text wortgleich.
- **Bewusst nach DelVO** sind Zellen, an denen die Webfassung nach Entscheidung des Inhabers vom 17.10.2026 nach der
  DelVO (EU) 2023/67 rechnet und nicht wie die Vorlage: Genauigkeit bei Ersetzung in Tabelle 2 (Anhang III; Blatt 18)
  und globale Neuberechnung bei AE ≥ TE (Anhang II; Blätter 05–07, 10–12). Je Zelle ist geprüft, dass die Webfassung
  den Wert zeigt, den `scripts/delvo_soll.py` unabhängig vom Rechenkern aus den Excel-Sollwerten nachrechnet
  (`test/golden-delvo/`); Folgegrößen eines nicht bestimmbaren Umfangs müssen leer sein.
- **Toleranzkanten** gibt es gegen Excel keine mehr: Die beiden Würdigungen, die gegen LibreOffice an der
  Vergleichstoleranz hingen (Blatt 06 C99, Blatt 12 C138), zeigt die Webfassung mit der Vergleichsregel von Excel
  genau wie Excel.
- **„Wie die Vorlage“** ist dieselbe Rechnung unter der Richtlinie `TEMPLATE_POLICY` (jede fehlende Angabe mit 0
  gerechnet): Dann muss jede Zelle den Wert der Vorlage zeigen.
- Die Fallsätze `abnahme-grund`, `abnahme-luecken` und `abnahme-schwelle` sind die 6.805 Fälle der unabhängigen
  Gesamtabnahme (eigener Generator, Einzellücken-Matrix, Schwellen- und Ganzzahlsonden).

| Blatt | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 02_Grundgesamtheit | 159 | 3021 | 2877 | 73 | 0 | 71 | 0 | 0 | 0 |
| 03_MUS_1Z | 783 | 29754 | 29347 | 308 | 0 | 99 | 0 | 0 | 0 |
| 04_MUS_1Z_S | 381 | 46482 | 45376 | 1003 | 0 | 103 | 0 | 0 | 0 |
| 05_MUS_2Z | 541 | 35165 | 32791 | 1924 | 0 | 103 | 347 | 0 | 0 |
| 06_MUS_2Z_S | 635 | 150495 | 145588 | 3192 | 0 | 127 | 1588 | 0 | 0 |
| 07_MUS_3Z | 612 | 56916 | 51913 | 4216 | 0 | 90 | 697 | 0 | 0 |
| 08_SRS_1Z | 660 | 24420 | 24078 | 210 | 0 | 132 | 0 | 0 | 0 |
| 09_SRS_1Z_S | 421 | 32417 | 31488 | 778 | 0 | 151 | 0 | 0 | 0 |
| 10_SRS_2Z | 714 | 42840 | 39082 | 3374 | 0 | 117 | 267 | 0 | 0 |
| 11_SRS_2Z_S | 724 | 118736 | 113853 | 3562 | 0 | 248 | 1073 | 0 | 0 |
| 12_SRS_3Z | 785 | 67510 | 61193 | 5800 | 0 | 135 | 382 | 0 | 0 |
| 13_NS_GW | 399 | 8778 | 8286 | 117 | 0 | 375 | 0 | 0 | 0 |
| 14_NS_GW_S | 410 | 16400 | 15709 | 301 | 0 | 390 | 0 | 0 | 0 |
| 15_NS_PPS | 406 | 10556 | 9970 | 222 | 0 | 364 | 0 | 0 | 0 |
| 16_NS_PPS_S | 412 | 28840 | 27840 | 618 | 0 | 382 | 0 | 0 | 0 |
| 17_Unterstichprobe | 102 | 612 | 577 | 35 | 0 | 0 | 0 | 0 | 0 |
| 18_GFQ_AnhIII | 677 | 14894 | 13866 | 289 | 0 | 438 | 301 | 0 | 0 |
| 20_Druck_KOM | 588 | 19404 | 17763 | 246 | 610 | 516 | 269 | 0 | 0 |
| X1_KonsMUS_2017 | 213 | 2769 | 2580 | 181 | 8 | 0 | 0 | 0 | 0 |
| X2_DiffSch_2017 | 434 | 5642 | 5445 | 193 | 4 | 0 | 0 | 0 | 0 |
| X3_DiffSch_S_2017 | 234 | 8424 | 7838 | 582 | 4 | 0 | 0 | 0 | 0 |
| X4_DiffSch_2Z_2017 | 241 | 4820 | 4486 | 330 | 4 | 0 | 0 | 0 | 0 |
| **Summe** | 10531 | 728895 | 691946 | 27554 | 630 | 3841 | 4924 | 0 | 0 |

## 02_Grundgesamtheit

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 69 | 1311 | 1266 | 38 | 0 | 7 | 0 | 0 | 0 |
| abnahme-luecken | 69 | 1311 | 1236 | 11 | 0 | 64 | 0 | 0 | 0 |
| Hauptsatz | 21 | 399 | 375 | 24 | 0 | 0 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall: abgestimmt, TH-Pauschale in SFC2021 enthalten | 19 | 0 | 0 |
| 2 | TH-Pauschale nicht enthalten | 19 | 0 | 0 |
| 3 | Differenz zum Zahlungsantrag, nicht erläutert | 19 | 0 | 0 |
| 4 | Differenz zum Zahlungsantrag, erläutert | 19 | 0 | 0 |
| 5 | Anzahl der Datensätze nicht abgestimmt, negative Summe positiv | 19 | 0 | 0 |
| 6 | Negative Datensätze mit negativer Summe, Datensätze nicht mit SFC2021 abgestimmt | 19 | 0 | 0 |
| 7 | Spezifische Ziele ausgeschlossen, wieder aufgenommene Ausgaben nicht enthalten | 19 | 0 | 0 |
| 8 | Wieder aufgenommene Ausgaben bereits enthalten (nur nachrichtlich) | 19 | 0 | 0 |
| 9 | Art. 80 Abs. 3: Ausschluss | 19 | 0 | 0 |
| 10 | Art. 80 Abs. 3: Ersetzung | 19 | 0 | 0 |
| 11 | Art. 80 Abs. 3: Einheiten erfasst, aber keine Behandlung gewählt | 19 | 0 | 0 |
| 12 | Art. 80 Abs. 3: Ansatz gewählt, aber keine Einheiten erfasst | 19 | 0 | 0 |
| 13 | Weniger als 300 Einheiten: nichtstatistisches Verfahren zulässig | 19 | 0 | 0 |
| 14 | Genau 300 Einheiten und Mindestumfang mit Aufrundung (N = 301) | 19 | 0 | 0 |
| 15 | Leeres Formular (nur Vorgaben der Vorlage) | 19 | 8 | 0 |
| 16 | Teilweise: nur Zahlungsantrag | 19 | 5 | 0 |
| 17 | Teilweise: nur Datensätze, Zahlungsantrag fehlt | 19 | 3 | 0 |
| 18 | Teilweise: alles ausgefüllt außer der Summe der positiven Datensätze | 19 | 3 | 0 |
| 19 | Teilweise: alles ausgefüllt außer der Anzahl der positiven Datensätze | 19 | 2 | 0 |
| 20 | Teilweise: alles ausgefüllt außer dem Betrag laut SFC2021 | 19 | 3 | 0 |
| 21 | Teilweise: Vorgaben geleert (TH enthalten, Wiederaufnahme, Schwellenwert, Behandlung) | 19 | 0 | 0 |

## 03_MUS_1Z

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 70 | 2660 | 2607 | 52 | 0 | 1 | 0 | 0 | 0 |
| abnahme-luecken | 355 | 13490 | 13414 | 48 | 0 | 28 | 0 | 0 | 0 |
| abnahme-schwelle | 60 | 2280 | 2260 | 0 | 0 | 20 | 0 | 0 | 0 |
| Hauptsatz | 40 | 1520 | 1414 | 103 | 0 | 3 | 0 | 0 | 0 |
| pruefer | 158 | 6004 | 5882 | 105 | 0 | 17 | 0 | 0 | 0 |
| zufall | 100 | 3800 | 3770 | 0 | 0 | 30 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Mittel 70 %, zweiseitig, Standardfall | 38 | 0 | 0 |
| 2 | Gering 90 %, einseitig, begrenzt Kategorie 1, systembedingte Fehler | 38 | 0 | 0 |
| 3 | Hoch 60 %, Art. 83 mit 30 Einheiten | 38 | 0 | 0 |
| 4 | Begrenzt beantragt, aber Kategorie 4 (unzulässig) | 38 | 0 | 0 |
| 5 | TE ≤ AE, Stichprobenumfang nicht bestimmbar | 38 | 0 | 0 |
| 6 | Mittel 80 %, begrenzt zulässig Kategorie 2: rechnerischer Umfang über 50 wird auf 50 begrenzt | 38 | 0 | 0 |
| 7 | Hoch 95 % einseitig (Konfidenzniveau außerhalb Anhang I) | 38 | 0 | 0 |
| 8 | Gering mit 60 %: Konfidenzniveau zu niedrig | 38 | 0 | 0 |
| 9 | Mittel mit 90 % zweiseitig: zu begründen | 38 | 0 | 0 |
| 10 | Hoch 70 % einseitig, anomale Fehler | 38 | 0 | 0 |
| 11 | Gering 95 % zweiseitig, systembedingte und anomale Fehler | 38 | 0 | 0 |
| 12 | Hoch 60 % einseitig und 80 % einseitig decken z' ab (hier 60 %) | 38 | 0 | 0 |
| 13 | Mittel 80 % einseitig | 38 | 0 | 0 |
| 14 | Weniger als 3 Einheiten in der Zufallsschicht | 38 | 0 | 0 |
| 15 | Zufallsschicht ohne Einheiten (n_s = 0) | 38 | 0 | 0 |
| 16 | Wesentlichkeitsschwelle 3 % unzulässig | 38 | 0 | 0 |
| 17 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 38 | 0 | 0 |
| 18 | GFQ unter, obere Fehlergrenze über der Schwelle | 38 | 0 | 0 |
| 19 | Iteration erforderlich (3 Einheiten über dem Auswahlintervall) | 38 | 0 | 0 |
| 20 | Rechnerischer Umfang nahe an einer ganzen Zahl (Aufrundung) | 38 | 0 | 0 |
| 21 | Leeres Formular (nur Vorgaben der Vorlage) | 38 | 6 | 0 |
| 22 | Teilweise: nur Grundgesamtheit und Parameter bis Standardabweichung | 38 | 0 | 0 |
| 23 | Teilweise: Standardabweichung fehlt | 38 | 11 | 0 |
| 24 | Teilweise: voraussichtliche Fehlerquote fehlt | 38 | 12 | 0 |
| 25 | Teilweise: Konfidenzniveau fehlt | 38 | 0 | 0 |
| 26 | Teilweise: Prüfergebnisse ohne Summe der Fehlerquoten | 38 | 0 | 0 |
| 27 | Teilweise: Prüfergebnisse ohne Standardabweichung der Stichprobe | 38 | 0 | 0 |
| 28 | Teilweise: hochwertige Schicht nicht angegeben | 38 | 0 | 0 |
| 29 | Teilweise: Vorgaben geleert (Testart, Schwelle, Art. 83, begrenzter Umfang) | 38 | 1 | 0 |
| 30 | Teilweise: Buchwert fehlt | 38 | 5 | 0 |
| 31 | Begrenzt mit Art. 83, rechnerischer Umfang unter 30 | 38 | 0 | 0 |
| 32 | Begrenzt zulässig, Standardabweichung fehlt (begrenzter Umfang ohne rechnerischen Umfang) | 38 | 11 | 0 |
| 33 | Teilweise: alles ausgefüllt außer der voraussichtlichen Standardabweichung | 38 | 20 | 0 |
| 34 | Teilweise: alles ausgefüllt außer der voraussichtlichen Fehlerquote | 38 | 21 | 0 |
| 35 | Teilweise: alles ausgefüllt außer Buchwert und Umfang der Grundgesamtheit | 38 | 6 | 0 |
| 36 | Teilweise: begrenzter Umfang zulässig, sonst keine Angaben | 38 | 9 | 0 |
| 37 | Teilweise: Wesentlichkeitsschwelle geleert, sonst vollständig | 38 | 1 | 0 |
| 38 | Buchwert und Umfang aus Blatt 02 übernommen (Verknüpfung) | 38 | 0 | 0 |
| 39 | Blatt 02 ausgefüllt, Buchwert im Methodenblatt überschrieben | 38 | 0 | 0 |
| 40 | Blatt 02 mit Ausschluss nach Art. 80 Abs. 3: angepasste Grundgesamtheit fließt ein | 38 | 0 | 0 |

## 04_MUS_1Z_S

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 70 | 8540 | 8351 | 178 | 0 | 11 | 0 | 0 | 0 |
| abnahme-luecken | 124 | 15128 | 14844 | 256 | 0 | 28 | 0 | 0 | 0 |
| abnahme-schwelle | 60 | 7320 | 7240 | 60 | 0 | 20 | 0 | 0 | 0 |
| Hauptsatz | 27 | 3294 | 2882 | 409 | 0 | 3 | 0 | 0 | 0 |
| zufall | 100 | 12200 | 12059 | 100 | 0 | 41 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Drei Schichten, mittel 70 %, zweiseitig, Standardfall | 122 | 1 | 0 |
| 2 | Sieben Schichten (alle Spalten der Vorlage) | 122 | 1 | 0 |
| 3 | Eine Schicht | 122 | 1 | 0 |
| 4 | Zwei Schichten, gering 90 %, einseitig, systembedingte und anomale Fehler | 122 | 1 | 0 |
| 5 | Hoch 60 %, Art. 83 mit 30 Einheiten | 122 | 1 | 0 |
| 6 | Begrenzt zulässig Kategorie 1 (50 Einheiten) | 122 | 1 | 0 |
| 7 | Begrenzt beantragt, aber Kategorie 3 (unzulässig) | 122 | 1 | 0 |
| 8 | TE ≤ AE, Stichprobenumfang nicht bestimmbar | 122 | 1 | 0 |
| 9 | Hoch 95 % einseitig, fünf Schichten | 122 | 1 | 0 |
| 10 | Gering mit 60 %: Konfidenzniveau zu niedrig; Wesentlichkeitsschwelle 3 % | 122 | 1 | 0 |
| 11 | Weniger als 3 Einheiten in einer Zufallsschicht | 122 | 1 | 0 |
| 12 | Zufallsschicht ohne Einheiten in einer Schicht (n_hs = 0) | 122 | 1 | 0 |
| 13 | Iteration in zwei Schichten | 122 | 1 | 0 |
| 14 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 122 | 1 | 0 |
| 15 | GFQ unter, obere Fehlergrenze über der Schwelle | 122 | 1 | 0 |
| 16 | Lücke: Schicht 2 leer, Schichten 1 und 3 belegt | 122 | 1 | 0 |
| 17 | Leeres Formular (nur Vorgaben der Vorlage) | 122 | 17 | 0 |
| 18 | Teilweise: nur Buchwerte und Anzahlen der Schichten | 122 | 24 | 0 |
| 19 | Teilweise: sieben Schichten, Standardabweichungen fehlen | 122 | 86 | 0 |
| 20 | Teilweise: sieben Schichten, Standardabweichung nur in Schicht 4 fehlt | 122 | 80 | 0 |
| 21 | Teilweise: sieben Schichten, voraussichtliche Fehlerquote fehlt | 122 | 78 | 0 |
| 22 | Teilweise: Konfidenzniveau fehlt | 122 | 1 | 0 |
| 23 | Teilweise: Prüfergebnisse fehlen | 122 | 1 | 0 |
| 24 | Teilweise: Standardabweichung der Stichprobe fehlt in einer Schicht | 122 | 1 | 0 |
| 25 | Teilweise: Wesentlichkeitsschwelle und Vorgaben geleert | 122 | 19 | 0 |
| 26 | Teilweise: begrenzt zulässig, Standardabweichungen fehlen | 122 | 86 | 0 |
| 27 | Blatt 02 ausgefüllt: Abweichung zur angepassten Grundgesamtheit | 122 | 0 | 0 |

## 05_MUS_2Z

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 70 | 4550 | 4359 | 169 | 0 | 11 | 11 | 0 | 0 |
| abnahme-luecken | 232 | 15080 | 14103 | 937 | 0 | 28 | 12 | 0 | 0 |
| abnahme-schwelle | 60 | 3900 | 3880 | 0 | 0 | 20 | 0 | 0 | 0 |
| fehlend | 5 | 325 | 261 | 30 | 0 | 1 | 33 | 0 | 0 |
| Hauptsatz | 74 | 4810 | 3972 | 788 | 0 | 9 | 41 | 0 | 0 |
| zufall | 100 | 6500 | 6216 | 0 | 0 | 34 | 250 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall: mittel 70 %, zweiseitig, Standardneuberechnung | 65 | 0 | 0 |
| 2 | Globale Neuberechnung | 65 | 0 | 0 |
| 3 | Negativer Nenner, Standardneuberechnung gewählt | 65 | 0 | 0 |
| 4 | Negativer Nenner, globale Neuberechnung mit Zusatzeinheiten in Zeitraum 1 | 65 | 0 | 0 |
| 5 | Negativer Nenner bei großem Umfang in Zeitraum 1 | 65 | 0 | 0 |
| 6 | Erhöhung bei begrenztem Umfang, Kategorie 1 (50 Einheiten), Umfang überschritten | 65 | 0 | 0 |
| 7 | Erhöhung bei begrenztem Umfang, Ist unter Prognose (Faktor 1), Umfang eingehalten | 65 | 0 | 0 |
| 8 | Erhöhung nach Anzahl der Einheiten (N-Verhältnis größer als BV-Verhältnis) | 65 | 0 | 0 |
| 9 | Keine Neuberechnung | 65 | 0 | 0 |
| 10 | Gering 90 %, einseitig, systembedingte und anomale Fehler | 65 | 0 | 0 |
| 11 | Hoch 60 %, Art. 83 mit 30 Einheiten, Standardneuberechnung | 65 | 0 | 0 |
| 12 | Hoch 95 %, einseitig, globale Neuberechnung | 65 | 0 | 0 |
| 13 | Hoch 80 %, begrenzt zulässig, globale Neuberechnung begrenzt | 65 | 0 | 0 |
| 14 | Begrenzt beantragt, aber Kategorie 3 (unzulässig) | 65 | 0 | 0 |
| 15 | TE ≤ AE, Stichprobenumfang nicht bestimmbar | 65 | 0 | 0 |
| 16 | TE = AE genau auf der Schwelle | 65 | 0 | 0 |
| 17 | TE knapp über AE | 65 | 0 | 0 |
| 18 | TE ≤ AE mit begrenztem Umfang | 65 | 0 | 0 |
| 19 | Wesentlichkeitsschwelle 2,01 % (unzulässig); gering mit 60 % | 65 | 0 | 0 |
| 20 | Mittel mit Eckwert 60 % | 65 | 0 | 0 |
| 21 | Mittel mit Eckwert 90 % | 65 | 0 | 0 |
| 22 | Gering mit 80 % (zu niedrig); hoch-Grenze | 65 | 0 | 0 |
| 23 | Rechnerischer Gesamtumfang genau 100 | 65 | 0 | 0 |
| 24 | Weniger als 3 Einheiten in der Zufallsschicht von Zeitraum 1 | 65 | 0 | 0 |
| 25 | Weniger als 3 Einheiten in der Zufallsschicht von Zeitraum 2 | 65 | 0 | 0 |
| 26 | Genau 3 Einheiten in der Zufallsschicht von Zeitraum 2 | 65 | 0 | 0 |
| 27 | Iteration in beiden Zeiträumen | 65 | 0 | 0 |
| 28 | Keine hochwertigen Einheiten | 65 | 0 | 0 |
| 29 | Hochwertige Einheiten mit Fehlern in beiden Zeiträumen | 65 | 0 | 0 |
| 30 | Zeitraum 2 ohne Fehler | 65 | 0 | 0 |
| 31 | Zeitraum 1 ohne Fehler, Summe der Fehlerquoten leer | 65 | 0 | 0 |
| 32 | Keine Fehlerquoten in beiden Zeiträumen (EE bleibt leer) | 65 | 0 | 0 |
| 33 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 65 | 0 | 0 |
| 34 | GFQ unter, obere Fehlergrenze über der Schwelle | 65 | 0 | 0 |
| 35 | Gesamtfehlerquote genau 2 % | 65 | 0 | 0 |
| 36 | Aktualisierte voraussichtliche Fehlerquote | 65 | 0 | 0 |
| 37 | Auffüllung auf 30 Einheiten im Geschäftsjahr | 65 | 0 | 0 |
| 38 | Standardneuberechnung ergibt 0 (σ_r2 = 0) | 65 | 0 | 0 |
| 39 | Standardabweichung der Stichprobe Zeitraum 1 gleich 0 | 65 | 0 | 0 |
| 40 | Globale Neuberechnung mit TE = AE (aktualisiert) | 65 | 0 | 0 |
| 41 | Globale Neuberechnung mit TE < AE (aktualisiert) | 65 | 0 | 0 |
| 42 | Leeres Formular (nur Vorgaben der Vorlage) | 65 | 11 | 0 |
| 43 | Leeres Formular ohne Vorgaben | 65 | 11 | 0 |
| 44 | Teilweise: nur der erste Zeitraum ausgefüllt | 65 | 35 | 0 |
| 45 | Teilweise: nur der erste Zeitraum ausgefüllt, globale Neuberechnung | 65 | 37 | 0 |
| 46 | Teilweise: nur Grundgesamtheit und Parameter | 65 | 26 | 0 |
| 47 | Teilweise: nur Buchwerte | 65 | 10 | 0 |
| 48 | Teilweise: Buchwert Zeitraum 1 fehlt | 65 | 46 | 0 |
| 49 | Teilweise: prognostizierter Buchwert Zeitraum 2 fehlt | 65 | 40 | 0 |
| 50 | Teilweise: Wesentlichkeitsschwelle geleert | 65 | 3 | 0 |
| 51 | Teilweise: voraussichtliche Fehlerquote fehlt | 65 | 40 | 0 |
| 52 | Teilweise: voraussichtliche Fehlerquote fehlt, aktualisierte vorhanden | 65 | 35 | 0 |
| 53 | Teilweise: voraussichtliche Standardabweichung Zeitraum 1 fehlt | 65 | 35 | 0 |
| 54 | Teilweise: voraussichtliche Standardabweichung Zeitraum 1 und der Stichprobe fehlen | 65 | 41 | 0 |
| 55 | Teilweise: voraussichtliche Standardabweichung Zeitraum 2 fehlt | 65 | 35 | 0 |
| 56 | Teilweise: beide voraussichtlichen Standardabweichungen fehlen, begrenzt zulässig | 65 | 36 | 0 |
| 57 | Teilweise: Buchwert Zeitraum 2 (Ist) fehlt | 65 | 35 | 0 |
| 58 | Teilweise: Buchwert Zeitraum 2 (Ist) fehlt, Erhöhung | 65 | 36 | 0 |
| 59 | Teilweise: aktualisierte Standardabweichung Zeitraum 2 fehlt | 65 | 27 | 0 |
| 60 | Teilweise: aktualisierte Standardabweichung Zeitraum 2 fehlt, globale Neuberechnung | 65 | 29 | 0 |
| 61 | Teilweise: aktualisierte Standardabweichung Zeitraum 2 fehlt, negativer Nenner | 65 | 26 | 0 |
| 62 | Teilweise: Standardabweichung der Stichprobe Zeitraum 1 fehlt | 65 | 0 | 0 |
| 63 | Teilweise: Standardabweichung der Stichprobe Zeitraum 2 fehlt | 65 | 0 | 0 |
| 64 | Teilweise: Standardabweichungen der Stichprobe fehlen in beiden Zeiträumen | 65 | 0 | 0 |
| 65 | Teilweise: Konfidenzniveau fehlt | 65 | 0 | 0 |
| 66 | Teilweise: Konfidenzniveau fehlt, begrenzt zulässig | 65 | 0 | 0 |
| 67 | Teilweise: Ist-Anzahl und Prognose der Einheiten fehlen, Erhöhung | 65 | 0 | 0 |
| 68 | Teilweise: Ansatz der Neuberechnung und Testart geleert | 65 | 0 | 0 |
| 69 | Teilweise: Prüfergebnisse fehlen | 65 | 0 | 0 |
| 70 | Teilweise: begrenzt zulässig, Buchwert Zeitraum 1 fehlt | 65 | 47 | 0 |
| 71 | Teilweise: begrenzt zulässig, prognostizierter Buchwert Zeitraum 2 fehlt | 65 | 41 | 0 |
| 72 | Teilweise: begrenzt zulässig, voraussichtliche Fehlerquote fehlt | 65 | 41 | 0 |
| 73 | Teilweise: begrenzt zulässig, aktualisierte Standardabweichung Zeitraum 2 fehlt | 65 | 28 | 0 |
| 74 | Teilweise: Buchwert Zeitraum 2 (Ist) fehlt, globale Neuberechnung | 65 | 37 | 0 |

## 06_MUS_2Z_S

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 110 | 26070 | 25507 | 449 | 0 | 7 | 107 | 0 | 0 |
| abnahme-luecken | 291 | 68967 | 66688 | 1589 | 0 | 67 | 623 | 0 | 0 |
| abnahme-schwelle | 60 | 14220 | 14200 | 0 | 0 | 20 | 0 | 0 | 0 |
| fehlend | 14 | 3318 | 2840 | 391 | 0 | 1 | 86 | 0 | 0 |
| Hauptsatz | 60 | 14220 | 13403 | 763 | 0 | 3 | 51 | 0 | 0 |
| zufall | 100 | 23700 | 22950 | 0 | 0 | 29 | 721 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall: drei Schichten, mittel 70 %, zweiseitig, Standardneuberechnung | 237 | 0 | 0 |
| 2 | Sieben Schichten (alle Spalten der Vorlage), Standardneuberechnung | 237 | 0 | 0 |
| 3 | Eine Schicht | 237 | 0 | 0 |
| 4 | Globale Neuberechnung, drei Schichten | 237 | 0 | 0 |
| 5 | Globale Neuberechnung, sieben Schichten | 237 | 0 | 0 |
| 6 | Negativer Nenner, Standardneuberechnung gewählt (kein Umfang für Zeitraum 2) | 237 | 0 | 0 |
| 7 | Negativer Nenner, globale Neuberechnung mit Zusatzeinheiten in Zeitraum 1 | 237 | 0 | 0 |
| 8 | Erhöhung bei begrenztem Umfang, Kategorie 1 (50 Einheiten), Umfang überschritten | 237 | 0 | 0 |
| 9 | Erhöhung bei begrenztem Umfang, Art. 83 (30 Einheiten), Ist unter Prognose | 237 | 0 | 0 |
| 10 | Erhöhung nach Anzahl der Einheiten in einer Schicht | 237 | 0 | 0 |
| 11 | Keine Neuberechnung | 237 | 0 | 0 |
| 12 | Gering 90 %, einseitig, systembedingte und anomale Fehler | 237 | 0 | 0 |
| 13 | Hoch 60 %, Art. 83 mit 30 Einheiten, Standardneuberechnung | 237 | 0 | 0 |
| 14 | Hoch 95 %, einseitig, globale Neuberechnung, fünf Schichten | 237 | 0 | 0 |
| 15 | Hoch 80 %, begrenzt zulässig, globale Neuberechnung begrenzt | 237 | 0 | 0 |
| 16 | Begrenzt beantragt, aber Kategorie 3 (unzulässig) | 237 | 0 | 0 |
| 17 | Begrenzt zulässig Kategorie 2: Summe der Schichtumfänge über dem begrenzten Umfang | 237 | 0 | 0 |
| 18 | TE ≤ AE, Stichprobenumfang nicht bestimmbar, sieben Schichten | 237 | 0 | 0 |
| 19 | TE = AE genau auf der Schwelle | 237 | 0 | 0 |
| 20 | Wesentlichkeitsschwelle 2,01 % (unzulässig); gering mit 60 % | 237 | 0 | 0 |
| 21 | Mittel mit Eckwert 90 % | 237 | 0 | 0 |
| 22 | Rechnerischer Gesamtumfang genau 100 | 237 | 0 | 0 |
| 23 | Weniger als 3 Einheiten in einer Zufallsschicht von Zeitraum 1 | 237 | 0 | 0 |
| 24 | Weniger als 3 Einheiten in einer Zufallsschicht von Zeitraum 2 | 237 | 0 | 0 |
| 25 | Zufallsschicht ohne Einheiten in einer Schicht (n_hs = 0) | 237 | 0 | 0 |
| 26 | Iteration: weitere hochwertige Einheiten in zwei Schichten | 237 | 0 | 0 |
| 27 | Keine hochwertigen Einheiten | 237 | 0 | 0 |
| 28 | Zeitraum 2 ohne Fehler | 237 | 0 | 0 |
| 29 | Keine Fehlerquoten in beiden Zeiträumen (EE bleibt leer) | 237 | 0 | 0 |
| 30 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 237 | 0 | 0 |
| 31 | GFQ unter, obere Fehlergrenze über der Schwelle | 237 | 0 | 0 |
| 32 | Gesamtfehlerquote genau 2 % | 237 | 0 | 0 |
| 33 | Aktualisierte voraussichtliche Fehlerquote | 237 | 0 | 0 |
| 34 | Auffüllung: kleiner Umfang, mindestens 3 je Schicht in Zeitraum 2 | 237 | 0 | 0 |
| 35 | Standardneuberechnung ergibt 0 (σ_rh2 = 0) | 237 | 0 | 0 |
| 36 | Globale Neuberechnung mit TE = AE (aktualisiert) | 237 | 0 | 0 |
| 37 | Lücke: Schicht 2 leer, Schichten 1 und 3 belegt | 237 | 0 | 0 |
| 38 | Schicht 3 nur im ersten Zeitraum (kein Ist-Buchwert Zeitraum 2) | 237 | 0 | 0 |
| 39 | Schicht 3 erst im zweiten Zeitraum (kein Buchwert Zeitraum 1) | 237 | 0 | 0 |
| 40 | Schicht 3 ohne Prognose für Zeitraum 2, keine Neuberechnung | 237 | 25 | 0 |
| 41 | Schicht 3 ohne Prognose für Zeitraum 2, Erhöhung | 237 | 1 | 0 |
| 42 | Leeres Formular (nur Vorgaben der Vorlage) | 237 | 33 | 0 |
| 43 | Leeres Formular ohne Vorgaben | 237 | 33 | 0 |
| 44 | Teilweise: nur der erste Zeitraum ausgefüllt | 237 | 34 | 0 |
| 45 | Teilweise: nur der erste Zeitraum ausgefüllt, sieben Schichten, globale Neuberechnung | 237 | 68 | 0 |
| 46 | Teilweise: nur Buchwerte und Anzahlen der Schichten | 237 | 54 | 0 |
| 47 | Teilweise: Wesentlichkeitsschwelle geleert | 237 | 47 | 0 |
| 48 | Teilweise: voraussichtliche Fehlerquote fehlt | 237 | 84 | 0 |
| 49 | Teilweise: sieben Schichten, voraussichtliche Standardabweichungen Zeitraum 1 und der Stichprobe fehlen | 237 | 174 | 0 |
| 50 | Teilweise: sieben Schichten, aktualisierte Standardabweichungen Zeitraum 2 fehlen | 237 | 94 | 0 |
| 51 | Teilweise: aktualisierte Standardabweichungen fehlen, begrenzt zulässig | 237 | 55 | 0 |
| 52 | Teilweise: aktualisierte Standardabweichung fehlt nur in Schicht 3 | 237 | 50 | 0 |
| 53 | Teilweise: aktualisierte Standardabweichung fehlt nur in Schicht 3, Erhöhung | 237 | 11 | 0 |
| 54 | Teilweise: Standardabweichung der Stichprobe Zeitraum 1 fehlt in einer Schicht | 237 | 0 | 0 |
| 55 | Teilweise: Standardabweichung der Stichprobe Zeitraum 2 fehlt in einer Schicht | 237 | 0 | 0 |
| 56 | Teilweise: Standardabweichungen der Stichprobe fehlen in allen Schichten | 237 | 0 | 0 |
| 57 | Teilweise: Konfidenzniveau fehlt | 237 | 0 | 0 |
| 58 | Teilweise: Ist-Anzahlen und Prognosen der Einheiten fehlen, Erhöhung | 237 | 0 | 0 |
| 59 | Teilweise: Ansatz der Neuberechnung und Testart geleert | 237 | 0 | 0 |
| 60 | Teilweise: Prüfergebnisse fehlen | 237 | 0 | 0 |

## 07_MUS_3Z

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 70 | 6510 | 6173 | 275 | 0 | 11 | 51 | 0 | 0 |
| abnahme-luecken | 289 | 26877 | 24501 | 2258 | 0 | 25 | 93 | 0 | 0 |
| abnahme-schwelle | 60 | 5580 | 5560 | 0 | 0 | 20 | 0 | 0 | 0 |
| fehlend | 7 | 651 | 503 | 92 | 0 | 1 | 55 | 0 | 0 |
| Hauptsatz | 86 | 7998 | 6337 | 1591 | 0 | 8 | 62 | 0 | 0 |
| zufall | 100 | 9300 | 8839 | 0 | 0 | 25 | 436 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall: mittel 70 %, zweiseitig, Standardneuberechnung | 93 | 0 | 0 |
| 2 | Globale Neuberechnung | 93 | 0 | 0 |
| 3 | Negativer Nenner nach Zeitraum 1, Standardneuberechnung gewählt | 93 | 0 | 0 |
| 4 | Negativer Nenner nach Zeitraum 2, Standardneuberechnung gewählt | 93 | 0 | 0 |
| 5 | Negativer Nenner nach beiden Zeiträumen, globale Neuberechnung mit Zusatzeinheiten | 93 | 0 | 0 |
| 6 | Negativer Nenner nach Zeitraum 2, globale Neuberechnung | 93 | 0 | 0 |
| 7 | Erhöhung bei begrenztem Umfang, Kategorie 1 (50 Einheiten), Umfang überschritten | 93 | 0 | 0 |
| 8 | Erhöhung bei begrenztem Umfang, Ist unter Prognose (Faktor 1), Umfang eingehalten | 93 | 0 | 0 |
| 9 | Erhöhung nach Anzahl der Einheiten | 93 | 0 | 0 |
| 10 | Keine Neuberechnung | 93 | 0 | 0 |
| 11 | Gering 90 %, einseitig, systembedingte und anomale Fehler | 93 | 0 | 0 |
| 12 | Hoch 60 %, Art. 83 mit 30 Einheiten, Standardneuberechnung | 93 | 0 | 0 |
| 13 | Hoch 95 %, einseitig, globale Neuberechnung | 93 | 0 | 0 |
| 14 | Hoch 80 %, begrenzt zulässig, globale Neuberechnung begrenzt | 93 | 0 | 0 |
| 15 | Begrenzt beantragt, aber Kategorie 3 (unzulässig) | 93 | 0 | 0 |
| 16 | TE ≤ AE, Stichprobenumfang nicht bestimmbar | 93 | 0 | 0 |
| 17 | TE = AE genau auf der Schwelle | 93 | 0 | 0 |
| 18 | TE knapp über AE | 93 | 0 | 0 |
| 19 | TE ≤ AE mit begrenztem Umfang | 93 | 0 | 0 |
| 20 | Wesentlichkeitsschwelle 2,01 % (unzulässig); gering mit 60 % | 93 | 0 | 0 |
| 21 | Mittel mit Eckwert 60 % | 93 | 0 | 0 |
| 22 | Mittel mit Eckwert 90 % | 93 | 0 | 0 |
| 23 | Rechnerischer Gesamtumfang genau 100 | 93 | 0 | 0 |
| 24 | Weniger als 3 Einheiten in der Zufallsschicht von Zeitraum 1 | 93 | 0 | 0 |
| 25 | Weniger als 3 Einheiten in der Zufallsschicht von Zeitraum 2 | 93 | 0 | 0 |
| 26 | Weniger als 3 Einheiten in der Zufallsschicht von Zeitraum 3 | 93 | 0 | 0 |
| 27 | Iteration in allen Zeiträumen | 93 | 0 | 0 |
| 28 | Keine hochwertigen Einheiten | 93 | 0 | 0 |
| 29 | Hochwertige Einheiten mit Fehlern in allen Zeiträumen | 93 | 0 | 0 |
| 30 | Zeitraum 2 ohne Fehler | 93 | 0 | 0 |
| 31 | Zeitraum 3 ohne Fehler, Summe der Fehlerquoten leer | 93 | 0 | 0 |
| 32 | Keine Fehlerquoten in allen Zeiträumen (EE bleibt leer) | 93 | 0 | 0 |
| 33 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 93 | 0 | 0 |
| 34 | GFQ unter, obere Fehlergrenze über der Schwelle | 93 | 0 | 0 |
| 35 | Gesamtfehlerquote genau 2 % | 93 | 0 | 0 |
| 36 | Aktualisierte voraussichtliche Fehlerquote nach Zeitraum 1 | 93 | 0 | 0 |
| 37 | Aktualisierte voraussichtliche Fehlerquote nach Zeitraum 2 | 93 | 0 | 0 |
| 38 | Aktualisierte voraussichtliche Fehlerquote nach beiden Zeiträumen | 93 | 0 | 0 |
| 39 | Auffüllung auf 30 Einheiten im Geschäftsjahr | 93 | 0 | 0 |
| 40 | Standardneuberechnung ergibt 0 (σ = 0 für die Zeiträume 2 und 3) | 93 | 0 | 0 |
| 41 | Globale Neuberechnung mit TE = AE (aktualisiert) | 93 | 0 | 0 |
| 42 | Globale Neuberechnung mit TE < AE nach Zeitraum 2 | 93 | 0 | 0 |
| 43 | Leeres Formular (nur Vorgaben der Vorlage) | 93 | 23 | 0 |
| 44 | Leeres Formular ohne Vorgaben | 93 | 23 | 0 |
| 45 | Teilweise: nur der erste Zeitraum ausgefüllt | 93 | 54 | 0 |
| 46 | Teilweise: nur der erste Zeitraum ausgefüllt, globale Neuberechnung | 93 | 59 | 0 |
| 47 | Teilweise: erster und zweiter Zeitraum ausgefüllt | 93 | 34 | 0 |
| 48 | Teilweise: erster und zweiter Zeitraum ausgefüllt, globale Neuberechnung | 93 | 38 | 0 |
| 49 | Teilweise: nur Grundgesamtheit und Parameter | 93 | 46 | 0 |
| 50 | Teilweise: nur Buchwerte | 93 | 23 | 0 |
| 51 | Teilweise: Wesentlichkeitsschwelle geleert | 93 | 12 | 0 |
| 52 | Teilweise: Konfidenzniveau fehlt | 93 | 0 | 0 |
| 53 | Teilweise: Konfidenzniveau fehlt, begrenzt zulässig | 93 | 0 | 0 |
| 54 | Teilweise: Ansatz der Neuberechnung und Testart geleert | 93 | 0 | 0 |
| 55 | Teilweise: Standardabweichung der Stichprobe Zeitraum 1 fehlt | 93 | 0 | 0 |
| 56 | Teilweise: Standardabweichung der Stichprobe Zeitraum 2 fehlt | 93 | 0 | 0 |
| 57 | Teilweise: Standardabweichung der Stichprobe Zeitraum 3 fehlt | 93 | 0 | 0 |
| 58 | Teilweise: Standardabweichungen der Stichprobe fehlen in allen Zeiträumen | 93 | 0 | 0 |
| 59 | Teilweise: voraussichtliche Standardabweichung Zeitraum 1 und der Stichprobe fehlen | 93 | 62 | 0 |
| 60 | Teilweise: aktualisierte Standardabweichung Zeitraum 2 und der Stichprobe fehlen | 93 | 48 | 0 |
| 61 | Teilweise: voraussichtliche Fehlerquote fehlt, aktualisierte vorhanden | 93 | 52 | 0 |
| 62 | Teilweise: alle voraussichtlichen Standardabweichungen fehlen, begrenzt zulässig | 93 | 53 | 0 |
| 63 | Teilweise: Ist-Anzahlen und Prognosen der Einheiten fehlen, Erhöhung | 93 | 0 | 0 |
| 64 | Teilweise: Prüfergebnisse fehlen | 93 | 0 | 0 |
| 65 | Teilweise: Buchwert Zeitraum 1 fehlt | 93 | 64 | 0 |
| 66 | Teilweise: prognostizierter Buchwert Zeitraum 2 fehlt | 93 | 56 | 0 |
| 67 | Teilweise: prognostizierter Buchwert Zeitraum 3 fehlt | 93 | 56 | 0 |
| 68 | Teilweise: voraussichtliche Fehlerquote fehlt | 93 | 61 | 0 |
| 69 | Teilweise: voraussichtliche Standardabweichung Zeitraum 1 fehlt | 93 | 52 | 0 |
| 70 | Teilweise: voraussichtliche Standardabweichung Zeitraum 2 fehlt | 93 | 52 | 0 |
| 71 | Teilweise: voraussichtliche Standardabweichung Zeitraum 3 fehlt | 93 | 52 | 0 |
| 72 | Teilweise: Buchwert Zeitraum 2 (Ist) fehlt | 93 | 58 | 0 |
| 73 | Teilweise: aktualisierte Prognose Buchwert Zeitraum 3 fehlt | 93 | 47 | 0 |
| 74 | Teilweise: aktualisierte Standardabweichung Zeitraum 2 fehlt | 93 | 42 | 0 |
| 75 | Teilweise: aktualisierte Standardabweichung Zeitraum 3 fehlt | 93 | 42 | 0 |
| 76 | Teilweise: Buchwert Zeitraum 3 (Ist) fehlt | 93 | 34 | 0 |
| 77 | Teilweise: aktualisierte Standardabweichung Zeitraum 3 (nach Zeitraum 2) fehlt | 93 | 27 | 0 |
| 78 | Teilweise: Buchwert Zeitraum 1 fehlt, globale Neuberechnung | 93 | 66 | 0 |
| 79 | Teilweise: Buchwert Zeitraum 2 (Ist) fehlt, globale Neuberechnung | 93 | 61 | 0 |
| 80 | Teilweise: Buchwert Zeitraum 3 (Ist) fehlt, globale Neuberechnung | 93 | 38 | 0 |
| 81 | Teilweise: prognostizierter Buchwert Zeitraum 2 fehlt, Erhöhung, begrenzt zulässig | 93 | 57 | 0 |
| 82 | Teilweise: aktualisierte Prognose Buchwert Zeitraum 3 fehlt, Erhöhung, begrenzt zulässig | 93 | 37 | 0 |
| 83 | Teilweise: voraussichtliche Fehlerquote fehlt, begrenzt zulässig | 93 | 62 | 0 |
| 84 | Teilweise: aktualisierte Standardabweichung Zeitraum 2 fehlt, begrenzt zulässig | 93 | 43 | 0 |
| 85 | Teilweise: aktualisierte Standardabweichung Zeitraum 3 (nach Zeitraum 2) fehlt, begrenzt zulässig | 93 | 28 | 0 |
| 86 | Teilweise: Buchwert Zeitraum 3 (Ist) fehlt, keine Neuberechnung | 93 | 29 | 0 |

## 08_SRS_1Z

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 70 | 2590 | 2524 | 39 | 0 | 27 | 0 | 0 | 0 |
| abnahme-luecken | 362 | 13394 | 13303 | 42 | 0 | 49 | 0 | 0 | 0 |
| abnahme-schwelle | 60 | 2220 | 2200 | 0 | 0 | 20 | 0 | 0 | 0 |
| Hauptsatz | 68 | 2516 | 2383 | 129 | 0 | 4 | 0 | 0 | 0 |
| zufall | 100 | 3700 | 3668 | 0 | 0 | 32 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Mittel 70 %, zweiseitig, Standardfall | 37 | 0 | 0 |
| 2 | Gering 90 %, einseitig, begrenzt Kategorie 1, systembedingte Fehler | 37 | 0 | 0 |
| 3 | Hoch 60 %, Art. 83 mit 30 Einheiten | 37 | 0 | 0 |
| 4 | Begrenzt beantragt, aber Kategorie 4 (unzulässig) | 37 | 0 | 0 |
| 5 | Begrenzt beantragt, Kategorie 3 (unzulässig), Art. 83 Nein | 37 | 0 | 0 |
| 6 | TE ≤ AE, Stichprobenumfang nicht bestimmbar | 37 | 0 | 0 |
| 7 | TE = AE genau auf der Schwelle | 37 | 0 | 0 |
| 8 | TE knapp über AE | 37 | 0 | 0 |
| 9 | TE ≤ AE mit begrenztem Umfang Kategorie 2 | 37 | 0 | 0 |
| 10 | Mittel 80 %, begrenzt zulässig Kategorie 2: rechnerischer Umfang über 50 wird begrenzt | 37 | 0 | 0 |
| 11 | Begrenzt zulässig, rechnerischer Umfang unter dem begrenzten Umfang | 37 | 0 | 0 |
| 12 | Begrenzt mit Art. 83, rechnerischer Umfang unter dem Mindestumfang | 37 | 0 | 0 |
| 13 | Hoch 95 % einseitig (Konfidenzniveau außerhalb Anhang I) | 37 | 0 | 0 |
| 14 | Hoch 95 % zweiseitig | 37 | 0 | 0 |
| 15 | Gering mit 60 %: Konfidenzniveau zu niedrig | 37 | 0 | 0 |
| 16 | Gering 90 % zweiseitig: Eckwert eingehalten | 37 | 0 | 0 |
| 17 | Gering 80 %: knapp unter dem Eckwert | 37 | 0 | 0 |
| 18 | Hoch 60 % einseitig: Eckwert eingehalten | 37 | 0 | 0 |
| 19 | Mittel mit 90 % zweiseitig: zu begründen | 37 | 0 | 0 |
| 20 | Mittel mit 60 %: zu begründen | 37 | 0 | 0 |
| 21 | Mittel 80 % einseitig | 37 | 0 | 0 |
| 22 | Hoch 70 % einseitig, anomale Fehler | 37 | 0 | 0 |
| 23 | Gering 95 % zweiseitig, systembedingte und anomale Fehler | 37 | 0 | 0 |
| 24 | Wesentlichkeitsschwelle 3 % unzulässig | 37 | 0 | 0 |
| 25 | Wesentlichkeitsschwelle knapp über 2 % | 37 | 0 | 0 |
| 26 | Wesentlichkeitsschwelle 1,5 % | 37 | 0 | 0 |
| 27 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 37 | 0 | 0 |
| 28 | GFQ unter, obere Fehlergrenze über der Schwelle | 37 | 0 | 0 |
| 29 | Gesamtfehlerquote genau auf der Wesentlichkeitsschwelle | 37 | 0 | 0 |
| 30 | Rechnerischer Umfang genau auf einer ganzen Zahl (64) | 37 | 0 | 0 |
| 31 | Rechnerischer Umfang knapp über einer ganzen Zahl | 37 | 0 | 0 |
| 32 | Ohne umfassende Schicht (C9–C11 leer) | 37 | 0 | 0 |
| 33 | Umfassende Schicht mit 28 Einheiten: Mindestumfang der Zufallsstichprobe 3 | 37 | 0 | 0 |
| 34 | Umfassende Schicht mit 40 Einheiten, begrenzt Kategorie 1: hochwertige Einheiten zehren den begrenzten Umfang auf | 37 | 0 | 0 |
| 35 | Hochwertige Einheiten über dem begrenzten Umfang (negativer Rest) | 37 | 0 | 0 |
| 36 | Stichprobenumfang größer als die Zufallsschicht | 37 | 0 | 0 |
| 37 | Keine Fehler in der Stichprobe | 37 | 0 | 0 |
| 38 | Leeres Formular (nur Vorgaben der Vorlage) | 37 | 7 | 0 |
| 39 | Teilweise: nur Grundgesamtheit und Parameter bis Standardabweichung | 37 | 0 | 0 |
| 40 | Teilweise: begrenzter Umfang zulässig, sonst keine Angaben | 37 | 7 | 0 |
| 41 | Teilweise: begrenzt zulässig, Standardabweichung fehlt | 37 | 7 | 0 |
| 42 | Teilweise: nur Prüfergebnisse | 37 | 10 | 0 |
| 43 | Teilweise: alles ausgefüllt außer dem Buchwert | 37 | 8 | 0 |
| 44 | Teilweise: alles ausgefüllt außer der Anzahl der Einheiten | 37 | 13 | 0 |
| 45 | Teilweise: alles ausgefüllt außer Buchwert und Anzahl | 37 | 10 | 0 |
| 46 | Teilweise: alles ausgefüllt außer der Zuverlässigkeit | 37 | 0 | 0 |
| 47 | Teilweise: alles ausgefüllt außer dem Konfidenzniveau | 37 | 0 | 0 |
| 48 | Teilweise: Testart geleert | 37 | 0 | 0 |
| 49 | Teilweise: Wesentlichkeitsschwelle geleert | 37 | 1 | 0 |
| 50 | Teilweise: alles ausgefüllt außer der voraussichtlichen Fehlerquote | 37 | 12 | 0 |
| 51 | Teilweise: alles ausgefüllt außer der voraussichtlichen Standardabweichung | 37 | 11 | 0 |
| 52 | Teilweise: alles ausgefüllt außer der Kategorie | 37 | 0 | 0 |
| 53 | Teilweise: Kategorie fehlt, begrenzter Umfang beantragt | 37 | 0 | 0 |
| 54 | Teilweise: Vorgaben geleert (Testart, Schwelle, Art. 83, begrenzter Umfang) | 37 | 1 | 0 |
| 55 | Teilweise: alles ausgefüllt außer der Summe der Buchwerte der Stichprobe | 37 | 0 | 0 |
| 56 | Teilweise: alles ausgefüllt außer der Summe der Fehler der Stichprobe | 37 | 0 | 0 |
| 57 | Teilweise: alles ausgefüllt außer der Standardabweichung der Variablen q | 37 | 0 | 0 |
| 58 | Teilweise: alles ausgefüllt außer den Fehlern der umfassenden Schicht | 37 | 0 | 0 |
| 59 | Teilweise: Prüfergebnisse fehlen | 37 | 0 | 0 |
| 60 | Teilweise: systembedingte und anomale Fehler nicht angegeben | 37 | 0 | 0 |
| 61 | Teilweise: voraussichtliche Fehlerquote fehlt, begrenzt zulässig | 37 | 12 | 0 |
| 62 | Teilweise: Buchwert fehlt, begrenzt zulässig | 37 | 10 | 0 |
| 63 | Teilweise: Anzahl der Einheiten fehlt, Gesamtfehlerquote über der Schwelle | 37 | 12 | 0 |
| 64 | Teilweise: Standardabweichung fehlt, Summe der Fehler fehlt | 37 | 8 | 0 |
| 65 | Buchwert und Umfang aus Blatt 02 übernommen (Verknüpfung) | 37 | 0 | 0 |
| 66 | Blatt 02 ausgefüllt, Buchwert im Methodenblatt überschrieben | 37 | 0 | 0 |
| 67 | Blatt 02 ausgefüllt, Buchwert und Anzahl überschrieben | 37 | 0 | 0 |
| 68 | Blatt 02 mit Ausschluss nach Art. 80 Abs. 3: angepasste Grundgesamtheit fließt ein | 37 | 0 | 0 |

## 09_SRS_1Z_S

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 70 | 5390 | 5218 | 145 | 0 | 27 | 0 | 0 | 0 |
| abnahme-luecken | 126 | 9702 | 9464 | 205 | 0 | 33 | 0 | 0 | 0 |
| abnahme-schwelle | 60 | 4620 | 4540 | 60 | 0 | 20 | 0 | 0 | 0 |
| Hauptsatz | 65 | 5005 | 4633 | 368 | 0 | 4 | 0 | 0 | 0 |
| zufall | 100 | 7700 | 7633 | 0 | 0 | 67 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Drei Schichten, mittel 70 %, zweiseitig, Standardfall | 77 | 1 | 0 |
| 2 | Sieben Schichten (alle Spalten der Vorlage) | 77 | 1 | 0 |
| 3 | Eine Schicht | 77 | 1 | 0 |
| 4 | Lücke: Schicht 2 leer, Schichten 1 und 3 belegt | 77 | 1 | 0 |
| 5 | Fünf Schichten, hoch 95 % einseitig | 77 | 1 | 0 |
| 6 | Zwei Schichten, gering 90 %, einseitig, systembedingte und anomale Fehler | 77 | 1 | 0 |
| 7 | Hoch 60 %, Art. 83 mit 30 Einheiten | 77 | 1 | 0 |
| 8 | Begrenzt zulässig Kategorie 1 (50 Einheiten): rechnerischer Umfang wird begrenzt | 77 | 1 | 0 |
| 9 | Begrenzt zulässig Kategorie 2, rechnerischer Umfang unter dem begrenzten Umfang | 77 | 1 | 0 |
| 10 | Begrenzt beantragt, aber Kategorie 3 (unzulässig) | 77 | 1 | 0 |
| 11 | Begrenzt beantragt, aber Kategorie 4 (unzulässig) | 77 | 1 | 0 |
| 12 | Begrenzt mit Art. 83, rechnerischer Umfang unter dem Mindestumfang | 77 | 1 | 0 |
| 13 | TE ≤ AE, Stichprobenumfang nicht bestimmbar | 77 | 1 | 0 |
| 14 | TE = AE genau auf der Schwelle | 77 | 1 | 0 |
| 15 | TE knapp über AE | 77 | 1 | 0 |
| 16 | TE ≤ AE mit begrenztem Umfang Kategorie 2 | 77 | 1 | 0 |
| 17 | Gering mit 60 %: Konfidenzniveau zu niedrig; Wesentlichkeitsschwelle 3 % | 77 | 1 | 0 |
| 18 | Gering 90 % zweiseitig: Eckwert eingehalten | 77 | 1 | 0 |
| 19 | Gering 80 %: knapp unter dem Eckwert | 77 | 1 | 0 |
| 20 | Hoch 60 % einseitig: Eckwert eingehalten | 77 | 1 | 0 |
| 21 | Hoch 70 % einseitig | 77 | 1 | 0 |
| 22 | Mittel mit 90 % zweiseitig: zu begründen | 77 | 1 | 0 |
| 23 | Mittel mit 60 %: zu begründen | 77 | 1 | 0 |
| 24 | Mittel 80 % einseitig | 77 | 1 | 0 |
| 25 | Gering 95 % zweiseitig | 77 | 1 | 0 |
| 26 | Wesentlichkeitsschwelle knapp über 2 % | 77 | 1 | 0 |
| 27 | Wesentlichkeitsschwelle 1,5 % | 77 | 1 | 0 |
| 28 | Weniger als 3 Einheiten in einer Zufallsschicht | 77 | 1 | 0 |
| 29 | Schichtumfänge heben beim Aufrunden die Summe über den Gesamtumfang | 77 | 1 | 0 |
| 30 | Sieben Schichten: Aufrundung je Schicht über dem Gesamtumfang, begrenzt Kategorie 1 | 77 | 1 | 0 |
| 31 | Rechnerischer Umfang genau auf einer ganzen Zahl (64) | 77 | 1 | 0 |
| 32 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 77 | 1 | 0 |
| 33 | GFQ unter, obere Fehlergrenze über der Schwelle | 77 | 1 | 0 |
| 34 | Ohne umfassende Schicht (C8–C10 und C43 leer) | 77 | 1 | 0 |
| 35 | Umfassende Schicht mit 28 Einheiten: Mindestumfang der Zufallsstichprobe 3 | 77 | 1 | 0 |
| 36 | Hochwertige Einheiten zehren den begrenzten Umfang auf | 77 | 1 | 0 |
| 37 | Stichprobenumfang größer als die Zufallsschichten | 77 | 1 | 0 |
| 38 | Keine Fehler in der Stichprobe | 77 | 1 | 0 |
| 39 | Buchwert ohne Anzahl in Schicht 4 (Schicht gilt als nicht belegt) | 77 | 1 | 0 |
| 40 | Leeres Formular (nur Vorgaben der Vorlage) | 77 | 14 | 0 |
| 41 | Teilweise: nur Anzahlen und Buchwerte der Schichten | 77 | 23 | 0 |
| 42 | Teilweise: sieben Schichten, Standardabweichungen fehlen | 77 | 35 | 0 |
| 43 | Teilweise: sieben Schichten, Standardabweichung nur in Schicht 4 fehlt | 77 | 29 | 0 |
| 44 | Teilweise: sieben Schichten, voraussichtliche Fehlerquote fehlt | 77 | 27 | 0 |
| 45 | Teilweise: sieben Schichten, Standardabweichung der Variablen q fehlt in Schicht 3 | 77 | 1 | 0 |
| 46 | Teilweise: sieben Schichten, Standardabweichung der Variablen q fehlt überall | 77 | 1 | 0 |
| 47 | Teilweise: sieben Schichten, Buchwert nur in Schicht 5 fehlt | 77 | 12 | 0 |
| 48 | Teilweise: sieben Schichten, Summe der Buchwerte der Stichprobe fehlt in Schicht 2 | 77 | 1 | 0 |
| 49 | Teilweise: sieben Schichten, Summe der Fehler fehlt in Schicht 6 | 77 | 1 | 0 |
| 50 | Teilweise: sieben Schichten, Buchwerte fehlen in allen Schichten | 77 | 45 | 0 |
| 51 | Teilweise: Buchwerte aller Schichten fehlen | 77 | 33 | 0 |
| 52 | Teilweise: Buchwert fehlt in Schicht 1, begrenzt zulässig | 77 | 12 | 0 |
| 53 | Teilweise: Konfidenzniveau fehlt | 77 | 1 | 0 |
| 54 | Teilweise: Zuverlässigkeit fehlt | 77 | 1 | 0 |
| 55 | Teilweise: Prüfergebnisse fehlen | 77 | 1 | 0 |
| 56 | Teilweise: Summen der Fehler fehlen in allen Schichten | 77 | 1 | 0 |
| 57 | Teilweise: alles ausgefüllt außer der Kategorie | 77 | 1 | 0 |
| 58 | Teilweise: Wesentlichkeitsschwelle und Vorgaben geleert | 77 | 7 | 0 |
| 59 | Teilweise: Wesentlichkeitsschwelle geleert | 77 | 7 | 0 |
| 60 | Teilweise: begrenzt zulässig, Standardabweichungen fehlen | 77 | 23 | 0 |
| 61 | Teilweise: voraussichtliche Fehlerquote fehlt, begrenzt zulässig | 77 | 19 | 0 |
| 62 | Teilweise: Standardabweichung fehlt in Schicht 2, Gesamtfehlerquote über der Schwelle | 77 | 20 | 0 |
| 63 | Teilweise: begrenzter Umfang zulässig, sonst keine Angaben | 77 | 14 | 0 |
| 64 | Blatt 02 ausgefüllt: Abweichung zur angepassten Grundgesamtheit | 77 | 0 | 0 |
| 65 | Blatt 02 ausgefüllt: Summe der Schichten stimmt mit der angepassten Grundgesamtheit überein | 77 | 0 | 0 |

## 10_SRS_2Z

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 70 | 4200 | 4049 | 116 | 0 | 24 | 11 | 0 | 0 |
| abnahme-luecken | 251 | 15060 | 14036 | 917 | 0 | 58 | 49 | 0 | 0 |
| abnahme-schwelle | 60 | 3600 | 3580 | 0 | 0 | 20 | 0 | 0 | 0 |
| Hauptsatz | 233 | 13980 | 11561 | 2341 | 0 | 10 | 68 | 0 | 0 |
| zufall | 100 | 6000 | 5856 | 0 | 0 | 5 | 139 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Mittel 70 %, zweiseitig, Standardneuberechnung (Standardfall) | 60 | 0 | 0 |
| 2 | Standardfall mit Ansatz „Global“ | 60 | 0 | 0 |
| 3 | Standardfall mit Ansatz „Erhöhung“ | 60 | 0 | 0 |
| 4 | Standardfall mit Ansatz „keine Neuberechnung“ | 60 | 0 | 0 |
| 5 | Gering 90 %, einseitig, begrenzt Kategorie 1, systembedingte Fehler | 60 | 0 | 0 |
| 6 | Hoch 60 %, Art. 83 mit 30 Einheiten | 60 | 0 | 0 |
| 7 | Begrenzt beantragt, aber Kategorie 4 (unzulässig) | 60 | 0 | 0 |
| 8 | Begrenzt beantragt, Kategorie 3 (unzulässig), Art. 83 Nein | 60 | 0 | 0 |
| 9 | Hoch 95 % einseitig (Konfidenzniveau außerhalb Anhang I) | 60 | 0 | 0 |
| 10 | Hoch 95 % zweiseitig, globale Neuberechnung | 60 | 0 | 0 |
| 11 | Gering mit 60 %: Konfidenzniveau zu niedrig | 60 | 0 | 0 |
| 12 | Gering 90 % zweiseitig: Eckwert eingehalten | 60 | 0 | 0 |
| 13 | Gering 80 %: knapp unter dem Eckwert | 60 | 0 | 0 |
| 14 | Hoch 60 % einseitig: Eckwert eingehalten | 60 | 0 | 0 |
| 15 | Mittel mit 90 % zweiseitig: zu begründen | 60 | 0 | 0 |
| 16 | Mittel mit 60 %: zu begründen | 60 | 0 | 0 |
| 17 | Mittel 80 % einseitig, keine Neuberechnung | 60 | 0 | 0 |
| 18 | Hoch 70 % einseitig, anomale Fehler | 60 | 0 | 0 |
| 19 | Gering 95 % zweiseitig, systembedingte und anomale Fehler | 60 | 0 | 0 |
| 20 | Wesentlichkeitsschwelle 3 % unzulässig | 60 | 0 | 0 |
| 21 | Wesentlichkeitsschwelle knapp über 2 % | 60 | 0 | 0 |
| 22 | Wesentlichkeitsschwelle 1,5 % | 60 | 0 | 0 |
| 23 | TE ≤ AE im ersten Zeitraum, Ansatz „Standard“ | 60 | 0 | 0 |
| 24 | TE ≤ AE im ersten Zeitraum, Ansatz „Global“ | 60 | 0 | 0 |
| 25 | TE ≤ AE im ersten Zeitraum, Ansatz „Erhöhung“ | 60 | 0 | 0 |
| 26 | TE ≤ AE im ersten Zeitraum, Ansatz „keine Neuberechnung“ | 60 | 0 | 0 |
| 27 | TE = AE genau auf der Schwelle | 60 | 0 | 0 |
| 28 | TE knapp über AE | 60 | 0 | 0 |
| 29 | TE ≤ AE mit begrenztem Umfang Kategorie 2 | 60 | 0 | 0 |
| 30 | TE ≤ AE mit begrenztem Umfang, globale Neuberechnung mit aktualisierter Fehlerquote | 60 | 0 | 0 |
| 31 | Aktualisierte Fehlerquote über der Schwelle (TE < AE in der Neuberechnung), Standard | 60 | 0 | 0 |
| 32 | Aktualisierte Fehlerquote über der Schwelle (TE < AE in der Neuberechnung), Global | 60 | 0 | 0 |
| 33 | Aktualisierte Fehlerquote gleich der Schwelle (TE = AE in der Neuberechnung), Standard | 60 | 0 | 0 |
| 34 | Aktualisierte Fehlerquote gleich der Schwelle (TE = AE in der Neuberechnung), Global | 60 | 0 | 0 |
| 35 | Aktualisierte Fehlerquote leer: Wert aus I | 60 | 0 | 0 |
| 36 | Aktualisierte Fehlerquote leer: Wert aus I, global | 60 | 0 | 0 |
| 37 | Aktualisierte Fehlerquote 0 | 60 | 0 | 0 |
| 38 | Mittel 80 %, begrenzt zulässig Kategorie 2: rechnerischer Umfang über 50 wird begrenzt | 60 | 0 | 0 |
| 39 | Begrenzt zulässig, rechnerischer Umfang unter dem begrenzten Umfang | 60 | 0 | 0 |
| 40 | Begrenzt mit Art. 83, rechnerischer Umfang unter dem Mindestumfang | 60 | 0 | 0 |
| 41 | Begrenzt mit Art. 83 (30 Einheiten), Auffüllung auf 30 in Zeitraum 2, Ansatz „Standard“ | 60 | 0 | 0 |
| 42 | Begrenzt mit Art. 83 (30 Einheiten), Auffüllung auf 30 in Zeitraum 2, Ansatz „Global“ | 60 | 0 | 0 |
| 43 | Begrenzt mit Art. 83 (30 Einheiten), Auffüllung auf 30 in Zeitraum 2, Ansatz „Erhöhung“ | 60 | 0 | 0 |
| 44 | Begrenzt mit Art. 83 (30 Einheiten), Auffüllung auf 30 in Zeitraum 2, Ansatz „keine Neuberechnung“ | 60 | 0 | 0 |
| 45 | Begrenzt Kategorie 1, großer Umfang: begrenzter Umfang überschritten?, Ansatz „Standard“ | 60 | 0 | 0 |
| 46 | Begrenzt Kategorie 1, großer Umfang: begrenzter Umfang überschritten?, Ansatz „Global“ | 60 | 0 | 0 |
| 47 | Begrenzt Kategorie 1, großer Umfang: begrenzter Umfang überschritten?, Ansatz „Erhöhung“ | 60 | 0 | 0 |
| 48 | Begrenzt Kategorie 1, großer Umfang: begrenzter Umfang überschritten?, Ansatz „keine Neuberechnung“ | 60 | 0 | 0 |
| 49 | Begrenzter Umfang eingehalten: hochwertige Einheiten zählen mit | 60 | 0 | 0 |
| 50 | Begrenzter Umfang genau erreicht | 60 | 0 | 0 |
| 51 | Begrenzter Umfang durch Aufrunden der Aufteilung um eine Einheit überschritten | 60 | 0 | 0 |
| 52 | Hochwertige Einheiten über dem begrenzten Umfang (negativer Rest) | 60 | 0 | 0 |
| 53 | Hochwertige Einheiten beider Zeiträume zehren den begrenzten Umfang auf, global | 60 | 0 | 0 |
| 54 | Ohne umfassende Schichten (C9–C11, C51–C53 leer) | 60 | 0 | 0 |
| 55 | Ohne umfassende Schichten, global | 60 | 0 | 0 |
| 56 | Umfassende Schicht mit 28 Einheiten in Zeitraum 1: Mindestumfang 6 | 60 | 0 | 0 |
| 57 | Umfassende Schichten mit zusammen über 30 Einheiten: keine Auffüllung | 60 | 0 | 0 |
| 58 | Negativer Nenner (große Standardabweichung s_e1), Ansatz „Standard“ | 60 | 0 | 0 |
| 59 | Negativer Nenner (große Standardabweichung s_e1), Ansatz „Global“ | 60 | 0 | 0 |
| 60 | Negativer Nenner (große Standardabweichung s_e1), Ansatz „Erhöhung“ | 60 | 0 | 0 |
| 61 | Negativer Nenner (große Standardabweichung s_e1), Ansatz „keine Neuberechnung“ | 60 | 0 | 0 |
| 62 | Negativer Nenner, s_e1 leer und σ_e1 groß (ersatzweise σ) | 60 | 0 | 0 |
| 63 | Negativer Nenner mit begrenztem Umfang Art. 83 | 60 | 0 | 0 |
| 64 | Negativer Nenner, umfassende Schichten über 30 Einheiten: Untergrenze 3 | 60 | 0 | 0 |
| 65 | Nenner knapp positiv: sehr großer Umfang für Zeitraum 2 | 60 | 0 | 0 |
| 66 | Standard: s_e1 leer, ersatzweise σ_e1 | 60 | 0 | 0 |
| 67 | Global: s_e1 leer, ersatzweise σ_e1 | 60 | 0 | 0 |
| 68 | Global mit Zusatzeinheiten in Zeitraum 1 (σ_e2 stark gestiegen) | 60 | 0 | 0 |
| 69 | Global mit Zusatzeinheiten in Zeitraum 1, begrenzter Umfang Kategorie 2 | 60 | 0 | 0 |
| 70 | Global ohne Zusatzeinheiten (σ gesunken) | 60 | 0 | 0 |
| 71 | Global: Zusatzeinheiten werden nur im Ansatz „Global“ angerechnet (Standard gewählt) | 60 | 0 | 0 |
| 72 | Standard: σ_e2 stark gestiegen | 60 | 0 | 0 |
| 73 | Ist-Werte Zeitraum 2 über der Prognose: Erhöhung mit Faktor > 1 (Buchwert maßgeblich) | 60 | 0 | 0 |
| 74 | Ist-Werte Zeitraum 2 über der Prognose: Erhöhung mit Faktor > 1 (Anzahl maßgeblich) | 60 | 0 | 0 |
| 75 | Ist-Werte Zeitraum 2 unter der Prognose: Erhöhung mit Faktor 1 | 60 | 0 | 0 |
| 76 | Ist-Werte Zeitraum 2 genau wie die Prognose: Faktor 1 | 60 | 0 | 0 |
| 77 | Erhöhung mit begrenztem Umfang Kategorie 2, Ist über der Prognose | 60 | 0 | 0 |
| 78 | Erhöhung: Prognose der Anzahl ist 0 (Fehlerwert zählt 1) | 60 | 0 | 0 |
| 79 | Erhöhung: Faktor genau 2 (glatter Wert) | 60 | 0 | 0 |
| 80 | Ist-Werte Zeitraum 2 über der Prognose, Standard | 60 | 0 | 0 |
| 81 | Ist-Werte Zeitraum 2 über der Prognose, Global | 60 | 0 | 0 |
| 82 | Ist-Werte Zeitraum 2 unter der Prognose, keine Neuberechnung | 60 | 0 | 0 |
| 83 | Auswahl der Neuberechnung geleert (wie keine Neuberechnung) | 60 | 0 | 0 |
| 84 | Aufteilung genau auf ganzen Zahlen (N₁ = N₂, gerader Umfang) | 60 | 0 | 0 |
| 85 | Rechnerischer Umfang genau auf einer ganzen Zahl (64) | 60 | 0 | 0 |
| 86 | Rechnerischer Umfang knapp über einer ganzen Zahl | 60 | 0 | 0 |
| 87 | Globaler Umfang genau auf einer ganzen Zahl | 60 | 0 | 0 |
| 88 | Standardabweichungen 0: rechnerischer Umfang 0, Mindestumfang greift | 60 | 0 | 0 |
| 89 | Standardabweichungen 0, global | 60 | 0 | 0 |
| 90 | Zufallsschicht Zeitraum 1 ohne Einheiten (N₁ = N_e) | 60 | 0 | 0 |
| 91 | Prognose Zeitraum 2 mit 0 Einheiten und 0 € | 60 | 0 | 0 |
| 92 | Stichprobenumfang größer als die Zufallsschichten | 60 | 0 | 0 |
| 93 | Keine Fehler in Zeitraum 1 | 60 | 0 | 0 |
| 94 | Keine Fehler in Zeitraum 2 | 60 | 0 | 0 |
| 95 | Keine Fehler in beiden Zeiträumen | 60 | 0 | 0 |
| 96 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 60 | 0 | 0 |
| 97 | GFQ unter, obere Fehlergrenze über der Schwelle | 60 | 0 | 0 |
| 98 | Gesamtfehlerquote genau auf der Wesentlichkeitsschwelle | 60 | 0 | 0 |
| 99 | Negative Fehlersumme in Zeitraum 2 (Überkorrektur) | 60 | 0 | 0 |
| 100 | Leeres Formular (nur Vorgaben der Vorlage) | 60 | 14 | 0 |
| 101 | Teilweise: nur Grundgesamtheit und Parameter des ersten Zeitraums | 60 | 21 | 0 |
| 102 | Teilweise: begrenzter Umfang zulässig, sonst keine Angaben | 60 | 14 | 0 |
| 103 | Teilweise: begrenzt zulässig, Standardabweichungen fehlen | 60 | 30 | 0 |
| 104 | Teilweise: nur Prüfergebnisse beider Zeiträume | 60 | 17 | 0 |
| 105 | Teilweise: nur Ist-Werte des zweiten Zeitraums | 60 | 13 | 0 |
| 106 | Nur Zeitraum 1 ausgefüllt, Ansatz „Standard“ | 60 | 21 | 0 |
| 107 | Nur Zeitraum 1 ausgefüllt, Ansatz „Global“ | 60 | 22 | 0 |
| 108 | Nur Zeitraum 1 ausgefüllt, Ansatz „Erhöhung“ | 60 | 17 | 0 |
| 109 | Nur Zeitraum 1 ausgefüllt, Ansatz „keine Neuberechnung“ | 60 | 17 | 0 |
| 110 | Nur Zeitraum 1 ausgefüllt, begrenzt Kategorie 2, Ansatz „Standard“ | 60 | 22 | 0 |
| 111 | Nur Zeitraum 1 ausgefüllt, begrenzt Kategorie 2, Ansatz „Global“ | 60 | 23 | 0 |
| 112 | Nur Zeitraum 1 ausgefüllt, begrenzt Kategorie 2, Ansatz „Erhöhung“ | 60 | 17 | 0 |
| 113 | Nur Zeitraum 1 ausgefüllt, begrenzt Kategorie 2, Ansatz „keine Neuberechnung“ | 60 | 17 | 0 |
| 114 | Nur Zeitraum 1 ausgefüllt, Prüfergebnisse des ersten Zeitraums fehlen noch | 60 | 21 | 0 |
| 115 | Nur Zeitraum 1 ausgefüllt, negativer Nenner | 60 | 21 | 0 |
| 116 | Zeitraum 2: Ist-Werte da, Prüfergebnisse fehlen noch | 60 | 0 | 0 |
| 117 | Zeitraum 2: Ist-Werte da, Prüfergebnisse fehlen noch, global | 60 | 0 | 0 |
| 118 | Teilweise: alles ausgefüllt außer Buchwert Zeitraum 1 (C7), Ansatz „Standard“ | 60 | 38 | 0 |
| 119 | Teilweise: alles ausgefüllt außer Anzahl Einheiten Zeitraum 1 (C8), Ansatz „Standard“ | 60 | 28 | 0 |
| 120 | Teilweise: alles ausgefüllt außer prognostizierter Buchwert Zeitraum 2 (C14), Ansatz „Standard“ | 60 | 24 | 0 |
| 121 | Teilweise: alles ausgefüllt außer prognostizierte Anzahl Zeitraum 2 (C15), Ansatz „Standard“ | 60 | 22 | 0 |
| 122 | Teilweise: alles ausgefüllt außer Wesentlichkeitsschwelle (C23), Ansatz „Standard“ | 60 | 3 | 0 |
| 123 | Teilweise: alles ausgefüllt außer voraussichtliche Fehlerquote (C26), Ansatz „Standard“ | 60 | 21 | 0 |
| 124 | Teilweise: alles ausgefüllt außer σ_e1 (C29), Ansatz „Standard“ | 60 | 21 | 0 |
| 125 | Teilweise: alles ausgefüllt außer σ_e2 (C30), Ansatz „Standard“ | 60 | 21 | 0 |
| 126 | Teilweise: alles ausgefüllt außer Buchwert Zeitraum 2 (C49), Ansatz „Standard“ | 60 | 28 | 0 |
| 127 | Teilweise: alles ausgefüllt außer Anzahl Einheiten Zeitraum 2 (C50), Ansatz „Standard“ | 60 | 19 | 0 |
| 128 | Teilweise: alles ausgefüllt außer aktualisierte σ_e2 (C56), Ansatz „Standard“ | 60 | 17 | 0 |
| 129 | Teilweise: alles ausgefüllt außer Buchwert Zeitraum 1 (C7), Ansatz „Global“ | 60 | 38 | 0 |
| 130 | Teilweise: alles ausgefüllt außer Anzahl Einheiten Zeitraum 1 (C8), Ansatz „Global“ | 60 | 28 | 0 |
| 131 | Teilweise: alles ausgefüllt außer prognostizierter Buchwert Zeitraum 2 (C14), Ansatz „Global“ | 60 | 24 | 0 |
| 132 | Teilweise: alles ausgefüllt außer prognostizierte Anzahl Zeitraum 2 (C15), Ansatz „Global“ | 60 | 22 | 0 |
| 133 | Teilweise: alles ausgefüllt außer Wesentlichkeitsschwelle (C23), Ansatz „Global“ | 60 | 3 | 0 |
| 134 | Teilweise: alles ausgefüllt außer voraussichtliche Fehlerquote (C26), Ansatz „Global“ | 60 | 21 | 0 |
| 135 | Teilweise: alles ausgefüllt außer σ_e1 (C29), Ansatz „Global“ | 60 | 21 | 0 |
| 136 | Teilweise: alles ausgefüllt außer σ_e2 (C30), Ansatz „Global“ | 60 | 21 | 0 |
| 137 | Teilweise: alles ausgefüllt außer Buchwert Zeitraum 2 (C49), Ansatz „Global“ | 60 | 29 | 0 |
| 138 | Teilweise: alles ausgefüllt außer Anzahl Einheiten Zeitraum 2 (C50), Ansatz „Global“ | 60 | 20 | 0 |
| 139 | Teilweise: alles ausgefüllt außer aktualisierte σ_e2 (C56), Ansatz „Global“ | 60 | 18 | 0 |
| 140 | Teilweise: alles ausgefüllt außer Buchwert Zeitraum 1 (C7), Ansatz „Erhöhung“ | 60 | 38 | 0 |
| 141 | Teilweise: alles ausgefüllt außer Anzahl Einheiten Zeitraum 1 (C8), Ansatz „Erhöhung“ | 60 | 28 | 0 |
| 142 | Teilweise: alles ausgefüllt außer prognostizierter Buchwert Zeitraum 2 (C14), Ansatz „Erhöhung“ | 60 | 24 | 0 |
| 143 | Teilweise: alles ausgefüllt außer prognostizierte Anzahl Zeitraum 2 (C15), Ansatz „Erhöhung“ | 60 | 22 | 0 |
| 144 | Teilweise: alles ausgefüllt außer Wesentlichkeitsschwelle (C23), Ansatz „Erhöhung“ | 60 | 3 | 0 |
| 145 | Teilweise: alles ausgefüllt außer voraussichtliche Fehlerquote (C26), Ansatz „Erhöhung“ | 60 | 21 | 0 |
| 146 | Teilweise: alles ausgefüllt außer σ_e1 (C29), Ansatz „Erhöhung“ | 60 | 21 | 0 |
| 147 | Teilweise: alles ausgefüllt außer σ_e2 (C30), Ansatz „Erhöhung“ | 60 | 21 | 0 |
| 148 | Teilweise: alles ausgefüllt außer Buchwert Zeitraum 2 (C49), Ansatz „Erhöhung“ | 60 | 22 | 0 |
| 149 | Teilweise: alles ausgefüllt außer Anzahl Einheiten Zeitraum 2 (C50), Ansatz „Erhöhung“ | 60 | 15 | 0 |
| 150 | Teilweise: alles ausgefüllt außer aktualisierte σ_e2 (C56), Ansatz „Erhöhung“ | 60 | 6 | 0 |
| 151 | Teilweise: alles ausgefüllt außer Buchwert Zeitraum 1 (C7), Ansatz „keine Neuberechnung“ | 60 | 38 | 0 |
| 152 | Teilweise: alles ausgefüllt außer Anzahl Einheiten Zeitraum 1 (C8), Ansatz „keine Neuberechnung“ | 60 | 28 | 0 |
| 153 | Teilweise: alles ausgefüllt außer prognostizierter Buchwert Zeitraum 2 (C14), Ansatz „keine Neuberechnung“ | 60 | 24 | 0 |
| 154 | Teilweise: alles ausgefüllt außer prognostizierte Anzahl Zeitraum 2 (C15), Ansatz „keine Neuberechnung“ | 60 | 22 | 0 |
| 155 | Teilweise: alles ausgefüllt außer Wesentlichkeitsschwelle (C23), Ansatz „keine Neuberechnung“ | 60 | 3 | 0 |
| 156 | Teilweise: alles ausgefüllt außer voraussichtliche Fehlerquote (C26), Ansatz „keine Neuberechnung“ | 60 | 21 | 0 |
| 157 | Teilweise: alles ausgefüllt außer σ_e1 (C29), Ansatz „keine Neuberechnung“ | 60 | 21 | 0 |
| 158 | Teilweise: alles ausgefüllt außer σ_e2 (C30), Ansatz „keine Neuberechnung“ | 60 | 21 | 0 |
| 159 | Teilweise: alles ausgefüllt außer Buchwert Zeitraum 2 (C49), Ansatz „keine Neuberechnung“ | 60 | 22 | 0 |
| 160 | Teilweise: alles ausgefüllt außer Anzahl Einheiten Zeitraum 2 (C50), Ansatz „keine Neuberechnung“ | 60 | 15 | 0 |
| 161 | Teilweise: alles ausgefüllt außer aktualisierte σ_e2 (C56), Ansatz „keine Neuberechnung“ | 60 | 6 | 0 |
| 162 | Teilweise: Buchwert Zeitraum 1 (C7) fehlt, begrenzt Kategorie 2 | 60 | 39 | 0 |
| 163 | Teilweise: Anzahl Einheiten Zeitraum 1 (C8) fehlt, begrenzt Kategorie 2 | 60 | 29 | 0 |
| 164 | Teilweise: prognostizierter Buchwert Zeitraum 2 (C14) fehlt, begrenzt Kategorie 2 | 60 | 25 | 0 |
| 165 | Teilweise: prognostizierte Anzahl Zeitraum 2 (C15) fehlt, begrenzt Kategorie 2 | 60 | 23 | 0 |
| 166 | Teilweise: Wesentlichkeitsschwelle (C23) fehlt, begrenzt Kategorie 2 | 60 | 16 | 0 |
| 167 | Teilweise: voraussichtliche Fehlerquote (C26) fehlt, begrenzt Kategorie 2 | 60 | 22 | 0 |
| 168 | Teilweise: σ_e1 (C29) fehlt, begrenzt Kategorie 2 | 60 | 22 | 0 |
| 169 | Teilweise: σ_e2 (C30) fehlt, begrenzt Kategorie 2 | 60 | 22 | 0 |
| 170 | Teilweise: Buchwert Zeitraum 2 (C49) fehlt, begrenzt Kategorie 2 | 60 | 29 | 0 |
| 171 | Teilweise: Anzahl Einheiten Zeitraum 2 (C50) fehlt, begrenzt Kategorie 2 | 60 | 20 | 0 |
| 172 | Teilweise: aktualisierte σ_e2 (C56) fehlt, begrenzt Kategorie 2 | 60 | 18 | 0 |
| 173 | Teilweise: Buchwert Zeitraum 1 (C7) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 39 | 0 |
| 174 | Teilweise: Anzahl Einheiten Zeitraum 1 (C8) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 29 | 0 |
| 175 | Teilweise: prognostizierter Buchwert Zeitraum 2 (C14) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 25 | 0 |
| 176 | Teilweise: prognostizierte Anzahl Zeitraum 2 (C15) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 23 | 0 |
| 177 | Teilweise: Wesentlichkeitsschwelle (C23) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 5 | 0 |
| 178 | Teilweise: voraussichtliche Fehlerquote (C26) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 26 | 0 |
| 179 | Teilweise: σ_e1 (C29) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 27 | 0 |
| 180 | Teilweise: σ_e2 (C30) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 22 | 0 |
| 181 | Teilweise: Buchwert Zeitraum 2 (C49) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 30 | 0 |
| 182 | Teilweise: Anzahl Einheiten Zeitraum 2 (C50) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 21 | 0 |
| 183 | Teilweise: aktualisierte σ_e2 (C56) fehlt, s_e1 und aktualisierte Fehlerquote leer, global, Art. 83 | 60 | 19 | 0 |
| 184 | Teilweise: Buchwert Zeitraum 1 (C7) fehlt, negativer Nenner | 60 | 38 | 0 |
| 185 | Teilweise: Anzahl Einheiten Zeitraum 1 (C8) fehlt, negativer Nenner | 60 | 28 | 0 |
| 186 | Teilweise: prognostizierter Buchwert Zeitraum 2 (C14) fehlt, negativer Nenner | 60 | 24 | 0 |
| 187 | Teilweise: prognostizierte Anzahl Zeitraum 2 (C15) fehlt, negativer Nenner | 60 | 22 | 0 |
| 188 | Teilweise: Wesentlichkeitsschwelle (C23) fehlt, negativer Nenner | 60 | 3 | 0 |
| 189 | Teilweise: voraussichtliche Fehlerquote (C26) fehlt, negativer Nenner | 60 | 21 | 0 |
| 190 | Teilweise: σ_e1 (C29) fehlt, negativer Nenner | 60 | 21 | 0 |
| 191 | Teilweise: σ_e2 (C30) fehlt, negativer Nenner | 60 | 21 | 0 |
| 192 | Teilweise: Buchwert Zeitraum 2 (C49) fehlt, negativer Nenner | 60 | 28 | 0 |
| 193 | Teilweise: Anzahl Einheiten Zeitraum 2 (C50) fehlt, negativer Nenner | 60 | 14 | 0 |
| 194 | Teilweise: aktualisierte σ_e2 (C56) fehlt, negativer Nenner | 60 | 5 | 0 |
| 195 | Teilweise: alles ausgefüllt außer Zuverlässigkeit (C18) | 60 | 0 | 0 |
| 196 | Teilweise: alles ausgefüllt außer Konfidenzniveau (C19) | 60 | 0 | 0 |
| 197 | Teilweise: alles ausgefüllt außer Kategorie (C34) | 60 | 0 | 0 |
| 198 | Teilweise: alles ausgefüllt außer Summe der Buchwerte Zeitraum 1 (C44) | 60 | 0 | 0 |
| 199 | Teilweise: alles ausgefüllt außer Summe der Fehler Zeitraum 1 (C45) | 60 | 0 | 0 |
| 200 | Teilweise: alles ausgefüllt außer s_e Zeitraum 1 (C46) | 60 | 0 | 0 |
| 201 | Teilweise: alles ausgefüllt außer s_q Zeitraum 1 (C47) | 60 | 0 | 0 |
| 202 | Teilweise: alles ausgefüllt außer Fehler der umfassenden Schicht Zeitraum 1 (C48) | 60 | 0 | 0 |
| 203 | Teilweise: alles ausgefüllt außer Summe der Buchwerte Zeitraum 2 (C77) | 60 | 0 | 0 |
| 204 | Teilweise: alles ausgefüllt außer Summe der Fehler Zeitraum 2 (C78) | 60 | 0 | 0 |
| 205 | Teilweise: alles ausgefüllt außer s_e Zeitraum 2 (C79) | 60 | 0 | 0 |
| 206 | Teilweise: alles ausgefüllt außer s_q Zeitraum 2 (C80) | 60 | 0 | 0 |
| 207 | Teilweise: alles ausgefüllt außer Fehler der umfassenden Schicht Zeitraum 2 (C81) | 60 | 0 | 0 |
| 208 | Teilweise: Konfidenzniveau fehlt, begrenzt Kategorie 2, Ansatz „Standard“ | 60 | 0 | 0 |
| 209 | Teilweise: Konfidenzniveau fehlt, begrenzt Kategorie 2, Ansatz „Global“ | 60 | 0 | 0 |
| 210 | Teilweise: Konfidenzniveau fehlt, begrenzt Kategorie 2, Ansatz „Erhöhung“ | 60 | 0 | 0 |
| 211 | Teilweise: Konfidenzniveau fehlt, begrenzt Kategorie 2, Ansatz „keine Neuberechnung“ | 60 | 0 | 0 |
| 212 | Teilweise: s_q fehlt in beiden Zeiträumen | 60 | 0 | 0 |
| 213 | Teilweise: s_q fehlt in beiden Zeiträumen, global, einseitig | 60 | 0 | 0 |
| 214 | Teilweise: s_q Zeitraum 1 fehlt, Gesamtfehlerquote über der Schwelle | 60 | 0 | 0 |
| 215 | Teilweise: Summen der Fehler fehlen in beiden Zeiträumen | 60 | 0 | 0 |
| 216 | Teilweise: Testart geleert | 60 | 0 | 0 |
| 217 | Teilweise: Vorgaben geleert (Testart, Schwelle, Ansatz, Art. 83, begrenzter Umfang) | 60 | 3 | 0 |
| 218 | Teilweise: Kategorie fehlt, begrenzter Umfang beantragt | 60 | 0 | 0 |
| 219 | Teilweise: systembedingte und anomale Fehler nicht angegeben | 60 | 0 | 0 |
| 220 | Teilweise: σ_e1 und s_e1 fehlen | 60 | 26 | 0 |
| 221 | Teilweise: σ_e1 und s_e1 fehlen, global | 60 | 26 | 0 |
| 222 | Teilweise: σ_e1 fehlt, s_e1 leer, keine Neuberechnung, begrenzt | 60 | 27 | 0 |
| 223 | Teilweise: voraussichtliche und aktualisierte Fehlerquote fehlen | 60 | 25 | 0 |
| 224 | Teilweise: voraussichtliche und aktualisierte Fehlerquote fehlen, global | 60 | 25 | 0 |
| 225 | Teilweise: voraussichtliche Fehlerquote fehlt, aktualisierte leer, Gesamtfehlerquote über der Schwelle | 60 | 24 | 0 |
| 226 | Teilweise: beide Buchwerte fehlen | 60 | 29 | 0 |
| 227 | Teilweise: Buchwert und Anzahl Zeitraum 2 fehlen, Prüfergebnisse Zeitraum 2 da | 60 | 31 | 0 |
| 228 | Teilweise: Buchwert und Anzahl Zeitraum 2 fehlen, keine Neuberechnung | 60 | 27 | 0 |
| 229 | Teilweise: aktualisierte σ_e2 fehlt, Gesamtfehlerquote über der Schwelle | 60 | 16 | 0 |
| 230 | Teilweise: Anzahl Zeitraum 2 fehlt, Erhöhung, Ist-Buchwert über der Prognose | 60 | 15 | 0 |
| 231 | Teilweise: Buchwert Zeitraum 2 fehlt, Erhöhung, Ist-Anzahl über der Prognose | 60 | 22 | 0 |
| 232 | Teilweise: Prognosen fehlen (C14, C15), Erhöhung | 60 | 26 | 0 |
| 233 | Teilweise: Prognosen fehlen (C14, C15), keine Neuberechnung, begrenzt | 60 | 27 | 0 |

## 11_SRS_2Z_S

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 110 | 18040 | 17361 | 529 | 0 | 34 | 116 | 0 | 0 |
| abnahme-luecken | 315 | 51660 | 49833 | 1212 | 0 | 115 | 500 | 0 | 0 |
| abnahme-schwelle | 60 | 9840 | 9820 | 0 | 0 | 20 | 0 | 0 | 0 |
| Hauptsatz | 126 | 20664 | 18937 | 1579 | 0 | 6 | 142 | 0 | 0 |
| teilbelegung | 13 | 2132 | 1890 | 242 | 0 | 0 | 0 | 0 | 0 |
| zufall | 100 | 16400 | 16012 | 0 | 0 | 73 | 315 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Drei Schichten, mittel 70 %, zweiseitig, Standardansatz | 164 | 0 | 0 |
| 2 | Sieben Schichten (alle Spalten der Vorlage) | 164 | 0 | 0 |
| 3 | Eine Schicht | 164 | 0 | 0 |
| 4 | Lücke: Schicht 2 leer, Schichten 1 und 3 belegt | 164 | 0 | 0 |
| 5 | Fünf Schichten, hoch 95 % einseitig, global | 164 | 0 | 0 |
| 6 | Gering 90 %, einseitig, systembedingte und anomale Fehler | 164 | 0 | 0 |
| 7 | Gering mit 60 %: Konfidenzniveau zu niedrig; Wesentlichkeitsschwelle 3 % | 164 | 0 | 0 |
| 8 | Gering 80 %: knapp unter dem Eckwert | 164 | 0 | 0 |
| 9 | Gering 95 % zweiseitig | 164 | 0 | 0 |
| 10 | Hoch 60 % einseitig: Eckwert eingehalten | 164 | 0 | 0 |
| 11 | Hoch 70 % einseitig, anomale Fehler | 164 | 0 | 0 |
| 12 | Mittel mit 90 % zweiseitig: zu begründen | 164 | 0 | 0 |
| 13 | Mittel mit 60 %: zu begründen | 164 | 0 | 0 |
| 14 | Mittel 80 % einseitig | 164 | 0 | 0 |
| 15 | Wesentlichkeitsschwelle knapp über 2 % | 164 | 0 | 0 |
| 16 | Wesentlichkeitsschwelle 1,5 % | 164 | 0 | 0 |
| 17 | Hoch 60 %, Art. 83 mit 30 Einheiten | 164 | 0 | 0 |
| 18 | Begrenzt zulässig Kategorie 1 (50 Einheiten): rechnerischer Umfang wird begrenzt | 164 | 0 | 0 |
| 19 | Begrenzt zulässig Kategorie 2, rechnerischer Umfang unter dem begrenzten Umfang | 164 | 0 | 0 |
| 20 | Begrenzt beantragt, aber Kategorie 3 (unzulässig) | 164 | 0 | 0 |
| 21 | Begrenzt beantragt, aber Kategorie 4 (unzulässig) | 164 | 0 | 0 |
| 22 | Begrenzt mit Art. 83, rechnerischer Umfang unter dem Mindestumfang | 164 | 0 | 0 |
| 23 | Begrenzt Kategorie 1, globaler Ansatz: hochwertige Einheiten beider Zeiträume angerechnet | 164 | 0 | 0 |
| 24 | Begrenzt Kategorie 2, Erhöhung: Ist über der Prognose | 164 | 0 | 0 |
| 25 | Begrenzt Kategorie 2, Erhöhung: Ist unter der Prognose (Faktor 1) | 164 | 0 | 0 |
| 26 | Hochwertige Einheiten zehren den begrenzten Umfang auf | 164 | 0 | 0 |
| 27 | Umfassende Schichten mit 28 Einheiten: Mindestumfang 6 | 164 | 0 | 0 |
| 28 | Ohne umfassende Schichten (C7–C9, C47, C53–C55, C82 leer) | 164 | 0 | 0 |
| 29 | TE ≤ AE, Standardansatz | 164 | 0 | 0 |
| 30 | TE ≤ AE, global | 164 | 0 | 0 |
| 31 | TE ≤ AE, Erhöhung | 164 | 0 | 0 |
| 32 | TE ≤ AE, keine Neuberechnung | 164 | 0 | 0 |
| 33 | TE = AE genau auf der Schwelle, global (Division durch 0) | 164 | 0 | 0 |
| 34 | TE = AE genau auf der Schwelle, Standardansatz | 164 | 0 | 0 |
| 35 | TE knapp über AE | 164 | 0 | 0 |
| 36 | TE ≤ AE mit begrenztem Umfang Kategorie 2 | 164 | 0 | 0 |
| 37 | TE ≤ AE in Abschnitt I, aktualisierte Fehlerquote darunter | 164 | 0 | 0 |
| 38 | Aktualisierte voraussichtliche Fehlerquote höher | 164 | 0 | 0 |
| 39 | Aktualisierte voraussichtliche Fehlerquote 0 | 164 | 0 | 0 |
| 40 | Globaler Ansatz | 164 | 0 | 0 |
| 41 | Globaler Ansatz mit Zusatzeinheiten für Zeitraum 1 | 164 | 0 | 0 |
| 42 | Erhöhung bei begrenztem Umfang ohne begrenzten Umfang | 164 | 0 | 0 |
| 43 | Keine Neuberechnung | 164 | 0 | 0 |
| 44 | Ansatz der Neuberechnung geleert | 164 | 0 | 0 |
| 45 | Negativer Nenner, Standardansatz | 164 | 0 | 0 |
| 46 | Negativer Nenner, global | 164 | 0 | 0 |
| 47 | Negativer Nenner, Erhöhung | 164 | 0 | 0 |
| 48 | Negativer Nenner, keine Neuberechnung | 164 | 0 | 0 |
| 49 | Negativer Nenner, sieben Schichten, Standardansatz | 164 | 0 | 0 |
| 50 | Nenner knapp positiv | 164 | 0 | 0 |
| 51 | Ohne s_eh: Standardabweichung Zeitraum 1 ersatzweise σ | 164 | 0 | 0 |
| 52 | s_eh nur in Schicht 2 leer | 164 | 0 | 0 |
| 53 | Schicht 4 nur in Zeitraum 1 belegt | 164 | 0 | 0 |
| 54 | Schicht 4 nur in Zeitraum 1 belegt, global | 164 | 0 | 0 |
| 55 | Schicht 4 nur in Zeitraum 2 belegt, Standardansatz | 164 | 0 | 0 |
| 56 | Schicht 4 nur in Zeitraum 2 belegt, global | 164 | 0 | 0 |
| 57 | Schicht 4 nur in Zeitraum 2 belegt, Erhöhung | 164 | 1 | 0 |
| 58 | Schicht 4 nur in Zeitraum 2 belegt, keine Neuberechnung | 164 | 0 | 0 |
| 59 | Schicht 4 in Zeitraum 1 ohne Prognose für Zeitraum 2 | 164 | 0 | 0 |
| 60 | Schichtumfänge heben beim Aufrunden die Summe über den Gesamtumfang | 164 | 0 | 0 |
| 61 | Sieben Schichten: Aufrundung über dem begrenzten Umfang, Kategorie 1, keine Neuberechnung | 164 | 0 | 0 |
| 62 | Sieben Schichten, global | 164 | 0 | 0 |
| 63 | Sieben Schichten, Erhöhung mit Art. 83 | 164 | 0 | 0 |
| 64 | Weniger als 3 Einheiten in einer Zufallsschicht (Zeitraum 1 und Planung Zeitraum 2) | 164 | 0 | 0 |
| 65 | Weniger als 3 Einheiten je Schicht, keine Neuberechnung: Zeitraum 2 auf 3 angehoben | 164 | 0 | 0 |
| 66 | Rechnerischer Gesamtumfang genau auf einer ganzen Zahl (64) | 164 | 0 | 0 |
| 67 | Stichprobenumfang größer als die Zufallsschichten | 164 | 0 | 0 |
| 68 | Ist-Werte Zeitraum 2 deutlich über der Prognose | 164 | 0 | 0 |
| 69 | Ist-Werte Zeitraum 2 deutlich unter der Prognose, global | 164 | 0 | 0 |
| 70 | Mindestumfang des Geschäftsjahres genau erreicht (30) | 164 | 0 | 0 |
| 71 | Mindestumfang des Geschäftsjahres knapp verfehlt (28) | 164 | 0 | 0 |
| 72 | Mindestumfang verfehlt, Standardansatz mit begrenztem Umfang | 164 | 0 | 0 |
| 73 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 164 | 0 | 0 |
| 74 | GFQ unter, obere Fehlergrenze über der Schwelle | 164 | 0 | 0 |
| 75 | Zeitraum 1 ohne Fehler | 164 | 0 | 0 |
| 76 | Zeitraum 2 ohne Fehler | 164 | 0 | 0 |
| 77 | Keine Fehler in beiden Zeiträumen | 164 | 0 | 0 |
| 78 | Fehlersummen Zeitraum 2 noch leer (nur Zeitraum 1 geprüft) | 164 | 0 | 0 |
| 79 | Leeres Formular (nur Vorgaben der Vorlage) | 164 | 32 | 0 |
| 80 | Teilweise: nur Anzahlen und Buchwerte der Schichten | 164 | 54 | 0 |
| 81 | Teilweise: nur Anzahl in Schicht 1 | 164 | 36 | 0 |
| 82 | Teilweise: Abschnitte H und I vollständig | 164 | 28 | 0 |
| 83 | Teilweise: nur Zeitraum 1 ausgefüllt (Abschnitte H bis K) | 164 | 35 | 0 |
| 84 | Teilweise: nur Zeitraum 1 ausgefüllt, sieben Schichten, keine Neuberechnung | 164 | 39 | 0 |
| 85 | Teilweise: nur Prüfergebnisse | 164 | 30 | 0 |
| 86 | Teilweise: begrenzter Umfang zulässig, sonst keine Angaben | 164 | 32 | 0 |
| 87 | Teilweise: nur umfassende Schicht und Parameter, begrenzt zulässig | 164 | 38 | 0 |
| 88 | Teilweise: alles ausgefüllt außer der Zuverlässigkeit | 164 | 0 | 0 |
| 89 | Teilweise: alles ausgefüllt außer dem Konfidenzniveau | 164 | 0 | 0 |
| 90 | Teilweise: Testart geleert | 164 | 0 | 0 |
| 91 | Teilweise: Wesentlichkeitsschwelle geleert | 164 | 29 | 0 |
| 92 | Teilweise: Wesentlichkeitsschwelle geleert, global | 164 | 11 | 0 |
| 93 | Teilweise: Wesentlichkeitsschwelle geleert, keine Neuberechnung, begrenzt zulässig | 164 | 5 | 0 |
| 94 | Teilweise: alles ausgefüllt außer der voraussichtlichen Fehlerquote | 164 | 52 | 0 |
| 95 | Teilweise: voraussichtliche Fehlerquote fehlt, aktualisierte Quote angegeben | 164 | 49 | 0 |
| 96 | Teilweise: voraussichtliche Fehlerquote fehlt, global, begrenzt zulässig | 164 | 52 | 0 |
| 97 | Teilweise: voraussichtliche Fehlerquote fehlt, Erhöhung | 164 | 52 | 0 |
| 98 | Teilweise: voraussichtliche Fehlerquote fehlt, keine Neuberechnung | 164 | 52 | 0 |
| 99 | Teilweise: voraussichtliche Fehlerquote fehlt, Gesamtfehlerquote über der Schwelle | 164 | 51 | 0 |
| 100 | Teilweise: alles ausgefüllt außer der Kategorie | 164 | 0 | 0 |
| 101 | Teilweise: Kategorie fehlt, begrenzter Umfang beantragt | 164 | 0 | 0 |
| 102 | Teilweise: Vorgaben geleert (Testart, Schwelle, Ansatz, Art. 83, begrenzter Umfang) | 164 | 29 | 0 |
| 103 | Teilweise: σ Zeitraum 1 fehlt in Schicht 3 | 164 | 51 | 0 |
| 104 | Teilweise: σ Zeitraum 1 und s_eh fehlen in Schicht 3 | 164 | 56 | 0 |
| 105 | Teilweise: σ Zeitraum 1 und s_eh fehlen in Schicht 3, global | 164 | 56 | 0 |
| 106 | Teilweise: σ Zeitraum 2 (Prognose) fehlt in Schicht 3 | 164 | 51 | 0 |
| 107 | Teilweise: σ Zeitraum 2 (Prognose) fehlt in Schicht 3, global | 164 | 44 | 0 |
| 108 | Teilweise: aktualisierte σ Zeitraum 2 fehlt in Schicht 3 | 164 | 32 | 0 |
| 109 | Teilweise: aktualisierte σ Zeitraum 2 fehlt in Schicht 3, global | 164 | 36 | 0 |
| 110 | Teilweise: aktualisierte σ Zeitraum 2 fehlt in Schicht 3, keine Neuberechnung | 164 | 11 | 0 |
| 111 | Teilweise: aktualisierte σ Zeitraum 2 fehlt, negativer Nenner | 164 | 24 | 0 |
| 112 | Teilweise: s_q Zeitraum 1 fehlt in Schicht 2 | 164 | 0 | 0 |
| 113 | Teilweise: s_q Zeitraum 2 fehlt in Schicht 2 | 164 | 0 | 0 |
| 114 | Teilweise: s_q fehlt in allen Schichten und Zeiträumen | 164 | 0 | 0 |
| 115 | Teilweise: Buchwert Zeitraum 1 fehlt in Schicht 1 | 164 | 11 | 0 |
| 116 | Teilweise: Buchwert Zeitraum 2 fehlt in Schicht 3 | 164 | 11 | 0 |
| 117 | Teilweise: Summe der Buchwerte der Stichprobe fehlt in Schicht 2 (Zeitraum 1) | 164 | 0 | 0 |
| 118 | Teilweise: Summe der Fehler fehlt in Schicht 2 (beide Zeiträume) | 164 | 0 | 0 |
| 119 | Teilweise: Prüfergebnisse fehlen | 164 | 0 | 0 |
| 120 | Teilweise: systembedingte und anomale Fehler nicht angegeben | 164 | 0 | 0 |
| 121 | Teilweise: sieben Schichten ohne voraussichtliche Fehlerquote | 164 | 88 | 0 |
| 122 | Teilweise: sieben Schichten ohne voraussichtliche Fehlerquote, global | 164 | 88 | 0 |
| 123 | Teilweise: sieben Schichten ohne Standardabweichungen für den Umfang | 164 | 118 | 0 |
| 124 | Teilweise: sieben Schichten ohne aktualisierte σ Zeitraum 2 | 164 | 60 | 0 |
| 125 | Teilweise: sieben Schichten ohne Buchwerte | 164 | 94 | 0 |
| 126 | Teilweise: sieben Schichten ohne Wesentlichkeitsschwelle | 164 | 41 | 0 |

## 12_SRS_3Z

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 70 | 6020 | 5758 | 201 | 0 | 26 | 35 | 0 | 0 |
| abnahme-luecken | 324 | 27864 | 25566 | 2205 | 0 | 32 | 61 | 0 | 0 |
| abnahme-schwelle | 60 | 5160 | 5140 | 0 | 0 | 20 | 0 | 0 | 0 |
| Hauptsatz | 231 | 19866 | 16239 | 3394 | 0 | 9 | 224 | 0 | 0 |
| zufall | 100 | 8600 | 8490 | 0 | 0 | 48 | 62 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Mittel 70 %, zweiseitig, Standardansatz (Standardfall) | 86 | 0 | 0 |
| 2 | Globale Neuberechnung ohne Zusatzeinheiten in früheren Zeiträumen | 86 | 0 | 0 |
| 3 | Globale Neuberechnung mit Zusatzeinheiten in Zeitraum 1 und 2 | 86 | 0 | 0 |
| 4 | Globale Neuberechnung: Zusatzeinheiten nur nach Zeitraum 2 | 86 | 0 | 0 |
| 5 | Standardansatz mit höheren aktualisierten Standardabweichungen | 86 | 0 | 0 |
| 6 | Erhöhung: Ist-Werte unter der Prognose (Faktor 1) | 86 | 0 | 0 |
| 7 | Erhöhung: Ist-Buchwerte über der Prognose (Faktor > 1) | 86 | 0 | 0 |
| 8 | Erhöhung: Ist-Anzahl über der Prognose (Faktor > 1) | 86 | 0 | 0 |
| 9 | Erhöhung: nur Zeitraum 2 über der Prognose | 86 | 0 | 0 |
| 10 | Erhöhung: nur Zeitraum 3 über der aktualisierten Prognose | 86 | 0 | 0 |
| 11 | Erhöhung: Ist genau gleich der Prognose | 86 | 0 | 0 |
| 12 | Erhöhung ohne Prognosen für Zeitraum 3 (aktualisierte Prognose fehlt) | 86 | 16 | 0 |
| 13 | Keine Neuberechnung | 86 | 0 | 0 |
| 14 | Keine Neuberechnung, begrenzt Kategorie 1 | 86 | 0 | 0 |
| 15 | Ansatz geleert (wie keine Neuberechnung) | 86 | 0 | 0 |
| 16 | Negativer Nenner nach Zeitraum 1 (C71), Ansatz Standard | 86 | 0 | 0 |
| 17 | Negativer Nenner nach Zeitraum 2 (C105), Ansatz Standard | 86 | 0 | 0 |
| 18 | Negativer Nenner nach Zeitraum 1 (C71), Ansatz Global | 86 | 0 | 0 |
| 19 | Negativer Nenner nach Zeitraum 2 (C105), Ansatz Global | 86 | 0 | 0 |
| 20 | Negativer Nenner nach Zeitraum 1 (C71), Ansatz Erhöhung | 86 | 0 | 0 |
| 21 | Negativer Nenner nach Zeitraum 2 (C105), Ansatz Erhöhung | 86 | 0 | 0 |
| 22 | Negativer Nenner nach Zeitraum 1 (C71), Ansatz keine Neuberechnung | 86 | 0 | 0 |
| 23 | Negativer Nenner nach Zeitraum 2 (C105), Ansatz keine Neuberechnung | 86 | 0 | 0 |
| 24 | Negativer Nenner in beiden Neuberechnungen, Standard | 86 | 0 | 0 |
| 25 | Negativer Nenner nach Zeitraum 2 mit Auffüllung auf 30 Einheiten | 86 | 0 | 0 |
| 26 | Negativer Nenner nach Zeitraum 1 mit Auffüllung auf 30 Einheiten | 86 | 0 | 0 |
| 27 | Negativer Nenner nach Zeitraum 1, begrenzt Art. 83 | 86 | 0 | 0 |
| 28 | Kleine Standardabweichungen: Auffüllung auf 30 Einheiten in Zeitraum 3, Ansatz Standard | 86 | 0 | 0 |
| 29 | Kleine Standardabweichungen: Auffüllung auf 30 Einheiten in Zeitraum 3, Ansatz Global | 86 | 0 | 0 |
| 30 | Kleine Standardabweichungen: Auffüllung auf 30 Einheiten in Zeitraum 3, Ansatz Erhöhung | 86 | 0 | 0 |
| 31 | Kleine Standardabweichungen: Auffüllung auf 30 Einheiten in Zeitraum 3, Ansatz keine Neuberechnung | 86 | 0 | 0 |
| 32 | Kleine Standardabweichungen ohne umfassende Schichten: Auffüllung | 86 | 0 | 0 |
| 33 | Große umfassende Schichten: Mindestumfang der Zufallsstichproben 9 | 86 | 0 | 0 |
| 34 | Große umfassende Schichten, global | 86 | 0 | 0 |
| 35 | Gesamtstichprobe unter 30 nicht möglich: Auffüllung genau auf 30 | 86 | 0 | 0 |
| 36 | Gering 90 %, einseitig, begrenzt Kategorie 1, systembedingte Fehler | 86 | 0 | 0 |
| 37 | Hoch 60 %, Art. 83 mit 30 Einheiten | 86 | 0 | 0 |
| 38 | Begrenzt beantragt, aber Kategorie 4 (unzulässig) | 86 | 0 | 0 |
| 39 | Begrenzt beantragt, Kategorie 3 (unzulässig), Art. 83 Nein | 86 | 0 | 0 |
| 40 | Begrenzt zulässig Kategorie 2: rechnerischer Umfang über 50 wird begrenzt | 86 | 0 | 0 |
| 41 | Begrenzt zulässig, rechnerischer Umfang unter dem begrenzten Umfang | 86 | 0 | 0 |
| 42 | Begrenzt Kategorie 1 mit hochwertigen Einheiten in allen Zeiträumen, Ansatz Standard | 86 | 0 | 0 |
| 43 | Begrenzt Kategorie 1 mit hochwertigen Einheiten in allen Zeiträumen, Ansatz Global | 86 | 0 | 0 |
| 44 | Begrenzt Kategorie 1 mit hochwertigen Einheiten in allen Zeiträumen, Ansatz Erhöhung | 86 | 0 | 0 |
| 45 | Begrenzt Kategorie 1 mit hochwertigen Einheiten in allen Zeiträumen, Ansatz keine Neuberechnung | 86 | 0 | 0 |
| 46 | Begrenzt Art. 83, global | 86 | 0 | 0 |
| 47 | Hochwertige Einheiten über dem begrenzten Umfang (negativer Rest) | 86 | 0 | 0 |
| 48 | Hoch 95 % einseitig (Konfidenzniveau außerhalb Anhang I) | 86 | 0 | 0 |
| 49 | Hoch 95 % zweiseitig | 86 | 0 | 0 |
| 50 | Gering mit 60 %: Konfidenzniveau zu niedrig | 86 | 0 | 0 |
| 51 | Gering 90 % zweiseitig: Eckwert eingehalten | 86 | 0 | 0 |
| 52 | Gering 80 %: knapp unter dem Eckwert | 86 | 0 | 0 |
| 53 | Hoch 60 % einseitig: Eckwert eingehalten | 86 | 0 | 0 |
| 54 | Mittel mit 90 % zweiseitig: zu begründen | 86 | 0 | 0 |
| 55 | Mittel mit 60 %: zu begründen | 86 | 0 | 0 |
| 56 | Mittel 80 % einseitig, global | 86 | 0 | 0 |
| 57 | Hoch 70 % einseitig, anomale Fehler | 86 | 0 | 0 |
| 58 | Gering 95 % zweiseitig, systembedingte und anomale Fehler | 86 | 0 | 0 |
| 59 | Wesentlichkeitsschwelle 3 % unzulässig | 86 | 0 | 0 |
| 60 | Wesentlichkeitsschwelle knapp über 2 % | 86 | 0 | 0 |
| 61 | Wesentlichkeitsschwelle 1,5 % | 86 | 0 | 0 |
| 62 | TE ≤ AE, Stichprobenumfang nicht bestimmbar, Ansatz Standard | 86 | 0 | 0 |
| 63 | TE ≤ AE, Stichprobenumfang nicht bestimmbar, Ansatz Global | 86 | 0 | 0 |
| 64 | TE ≤ AE, Stichprobenumfang nicht bestimmbar, Ansatz Erhöhung | 86 | 0 | 0 |
| 65 | TE ≤ AE, Stichprobenumfang nicht bestimmbar, Ansatz keine Neuberechnung | 86 | 0 | 0 |
| 66 | TE = AE genau auf der Schwelle | 86 | 0 | 0 |
| 67 | TE = AE genau auf der Schwelle, global | 86 | 0 | 0 |
| 68 | TE knapp über AE | 86 | 0 | 0 |
| 69 | TE ≤ AE mit begrenztem Umfang Kategorie 2 | 86 | 0 | 0 |
| 70 | TE ≤ AE mit begrenztem Umfang Kategorie 2, global | 86 | 0 | 0 |
| 71 | TE ≤ AE zu Beginn, aktualisierte Fehlerquote darunter | 86 | 0 | 0 |
| 72 | TE ≤ AE zu Beginn, aktualisierte Fehlerquote darunter, global | 86 | 0 | 0 |
| 73 | Aktualisierte Fehlerquote nach Zeitraum 1 über der Schwelle | 86 | 0 | 0 |
| 74 | Aktualisierte Fehlerquote nach Zeitraum 1 über der Schwelle, global | 86 | 0 | 0 |
| 75 | Aktualisierte Fehlerquoten nach Zeitraum 1 und 2 | 86 | 0 | 0 |
| 76 | Aktualisierte Fehlerquote nur nach Zeitraum 2 | 86 | 0 | 0 |
| 77 | Aktualisierte Fehlerquote 0 % nach Zeitraum 1 (nicht leer) | 86 | 0 | 0 |
| 78 | Aktualisierte Fehlerquoten, global | 86 | 0 | 0 |
| 79 | Aktualisierte Fehlerquote nach Zeitraum 2 gleich der Schwelle, global | 86 | 0 | 0 |
| 80 | Ohne s_e aus Zeitraum 1: ersatzweise σ (C50 leer) | 86 | 0 | 0 |
| 81 | Ohne s_e aus Zeitraum 2: ersatzweise aktualisierte σ (C89 leer) | 86 | 0 | 0 |
| 82 | Ohne s_e aus beiden Zeiträumen, global | 86 | 0 | 0 |
| 83 | s_e Zeitraum 1 gleich 0 | 86 | 0 | 0 |
| 84 | s_e Zeitraum 3 nicht angegeben (wird nicht verwendet) | 86 | 0 | 0 |
| 85 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 86 | 0 | 0 |
| 86 | GFQ unter, obere Fehlergrenze über der Schwelle | 86 | 0 | 0 |
| 87 | Keine Fehler in den Stichproben | 86 | 0 | 0 |
| 88 | Zeitraum 2 ohne Fehler | 86 | 0 | 0 |
| 89 | Zeitraum 1 und 3 ohne Fehler | 86 | 0 | 0 |
| 90 | Ohne umfassende Schichten (leer) | 86 | 0 | 0 |
| 91 | Rechnerischer Umfang genau auf einer ganzen Zahl (64) | 86 | 0 | 0 |
| 92 | Rechnerischer Umfang knapp über einer ganzen Zahl | 86 | 0 | 0 |
| 93 | Stichprobenumfang größer als die Zufallsschichten | 86 | 0 | 0 |
| 94 | Gesamtfehlerquote genau auf der Wesentlichkeitsschwelle | 86 | 0 | 0 |
| 95 | Leeres Formular (nur Vorgaben der Vorlage) | 86 | 24 | 0 |
| 96 | Teilweise: nur Zeitraum 1 ausgefüllt, Ansatz Standard | 86 | 40 | 0 |
| 97 | Teilweise: Zeiträume 1 und 2 ausgefüllt, Zeitraum 3 leer, Ansatz Standard | 86 | 22 | 0 |
| 98 | Teilweise: nur Zeitraum 1 ausgefüllt, Ansatz Global | 86 | 44 | 0 |
| 99 | Teilweise: Zeiträume 1 und 2 ausgefüllt, Zeitraum 3 leer, Ansatz Global | 86 | 24 | 0 |
| 100 | Teilweise: nur Zeitraum 1 ausgefüllt, Ansatz Erhöhung | 86 | 34 | 0 |
| 101 | Teilweise: Zeiträume 1 und 2 ausgefüllt, Zeitraum 3 leer, Ansatz Erhöhung | 86 | 18 | 0 |
| 102 | Teilweise: nur Zeitraum 1 ausgefüllt, Ansatz keine Neuberechnung | 86 | 34 | 0 |
| 103 | Teilweise: Zeiträume 1 und 2 ausgefüllt, Zeitraum 3 leer, Ansatz keine Neuberechnung | 86 | 18 | 0 |
| 104 | Teilweise: nur Zeitraum 1, begrenzt Kategorie 1 | 86 | 40 | 0 |
| 105 | Teilweise: Zeiträume 1 und 2, begrenzt Kategorie 1, global | 86 | 24 | 0 |
| 106 | Teilweise: Zeitraum 3 nur mit Ist-Werten, Prüfergebnisse fehlen | 86 | 0 | 0 |
| 107 | Teilweise: Zeitraum 2 nur mit Ist-Werten, Prüfergebnisse fehlen | 86 | 22 | 0 |
| 108 | Teilweise: nur Grundgesamtheit und Parameter bis zu den Standardabweichungen | 86 | 40 | 0 |
| 109 | Teilweise: begrenzter Umfang zulässig, sonst keine Angaben | 86 | 24 | 0 |
| 110 | Teilweise: nur Prüfergebnisse | 86 | 27 | 0 |
| 111 | Teilweise: alles ausgefüllt außer dem Buchwert Zeitraum 1 (C7) | 86 | 57 | 0 |
| 112 | Teilweise: alles ausgefüllt außer der Anzahl Zeitraum 1 (C8) | 86 | 46 | 0 |
| 113 | Teilweise: alles ausgefüllt außer dem prognostizierten Buchwert Zeitraum 2 (C14) | 86 | 36 | 0 |
| 114 | Teilweise: alles ausgefüllt außer der prognostizierten Anzahl Zeitraum 2 (C15) | 86 | 34 | 0 |
| 115 | Teilweise: alles ausgefüllt außer dem prognostizierten Buchwert Zeitraum 3 (C16) | 86 | 36 | 0 |
| 116 | Teilweise: alles ausgefüllt außer der prognostizierten Anzahl Zeitraum 3 (C17) | 86 | 34 | 0 |
| 117 | Teilweise: alles ausgefüllt außer der Zuverlässigkeit (C20) | 86 | 0 | 0 |
| 118 | Teilweise: alles ausgefüllt außer dem Konfidenzniveau (C21) | 86 | 0 | 0 |
| 119 | Teilweise: alles ausgefüllt außer der voraussichtlichen Fehlerquote (C28) | 86 | 42 | 0 |
| 120 | Teilweise: alles ausgefüllt außer σ_e1 (C31) | 86 | 33 | 0 |
| 121 | Teilweise: alles ausgefüllt außer σ_e2 (C32) | 86 | 33 | 0 |
| 122 | Teilweise: alles ausgefüllt außer σ_e3 (C33) | 86 | 33 | 0 |
| 123 | Teilweise: alles ausgefüllt außer der Kategorie (C37) | 86 | 0 | 0 |
| 124 | Teilweise: alles ausgefüllt außer der Summe der Buchwerte Zeitraum 1 (C48) | 86 | 0 | 0 |
| 125 | Teilweise: alles ausgefüllt außer der Summe der Fehler Zeitraum 1 (C49) | 86 | 0 | 0 |
| 126 | Teilweise: alles ausgefüllt außer s_q Zeitraum 1 (C51) | 86 | 0 | 0 |
| 127 | Teilweise: alles ausgefüllt außer den Fehlern der umfassenden Schicht Zeitraum 1 (C52) | 86 | 0 | 0 |
| 128 | Teilweise: alles ausgefüllt außer dem Buchwert Zeitraum 2 (C53) | 86 | 45 | 0 |
| 129 | Teilweise: alles ausgefüllt außer der Anzahl Zeitraum 2 (C54) | 86 | 37 | 0 |
| 130 | Teilweise: alles ausgefüllt außer der aktualisierten Prognose Buchwert Zeitraum 3 (C60) | 86 | 30 | 0 |
| 131 | Teilweise: alles ausgefüllt außer der aktualisierten Prognose Anzahl Zeitraum 3 (C61) | 86 | 30 | 0 |
| 132 | Teilweise: alles ausgefüllt außer der aktualisierten σ_e2 (C62) | 86 | 28 | 0 |
| 133 | Teilweise: alles ausgefüllt außer der aktualisierten σ_e3 (C63) | 86 | 28 | 0 |
| 134 | Teilweise: alles ausgefüllt außer der Summe der Buchwerte Zeitraum 2 (C87) | 86 | 0 | 0 |
| 135 | Teilweise: alles ausgefüllt außer der Summe der Fehler Zeitraum 2 (C88) | 86 | 0 | 0 |
| 136 | Teilweise: alles ausgefüllt außer s_q Zeitraum 2 (C90) | 86 | 0 | 0 |
| 137 | Teilweise: alles ausgefüllt außer dem Buchwert Zeitraum 3 (C92) | 86 | 29 | 0 |
| 138 | Teilweise: alles ausgefüllt außer der Anzahl Zeitraum 3 (C93) | 86 | 20 | 0 |
| 139 | Teilweise: alles ausgefüllt außer der aktualisierten σ_e3 nach Zeitraum 2 (C99) | 86 | 18 | 0 |
| 140 | Teilweise: alles ausgefüllt außer der Summe der Buchwerte Zeitraum 3 (C121) | 86 | 0 | 0 |
| 141 | Teilweise: alles ausgefüllt außer der Summe der Fehler Zeitraum 3 (C122) | 86 | 0 | 0 |
| 142 | Teilweise: alles ausgefüllt außer s_q Zeitraum 3 (C124) | 86 | 0 | 0 |
| 143 | Teilweise: C7 fehlt, Ansatz Global | 86 | 57 | 0 |
| 144 | Teilweise: C8 fehlt, Ansatz Global | 86 | 46 | 0 |
| 145 | Teilweise: C14 fehlt, Ansatz Global | 86 | 31 | 0 |
| 146 | Teilweise: C15 fehlt, Ansatz Global | 86 | 29 | 0 |
| 147 | Teilweise: C16 fehlt, Ansatz Global | 86 | 31 | 0 |
| 148 | Teilweise: C17 fehlt, Ansatz Global | 86 | 29 | 0 |
| 149 | Teilweise: C28 fehlt, Ansatz Global | 86 | 42 | 0 |
| 150 | Teilweise: C31 fehlt, Ansatz Global | 86 | 28 | 0 |
| 151 | Teilweise: C32 fehlt, Ansatz Global | 86 | 28 | 0 |
| 152 | Teilweise: C33 fehlt, Ansatz Global | 86 | 28 | 0 |
| 153 | Teilweise: C53 fehlt, Ansatz Global | 86 | 47 | 0 |
| 154 | Teilweise: C54 fehlt, Ansatz Global | 86 | 39 | 0 |
| 155 | Teilweise: C60 fehlt, Ansatz Global | 86 | 33 | 0 |
| 156 | Teilweise: C61 fehlt, Ansatz Global | 86 | 33 | 0 |
| 157 | Teilweise: C62 fehlt, Ansatz Global | 86 | 31 | 0 |
| 158 | Teilweise: C63 fehlt, Ansatz Global | 86 | 31 | 0 |
| 159 | Teilweise: C92 fehlt, Ansatz Global | 86 | 31 | 0 |
| 160 | Teilweise: C93 fehlt, Ansatz Global | 86 | 22 | 0 |
| 161 | Teilweise: C99 fehlt, Ansatz Global | 86 | 20 | 0 |
| 162 | Teilweise: C7 fehlt, Ansatz Erhöhung | 86 | 57 | 0 |
| 163 | Teilweise: C8 fehlt, Ansatz Erhöhung | 86 | 46 | 0 |
| 164 | Teilweise: C14 fehlt, Ansatz Erhöhung | 86 | 36 | 0 |
| 165 | Teilweise: C15 fehlt, Ansatz Erhöhung | 86 | 34 | 0 |
| 166 | Teilweise: C16 fehlt, Ansatz Erhöhung | 86 | 36 | 0 |
| 167 | Teilweise: C17 fehlt, Ansatz Erhöhung | 86 | 34 | 0 |
| 168 | Teilweise: C28 fehlt, Ansatz Erhöhung | 86 | 42 | 0 |
| 169 | Teilweise: C31 fehlt, Ansatz Erhöhung | 86 | 33 | 0 |
| 170 | Teilweise: C32 fehlt, Ansatz Erhöhung | 86 | 33 | 0 |
| 171 | Teilweise: C33 fehlt, Ansatz Erhöhung | 86 | 33 | 0 |
| 172 | Teilweise: C53 fehlt, Ansatz Erhöhung | 86 | 35 | 0 |
| 173 | Teilweise: C54 fehlt, Ansatz Erhöhung | 86 | 29 | 0 |
| 174 | Teilweise: C60 fehlt, Ansatz Erhöhung | 86 | 12 | 0 |
| 175 | Teilweise: C61 fehlt, Ansatz Erhöhung | 86 | 12 | 0 |
| 176 | Teilweise: C62 fehlt, Ansatz Erhöhung | 86 | 10 | 0 |
| 177 | Teilweise: C63 fehlt, Ansatz Erhöhung | 86 | 10 | 0 |
| 178 | Teilweise: C92 fehlt, Ansatz Erhöhung | 86 | 23 | 0 |
| 179 | Teilweise: C93 fehlt, Ansatz Erhöhung | 86 | 16 | 0 |
| 180 | Teilweise: C99 fehlt, Ansatz Erhöhung | 86 | 7 | 0 |
| 181 | Teilweise: C7 fehlt, Ansatz keine Neuberechnung | 86 | 57 | 0 |
| 182 | Teilweise: C8 fehlt, Ansatz keine Neuberechnung | 86 | 46 | 0 |
| 183 | Teilweise: C14 fehlt, Ansatz keine Neuberechnung | 86 | 36 | 0 |
| 184 | Teilweise: C15 fehlt, Ansatz keine Neuberechnung | 86 | 34 | 0 |
| 185 | Teilweise: C16 fehlt, Ansatz keine Neuberechnung | 86 | 36 | 0 |
| 186 | Teilweise: C17 fehlt, Ansatz keine Neuberechnung | 86 | 34 | 0 |
| 187 | Teilweise: C28 fehlt, Ansatz keine Neuberechnung | 86 | 42 | 0 |
| 188 | Teilweise: C31 fehlt, Ansatz keine Neuberechnung | 86 | 33 | 0 |
| 189 | Teilweise: C32 fehlt, Ansatz keine Neuberechnung | 86 | 33 | 0 |
| 190 | Teilweise: C33 fehlt, Ansatz keine Neuberechnung | 86 | 33 | 0 |
| 191 | Teilweise: C53 fehlt, Ansatz keine Neuberechnung | 86 | 35 | 0 |
| 192 | Teilweise: C54 fehlt, Ansatz keine Neuberechnung | 86 | 29 | 0 |
| 193 | Teilweise: C60 fehlt, Ansatz keine Neuberechnung | 86 | 12 | 0 |
| 194 | Teilweise: C61 fehlt, Ansatz keine Neuberechnung | 86 | 12 | 0 |
| 195 | Teilweise: C62 fehlt, Ansatz keine Neuberechnung | 86 | 10 | 0 |
| 196 | Teilweise: C63 fehlt, Ansatz keine Neuberechnung | 86 | 10 | 0 |
| 197 | Teilweise: C92 fehlt, Ansatz keine Neuberechnung | 86 | 23 | 0 |
| 198 | Teilweise: C93 fehlt, Ansatz keine Neuberechnung | 86 | 16 | 0 |
| 199 | Teilweise: C99 fehlt, Ansatz keine Neuberechnung | 86 | 7 | 0 |
| 200 | Teilweise: Testart geleert | 86 | 0 | 0 |
| 201 | Teilweise: Wesentlichkeitsschwelle geleert | 86 | 7 | 0 |
| 202 | Teilweise: Wesentlichkeitsschwelle geleert, global | 86 | 5 | 0 |
| 203 | Teilweise: Vorgaben geleert (Testart, Schwelle, Ansatz, Art. 83, begrenzter Umfang) | 86 | 7 | 0 |
| 204 | Teilweise: Kategorie fehlt, begrenzter Umfang beantragt | 86 | 0 | 0 |
| 205 | Teilweise: σ_e1 und s_e1 fehlen (C31, C50) | 86 | 43 | 0 |
| 206 | Teilweise: σ_e1 und s_e1 fehlen, global | 86 | 43 | 0 |
| 207 | Teilweise: aktualisierte σ_e2 und s_e2 fehlen (C62, C89) | 86 | 34 | 0 |
| 208 | Teilweise: aktualisierte σ_e2 und s_e2 fehlen, global | 86 | 36 | 0 |
| 209 | Teilweise: aktualisierte σ_e2 fehlt, s_e2 vorhanden, global | 86 | 31 | 0 |
| 210 | Teilweise: voraussichtliche Fehlerquote fehlt, aktualisierte vorhanden | 86 | 33 | 0 |
| 211 | Teilweise: voraussichtliche Fehlerquote fehlt, nur letzte aktualisierte vorhanden | 86 | 38 | 0 |
| 212 | Teilweise: voraussichtliche Fehlerquote fehlt, begrenzt zulässig | 86 | 42 | 0 |
| 213 | Teilweise: Buchwert Zeitraum 1 fehlt, begrenzt zulässig, global | 86 | 57 | 0 |
| 214 | Teilweise: alle s_q fehlen | 86 | 0 | 0 |
| 215 | Teilweise: Summen der Fehler aller Zeiträume fehlen | 86 | 0 | 0 |
| 216 | Teilweise: Summen der Fehler fehlen, Fehler der umfassenden Schichten vorhanden | 86 | 0 | 0 |
| 217 | Teilweise: systembedingte und anomale Fehler nicht angegeben | 86 | 0 | 0 |
| 218 | Teilweise: Anzahl Zeitraum 2 fehlt, Gesamtfehlerquote über der Schwelle | 86 | 36 | 0 |
| 219 | Teilweise: σ_e3 nach Zeitraum 2 fehlt, Gesamtfehlerquote über der Schwelle | 86 | 17 | 0 |
| 220 | Teilweise: σ_e3 nach Zeitraum 2 fehlt, negativer Nenner nach Zeitraum 2 | 86 | 6 | 0 |
| 221 | Teilweise: aktualisierte σ fehlen, negativer Nenner nach Zeitraum 1 | 86 | 7 | 0 |
| 222 | Teilweise: Ist-Werte Zeitraum 3 fehlen, kleine Standardabweichungen (Auffüllung) | 86 | 32 | 0 |
| 223 | Nenner nach Zeitraum 1 genau 0 | 86 | 0 | 0 |
| 224 | Nenner nach Zeitraum 1 knapp über 0 | 86 | 0 | 0 |
| 225 | Nenner nach Zeitraum 1 knapp unter 0 | 86 | 0 | 0 |
| 226 | Teilweise: Wesentlichkeitsschwelle geleert, begrenzt Kategorie 1, Ansatz Standard | 86 | 25 | 0 |
| 227 | Teilweise: Wesentlichkeitsschwelle geleert, begrenzt Kategorie 1, Ansatz Global | 86 | 9 | 0 |
| 228 | Teilweise: Wesentlichkeitsschwelle geleert, begrenzt Kategorie 1, Ansatz Erhöhung | 86 | 11 | 0 |
| 229 | Teilweise: Wesentlichkeitsschwelle geleert, begrenzt Kategorie 1, Ansatz keine Neuberechnung | 86 | 11 | 0 |
| 230 | Teilweise: Wesentlichkeitsschwelle geleert, begrenzt, global, keine Fehler in den Stichproben | 86 | 9 | 0 |
| 231 | Teilweise: voraussichtliche Fehlerquote und Standardabweichungen fehlen, begrenzt Art. 83, global | 86 | 43 | 0 |

## 13_NS_GW

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 64 | 1408 | 1328 | 22 | 0 | 58 | 0 | 0 | 0 |
| abnahme-luecken | 108 | 2376 | 2234 | 38 | 0 | 104 | 0 | 0 | 0 |
| abnahme-schwelle | 60 | 1320 | 1260 | 0 | 0 | 60 | 0 | 0 | 0 |
| Hauptsatz | 47 | 1034 | 944 | 57 | 0 | 33 | 0 | 0 | 0 |
| zufall | 120 | 2640 | 2520 | 0 | 0 | 120 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall: N = 180, umfassende Schicht mit vier Einheiten | 22 | 0 | 0 |
| 2 | N = 299: knapp unter der Schwelle des Art. 79 Abs. 2 | 22 | 0 | 0 |
| 3 | N = 300: genau auf der Schwelle (nur im Fall des Art. 6 Abs. 3) | 22 | 0 | 0 |
| 4 | N = 301: knapp über der Schwelle | 22 | 0 | 0 |
| 5 | N = 450: Wechsel nach Art. 6 Abs. 3 | 22 | 0 | 0 |
| 6 | Mindesterfassung genau erreicht (18 von 180) | 22 | 0 | 0 |
| 7 | Mindesterfassung knapp verfehlt (17 von 180) | 22 | 0 | 0 |
| 8 | Mindesterfassung aufgerundet: N = 181 verlangt 19 Einheiten, 19 geprüft | 22 | 0 | 0 |
| 9 | Mindesterfassung aufgerundet: N = 181 verlangt 19 Einheiten, 18 geprüft | 22 | 0 | 0 |
| 10 | Mindesterfassung bei N = 30 (0,1 · 30 ist im Gleitkomma knapp über 3) | 22 | 0 | 0 |
| 11 | Mindesterfassung bei N = 70 (0,1 · 70 ist im Gleitkomma knapp über 7) | 22 | 0 | 0 |
| 12 | Mindesterfassung bei N = 290, eine Einheit zu wenig | 22 | 0 | 0 |
| 13 | Ohne umfassende Schicht | 22 | 0 | 0 |
| 14 | Umfassende Schicht mit 0 angegeben | 22 | 0 | 0 |
| 15 | Systembedingte und anomale Fehler | 22 | 0 | 0 |
| 16 | Nur systembedingte Fehler | 22 | 0 | 0 |
| 17 | Nur anomale Fehler | 22 | 0 | 0 |
| 18 | Gesamtfehlerquote genau auf der Wesentlichkeitsschwelle (2,00 %) | 22 | 0 | 0 |
| 19 | Gesamtfehlerquote knapp über der Wesentlichkeitsschwelle | 22 | 0 | 0 |
| 20 | Gesamtfehlerquote knapp unter der Wesentlichkeitsschwelle | 22 | 0 | 0 |
| 21 | Gesamtfehlerquote über der Schwelle durch systembedingte Fehler | 22 | 0 | 0 |
| 22 | Gesamtfehlerquote deutlich über der Wesentlichkeitsschwelle | 22 | 0 | 0 |
| 23 | Wesentlichkeitsschwelle 1 %: Gesamtfehlerquote darüber | 22 | 0 | 0 |
| 24 | Keine Fehler festgestellt (Σ E = 0) | 22 | 0 | 0 |
| 25 | Fehler der umfassenden Schicht und der Zufallsschicht heben sich auf | 22 | 0 | 0 |
| 26 | Umfassende Schicht umfasst die gesamte Grundgesamtheit (BV_s = 0) | 22 | 0 | 0 |
| 27 | Summe der Buchwerte der Stichprobe = 0 (Division durch null) | 22 | 0 | 0 |
| 28 | Leeres Formular (nur Vorgaben der Vorlage) | 22 | 9 | 0 |
| 29 | Leeres Formular, Wesentlichkeitsschwelle geleert | 22 | 9 | 0 |
| 30 | Teilweise: nur Grundgesamtheit | 22 | 3 | 0 |
| 31 | Teilweise: nur die Anzahl der Einheiten (N ≥ 300) | 22 | 6 | 0 |
| 32 | Teilweise: Grundgesamtheit und Stichprobe, noch keine Prüfergebnisse | 22 | 0 | 0 |
| 33 | Teilweise: umfassende Schicht ohne Umfang der Zufallsstichprobe | 22 | 3 | 0 |
| 34 | Teilweise: alles ausgefüllt außer dem Buchwert der Grundgesamtheit | 22 | 6 | 0 |
| 35 | Teilweise: alles ausgefüllt außer der Anzahl der Einheiten | 22 | 4 | 0 |
| 36 | Teilweise: alles ausgefüllt außer Buchwert und Anzahl der Einheiten | 22 | 10 | 0 |
| 37 | Teilweise: alles ausgefüllt außer dem Umfang der Zufallsstichprobe | 22 | 3 | 0 |
| 38 | Teilweise: alles ausgefüllt außer der Summe der Buchwerte der Stichprobe | 22 | 0 | 0 |
| 39 | Teilweise: alles ausgefüllt außer der Summe der Fehler der Stichprobe | 22 | 0 | 0 |
| 40 | Teilweise: alles ausgefüllt außer den Fehlern der umfassenden Schicht | 22 | 0 | 0 |
| 41 | Teilweise: alles ausgefüllt außer systembedingten und anomalen Fehlern | 22 | 0 | 0 |
| 42 | Teilweise: Wesentlichkeitsschwelle geleert, sonst vollständig | 22 | 1 | 0 |
| 43 | Buchwert und Anzahl aus Blatt 02 übernommen (Verknüpfung) | 22 | 0 | 0 |
| 44 | Blatt 02 ausgefüllt, Buchwert im Methodenblatt überschrieben | 22 | 0 | 0 |
| 45 | Blatt 02 ausgefüllt, Anzahl im Methodenblatt überschrieben | 22 | 0 | 0 |
| 46 | Blatt 02 mit Ausschluss nach Art. 80 Abs. 3: angepasste Grundgesamtheit fließt ein | 22 | 0 | 0 |
| 47 | Blatt 02 ausgefüllt, Methodenblatt sonst leer | 22 | 3 | 0 |

## 14_NS_GW_S

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 64 | 2560 | 2460 | 40 | 0 | 60 | 0 | 0 | 0 |
| abnahme-luecken | 112 | 4480 | 4260 | 111 | 0 | 109 | 0 | 0 | 0 |
| abnahme-schwelle | 60 | 2400 | 2340 | 0 | 0 | 60 | 0 | 0 | 0 |
| Hauptsatz | 54 | 2160 | 1969 | 150 | 0 | 41 | 0 | 0 | 0 |
| zufall | 120 | 4800 | 4680 | 0 | 0 | 120 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall: drei Schichten, umfassende Schicht mit vier Einheiten | 40 | 0 | 0 |
| 2 | Eine Schicht | 40 | 0 | 0 |
| 3 | Sieben Schichten (alle Spalten der Vorlage) | 40 | 0 | 0 |
| 4 | Leere Schichten zwischen belegten (Spalten D, F und H) | 40 | 0 | 0 |
| 5 | Aufrundung je Schicht hebt die Summe über den Umfang (3 × 50 Einheiten, n = 10) | 40 | 0 | 0 |
| 6 | Glatte Aufteilung: 60 und 120 von 180 Einheiten, n = 18 | 40 | 0 | 0 |
| 7 | Glatte Aufteilung: 30, 70 und 110 von 210 Einheiten, n = 21 | 40 | 0 | 0 |
| 8 | Mindestwert 1 für eine sehr kleine Schicht | 40 | 0 | 0 |
| 9 | Umfang der Zufallsstichprobe 0: je Schicht der Mindestwert 1 | 40 | 0 | 0 |
| 10 | Schicht mit N_h = 0 | 40 | 0 | 0 |
| 11 | Einzige Schicht mit N_h = 0 (Division durch null) | 40 | 0 | 0 |
| 12 | N = 299: knapp unter der Schwelle des Art. 79 Abs. 2 | 40 | 0 | 0 |
| 13 | N = 300: genau auf der Schwelle (nur im Fall des Art. 6 Abs. 3) | 40 | 0 | 0 |
| 14 | N = 301: knapp über der Schwelle | 40 | 0 | 0 |
| 15 | N = 450: Wechsel nach Art. 6 Abs. 3 | 40 | 0 | 0 |
| 16 | N = 299 nur mit den Einheiten der umfassenden Schicht unter 300 gehalten | 40 | 0 | 0 |
| 17 | Mindesterfassung genau erreicht (18 von 180) | 40 | 0 | 0 |
| 18 | Mindesterfassung knapp verfehlt (17 von 180) | 40 | 0 | 0 |
| 19 | Mindesterfassung nur durch die Aufrundung je Schicht erreicht | 40 | 0 | 0 |
| 20 | Mindesterfassung bei N = 30 (0,1 · 30 ist im Gleitkomma knapp über 3) | 40 | 0 | 0 |
| 21 | Ohne umfassende Schicht | 40 | 0 | 0 |
| 22 | Umfassende Schicht mit 0 angegeben | 40 | 0 | 0 |
| 23 | Systembedingte und anomale Fehler | 40 | 0 | 0 |
| 24 | Nur systembedingte Fehler | 40 | 0 | 0 |
| 25 | Nur anomale Fehler | 40 | 0 | 0 |
| 26 | Gesamtfehlerquote genau auf der Wesentlichkeitsschwelle (2,00 %) | 40 | 0 | 0 |
| 27 | Gesamtfehlerquote knapp über der Wesentlichkeitsschwelle | 40 | 0 | 0 |
| 28 | Gesamtfehlerquote knapp unter der Wesentlichkeitsschwelle | 40 | 0 | 0 |
| 29 | Gesamtfehlerquote deutlich über der Wesentlichkeitsschwelle | 40 | 0 | 0 |
| 30 | Wesentlichkeitsschwelle 1 %: Gesamtfehlerquote darüber | 40 | 0 | 0 |
| 31 | Keine Fehler festgestellt | 40 | 0 | 0 |
| 32 | Fehler nur in einer Schicht eingetragen, übrige leer | 40 | 0 | 0 |
| 33 | Keine Fehlersummen eingetragen | 40 | 0 | 0 |
| 34 | Fehlende Angabe in nur einer Schicht: Buchwert der Schicht 2 | 40 | 8 | 0 |
| 35 | Fehlende Angabe in nur einer Schicht: Summe der Buchwerte der Stichprobe der Schicht 2 | 40 | 0 | 0 |
| 36 | Fehlende Angabe in nur einer Schicht: Anzahl der Einheiten der Schicht 2 | 40 | 0 | 0 |
| 37 | Summe der Buchwerte der Stichprobe einer Schicht = 0 (Division durch null) | 40 | 0 | 0 |
| 38 | Leeres Formular (nur Vorgaben der Vorlage) | 40 | 14 | 0 |
| 39 | Leeres Formular, Wesentlichkeitsschwelle geleert | 40 | 14 | 0 |
| 40 | Teilweise: nur Einheiten und Buchwerte der Schichten | 40 | 10 | 0 |
| 41 | Teilweise: nur die Anzahl der Einheiten je Schicht (N ≥ 300) | 40 | 12 | 0 |
| 42 | Teilweise: nur die umfassende Schicht | 40 | 14 | 0 |
| 43 | Teilweise: nur Umfang der Zufallsstichprobe und umfassende Schicht | 40 | 14 | 0 |
| 44 | Teilweise: Schichten und Stichprobe, noch keine Prüfergebnisse | 40 | 0 | 0 |
| 45 | Teilweise: alles ausgefüllt außer dem Umfang der Zufallsstichprobe | 40 | 7 | 0 |
| 46 | Teilweise: alles ausgefüllt außer der Anzahl der Einheiten je Schicht | 40 | 0 | 0 |
| 47 | Teilweise: alles ausgefüllt außer den Buchwerten je Schicht | 40 | 13 | 0 |
| 48 | Teilweise: alles ausgefüllt außer Einheiten je Schicht und Umfang der Zufallsstichprobe | 40 | 15 | 0 |
| 49 | Teilweise: alles ausgefüllt außer den Fehlern der umfassenden Schicht | 40 | 0 | 0 |
| 50 | Teilweise: alles ausgefüllt außer systembedingten und anomalen Fehlern | 40 | 0 | 0 |
| 51 | Teilweise: Wesentlichkeitsschwelle geleert, sonst vollständig | 40 | 1 | 0 |
| 52 | Teilweise: sieben Schichten ohne Umfang der Zufallsstichprobe | 40 | 11 | 0 |
| 53 | Teilweise: sieben Schichten ohne Buchwerte je Schicht | 40 | 17 | 0 |
| 54 | Teilweise: sieben Schichten ohne Summen der Buchwerte der Stichprobe | 40 | 0 | 0 |

## 15_NS_PPS

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 64 | 1664 | 1577 | 32 | 0 | 55 | 0 | 0 | 0 |
| abnahme-luecken | 108 | 2808 | 2608 | 104 | 0 | 96 | 0 | 0 | 0 |
| abnahme-schwelle | 60 | 1560 | 1500 | 0 | 0 | 60 | 0 | 0 | 0 |
| Hauptsatz | 54 | 1404 | 1280 | 86 | 0 | 38 | 0 | 0 | 0 |
| zufall | 120 | 3120 | 3005 | 0 | 0 | 115 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall: N = 180, drei hochwertige Einheiten mit Fehlern | 26 | 0 | 0 |
| 2 | N = 299: knapp unter der Schwelle des Art. 79 Abs. 2 | 26 | 0 | 0 |
| 3 | N = 300: genau auf der Schwelle (nur im Fall des Art. 6 Abs. 3) | 26 | 0 | 0 |
| 4 | N = 301: knapp über der Schwelle | 26 | 0 | 0 |
| 5 | N = 450: Wechsel nach Art. 6 Abs. 3 | 26 | 0 | 0 |
| 6 | Mindesterfassung genau erreicht (18 von 180) | 26 | 0 | 0 |
| 7 | Mindesterfassung knapp verfehlt (17 von 180) | 26 | 0 | 0 |
| 8 | Mindesterfassung aufgerundet: N = 181 verlangt 19 Einheiten, 19 geprüft | 26 | 0 | 0 |
| 9 | Mindesterfassung aufgerundet: N = 181 verlangt 19 Einheiten, 18 geprüft | 26 | 0 | 0 |
| 10 | Mindesterfassung bei N = 30 (0,1 · 30 ist im Gleitkomma knapp über 3) | 26 | 0 | 0 |
| 11 | Mindesterfassung bei N = 70 (0,1 · 70 ist im Gleitkomma knapp über 7) | 26 | 0 | 0 |
| 12 | Mindesterfassung bei N = 290, eine Einheit zu wenig | 26 | 0 | 0 |
| 13 | Ohne hochwertige Einheiten (Angaben leer) | 26 | 0 | 0 |
| 14 | Ohne hochwertige Einheiten (mit 0 angegeben) | 26 | 0 | 0 |
| 15 | Hochwertige Einheiten ohne Fehler | 26 | 0 | 0 |
| 16 | Hochwertige Einheiten mit hohen Fehlern | 26 | 0 | 0 |
| 17 | Genau drei Einheiten in der Zufallsschicht | 26 | 0 | 0 |
| 18 | Weniger als drei Einheiten in der Zufallsschicht | 26 | 0 | 0 |
| 19 | Zufallsschicht ohne Einheiten (n_s = 0, Division durch null) | 26 | 0 | 0 |
| 20 | Mehr hochwertige Einheiten als Stichprobenumfang (n_s negativ) | 26 | 0 | 0 |
| 21 | Hochwertige Einheiten umfassen die gesamte Grundgesamtheit | 26 | 0 | 0 |
| 22 | Iteration erforderlich (zwei Einheiten über dem Auswahlintervall) | 26 | 0 | 0 |
| 23 | Iteration nicht angegeben | 26 | 0 | 0 |
| 24 | Systembedingte und anomale Fehler | 26 | 0 | 0 |
| 25 | Nur systembedingte Fehler | 26 | 0 | 0 |
| 26 | Nur anomale Fehler | 26 | 0 | 0 |
| 27 | Gesamtfehlerquote genau auf der Wesentlichkeitsschwelle (2,00 %) | 26 | 0 | 0 |
| 28 | Gesamtfehlerquote knapp über der Wesentlichkeitsschwelle | 26 | 0 | 0 |
| 29 | Gesamtfehlerquote knapp unter der Wesentlichkeitsschwelle | 26 | 0 | 0 |
| 30 | Gesamtfehlerquote über der Schwelle durch systembedingte Fehler | 26 | 0 | 0 |
| 31 | Gesamtfehlerquote deutlich über der Wesentlichkeitsschwelle | 26 | 0 | 0 |
| 32 | Wesentlichkeitsschwelle 1 %: Gesamtfehlerquote darüber | 26 | 0 | 0 |
| 33 | Keine Fehler festgestellt | 26 | 0 | 0 |
| 34 | Leeres Formular (nur Vorgaben der Vorlage) | 26 | 9 | 0 |
| 35 | Leeres Formular, Wesentlichkeitsschwelle geleert | 26 | 9 | 0 |
| 36 | Teilweise: nur Grundgesamtheit | 26 | 3 | 0 |
| 37 | Teilweise: nur die Anzahl der Einheiten (N ≥ 300) | 26 | 6 | 0 |
| 38 | Teilweise: Grundgesamtheit und Stichprobenumfang | 26 | 0 | 0 |
| 39 | Teilweise: Grundgesamtheit und Stichprobe, noch keine Prüfergebnisse | 26 | 0 | 0 |
| 40 | Teilweise: nur Stichprobenumfang und hochwertige Einheiten | 26 | 10 | 0 |
| 41 | Teilweise: alles ausgefüllt außer dem Buchwert der Grundgesamtheit | 26 | 8 | 0 |
| 42 | Teilweise: alles ausgefüllt außer der Anzahl der Einheiten | 26 | 4 | 0 |
| 43 | Teilweise: alles ausgefüllt außer Buchwert und Anzahl der Einheiten | 26 | 12 | 0 |
| 44 | Teilweise: alles ausgefüllt außer dem Stichprobenumfang | 26 | 11 | 0 |
| 45 | Teilweise: alles ausgefüllt außer Buchwert und Stichprobenumfang | 26 | 10 | 0 |
| 46 | Teilweise: alles ausgefüllt außer den Fehlern der hochwertigen Einheiten | 26 | 0 | 0 |
| 47 | Teilweise: alles ausgefüllt außer der Summe der Fehlerquoten | 26 | 0 | 0 |
| 48 | Teilweise: alles ausgefüllt außer systembedingten und anomalen Fehlern | 26 | 0 | 0 |
| 49 | Teilweise: Wesentlichkeitsschwelle geleert, sonst vollständig | 26 | 1 | 0 |
| 50 | Buchwert und Anzahl aus Blatt 02 übernommen (Verknüpfung) | 26 | 0 | 0 |
| 51 | Blatt 02 ausgefüllt, Buchwert im Methodenblatt überschrieben | 26 | 0 | 0 |
| 52 | Blatt 02 ausgefüllt, Anzahl im Methodenblatt überschrieben | 26 | 0 | 0 |
| 53 | Blatt 02 mit Ausschluss nach Art. 80 Abs. 3: angepasste Grundgesamtheit fließt ein | 26 | 0 | 0 |
| 54 | Blatt 02 ausgefüllt, Methodenblatt sonst leer | 26 | 3 | 0 |

## 16_NS_PPS_S

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 64 | 4480 | 4347 | 75 | 0 | 58 | 0 | 0 | 0 |
| abnahme-luecken | 113 | 7910 | 7435 | 372 | 0 | 103 | 0 | 0 | 0 |
| abnahme-schwelle | 60 | 4200 | 4140 | 0 | 0 | 60 | 0 | 0 | 0 |
| Hauptsatz | 55 | 3850 | 3638 | 171 | 0 | 41 | 0 | 0 | 0 |
| zufall | 120 | 8400 | 8280 | 0 | 0 | 120 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall: drei Schichten, hochwertige Einheiten in zwei Schichten | 70 | 0 | 0 |
| 2 | Eine Schicht | 70 | 0 | 0 |
| 3 | Sieben Schichten (alle Spalten der Vorlage) | 70 | 0 | 0 |
| 4 | Leere Schichten zwischen belegten (Spalten D, F und H) | 70 | 0 | 0 |
| 5 | Aufrundung je Schicht hebt die Summe über den Umfang (drei gleich große Schichten, n = 10) | 70 | 0 | 0 |
| 6 | Glatte Aufteilung: 1,5 Mio. € und 3 Mio. € von 4,5 Mio. €, n = 18 | 70 | 0 | 0 |
| 7 | Glatte Aufteilung: 0,3, 0,7 und 1,1 Mio. € von 2,1 Mio. €, n = 21 | 70 | 0 | 0 |
| 8 | Mindestwert 1 für eine sehr kleine Schicht | 70 | 0 | 0 |
| 9 | Stichprobenumfang 0: je Schicht der Mindestwert 1 | 70 | 0 | 0 |
| 10 | Schicht mit Buchwert 0 | 70 | 0 | 0 |
| 11 | Einzige Schicht mit Buchwert 0 (Division durch null) | 70 | 0 | 0 |
| 12 | N = 299: knapp unter der Schwelle des Art. 79 Abs. 2 | 70 | 0 | 0 |
| 13 | N = 300: genau auf der Schwelle (nur im Fall des Art. 6 Abs. 3) | 70 | 0 | 0 |
| 14 | N = 301: knapp über der Schwelle | 70 | 0 | 0 |
| 15 | N = 450: Wechsel nach Art. 6 Abs. 3 | 70 | 0 | 0 |
| 16 | Mindesterfassung genau erreicht (18 von 180) | 70 | 0 | 0 |
| 17 | Mindesterfassung knapp verfehlt (17 von 180) | 70 | 0 | 0 |
| 18 | Mindesterfassung nur durch die Aufrundung je Schicht erreicht | 70 | 0 | 0 |
| 19 | Mindesterfassung bei N = 30 (0,1 · 30 ist im Gleitkomma knapp über 3) | 70 | 0 | 0 |
| 20 | Mindesterfassung bei N = 70, eine Einheit zu wenig | 70 | 0 | 0 |
| 21 | Ohne hochwertige Einheiten (Angaben leer) | 70 | 0 | 0 |
| 22 | Hochwertige Einheiten ohne Fehler | 70 | 0 | 0 |
| 23 | Hochwertige Einheiten mit hohen Fehlern | 70 | 0 | 0 |
| 24 | Alle Einheiten einer Schicht hochwertig (n_hs = 0, Division durch null) | 70 | 0 | 0 |
| 25 | Mehr hochwertige Einheiten als Schichtumfang (n_hs negativ) | 70 | 0 | 0 |
| 26 | Systembedingte und anomale Fehler | 70 | 0 | 0 |
| 27 | Nur systembedingte Fehler | 70 | 0 | 0 |
| 28 | Nur anomale Fehler | 70 | 0 | 0 |
| 29 | Gesamtfehlerquote genau auf der Wesentlichkeitsschwelle (2,00 %) | 70 | 0 | 0 |
| 30 | Gesamtfehlerquote knapp über der Wesentlichkeitsschwelle | 70 | 0 | 0 |
| 31 | Gesamtfehlerquote knapp unter der Wesentlichkeitsschwelle | 70 | 0 | 0 |
| 32 | Gesamtfehlerquote deutlich über der Wesentlichkeitsschwelle | 70 | 0 | 0 |
| 33 | Wesentlichkeitsschwelle 1 %: Gesamtfehlerquote darüber | 70 | 0 | 0 |
| 34 | Keine Fehler festgestellt | 70 | 0 | 0 |
| 35 | Fehlerquoten nur in einer Schicht eingetragen, übrige leer | 70 | 0 | 0 |
| 36 | Keine Summen der Fehlerquoten eingetragen | 70 | 0 | 0 |
| 37 | Fehlende Angabe in nur einer Schicht: Anzahl der Einheiten der Schicht 2 | 70 | 0 | 0 |
| 38 | Fehlende Angabe in nur einer Schicht: Buchwert der Schicht 2 | 70 | 0 | 0 |
| 39 | Fehlende Angabe in nur einer Schicht: hochwertige Einheiten der Schicht 1 | 70 | 0 | 0 |
| 40 | Leeres Formular (nur Vorgaben der Vorlage) | 70 | 13 | 0 |
| 41 | Leeres Formular, Wesentlichkeitsschwelle geleert | 70 | 13 | 0 |
| 42 | Teilweise: nur Buchwerte und Einheiten der Schichten | 70 | 21 | 0 |
| 43 | Teilweise: nur die Buchwerte je Schicht | 70 | 20 | 0 |
| 44 | Teilweise: nur die Anzahl der Einheiten je Schicht (N ≥ 300) | 70 | 9 | 0 |
| 45 | Teilweise: nur der Stichprobenumfang | 70 | 0 | 0 |
| 46 | Teilweise: Schichten und Stichprobe, noch keine Prüfergebnisse | 70 | 0 | 0 |
| 47 | Teilweise: alles ausgefüllt außer dem Stichprobenumfang | 70 | 24 | 0 |
| 48 | Teilweise: alles ausgefüllt außer der Anzahl der Einheiten je Schicht | 70 | 0 | 0 |
| 49 | Teilweise: alles ausgefüllt außer Einheiten je Schicht und Stichprobenumfang | 70 | 28 | 0 |
| 50 | Teilweise: alles ausgefüllt außer den Buchwerten je Schicht | 70 | 0 | 0 |
| 51 | Teilweise: alles ausgefüllt außer systembedingten und anomalen Fehlern | 70 | 0 | 0 |
| 52 | Teilweise: Wesentlichkeitsschwelle geleert, sonst vollständig | 70 | 1 | 0 |
| 53 | Teilweise: sieben Schichten ohne Stichprobenumfang | 70 | 42 | 0 |
| 54 | Teilweise: sieben Schichten ohne Anzahl der Einheiten je Schicht | 70 | 0 | 0 |
| 55 | Einzige Schicht, alle Einheiten hochwertig: keine Schicht hochrechenbar (n_hs = 0) | 70 | 0 | 0 |

## 17_Unterstichprobe

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 72 | 432 | 408 | 24 | 0 | 0 | 0 | 0 | 0 |
| abnahme-luecken | 14 | 84 | 77 | 7 | 0 | 0 | 0 | 0 | 0 |
| Hauptsatz | 16 | 96 | 92 | 4 | 0 | 0 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Variante 1: Standardfall | 6 | 0 | 0 |
| 2 | Variante 1: mit umfassend geprüften Unterstichprobeneinheiten | 6 | 0 | 0 |
| 3 | Variante 1: ohne Fehler | 6 | 0 | 0 |
| 4 | Variante 1: nur umfassend geprüfte Einheiten mit Fehler, Zufallsteil ohne Fehlerangabe | 6 | 0 | 0 |
| 5 | Variante 2: Standardfall PPS | 6 | 0 | 0 |
| 6 | Variante 2: mit hochwertigen Unterstichprobeneinheiten | 6 | 0 | 0 |
| 7 | Variante 2: alle Unterstichprobeneinheiten hochwertig (m = m_e) | 6 | 0 | 0 |
| 8 | Variante 2: ohne Fehler | 6 | 0 | 0 |
| 9 | Beide Varianten ausgefüllt | 6 | 0 | 0 |
| 10 | Fehler über dem Buchwert der Unterstichprobe (Fehlerquote über 100 %) | 6 | 0 | 0 |
| 11 | Leeres Formular | 6 | 0 | 0 |
| 12 | Teilweise: nur Kennung und Buchwert | 6 | 0 | 0 |
| 13 | Teilweise: Variante 1 ohne Buchwert der Stichprobeneinheit | 6 | 1 | 0 |
| 14 | Teilweise: Variante 1 ohne Summe der Buchwerte der Unterstichprobe | 6 | 0 | 0 |
| 15 | Teilweise: Variante 2 ohne Umfang der Unterstichprobe | 6 | 0 | 0 |
| 16 | Teilweise: Variante 2 ohne Buchwert der Stichprobeneinheit | 6 | 3 | 0 |

## 18_GFQ_AnhIII

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 126 | 2772 | 2618 | 7 | 0 | 85 | 62 | 0 | 0 |
| abnahme-luecken | 370 | 8140 | 7533 | 217 | 0 | 206 | 184 | 0 | 0 |
| Hauptsatz | 55 | 1210 | 1104 | 65 | 0 | 37 | 4 | 0 | 0 |
| zufall | 126 | 2772 | 2611 | 0 | 0 | 110 | 51 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | MUS, 1 Zeitraum (03): keine Behandlung nach Art. 80 Abs. 3, mit TH-Pauschale | 22 | 0 | 0 |
| 2 | MUS geschichtet (04): keine Behandlung, mit TH-Pauschale | 22 | 0 | 0 |
| 3 | MUS, 2 Zeiträume (05) | 22 | 0 | 0 |
| 4 | MUS, 2 Zeiträume, geschichtet (06) | 22 | 0 | 0 |
| 5 | MUS, 3 Zeiträume (07) | 22 | 0 | 0 |
| 6 | SRS, 1 Zeitraum (08): keine Behandlung, ohne TH-Pauschale | 22 | 0 | 0 |
| 7 | SRS geschichtet (09) | 22 | 0 | 0 |
| 8 | SRS, 2 Zeiträume (10) | 22 | 0 | 0 |
| 9 | SRS, 2 Zeiträume, geschichtet (11) | 22 | 0 | 0 |
| 10 | SRS, 3 Zeiträume (12) | 22 | 0 | 0 |
| 11 | Nichtstatistisch, gleiche Wahrscheinlichkeit (13): Genauigkeit „n. a.“ | 22 | 0 | 0 |
| 12 | Nichtstatistisch, gleiche Wahrscheinlichkeit, geschichtet (14) | 22 | 0 | 0 |
| 13 | Nichtstatistisch, PPS (15): Tabelle 1 | 22 | 0 | 0 |
| 14 | Nichtstatistisch, PPS, geschichtet (16) | 22 | 0 | 0 |
| 15 | MUS (03), Ausschluss: Buchwert aus Blatt 02 verknüpft (reduzierte Grundgesamtheit) | 22 | 0 | 0 |
| 16 | MUS (03), Ausschluss: Buchwert im Methodenblatt überschrieben (Basis weicht ab) | 22 | 0 | 0 |
| 17 | MUS (03), Ersetzung: Tabelle 1, Genauigkeit unverändert | 22 | 0 | 0 |
| 18 | SRS (08), Ausschluss: Tabelle 2 | 22 | 0 | 0 |
| 19 | SRS (08), Ersetzung: Tabelle 2, Genauigkeit mit dem Faktor angepasst | 22 | 0 | 0 |
| 20 | Nichtstatistisch (13), Ersetzung: Genauigkeit bleibt „n. a.“ | 22 | 0 | 0 |
| 21 | Nichtstatistisch PPS (15), Ausschluss | 22 | 0 | 0 |
| 22 | Einheiten erfasst, aber keine Behandlung gewählt | 22 | 0 | 0 |
| 23 | Ausschluss gewählt, aber keine Einheiten erfasst (Faktor 1) | 22 | 0 | 0 |
| 24 | Anpassung hochwertige Schicht Ja (03), keine Behandlung | 22 | 0 | 0 |
| 25 | Anpassung hochwertige Schicht Ja (03), Ausschluss | 22 | 0 | 0 |
| 26 | Anpassung hochwertige Schicht Ja (08), Ersetzung | 22 | 0 | 0 |
| 27 | Anpassung hochwertige Schicht Nein, Buchwerte dennoch eingetragen | 22 | 0 | 0 |
| 28 | Alles außer BV_e,u: Anpassung Ja ohne Buchwert der ursprünglichen hochwertigen Schicht | 22 | 6 | 0 |
| 29 | Alles außer BV_e,r: Anpassung Ja ohne Buchwert der geprüften hochwertigen Schicht | 22 | 0 | 0 |
| 30 | Anpassung Ja, BV_e,r = 0 (Division durch null) | 22 | 0 | 0 |
| 31 | Auswahl Ja/Nein geleert | 22 | 0 | 0 |
| 32 | GFQ über der Wesentlichkeitsschwelle (03, Fall 16) | 22 | 0 | 0 |
| 33 | GFQ unter, obere Fehlergrenze über der Schwelle (03, Fall 17) | 22 | 0 | 0 |
| 34 | Wesentlichkeitsschwelle 0.05 % (03) | 22 | 0 | 0 |
| 35 | Wesentlichkeitsschwelle 0.4 % (03) | 22 | 0 | 0 |
| 36 | Wesentlichkeitsschwelle 0.8 % (03) | 22 | 0 | 0 |
| 37 | Wesentlichkeitsschwelle 1.2 % (03) | 22 | 0 | 0 |
| 38 | Alles außer der Wesentlichkeitsschwelle (geleert) | 22 | 1 | 0 |
| 39 | Nichtstatistisch (13), GFQ über der Schwelle 0,01 % | 22 | 0 | 0 |
| 40 | Kein Methodenblatt gewählt, Blatt 02 ausgefüllt | 22 | 2 | 0 |
| 41 | Leeres Formular (nichts gewählt, nichts eingetragen) | 22 | 5 | 0 |
| 42 | Methodenblatt leer (03), Blatt 02 ausgefüllt | 22 | 2 | 0 |
| 43 | Methodenblatt leer (04, geschichtet), Buchwerte der hochwertigen Schicht eingetragen | 22 | 6 | 0 |
| 44 | Methodenblatt leer (13, nichtstatistisch) | 22 | 0 | 0 |
| 45 | Methodenblatt (03) ohne voraussichtliche Standardabweichung | 22 | 8 | 0 |
| 46 | Methodenblatt (03) ohne voraussichtliche Standardabweichung, Ausschluss und Anpassung Ja | 22 | 8 | 0 |
| 47 | Methodenblatt (03) ohne Summe der Fehlerquoten | 22 | 0 | 0 |
| 48 | Methodenblatt (03) ohne Standardabweichung der Stichprobe (mit 0 gerechnet) | 22 | 0 | 0 |
| 49 | SRS (08): extrapolierter Fehler bestimmt, Genauigkeit nicht (Umfang nicht bestimmbar) | 22 | 2 | 0 |
| 50 | SRS geschichtet (09): extrapolierter Fehler bestimmt, Genauigkeit nicht, Schwelle 0,01 % | 22 | 2 | 0 |
| 51 | Blatt 02 leer, Methodenblatt (03) mit eigenem Buchwert | 22 | 4 | 0 |
| 52 | Blatt 02 leer, Methodenblatt (03) mit verknüpftem Buchwert | 22 | 7 | 0 |
| 53 | Blatt 02 ohne Summe der positiven Datensätze, mit TH-Pauschale und nicht prüfbaren Einheiten | 22 | 7 | 0 |
| 54 | Blatt 02: Behandlung nach Art. 80 Abs. 3 geleert | 22 | 1 | 0 |
| 55 | Blatt 02: nur TH-Pauschale eingetragen | 22 | 4 | 0 |

## 20_Druck_KOM

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 98 | 3234 | 2989 | 13 | 108 | 73 | 51 | 0 | 0 |
| abnahme-luecken | 410 | 13530 | 12332 | 200 | 422 | 370 | 206 | 0 | 0 |
| Hauptsatz | 24 | 792 | 718 | 33 | 24 | 17 | 0 | 0 | 0 |
| zufall | 56 | 1848 | 1724 | 0 | 56 | 56 | 12 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standard: MUS (03), TH-Pauschale, Fehlertabelle mit vorläufigen Fällen | 33 | 0 | 0 |
| 2 | Stand und Status geleert, keine Fehlerfälle | 33 | 0 | 0 |
| 3 | Status „endgültig“, Geschäftsjahr als Zahl, nur geprüfte Ausgaben | 33 | 0 | 0 |
| 4 | SRS (08), Ausschluss, Beträge nach Art. 98 Abs. 6 und Finanzkorrekturen | 33 | 0 | 0 |
| 5 | Nichtstatistisch (13): Genauigkeit und obere Fehlergrenze „nicht berechnet“ | 33 | 0 | 0 |
| 6 | Nichtstatistisch PPS geschichtet (16), Ersetzung | 33 | 0 | 0 |
| 7 | MUS geschichtet (04) | 33 | 0 | 0 |
| 8 | MUS, 2 Zeiträume, geschichtet (06) | 33 | 0 | 0 |
| 9 | SRS, 3 Zeiträume (12), Anpassung hochwertige Schicht Ja | 33 | 0 | 0 |
| 10 | GFQ über der Schwelle: Finanzkorrektur bis 2 % erforderlich | 33 | 0 | 0 |
| 11 | GFQ über der Schwelle, Finanzkorrekturen senken die Restfehlerquote unter 2 % | 33 | 0 | 0 |
| 12 | Finanzkorrekturen größer als der Fehlerbetrag (negative Restfehlerquote) | 33 | 0 | 0 |
| 13 | Restfehlerquote nicht bestimmbar: Art. 98 Abs. 6 und Finanzkorrekturen erreichen die Hochrechnungsbasis | 33 | 1 | 0 |
| 14 | Wesentlichkeitsschwelle in Blatt 18 abweichend (0,5 %) | 33 | 0 | 0 |
| 15 | Alles außer der Wesentlichkeitsschwelle in Blatt 18 (geleert) | 33 | 1 | 0 |
| 16 | Fehlertabelle voll: Schreibweisen von „vorläufig“, Zeilen ohne Buchwert bzw. ohne Fehler | 33 | 0 | 0 |
| 17 | Kein Methodenblatt gewählt | 33 | 2 | 0 |
| 18 | Leeres Formular (nichts gewählt, nichts eingetragen) | 33 | 6 | 0 |
| 19 | Methodenblatt leer (03) | 33 | 2 | 0 |
| 20 | Methodenblatt (03) ohne voraussichtliche Standardabweichung | 33 | 9 | 0 |
| 21 | SRS (08): extrapolierter Fehler bestimmt, Genauigkeit nicht | 33 | 2 | 0 |
| 22 | Blatt 02 leer | 33 | 5 | 0 |
| 23 | Blatt 02 ohne Anzahl der Datensätze und ohne Betrag laut SFC2021 | 33 | 2 | 0 |
| 24 | Blatt 02 ohne positive Datensätze (Anzahl und Summe) | 33 | 3 | 0 |

## X1_KonsMUS_2017

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 80 | 1040 | 943 | 89 | 8 | 0 | 0 | 0 | 0 |
| abnahme-luecken | 9 | 117 | 82 | 35 | 0 | 0 | 0 | 0 | 0 |
| Hauptsatz | 24 | 312 | 255 | 57 | 0 | 0 | 0 | 0 | 0 |
| zufall | 100 | 1300 | 1300 | 0 | 0 | 0 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall, Konfidenzniveau 90 % | 13 | 0 | 0 |
| 2 | Konfidenzniveau 60 % | 13 | 0 | 0 |
| 3 | Konfidenzniveau 70 % | 13 | 0 | 0 |
| 4 | Konfidenzniveau 80 % | 13 | 0 | 0 |
| 5 | Konfidenzniveau 95 % | 13 | 0 | 0 |
| 6 | Leeres Formular | 13 | 4 | 0 |
| 7 | Alles ausgefüllt außer C1 | 13 | 2 | 0 |
| 8 | Alles ausgefüllt außer C4 | 13 | 11 | 0 |
| 9 | Alles ausgefüllt außer C7 | 13 | 10 | 0 |
| 10 | Alles ausgefüllt außer C13 | 13 | 4 | 0 |
| 11 | Alles ausgefüllt außer C14 | 13 | 4 | 0 |
| 12 | Alles ausgefüllt außer C16 | 13 | 4 | 0 |
| 13 | Ohne Stichprobeneinheit und Umfang der Grundgesamtheit (C2, C3 werden nicht gelesen) | 13 | 0 | 0 |
| 14 | Nur Planung ausgefüllt, Prüfergebnisse leer | 13 | 6 | 0 |
| 15 | Nur Buchwert ausgefüllt | 13 | 12 | 0 |
| 16 | TE = AE × EF (95 %, erwartete Fehlerquote 1,25 %): Nenner null | 13 | 0 | 0 |
| 17 | Knapp unter TE = AE × EF (95 %, 1,24 %) | 13 | 0 | 0 |
| 18 | Knapp über TE = AE × EF (95 %, 1,26 %): negativer Nenner, Umfang 30 | 13 | 0 | 0 |
| 19 | Erwartete Fehlerquote über der Wesentlichkeitsschwelle (3 %) | 13 | 0 | 0 |
| 20 | Rechnerischer Umfang genau 150 (95 %, erwartete Fehlerquote 0) | 13 | 0 | 0 |
| 21 | Erwartete Fehlerquote 0 eingetragen | 13 | 0 | 0 |
| 22 | Keine Fehler in der Stichprobe (Nullen eingetragen) | 13 | 0 | 0 |
| 23 | Buchwert 0: Division durch null | 13 | 0 | 0 |
| 24 | Kleine Grundgesamtheit, Konfidenzniveau 60 % | 13 | 0 | 0 |

## X2_DiffSch_2017

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 80 | 1040 | 958 | 78 | 4 | 0 | 0 | 0 | 0 |
| abnahme-luecken | 226 | 2938 | 2891 | 47 | 0 | 0 | 0 | 0 | 0 |
| Hauptsatz | 28 | 364 | 296 | 68 | 0 | 0 | 0 | 0 | 0 |
| zufall | 100 | 1300 | 1300 | 0 | 0 | 0 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall, Konfidenzniveau 90 % | 13 | 0 | 0 |
| 2 | Konfidenzniveau 60 % | 13 | 0 | 0 |
| 3 | Konfidenzniveau 70 % | 13 | 0 | 0 |
| 4 | Konfidenzniveau 80 % | 13 | 0 | 0 |
| 5 | Konfidenzniveau 95 % | 13 | 0 | 0 |
| 6 | Leeres Formular | 13 | 4 | 0 |
| 7 | Alles ausgefüllt außer C1 | 13 | 3 | 0 |
| 8 | Alles ausgefüllt außer C3 | 13 | 9 | 0 |
| 9 | Alles ausgefüllt außer C4 | 13 | 9 | 0 |
| 10 | Alles ausgefüllt außer C5 | 13 | 10 | 0 |
| 11 | Alles ausgefüllt außer C7 | 13 | 10 | 0 |
| 12 | Alles ausgefüllt außer C13 | 13 | 6 | 0 |
| 13 | Alles ausgefüllt außer C15 | 13 | 0 | 0 |
| 14 | Ohne Stichprobeneinheit und Ausgaben der Stichprobe (C2, C12 werden nicht gelesen) | 13 | 0 | 0 |
| 15 | Nur Planung ausgefüllt, Prüfergebnisse leer | 13 | 6 | 0 |
| 16 | Nur Buchwert ausgefüllt | 13 | 11 | 0 |
| 17 | TE = AE (erwartete Fehlerquote 2 %): Nenner null | 13 | 0 | 0 |
| 18 | Knapp unter TE = AE (1,99 %) | 13 | 0 | 0 |
| 19 | Knapp über TE = AE (2,01 %): negativer Nenner wird quadriert | 13 | 0 | 0 |
| 20 | Rechnerischer Umfang unter 30: Mindestumfang 30 | 13 | 0 | 0 |
| 21 | Rechnerischer Umfang genau 100 (95 %) | 13 | 0 | 0 |
| 22 | Rechnerischer Umfang genau 30 | 13 | 0 | 0 |
| 23 | Rechnerischer Umfang knapp über 30: 31 | 13 | 0 | 0 |
| 24 | Erwartete Fehlerquote 0 eingetragen | 13 | 0 | 0 |
| 25 | Keine Fehler in der Stichprobe (Nullen eingetragen) | 13 | 0 | 0 |
| 26 | Buchwert 0: Division durch null | 13 | 0 | 0 |
| 27 | Umfang der Grundgesamtheit 0 | 13 | 0 | 0 |
| 28 | Fehler zugunsten des Haushalts überwiegen (negativer Stichprobenfehler) | 13 | 0 | 0 |

## X3_DiffSch_S_2017

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 80 | 2880 | 2700 | 176 | 4 | 0 | 0 | 0 | 0 |
| abnahme-luecken | 16 | 576 | 412 | 164 | 0 | 0 | 0 | 0 | 0 |
| Hauptsatz | 35 | 1260 | 1029 | 231 | 0 | 0 | 0 | 0 | 0 |
| teilbelegung | 3 | 108 | 97 | 11 | 0 | 0 | 0 | 0 | 0 |
| zufall | 100 | 3600 | 3600 | 0 | 0 | 0 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall, drei Schichten, Konfidenzniveau 90 % | 36 | 0 | 0 |
| 2 | Konfidenzniveau 60 % | 36 | 0 | 0 |
| 3 | Konfidenzniveau 70 % | 36 | 0 | 0 |
| 4 | Konfidenzniveau 80 % | 36 | 0 | 0 |
| 5 | Konfidenzniveau 95 % | 36 | 0 | 0 |
| 6 | Leeres Formular | 36 | 8 | 0 |
| 7 | Eine Schicht (Spalte E) | 36 | 0 | 0 |
| 8 | Nur Schicht k (Spalte K) | 36 | 0 | 0 |
| 9 | Sieben Schichten (alle Spalten der Vorlage) | 36 | 0 | 0 |
| 10 | Leere Schicht zwischen belegten (E, G, K) | 36 | 0 | 0 |
| 11 | Alles ausgefüllt außer D9 | 36 | 22 | 0 |
| 12 | Alles ausgefüllt außer D11 | 36 | 22 | 0 |
| 13 | Ohne Stichprobeneinheit (D2 wird nicht gelesen) | 36 | 0 | 0 |
| 14 | Sieben Schichten, Buchwerte der Schichten leer (Zeile 6) | 36 | 6 | 0 |
| 15 | Sieben Schichten, σ der Planung leer (Zeile 8) | 36 | 30 | 0 |
| 16 | Sieben Schichten, Ausgaben der Stichprobe leer (Zeile 18 wird nicht gelesen) | 36 | 0 | 0 |
| 17 | Sieben Schichten, Fehler der Stichprobe leer (Zeile 19) | 36 | 19 | 0 |
| 18 | Sieben Schichten, s der Stichprobe leer (Zeile 21) | 36 | 0 | 0 |
| 19 | Sieben Schichten, nur Planung ausgefüllt | 36 | 19 | 0 |
| 20 | Fehlende Angabe in nur einer Schicht: Buchwert F6 | 36 | 25 | 0 |
| 21 | Fehlende Angabe in nur einer Schicht: σ der Planung F8 | 36 | 22 | 0 |
| 22 | Fehlende Angabe in nur einer Schicht: Fehler F19 | 36 | 0 | 0 |
| 23 | Fehlende Angabe in nur einer Schicht: s der Stichprobe F21 | 36 | 0 | 0 |
| 24 | Schicht nur mit Buchwert, ohne Umfang (H6) | 36 | 23 | 0 |
| 25 | Schicht nur mit Umfang (H7) | 36 | 28 | 0 |
| 26 | Schichtumfänge heben beim Aufrunden die Summe über den Gesamtumfang | 36 | 0 | 0 |
| 27 | TE = AE (erwartete Fehlerquote 2 %): Nenner null | 36 | 0 | 0 |
| 28 | Knapp unter TE = AE (1,99 %) | 36 | 0 | 0 |
| 29 | Knapp über TE = AE (2,01 %): negativer Nenner wird quadriert | 36 | 0 | 0 |
| 30 | Rechnerischer Umfang unter 30: Mindestumfang 30 | 36 | 0 | 0 |
| 31 | Rechnerischer Umfang genau 100 (95 %, eine Schicht) | 36 | 0 | 0 |
| 32 | Erwartete Fehlerquote 0 eingetragen | 36 | 0 | 0 |
| 33 | Keine Fehler in der Stichprobe (Nullen eingetragen) | 36 | 0 | 0 |
| 34 | Schicht mit Umfang 0 | 36 | 0 | 0 |
| 35 | Nur Konfidenzniveau und erwartete Fehlerquote ausgefüllt | 36 | 7 | 0 |

## X4_DiffSch_2Z_2017

| Fallsatz | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | bewusst anders dargestellt | amtlicher Begriff | bewusst nach DelVO | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abnahme-grund | 80 | 1600 | 1535 | 61 | 4 | 0 | 0 | 0 | 0 |
| abnahme-luecken | 20 | 400 | 281 | 119 | 0 | 0 | 0 | 0 | 0 |
| Hauptsatz | 38 | 760 | 623 | 137 | 0 | 0 | 0 | 0 | 0 |
| teilbelegung | 3 | 60 | 47 | 13 | 0 | 0 | 0 | 0 | 0 |
| zufall | 100 | 2000 | 2000 | 0 | 0 | 0 | 0 | 0 | 0 |

| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Standardfall, Konfidenzniveau 90 % | 20 | 0 | 0 |
| 2 | Konfidenzniveau 60 % | 20 | 0 | 0 |
| 3 | Konfidenzniveau 70 % | 20 | 0 | 0 |
| 4 | Konfidenzniveau 80 % | 20 | 0 | 0 |
| 5 | Konfidenzniveau 95 % | 20 | 0 | 0 |
| 6 | Leeres Formular | 20 | 8 | 0 |
| 7 | Nur der erste Zeitraum ausgefüllt | 20 | 5 | 0 |
| 8 | Nur Planung des ersten Zeitraums ausgefüllt | 20 | 5 | 0 |
| 9 | Alles ausgefüllt außer C3 | 20 | 18 | 0 |
| 10 | Alles ausgefüllt außer C4 | 20 | 14 | 0 |
| 11 | Alles ausgefüllt außer C5 | 20 | 4 | 0 |
| 12 | Alles ausgefüllt außer C6 | 20 | 12 | 0 |
| 13 | Alles ausgefüllt außer C7 | 20 | 12 | 0 |
| 14 | Alles ausgefüllt außer C8 | 20 | 12 | 0 |
| 15 | Alles ausgefüllt außer C10 | 20 | 4 | 0 |
| 16 | Alles ausgefüllt außer C12 | 20 | 12 | 0 |
| 17 | Alles ausgefüllt außer C21 | 20 | 0 | 0 |
| 18 | Alles ausgefüllt außer C22 | 20 | 8 | 0 |
| 19 | Alles ausgefüllt außer C23 | 20 | 1 | 0 |
| 20 | Alles ausgefüllt außer C25 | 20 | 12 | 0 |
| 21 | Alles ausgefüllt außer C26 | 20 | 1 | 0 |
| 22 | Alles ausgefüllt außer C27 | 20 | 9 | 0 |
| 23 | Alles ausgefüllt außer C34 | 20 | 0 | 0 |
| 24 | Alles ausgefüllt außer C35 | 20 | 0 | 0 |
| 25 | Ohne Stichprobeneinheit und Buchwerte der Stichproben (C2, C20, C33 werden nicht gelesen) | 20 | 0 | 0 |
| 26 | Negativer Nenner bei der Neuberechnung (hohe Streuung im ersten Zeitraum) | 20 | 0 | 0 |
| 27 | Negativer Nenner mit negativer Varianzsumme: Genauigkeit nicht bestimmbar | 20 | 0 | 0 |
| 28 | Nenner der Neuberechnung knapp über null | 20 | 0 | 0 |
| 29 | TE = AE im ersten Zeitraum (erwartete Fehlerquote 2 %): Nenner null | 20 | 0 | 0 |
| 30 | TE = AE im zweiten Zeitraum (erwartete Fehlerquote 2 %) | 20 | 0 | 0 |
| 31 | Erwartete Fehlerquote über der Wesentlichkeitsschwelle im ersten Zeitraum (2,5 %) | 20 | 0 | 0 |
| 32 | Erster Zeitraum ohne Fehler | 20 | 0 | 0 |
| 33 | Zweiter Zeitraum ohne Fehler | 20 | 0 | 0 |
| 34 | Erwartete Fehlerquoten 0 eingetragen | 20 | 0 | 0 |
| 35 | Rechnerischer Umfang genau 100 (95 %, gleiche Zeiträume) | 20 | 0 | 0 |
| 36 | Zweiter Zeitraum ohne Einheiten (C26 = 0) | 20 | 0 | 0 |
| 37 | Umfänge der Grundgesamtheit 0 | 20 | 0 | 0 |
| 38 | Sehr kleine Stichprobe (kein Mindestumfang in der Vorlage) | 20 | 0 | 0 |
