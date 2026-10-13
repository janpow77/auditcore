# Abgleich der Rechenkerne mit der Vorlage

<!-- Erzeugt mit `npm run docs:write -w @auditcore/sampling-templates-core`; nicht von Hand ändern. -->

Je Fall werden die Eingaben in eine Kopie der Excel-Vorlage geschrieben, die Mappe wird mit LibreOffice
neu berechnet (`scripts/golden_recalc.py`), und jede Formelzelle des Blatts wird mit dem Rechenkern verglichen:
Zahlen mit relativer Toleranz 1e-9, Texte wortgleich. „Begründet“ sind Zellen, an denen die Webfassung bei
leeren Eingaben „Angabe fehlt“ zeigt, während die Vorlage mit 0 weiterrechnet ([abweichungen.md](abweichungen.md)).

| Blatt | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | unbegründete Abweichungen (Soll 0) |
|---|---:|---:|---:|---:|---:|
| 02_Grundgesamtheit | 21 | 399 | 375 | 24 | 0 |
| 03_MUS_1Z | 198 | 7524 | 7316 | 208 | 0 |
| 04_MUS_1Z_S | 27 | 3294 | 2914 | 380 | 0 |
| 17_Unterstichprobe | 16 | 96 | 92 | 4 | 0 |

## 02_Grundgesamtheit

| Nr. | Fall | Zellen | begründet | unbegründet |
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

