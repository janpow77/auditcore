/**
 * Nachschlagetabelle der Vorlage als reine Daten (Blatt X1a): Sie lässt sich
 * ohne Kenntnis des Blatts anzeigen. Texte stehen wörtlich wie in der Vorlage,
 * Zahlen als Zahlen. Ein Blatt mit Tabelle ist kein Rechenblatt; es wird im
 * Register mit `tableSheet` angemeldet und aus dem zugehörigen Verfahren heraus geöffnet.
 */
import type { CellValue } from './types'

export interface DataTable {
  /** Überschrift der Tabelle. */
  title: string
  /** Herkunft der Tabelle. */
  source: string
  columns: readonly DataTableColumn[]
  /** Zeilen in der Reihenfolge der Vorlage; je Spalte ein Wert in der Reihenfolge von `columns`. */
  rows: readonly (readonly CellValue[])[]
  /** Hinweise zur Tabelle, wörtlich. */
  notes: readonly string[]
}

/** Spalte einer Nachschlagetabelle. */
export interface DataTableColumn {
  /** Stabile Kennung: die Spalte der Vorlage (`A`, `B`, …). */
  key: string
  /** Spaltenüberschrift als Text. */
  label: string
  /** Spaltenüberschrift als Zahl, wenn die Vorlage dort eine Zahl führt (z. B. das Risiko 0,05). */
  value?: number
  /** Gemeinsame Überschrift über mehreren Spalten, wörtlich. */
  group?: string
  /** Zahlenformat der Werte der Spalte (Schreibweise der Definitionen, z. B. `0.00`). */
  format?: string
}
