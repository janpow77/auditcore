/**
 * Blatt X1a_RF_2017 als Daten: Tabelle der Zuverlässigkeitsfaktoren der Vorlage
 * von 2017 (Template 1.1) zum konservativen MUS-Ansatz – je Anzahl der Fehler
 * (0 bis 50, Zeilen 3–53) und Risiko der irrtümlichen Annahme (Spalten B–K).
 * Das Blatt hat keine Eingaben und keine Formeln: 574 belegte Zellen, davon
 * drei Texte (A1, B1 und der Hinweis in M1). Blatt X1 liest die Tabelle nicht;
 * seine Faktoren für null Fehler stehen als feste Stufen in X1!C5.
 *
 * Die Werte sind aus der Vorlage gelesen; `test/legacy.spec.ts` vergleicht
 * alle 574 Zellen mit der Arbeitsmappe, sobald sie bereitliegt.
 *
 * `table` gibt dieselben Daten als Nachschlagetabelle aus (`DataTable`), die
 * sich ohne Kenntnis des Blatts anzeigen lässt.
 */
import { FormulaError, eq } from '../../excel/index'
import type { CellAddress, CellValue } from '../../model/types'
import { LEGACY_NOTICE, LEGACY_NOTICE_LABEL, type DataTable, type DataTableColumn } from '../shared/legacy'

/** Spaltenkopf A1 und Tabellenkopf B1, wörtlich mit dem Leerzeichen am Ende. */
export const ERRORS_LABEL = 'Number of errors '
export const RISK_LABEL = 'Risk of incorrect acceptation '

/** Spalten der Risikostufen (B2–K2). */
export const RISK_COLUMNS: readonly string[] = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']

/** Erste Zeile der Faktoren (Anzahl der Fehler 0). */
export const FIRST_ROW = 3

/** Risiko der irrtümlichen Annahme je Spalte (B2–K2); das Konfidenzniveau ist 1 − Risiko. */
export const RISK_LEVELS: readonly number[] = [0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.37, 0.4, 0.5]