| Nr. | Fall | Zellen | begründet | unbegründet |
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
| 41 | Raster hoch 60 % zweiseitig | 38 | 0 | 0 |
| 42 | Raster hoch 60 % einseitig | 38 | 0 | 0 |
| 43 | Raster hoch 70 % zweiseitig | 38 | 0 | 0 |
| 44 | Raster hoch 70 % einseitig | 38 | 0 | 0 |
| 45 | Raster hoch 80 % zweiseitig | 38 | 0 | 0 |
| 46 | Raster hoch 80 % einseitig | 38 | 0 | 0 |
| 47 | Raster hoch 90 % zweiseitig | 38 | 0 | 0 |
| 48 | Raster hoch 90 % einseitig | 38 | 0 | 0 |
| 49 | Raster hoch 95 % zweiseitig | 38 | 0 | 0 |
| 50 | Raster hoch 95 % einseitig | 38 | 0 | 0 |
| 51 | Raster mittel 60 % zweiseitig | 38 | 0 | 0 |
| 52 | Raster mittel 60 % einseitig | 38 | 0 | 0 |
| 53 | Raster mittel 70 % zweiseitig | 38 | 0 | 0 |
| 54 | Raster mittel 70 % einseitig | 38 | 0 | 0 |
| 55 | Raster mittel 80 % zweiseitig | 38 | 0 | 0 |
| 56 | Raster mittel 80 % einseitig | 38 | 0 | 0 |
| 57 | Raster mittel 90 % zweiseitig | 38 | 0 | 0 |
| 58 | Raster mittel 90 % einseitig | 38 | 0 | 0 |
| 59 | Raster mittel 95 % zweiseitig | 38 | 0 | 0 |
| 60 | Raster mittel 95 % einseitig | 38 | 0 | 0 |
| 61 | Raster gering 60 % zweiseitig | 38 | 0 | 0 |
| 62 | Raster gering 60 % einseitig | 38 | 0 | 0 |
| 63 | Raster gering 70 % zweiseitig | 38 | 0 | 0 |
| 64 | Raster gering 70 % einseitig | 38 | 0 | 0 |
| 65 | Raster gering 80 % zweiseitig | 38 | 0 | 0 |
| 66 | Raster gering 80 % einseitig | 38 | 0 | 0 |
| 67 | Raster gering 90 % zweiseitig | 38 | 0 | 0 |
| 68 | Raster gering 90 % einseitig | 38 | 0 | 0 |
| 69 | Raster gering 95 % zweiseitig | 38 | 0 | 0 |
| 70 | Raster gering 95 % einseitig | 38 | 0 | 0 |
| 71 | G01 TE = AE exakt | 38 | 0 | 0 |
| 72 | G02 TE knapp über AE (1,99 %) | 38 | 0 | 0 |
| 73 | G03 TE sehr knapp über AE (n > 1e9) | 38 | 0 | 0 |
| 74 | G04 TE extrem knapp über AE (n > 2^53) | 38 | 0 | 0 |
| 75 | G05 AE knapp über TE | 38 | 0 | 0 |
| 76 | G06 AE = TE, begrenzt zulässig | 38 | 0 | 0 |
| 77 | G07 AE = 0 ausdrücklich | 38 | 0 | 0 |
| 78 | G08 σ = 0 ausdrücklich | 38 | 0 | 0 |
| 79 | G09 σ negativ | 38 | 0 | 0 |
| 80 | G10 Schwelle 0 ausdrücklich | 38 | 0 | 0 |
| 81 | G11 Schwelle 2,0000001 % (knapp unzulässig) | 38 | 0 | 0 |
| 82 | G12 Schwelle 1,99 % | 38 | 0 | 0 |
| 83 | P01 sehr kleine GG: BV 100 €, N 5 | 38 | 0 | 0 |
| 84 | P02 BV 0,01 € | 38 | 0 | 0 |
| 85 | P03 BV 9,99e14 € | 38 | 0 | 0 |
| 86 | P04 BV 1e18 € | 38 | 0 | 0 |
| 87 | P05 N kleiner als errechneter Umfang | 38 | 0 | 0 |
| 88 | P06 N = 1, σ groß (n » N) | 38 | 0 | 0 |
| 89 | P07 BV 0 ausdrücklich | 38 | 0 | 0 |
| 90 | P08 BV 0 ausdrücklich, begrenzt zulässig | 38 | 0 | 0 |
| 91 | P09 BV negativ | 38 | 0 | 0 |
| 92 | P10 BV mit Cent-Bruch | 38 | 0 | 0 |
| 93 | L01 begrenzt Kat. 2, rechnerisch < 30 | 38 | 0 | 0 |
| 94 | L02 begrenzt Kat. 1, rechnerisch zwischen 30 und 50 | 38 | 0 | 0 |
| 95 | L03 begrenzt Kat. 3 unzulässig | 38 | 0 | 0 |
| 96 | L04 begrenzt + Art. 83 + Kat. 1 (30 hat Vorrang) | 38 | 0 | 0 |
| 97 | L05 Art. 83 Ja, begrenzt Nein | 38 | 0 | 0 |
| 98 | L06 begrenzt Ja, Kategorie leer | 38 | 0 | 0 |
| 99 | L07 begrenzt "ja" klein, Art. 83 "JA" groß | 38 | 0 | 0 |
| 100 | L08 Testart "EINSEITIG", Zuverlässigkeit "Gering" | 38 | 0 | 0 |
| 101 | L09 Kategorie 2 als Text | 38 | 0 | 0 |
| 102 | L10 begrenzt zulässig, rechnerisch genau 50 | 38 | 0 | 0 |
| 103 | L11 Kategorie 0 | 38 | 0 | 0 |
| 104 | I01 Iteration 1 Einheit | 38 | 0 | 0 |
| 105 | I02 Iteration negativ | 38 | 0 | 0 |
| 106 | I03 Iteration 0,4 | 38 | 0 | 0 |
| 107 | I04 Iteration leer | 38 | 0 | 0 |
| 108 | I05 n_s genau 3 | 38 | 0 | 0 |
| 109 | I06 n_s genau 2 | 38 | 0 | 0 |
| 110 | I07 n_e größer n (n_s negativ) | 38 | 0 | 0 |
| 111 | I08 BV_e größer BV (BV_s negativ) | 38 | 0 | 0 |
| 112 | I09 n_e = 0, BV_e = 0 | 38 | 0 | 0 |
| 113 | I10 n_e gebrochen 4,5 | 38 | 0 | 0 |
| 114 | S01 systembedingt groß (GFQ über Schwelle) | 38 | 0 | 0 |
| 115 | S02 anomal negativ | 38 | 0 | 0 |
| 116 | S03 nur systembedingt, einseitig | 38 | 0 | 0 |
| 117 | S04 nur anomal | 38 | 0 | 0 |
| 118 | S05 systembedingt und anomal leer | 38 | 0 | 0 |
| 119 | S06 fehlerfrei (0, 0, 0) | 38 | 0 | 0 |
| 120 | S07 Fehlerquotensumme 0, Fehler hochwertig > 0 | 38 | 0 | 0 |
| 121 | S08 s_r negativ | 38 | 0 | 0 |
| 122 | T01 GFQ rechnerisch genau 2 % (0,1+0,2)/15 | 38 | 0 | 0 |
| 123 | T02 GFQ genau 2 % glatt | 38 | 0 | 0 |
| 124 | T03 OFG genau 2 %, GFQ darunter | 38 | 0 | 0 |
| 125 | T04 Konfidenzniveau 65 % (nicht in Tabelle) | 38 | 0 | 0 |
| 126 | T05 Konfidenzniveau 65 %, begrenzt zulässig | 38 | 0 | 0 |
| 127 | T06 Konfidenzniveau 0,7000000000000001 | 38 | 0 | 0 |
| 128 | T07 Schwelle 0,020000000000000004 (0,1+0,2)/15 | 38 | 0 | 0 |
| 129 | T08 AE-Quote 0,30000000000000004 gegen Schwelle 0,3 | 38 | 0 | 0 |
| 130 | T09 Schwelle 0,30000000000000004 gegen AE-Quote 0,3 | 38 | 0 | 0 |
| 131 | R-nat 10² = 100, Gleitkomma über (100.00000000000004) | 38 | 0 | 0 |
| 132 | R-nat 10² = 100, Gleitkomma über (100.00000000000004) (2) | 38 | 0 | 0 |
| 133 | R-nat 10² = 100, Gleitkomma über (100.00000000000004) (3) | 38 | 0 | 0 |
| 134 | R-nat 10² = 100, Gleitkomma über (100.00000000000004) (4) | 38 | 0 | 0 |
| 135 | R-nat 20² = 400, Gleitkomma über (400.0000000000003) | 38 | 0 | 0 |
| 136 | R-nat 20² = 400, Gleitkomma über (400.00000000000045) | 38 | 0 | 0 |
| 137 | R-nat 10² = 100, Gleitkomma unter (99.9999999999999) | 38 | 0 | 0 |
| 138 | R-nat 10² = 100, Gleitkomma unter (99.99999999999993) | 38 | 0 | 0 |
| 139 | R-nat 10² = 100, Gleitkomma unter (99.99999999999986) | 38 | 0 | 0 |
| 140 | R-nat 10² = 100, Gleitkomma unter (99.9999999999999) (2) | 38 | 0 | 0 |
| 141 | R-nat 10² = 100, Gleitkomma unter (99.9999999999999) (3) | 38 | 0 | 0 |
| 142 | R-nat 20² = 400, Gleitkomma unter (399.9999999999996) | 38 | 0 | 0 |
| 143 | R-off 100 · (1 + 0) → Rohwert 100 | 38 | 0 | 0 |
| 144 | R-off 100 · (1 + 3e-16) → Rohwert 100.00000000000004 | 38 | 0 | 0 |
| 145 | R-off 100 · (1 + 1e-14) → Rohwert 100.000000000001 | 38 | 0 | 0 |
| 146 | R-off 100 · (1 + 1e-13) → Rohwert 100.00000000000999 | 38 | 0 | 0 |
| 147 | R-off 100 · (1 + 1e-12) → Rohwert 100.00000000010004 | 38 | 0 | 0 |
| 148 | R-off 100 · (1 + 1e-11) → Rohwert 100.00000000100002 | 38 | 0 | 0 |
| 149 | R-off 100 · (1 + 5e-10) → Rohwert 100.00000005000004 | 38 | 0 | 0 |
| 150 | R-off 100 · (1 + 2e-9) → Rohwert 100.00000019999999 | 38 | 0 | 0 |
| 151 | R-off 100 · (1 + 1e-7) → Rohwert 100.00001000000002 | 38 | 0 | 0 |
| 152 | R-off 1000000 · (1 + 5e-10) → Rohwert 1000000.0005000002 | 38 | 0 | 0 |
| 153 | R-off 1000000 · (1 + 1e-7) → Rohwert 1000000.1000000002 | 38 | 0 | 0 |
| 154 | R-off 1000 · (1 + -1e-15) → Rohwert 999.9999999999991 | 38 | 0 | 0 |
| 155 | R-off 1000 · (1 + -1e-12) → Rohwert 999.999999999 | 38 | 0 | 0 |
| 156 | R-off 39 · (1 + 1e-10) → Rohwert 39.0000000039 | 38 | 0 | 0 |
| 157 | E01 BV leer, begrenzt zulässig, sonst vollständig | 38 | 14 | 0 |
| 158 | E02 Schwelle leer, begrenzt zulässig | 38 | 1 | 0 |
| 159 | E03 σ leer, TE ≤ AE, begrenzt zulässig | 38 | 0 | 0 |
| 160 | E04 σ und Fehlerquote leer | 38 | 21 | 0 |
| 161 | E05 Konfidenzniveau und σ leer, begrenzt zulässig | 38 | 0 | 0 |
| 162 | E06 σ leer, Art. 83 begrenzt | 38 | 20 | 0 |
| 163 | E07 Fehlerquote leer, begrenzt unzulässig | 38 | 21 | 0 |
| 164 | E08 s_r leer, sonst vollständig | 38 | 0 | 0 |
| 165 | E09 Testart geleert | 38 | 0 | 0 |
| 166 | E10 Zuverlässigkeit leer | 38 | 0 | 0 |
| 167 | E11 n_e leer, BV_e gesetzt | 38 | 0 | 0 |
| 168 | E12 BV_e leer, n_e gesetzt | 38 | 0 | 0 |
| 169 | E13 Fehler hochwertig leer | 38 | 0 | 0 |
| 170 | E14 σ leer und BV leer | 38 | 5 | 0 |
| 171 | E15 nur BV und σ | 38 | 2 | 0 |
| 172 | E16 Fehlerquote leer, TE-Zeile sonst vollständig, Art. 83 Nein, begrenzt Ja Kat. 1 | 38 | 21 | 0 |
| 173 | E17 Art. 83 und begrenzt geleert | 38 | 0 | 0 |
| 174 | N1 n_s negativ (n_e 95 > n 92) | 38 | 0 | 0 |
| 175 | N2 n_s genau 3 | 38 | 0 | 0 |
| 176 | N3 n_s genau 2 | 38 | 0 | 0 |
| 177 | N4 n_s = 0 | 38 | 0 | 0 |
| 178 | B-GFQ genau 2 % (Cent-Beträge), Gleitkomma darüber: (411130.9+1023471.01+353646.09)/89412400 = 0.020000000000000004 | 38 | 0 | 0 |
| 179 | B-GFQ genau 2 % (Cent-Beträge), Gleitkomma darüber: (279583.34+307396.02+130530.64)/35875500 = 0.020000000000000004 | 38 | 0 | 0 |
| 180 | B-GFQ genau 2 % (Cent-Beträge), Gleitkomma darüber: (1509931.11+881338.67+121031.22)/125615050 = 0.020000000000000004 | 38 | 0 | 0 |
| 181 | B-GFQ genau 2 % (Cent-Beträge), Gleitkomma darunter: (973194.82+27161.07+11270.11)/50581300 = 0.019999999999999997 | 38 | 0 | 0 |
| 182 | B-GFQ genau 2 % (Cent-Beträge), Gleitkomma darunter: (1857764.21+1114247.97+299948.82)/163598050 = 0.019999999999999997 | 38 | 0 | 0 |
| 183 | R2 100 · (1 + 2e-12) → Rohwert 100.00000000020002 | 38 | 0 | 0 |
| 184 | R2 100 · (1 + 4e-12) → Rohwert 100.00000000040001 | 38 | 0 | 0 |
| 185 | R2 100 · (1 + 6e-12) → Rohwert 100.00000000060002 | 38 | 0 | 0 |
| 186 | R2 100 · (1 + 8e-12) → Rohwert 100.0000000008 | 38 | 0 | 0 |
| 187 | R2 1000000 · (1 + 4e-13) → Rohwert 1000000.0000003998 | 38 | 0 | 0 |
| 188 | R2 1000000 · (1 + 6e-13) → Rohwert 1000000.0000006 | 38 | 0 | 0 |
| 189 | R2 1000000 · (1 + 2e-12) → Rohwert 1000000.000002 | 38 | 0 | 0 |
| 190 | R2 10000 · (1 + 4e-12) → Rohwert 10000.000000040001 | 38 | 0 | 0 |
| 191 | R2 10000 · (1 + 6e-12) → Rohwert 10000.000000059998 | 38 | 0 | 0 |
| 192 | R2 31 · (1 + 3e-12) → Rohwert 31.000000000093003 | 38 | 0 | 0 |
| 193 | R2 31 · (1 + 2e-11) → Rohwert 31.000000000620002 | 38 | 0 | 0 |
| 194 | R2 100 · (1 + -2e-12) → Rohwert 99.99999999980002 | 38 | 0 | 0 |
| 195 | R2 100 · (1 + -1e-9) → Rohwert 99.99999989999999 | 38 | 0 | 0 |
| 196 | R2 999999 · (1 + 4.9e-13) → Rohwert 999999.0000004901 | 38 | 0 | 0 |
| 197 | R2 123456 · (1 + 4e-12) → Rohwert 123456.00000049385 | 38 | 0 | 0 |
| 198 | R2 123456 · (1 + 6e-12) → Rohwert 123456.00000074075 | 38 | 0 | 0 |

