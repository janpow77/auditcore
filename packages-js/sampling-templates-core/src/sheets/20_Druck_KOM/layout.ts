/**
 * Aufteilung der Druckseite von Blatt 20 (Druckbereich A1:G45 der Vorlage, eine
 * A4-Seite hoch): Kopf, vier Abschnitte mit Freitext, Tabellen und Kennzahlen,
 * Fußzeile. Alle Texte stammen wörtlich aus der Vorlage; die Werte holt die
 * Berichtsansicht (`view/reportView.ts`) über die Zelladressen.
 */
import type { CellAddress } from '../../model/types'
import { CASE_HEADERS, CASE_ROWS, TITLE } from './definition'

/** Zeile einer Tabelle: Zeilenbeschriftung (Spalte A) und Zellen; `span` verbindet die Zelle über mehrere Spalten. */
export interface ReportRowLayout {
  label?: string
  cells: readonly ({ cell: CellAddress; span?: number } | null)[]
}

export type ReportBlockLayout =
  | { kind: 'text'; cell: CellAddress }
  | { kind: 'table'; columns: readonly string[]; rows: readonly ReportRowLayout[]; foot?: ReportRowLayout }
  | { kind: 'statement'; cell: CellAddress }

export interface ReportSectionLayout {
  id: string
  /** Überschrift mit Nummer, wie sie die Vorlage druckt. */
  title: string
  blocks: readonly ReportBlockLayout[]
}

const value = (cell: CellAddress, span?: number): { cell: CellAddress; span?: number } => (span ? { cell, span } : { cell })
const figure = (label: string, cell: CellAddress): ReportRowLayout => ({ label, cells: [value(cell)] })

export const REPORT_LAYOUT = {
  /** C1 und C2 neben dem Emblem. */
  cofinanced: ['Kofinanziert von der', 'Europäischen Union'],
  title: TITLE,
  subtitle: 'A6',
  asOf: 'G6',
  controls: {
    title: 'Steuerfelder (werden nicht gedruckt)',
    cells: ['J4', 'J5', 'J6', 'J7', 'J8'],
    /** Aus dem Hinweis I10 die Sätze, die auch für die Webfassung gelten (ohne die Anleitung zum Druck aus Excel). */
    note: 'Die Kennzahlen stammen aus Blatt 02 und aus dem in Blatt 18 gewählten Methodenblatt. Die Restfehlerquote folgt der Logik der Kommissionsvorlage (F = A − E, G = D × F, I = F − H, J = G − H, K = J / I).',
  },
  sections: [
    {
      id: '1',
      title: '1. Grundgesamtheit und Stichprobe',
      blocks: [
        { kind: 'text', cell: 'A9' },
        {
          kind: 'table',
          columns: ['', 'Datensätze', 'Ausgaben'],
          rows: [
            { label: 'Zahlungsanträge insgesamt (SFC2021)', cells: [value('F11'), value('G11')] },
            { label: 'Positive Grundgesamtheit (Artikel 3 Absatz 4 DelVO)', cells: [value('F12'), value('G12')] },
            { label: 'Negative Werte und Nullwerte', cells: [value('F13'), value('G13')] },
            { label: 'Stichprobe (Einheiten / geprüfte Ausgaben)', cells: [value('F14'), value('G14')] },
            { label: 'Stichprobenverfahren', cells: [value('D15', 2)] },
          ],
        },
      ],
    },
    {
      id: '2',
      title: '2. Ergebnisse der Vorhabenprüfungen',
      blocks: [
        { kind: 'text', cell: 'A18' },
        {
          kind: 'table',
          columns: Object.values(CASE_HEADERS),
          rows: CASE_ROWS.map((row) => ({ cells: Object.keys(CASE_HEADERS).map((column) => value(`${column}${row}`)) })),
          foot: { label: 'Summe', cells: [null, value('C28'), value('D28'), null, value('F28'), value('G28')] },
        },
      ],
    },
    {
      id: '3',
      title: '3. Hochrechnung und Gesamtfehlerquote',
      blocks: [
        { kind: 'text', cell: 'A31' },
        {
          kind: 'table',
          columns: [],
          rows: [
            figure('Gesamtfehlerquote', 'G32'),
            figure('Hochgerechneter Fehler (angepasst nach Anhang III)', 'G33'),
            figure('Genauigkeit der Stichprobe', 'G34'),
            figure('Obere Fehlergrenze', 'G35'),
            figure('Fehlerbetrag einschließlich Pauschale der technischen Hilfe (Artikel 8 Absatz 5 DelVO)', 'G36'),
          ],
        },
        { kind: 'statement', cell: 'A37' },
      ],
    },
    {
      id: '4',
      title: '4. Restfehlerquote und weiteres Vorgehen',
      blocks: [
        {
          kind: 'table',
          columns: [],
          rows: [
            figure('Beträge nach Artikel 98 Absatz 6 VO (EU) 2021/1060 (E)', 'G40'),
            figure('Finanzkorrekturen (H)', 'G41'),
            figure('Restfehlerquote nach Finanzkorrekturen', 'G42'),
            figure('Hochgerechnete Finanzkorrektur bis zur Wesentlichkeitsschwelle von 2 %', 'G43'),
          ],
        },
        { kind: 'text', cell: 'A45' },
      ],
    },
  ] as readonly ReportSectionLayout[],
  /** Linke Fußzeile der Druckseite; die Vorlage nennt hier fest die Prüfbehörde. */
  /** Fußzeile: Prüfbehörde, Organisationseinheit und Ort aus den Angaben W5–W7 (in der Vorlage ein fester Text). */
  footer: 'W8',
  /** Angaben für Kopf- und Fußzeile; sie stehen bei den Steuerfeldern. */
  identity: ['W4', 'W5', 'W6', 'W7'],
} as const