/** Zuverlässigkeitsfaktoren: Zeile = Anzahl der Fehler (0–50), Spalte = Risikostufe (B3–K53). */
export const RELIABILITY_FACTORS: readonly (readonly number[])[] = [
  [4.61, 3, 2.3, 1.9, 1.61, 1.39, 1.2, 0.99, 0.92, 0.69],
  [6.64, 4.74, 3.89, 3.37, 2.99, 2.69, 2.44, 2.14, 2.02, 1.68],
  [8.41, 6.3, 5.32, 4.72, 4.28, 3.92, 3.62, 3.25, 3.11, 2.67],
  [10.05, 7.75, 6.68, 6.01, 5.52, 5.11, 4.76, 4.34, 4.18, 3.67],
  [11.6, 9.15, 7.99, 7.27, 6.72, 6.27, 5.89, 5.42, 5.24, 4.67],
  [13.11, 10.51, 9.27, 8.49, 7.91, 7.42, 7.01, 6.49, 6.29, 5.67],
  [14.57, 11.84, 10.53, 9.7, 9.08, 8.56, 8.11, 7.56, 7.34, 6.67],
  [16, 13.15, 11.77, 10.9, 10.23, 9.68, 9.21, 8.62, 8.39, 7.67],
  [17.4, 14.43, 12.99, 12.08, 11.38, 10.8, 10.3, 9.68, 9.43, 8.67],
  [18.78, 15.71, 14.21, 13.25, 12.52, 11.91, 11.39, 10.73, 10.48, 9.67],
  [20.14, 16.96, 15.41, 14.41, 13.65, 13.02, 12.47, 11.79, 11.52, 10.67],
  [21.49, 18.21, 16.6, 15.57, 14.78, 14.12, 13.55, 12.84, 12.55, 11.67],
  [22.82, 19.44, 17.78, 16.71, 15.9, 15.22, 14.62, 13.88, 13.59, 12.67],
  [24.14, 20.67, 18.96, 17.86, 17.01, 16.31, 15.7, 14.93, 14.62, 13.67],
  [25.45, 21.89, 20.13, 19, 18.13, 17.4, 16.77, 15.97, 15.66, 14.67],
  [26.74, 23.1, 21.29, 20.13, 19.23, 18.49, 17.83, 17.02, 16.69, 15.67],
  [28.03, 24.3, 22.45, 21.26, 20.34, 19.57, 18.9, 18.06, 17.72, 16.67],
  [29.31, 25.5, 23.61, 22.38, 21.44, 20.65, 19.96, 19.1, 18.75, 17.67],
  [30.58, 26.69, 24.76, 23.5, 22.54, 21.73, 21.02, 20.14, 19.78, 18.67],
  [31.85, 27.88, 25.9, 24.62, 23.63, 22.81, 22.08, 21.17, 20.81, 19.67],
  [33.1, 29.06, 27.05, 25.74, 24.73, 23.88, 23.14, 22.21, 21.84, 20.67],
  [34.35, 30.24, 28.18, 26.85, 25.82, 24.96, 24.2, 23.25, 22.87, 21.67],
  [35.6, 31.41, 29.32, 27.96, 26.91, 26.03, 25.25, 24.28, 23.89, 22.67],
  [36.84, 32.59, 30.45, 29.07, 28, 27.1, 26.31, 25.32, 24.92, 23.67],
  [38.08, 33.75, 31.58, 30.17, 29.08, 28.17, 27.36, 26.35, 25.95, 24.67],
  [39.31, 34.92, 32.71, 31.28, 30.17, 29.23, 28.41, 27.38, 26.97, 25.67],
  [40.53, 36.08, 33.84, 32.38, 31.25, 30.3, 29.46, 28.42, 28, 26.67],
  [41.76, 37.23, 34.96, 33.48, 32.33, 31.36, 30.52, 29.45, 29.02, 27.67],
  [42.98, 38.39, 36.08, 34.57, 33.41, 32.43, 31.56, 30.48, 30.04, 28.67],
  [44.19, 39.54, 37.2, 35.67, 34.49, 33.49, 32.61, 31.51, 31.07, 29.67],
  [45.4, 40.69, 38.32, 36.76, 35.56, 34.55, 33.66, 32.54, 32.09, 30.67],
  [46.61, 41.84, 39.43, 37.86, 36.64, 35.61, 34.71, 33.57, 33.11, 31.67],
  [47.81, 42.98, 40.54, 38.95, 37.71, 36.67, 35.75, 34.6, 34.14, 32.67],
  [49.01, 44.13, 41.65, 40.04, 38.79, 37.73, 36.8, 35.63, 35.16, 33.67],
  [50.21, 45.27, 42.76, 41.13, 39.86, 38.79, 37.84, 36.66, 36.18, 34.67],
  [51.41, 46.4, 43.87, 42.22, 40.93, 39.85, 38.89, 37.68, 37.2, 35.67],
  [52.6, 47.54, 44.98, 43.3, 42, 40.9, 39.93, 38.71, 38.22, 36.67],
  [53.79, 48.68, 46.08, 44.39, 43.07, 41.96, 40.98, 39.74, 39.24, 37.67],
  [54.98, 49.81, 47.19, 45.47, 44.14, 43.01, 42.02, 40.77, 40.26, 38.67],
  [56.16, 50.94, 48.29, 46.55, 45.2, 44.07, 43.06, 41.79, 41.28, 39.67],
  [57.35, 52.07, 49.39, 47.63, 46.27, 45.12, 44.1, 42.82, 42.3, 40.67],
  [58.53, 53.2, 50.49, 48.72, 47.33, 46.17, 45.14, 43.84, 43.32, 41.67],
  [59.71, 54.32, 51.59, 49.8, 48.4, 47.22, 46.18, 44.87, 44.34, 42.67],
  [60.88, 55.45, 52.69, 50.87, 49.46, 48.27, 47.22, 45.9, 45.36, 43.67],
  [62.06, 56.57, 53.78, 51.95, 50.53, 49.32, 48.26, 46.92, 46.38, 44.67],
  [63.23, 57.69, 54.88, 53.03, 51.59, 50.38, 49.3, 47.95, 47.4, 45.67],
  [64.4, 58.82, 55.97, 54.11, 52.65, 51.42, 50.34, 48.97, 48.42, 46.67],
  [65.57, 59.94, 57.07, 55.18, 53.71, 52.47, 51.38, 49.99, 49.44, 47.67],
  [66.74, 61.05, 58.16, 56.26, 54.77, 53.52, 52.42, 51.02, 50.45, 48.67],
  [67.9, 62.17, 59.25, 57.33, 55.83, 54.57, 53.45, 52.04, 51.47, 49.67],
  [69.07, 63.29, 60.34, 58.4, 56.89, 55.62, 54.49, 53.06, 52.49, 50.67],
]

