/**
 * Begründete Abweichungen des Blatts 02 bei leeren Eingaben: Die Webfassung
 * zeigt „Angabe fehlt“, wo die Vorlage mit 0 weiterrechnet. Wichtig für den
 * Kontextfluss: Ein leeres Blatt 02 liefert den Methodenblättern keinen
 * Buchwert 0, sondern keinen Wert.
 */
import type { CellAddress, Deviation } from '../../model/types'

function entries(cells: readonly CellAddress[], whenEmpty: readonly CellAddress[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

const CLAIM = 'Ohne den Betrag laut SFC2021 bzw. laut Datenbestand gibt es nichts abzustimmen; eine Differenz gegen 0 wäre irreführend.'
const RECORDS = 'Ohne die Datensätze mit positivem Wert ist die Grundgesamtheit unbekannt, nicht null.'

export const deviations: readonly Deviation[] = [
  ...entries(['C17'], ['C15', 'C16'], 'Differenz gegen 0 (leere Zelle zählt als 0)', CLAIM),
  ...entries(['C22', 'C30'], ['C16'], 'Betrag bzw. Differenz auf Grundlage von 0 €', CLAIM),
  ...entries(['C37', 'C39', 'C51'], ['C25'], '0 € bzw. nur die TH-Pauschale', RECORDS),
  ...entries(['C38', 'C52'], ['C24'], '0 Einheiten', RECORDS),
  ...entries(['C53', 'C54'], ['C24'], 'Prüfhinweis und Mindestumfang auf Grundlage von 0 Einheiten abzüglich der Abzüge (bei vorhandenen Abzügen eine negative Anzahl, z. B. „✔ weniger als 300 Einheiten“ und Mindestumfang −1)', RECORDS),
]
