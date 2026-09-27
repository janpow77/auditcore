# Donut-Training: Verlauf der Ergebnisse

Stand 2026-09-27 · erzeugt mit `tools/donut_verlauf.py` aus den Läufen auf janpow-ai (Kennzahlen: `docs/donut-verlauf/kennzahlen.json`). Hintergrund, Datensätze und Aufrufe: [training.md](training.md).

## Vergleichbarkeit

- **Stufe 0** ist das unveränderte Donut-CORD-Modell (`naver-clova-ix/donut-cord-v2`); es kennt das Rechnungsschema nicht und dient nur als Nullpunkt.
- **Pilot** und **Volllauf** wurden auf **unterschiedlichen Testsätzen** bewertet: der Pilot auf den Testsätzen des Pilot-Datensatzes (T1 163 / T2 100 Belege), alle späteren Stufen auf denen des Vollsatzes (T1 1 121 / T2 500 Belege). Beide stammen aus demselben Generator, sind aber verschiedene Belege; Unterschiede von wenigen Prozentpunkten zwischen Pilot und Volllauf sind deshalb nicht belastbar.
- T1 = synthetische Belege aus den Trainingsvorlagen, T2 = Layouts und Schriften, die im Training nie vorkamen. Für die Praxis zählt T2.
- Abnahme (Entscheidung E6): Pflichtfelder mit Mindestgenauigkeit, zusätzlich höchstens 0,5 % Falschwerte nach Plausibilitätsprüfung je Feld. Die Bewertung (`train/evaluate.py`) läuft derzeit **ohne** Plausibilitätsprüfung; das zweite Kriterium ist deshalb nicht gemessen, geprüft wird nur die Feldgenauigkeit.

## Stufen

| Stufe | Lauf | Karte | Datensatz | Bildgröße | Batch × Akk. | Seed | Epochen | Schritte | Dauer | Loss Start → Ende |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 · Donut-CORD | – | – | – | – | – | – | – | – | – | – |
| 1 · Pilot | `6cb8d70e0befc10e-0` | RTX 5070 Ti | Pilot | 1280×960 | 4 × 2 | 42 | 3 | 675 / 675 | 0,3 h | 11,64 → 0,1133 |
| 2 · Volllauf 1 | `2835be42bd3c1e1a-0` | RTX 5070 Ti | Voll | 1280×960 | 4 × 2 | 42 | 6 | 16 866 / 16 866 | 7,7 h | 11,55 → 0,0018 |
| 3 · Große Bilder, Lauf 1 | `17565fffc1110197-0` | RTX 5070 Ti | Voll | 1536×1152 | 2 × 4 | 42 | 6 | 36 / 9 000 | 0,0 h | 11,06 → 10,0569 |
| 3 · Große Bilder, Lauf 2 | `a476eca68cb5367f-1` | RTX 5060 Ti | Voll | 1536×1152 | 2 × 4 | 43 | 6 | 21 / 5 500 | 0,0 h | 11,10 → 11,0516 |

![Loss-Verlauf](donut-verlauf/loss.svg)

## Kernzahlen auf den Pilot-Testsätzen (T1 163 / T2 100 Belege)

| Stufe | Belegquote T1 | Belegquote T2 | s/Seite (T2) | Abnahme T1 | Abnahme T2 |
|---|---|---|---|---|---|
| 0 · Donut-CORD | 0,0 % | 0,0 % | 0,64 | nein | nein |
| 1 · Pilot | 40,5 % | 13,0 % | 0,27 | nein | nein |

Belegquote = Anteil der Belege, bei denen **alle fünf Pflichtfelder** stimmen (Gesamtbetrag, Rechnungsdatum, Rechnungsnummer, IBAN, USt-IdNr.).

## Kernzahlen auf den Voll-Testsätzen (T1 1121 / T2 500 Belege)

| Stufe | Belegquote T1 | Belegquote T2 | s/Seite (T2) | Abnahme T1 | Abnahme T2 |
|---|---|---|---|---|---|
| 0 · Donut-CORD | 0,0 % | 0,0 % | 0,72 | nein | nein |
| 2 · Volllauf 1 | 89,9 % | 36,2 % | 0,42 | nein | nein |