/** Zuverlässigkeitsfaktor zur Anzahl der Fehler und zum Risiko; außerhalb der Tabelle ein Fehlerwert. */
export function reliabilityFactor(errors: number, risk: number): number {
  const column = RISK_LEVELS.findIndex((level) => eq(level, risk))
  const factor = Number.isInteger(errors) ? RELIABILITY_FACTORS[errors]?.[column] : undefined
  if (factor === undefined) throw new FormulaError('#NV')
  return factor
}

/**
 * Überschrift der Tabelle. Das Blatt selbst trägt keine Überschrift; die
 * Bezeichnung steht in Blatt 00 der Vorlage (Zeile „X1–X4 (grau)“, Zelle C31:
 * „Konservativer MUS-Ansatz, Zuverlässigkeitsfaktoren, Differenzschätzung“).
 */
export const TABLE_TITLE = 'Zuverlässigkeitsfaktoren'

/** Spaltenüberschrift einer Risikostufe: die Zahl aus Zeile 2 als Prozentangabe (0,05 → „5 %“). */
const riskLabel = (level: number): string => `${Math.round(level * 100)} %`

const columns: readonly DataTableColumn[] = [
  { key: 'A', label: ERRORS_LABEL, format: '0' },
  ...RISK_COLUMNS.map((key, index): DataTableColumn => {
    const level = RISK_LEVELS[index] ?? 0
    return { key, label: riskLabel(level), value: level, group: RISK_LABEL, format: '0.00' }
  }),
]

/**
 * Die Tabelle als reine Daten: je Zeile die Anzahl der Fehler (Spalte A) und
 * die zehn Zuverlässigkeitsfaktoren (Spalten B–K), Zahlen als Zahlen. Die
 * Texte stehen wörtlich wie in der Vorlage (A1 und B1 mit dem Leerzeichen am
 * Ende); Quelle ist der Anfang des Hinweises in M1, der Hinweis selbst steht
 * unter `notes`. Die Zahlenformate der Spalten sind ein Vorschlag der
 * Webfassung – die Zellen der Vorlage tragen das Standardformat.
 */
export const table: DataTable = {
  title: TABLE_TITLE,
  source: LEGACY_NOTICE_LABEL,
  columns,
  rows: RELIABILITY_FACTORS.map((factors, errors) => [errors, ...factors]),
  notes: [LEGACY_NOTICE],
}

/** Alle belegten Zellen des Blatts mit ihrer Adresse, wie sie in der Vorlage stehen. */
export function tableCells(): Record<CellAddress, CellValue> {
  const cells: Record<CellAddress, CellValue> = { A1: ERRORS_LABEL, B1: RISK_LABEL, M1: LEGACY_NOTICE }
  RISK_COLUMNS.forEach((column, index) => (cells[`${column}2`] = RISK_LEVELS[index] ?? null))
  RELIABILITY_FACTORS.forEach((factors, errors) => {
    cells[`A${FIRST_ROW + errors}`] = errors
    RISK_COLUMNS.forEach((column, index) => (cells[`${column}${FIRST_ROW + errors}`] = factors[index] ?? null))
  })
  return cells
}
