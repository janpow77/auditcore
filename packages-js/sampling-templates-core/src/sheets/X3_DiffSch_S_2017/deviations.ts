/**
 * Begründete Abweichungen des Blatts X3 vom Verhalten der Vorlage bei leeren
 * Eingaben. Die Altvorlage rechnet mit jeder leeren Zelle als 0 weiter; die
 * Webfassung zeigt „Angabe fehlt“ (`null`), nie einen anderen Wert. Für eine
 * belegte Schicht (Buchwert, Umfang oder σ der Planung eingetragen) sind alle
 * drei Angaben Pflicht, für die Hochrechnung auch der Fehler der Stichprobe –
 * solange keine belegte Schicht einen trägt. Die Abweichungen gelten für alle
 * Schichtspalten des Blatts (E–K der Vorlage und AA–AM der Webfassung); jede
 * Zeile ist durch einen Golden-Fall in einer Schichtspalte belegt
 * (test/deviations.spec.ts).
 *
 * Keine Abweichung, sondern wie in der Vorlage mit 0 gerechnet und ausgewiesen
 * (`zeroAssumed`): die Standardabweichung der Stichprobe (Zeile 21) und der
 * Fehler der Stichprobe einer Schicht (Zeile 19), wenn eine andere Schicht
 * einen trägt.
 *
 * Ohne Grundlage (`withoutBasis`): Trägt keine Schicht einen hochgerechneten
 * Fehler (Zeile 22) – leeres Formular oder kein Stichprobenumfang, etwa bei
 * TE = AE –, zeigt die Vorlage als Summe 0 und rechnet damit weiter.
 */
import { stratumCell } from '../../model/strata'
import type { Deviation } from '../../model/types'
import { LEGACY_STRATA, deviationRows, unfoundedRows } from '../shared/legacy'

/** Zellen einer Schichtzeile in allen Schichtspalten des Blatts. */
const row = (number: number): string[] => LEGACY_STRATA.map((column) => stratumCell(column, number))

const BOOK_VALUES = row(6)
const UNITS = row(7)
const DEVIATIONS = row(8)
const SIZE_INPUTS = ['D9', 'D11', ...BOOK_VALUES, ...UNITS, ...DEVIATIONS]
const STRATUM = 'Zu einer belegten Schicht gehören Buchwert, Umfang und Standardabweichung; fehlt eine Angabe, sind die Summen des Blatts nicht bestimmt.'
const SIZE = 'Ohne Konfidenzniveau, erwartete Fehlerquote und die Angaben jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen.'

export const deviations: readonly Deviation[] = [
  ...deviationRows(['D1', 'D14', 'D30'], BOOK_VALUES, 'Wert ohne den Buchwert der Schicht mit fehlender Angabe', STRATUM),
  ...deviationRows(['D3'], UNITS, 'Summe ohne den Umfang der Schicht mit fehlender Angabe', STRATUM),
  ...deviationRows(['D4'], [...UNITS, ...DEVIATIONS], 'Wert ohne den Beitrag der Schicht mit fehlender Angabe', STRATUM),
  ...deviationRows(['D10'], ['D9'], '0 (keine Stufe des Konfidenzniveaus trifft zu; Excel zeigt FALSCH)', 'Ohne Konfidenzniveau gibt es keinen Koeffizienten z.'),
  ...deviationRows(['D12'], ['D11', ...BOOK_VALUES], '0 € bzw. Wert ohne den Buchwert der Schicht mit fehlender Angabe', 'Der voraussichtliche Fehler setzt die erwartete Fehlerquote und den Buchwert jeder belegten Schicht voraus.'),
  ...deviationRows(['D15', ...row(17), 'D26', 'D27'], SIZE_INPUTS, 'Wert auf Grundlage des mit 0 berechneten Umfangs (mindestens 30)', SIZE),
  ...deviationRows(
    [...row(20), ...row(22), 'D23', 'D24', 'D25', 'D28', 'D29'],
    [...SIZE_INPUTS, ...row(19)],
    'Hochrechnung mit einem Stichprobenfehler von 0 € bzw. auf Grundlage des mit 0 berechneten Umfangs',
    'Die Hochrechnung setzt den Stichprobenumfang und den Fehler der Stichprobe mindestens einer belegten Schicht voraus.',
  ),
  ...unfoundedRows(['D23'], row(22), '0 € (Summe über Schichten ohne hochgerechneten Fehler)', 'Trägt keine Schicht einen hochgerechneten Fehler, gibt es nichts zu summieren; eine Summe von 0 € sähe wie ein Ergebnis aus.'),
  ...unfoundedRows(
    ['D24', 'D25'],
    ['D23'],
    'Fehlerquote 0 % bzw. berichtigter Buchwert in Höhe des Buchwerts, gerechnet mit einem hochgerechneten Fehler von 0 €',
    'Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt.',
  ),
]
