/**
 * Begründete Abweichungen des Blatts X1 vom Verhalten der Vorlage bei leeren
 * Eingaben. Die Altvorlage rechnet mit jeder leeren Zelle als 0 weiter; fehlt
 * eine Pflichteingabe, zeigt die Webfassung „Angabe fehlt“ (`null`), nie einen
 * anderen Wert. Sind alle Pflichteingaben vorhanden, zeigt sie, was die Vorlage
 * zeigt – fragwürdige Ergebnisse mit Hinweis in Warnfarbe. Jede Zeile
 * nennt genau die Eingaben, deren Fehlen die Vorlage einen Wert zeigen lässt,
 * und ist durch einen Golden-Fall belegt (test/deviations.spec.ts). Fehlt der
 * Buchwert (C1), zeigt auch die Vorlage ab C11 keinen Wert (Division durch null).
 */
import type { Deviation } from '../../model/types'
import { deviationRows } from '../shared/legacy'

const SIZE = 'Ohne Konfidenzniveau und erwartete Fehlerquote ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen.'
const RESULTS = 'Die Hochrechnung setzt den Stichprobenumfang und die Fehler der Stichprobe voraus.'

export const deviations: readonly Deviation[] = [
  ...deviationRows(['C5', 'C6'], ['C4'], '0 (keine Stufe des Konfidenzniveaus trifft zu; Excel zeigt FALSCH)', 'Ohne Konfidenzniveau gibt es keinen Zuverlässigkeits- und keinen Erweiterungsfaktor.'),
  ...deviationRows(['C8'], ['C1', 'C7'], '0 € (leere Zelle zählt als 0)', 'Der voraussichtliche Fehler setzt Buchwert und erwartete Fehlerquote voraus.'),
  ...deviationRows(['C10'], ['C1'], '0 € (leere Zelle zählt als 0)', 'Der zulässige Fehler setzt den Buchwert voraus.'),
  ...deviationRows(['C11', 'C12', 'C15'], ['C4', 'C7'], 'Wert auf Grundlage des mit RF = 0 bzw. AE = 0 berechneten Umfangs (z. B. Mindestumfang 30)', SIZE),
  ...deviationRows(['C17', 'C18'], ['C4', 'C7', 'C16'], 'Genauigkeit mit Incremental Allowance = 0 bzw. auf Grundlage des mit 0 berechneten Umfangs', 'Die Genauigkeit setzt den Stichprobenumfang und die Incremental Allowance voraus.'),
  ...deviationRows(['C19', 'C21'], ['C4', 'C7', 'C13', 'C14'], 'Hochrechnung mit Fehlern = 0 bzw. auf Grundlage des mit 0 berechneten Umfangs', RESULTS),
  ...deviationRows(['C20', 'C22'], ['C4', 'C7', 'C13', 'C14', 'C16'], 'Obere Fehlergrenze mit Fehlern bzw. Incremental Allowance = 0 oder auf Grundlage des mit 0 berechneten Umfangs', RESULTS),
]