## 04_MUS_1Z_S

| Nr. | Fall | Zellen | begründet | unbegründet |
|---:|---|---:|---:|---:|
| 1 | Drei Schichten, mittel 70 %, zweiseitig, Standardfall | 122 | 1 | 0 |
| 2 | Sieben Schichten (alle Spalten der Vorlage) | 122 | 1 | 0 |
| 3 | Eine Schicht | 122 | 1 | 0 |
| 4 | Zwei Schichten, gering 90 %, einseitig, systembedingte und anomale Fehler | 122 | 1 | 0 |
| 5 | Hoch 60 %, Art. 83 mit 30 Einheiten | 122 | 1 | 0 |
| 6 | Begrenzt zulässig Kategorie 1 (50 Einheiten) | 122 | 1 | 0 |
| 7 | Begrenzt beantragt, aber Kategorie 3 (unzulässig) | 122 | 1 | 0 |
| 8 | TE ≤ AE, Stichprobenumfang nicht bestimmbar | 122 | 4 | 0 |
| 9 | Hoch 95 % einseitig, fünf Schichten | 122 | 1 | 0 |
| 10 | Gering mit 60 %: Konfidenzniveau zu niedrig; Wesentlichkeitsschwelle 3 % | 122 | 1 | 0 |
| 11 | Weniger als 3 Einheiten in einer Zufallsschicht | 122 | 1 | 0 |
| 12 | Zufallsschicht ohne Einheiten in einer Schicht (n_hs = 0) | 122 | 1 | 0 |
| 13 | Iteration in zwei Schichten | 122 | 1 | 0 |
| 14 | Gesamtfehlerquote über der Wesentlichkeitsschwelle | 122 | 1 | 0 |
| 15 | GFQ unter, obere Fehlergrenze über der Schwelle | 122 | 1 | 0 |
| 16 | Lücke: Schicht 2 leer, Schichten 1 und 3 belegt | 122 | 1 | 0 |
| 17 | Leeres Formular (nur Vorgaben der Vorlage) | 122 | 2 | 0 |
| 18 | Teilweise: nur Buchwerte und Anzahlen der Schichten | 122 | 18 | 0 |
| 19 | Teilweise: sieben Schichten, Standardabweichungen fehlen | 122 | 86 | 0 |
| 20 | Teilweise: sieben Schichten, Standardabweichung nur in Schicht 4 fehlt | 122 | 80 | 0 |
| 21 | Teilweise: sieben Schichten, voraussichtliche Fehlerquote fehlt | 122 | 78 | 0 |
| 22 | Teilweise: Konfidenzniveau fehlt | 122 | 4 | 0 |
| 23 | Teilweise: Prüfergebnisse fehlen | 122 | 1 | 0 |
| 24 | Teilweise: Standardabweichung der Stichprobe fehlt in einer Schicht | 122 | 1 | 0 |
| 25 | Teilweise: Wesentlichkeitsschwelle und Vorgaben geleert | 122 | 5 | 0 |
| 26 | Teilweise: begrenzt zulässig, Standardabweichungen fehlen | 122 | 86 | 0 |
| 27 | Blatt 02 ausgefüllt: Abweichung zur angepassten Grundgesamtheit | 122 | 0 | 0 |

## 17_Unterstichprobe

| Nr. | Fall | Zellen | begründet | unbegründet |
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