Belegquote = Anteil der Belege, bei denen **alle fünf Pflichtfelder** stimmen (Gesamtbetrag, Rechnungsdatum, Rechnungsnummer, IBAN, USt-IdNr.).

## Feldgenauigkeit T2 neue Layouts

| Feld | Schwelle | 1 · Pilot¹ | 2 · Volllauf 1 |
|---|---|---|---|
| Gesamtbetrag (Pflicht) | 98 % | 66,0 % | 80,8 % |
| Rechnungsdatum (Pflicht) | 98 % | 53,0 % | 89,8 % |
| Rechnungsnummer (Pflicht) | 95 % | 53,0 % | 90,2 % |
| IBAN (Pflicht) | 97 % | 16,5 % | 40,9 % |
| USt-IdNr. (Pflicht) | 97 % | 45,4 % | 70,8 % |
| Lieferant | – | 89,0 % | 93,2 % |
| Nettobetrag | – | 78,0 % | 85,2 % |
| Steuerbetrag | – | 69,4 % | 87,7 % |
| Steuersätze | – | 85,9 % | 94,3 % |
| Fälligkeit | – | 60,0 % | 86,2 % |
| Leistungsdatum | – | 50,0 % | 76,0 % |
| BIC | – | 32,0 % | 35,5 % |

Fett = Abnahmeschwelle erreicht. ¹ Pilot-Testsatz (andere, kleinere Stichprobe).

![Feldgenauigkeit T2 neue Layouts](donut-verlauf/felder-t2.svg)

## Feldgenauigkeit T1 synthetisch

| Feld | Schwelle | 1 · Pilot¹ | 2 · Volllauf 1 |
|---|---|---|---|
| Gesamtbetrag (Pflicht) | 98 % | 72,0 % | **99,2 %** |
| Rechnungsdatum (Pflicht) | 98 % | 96,7 % | **99,6 %** |
| Rechnungsnummer (Pflicht) | 95 % | 85,3 % | **98,7 %** |
| IBAN (Pflicht) | 97 % | 50,7 % | 93,6 % |
| USt-IdNr. (Pflicht) | 97 % | 85,3 % | 95,9 % |
| Lieferant | – | 97,5 % | 100,0 % |
| Nettobetrag | – | 85,5 % | 98,8 % |
| Steuerbetrag | – | 72,2 % | 98,9 % |
| Steuersätze | – | 95,4 % | 99,7 % |
| Fälligkeit | – | 97,3 % | 99,4 % |
| Leistungsdatum | – | 97,3 % | 99,7 % |
| BIC | – | 74,3 % | 78,9 % |

Fett = Abnahmeschwelle erreicht. ¹ Pilot-Testsatz (andere, kleinere Stichprobe).

## Fehlerbild der Pflichtfelder auf T2 (2 · Volllauf 1)

| Feld | erwartet | richtig | fehlt | falsch | davon erfunden |
|---|---|---|---|---|---|
| Gesamtbetrag | 500 | 404 (81 %) | 72 (14 %) | 24 (5 %) | 24 (5 %) |
| Rechnungsdatum | 500 | 449 (90 %) | 27 (5 %) | 24 (5 %) | 3 (1 %) |
| Rechnungsnummer | 500 | 451 (90 %) | 29 (6 %) | 20 (4 %) | 13 (3 %) |
| IBAN | 487 | 199 (41 %) | 272 (56 %) | 16 (3 %) | 16 (3 %) |
| USt-IdNr. | 487 | 345 (71 %) | 38 (8 %) | 104 (21 %) | 105 (22 %) |

Fehlt = kein Wert ausgegeben. Falsch = Wert ausgegeben, aber nicht der erwartete. Erfunden = ausgegebener Wert, der in keinem erwarteten Feld dieses Belegs vorkommt. Ein fehlender Wert ist für die Prüfung harmloser als ein falscher, weil er auffällt.

## Stufe 3: Läufe mit großen Bildern (1536×1152)

- 3 · Große Bilder, Lauf 1 (`17565fffc1110197-0`): noch nicht bewertet, Training laeuft, 36 von 9 000 Schritten.
- 3 · Große Bilder, Lauf 2 (`a476eca68cb5367f-1`): noch nicht bewertet, Training laeuft, 21 von 5 500 Schritten.

Ohne Bewertung: `17565fffc1110197-0`, `a476eca68cb5367f-1`.
