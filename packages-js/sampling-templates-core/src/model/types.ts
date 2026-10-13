/**
 * Grundtypen der Rechenkerne. Schlüssel sind immer die Zelladressen der
 * Vorlage (`"C27"`), damit jeder Wert bis in die Arbeitsmappe nachvollziehbar
 * bleibt; lesbare Namen kommen über `aliases` dazu.
 */

/** Blattname der Vorlage, z. B. `03_MUS_1Z`. */
export type SheetId = string

/** Zelladresse ohne Blatt, z. B. `C27`. */
export type CellAddress = string

/** Wert einer Zelle: Zahl, Text oder leer. Fehlerwerte und `""` der Vorlage sind `null`. */
export type CellValue = number | string | null

/** Zellwerte eines Blatts. */
export type CellMap = Readonly<Record<CellAddress, CellValue>>

/** Veränderliche Zellwerte während der Berechnung eines Blatts. */
export type Cells = Record<CellAddress, CellValue>

/** Eine Zeile der z-Tabelle aus Blatt 01 (Anhang I Nr. 3 DelVO). */
export interface ZRow {
  /** Konfidenzniveau als Anteil (0,6 … 0,95). */
  confidence: number
  /** z für den zweiseitigen Test. */
  twoSided: number
  /** z' für den einseitigen Test. */
  oneSided: number
  /** Fundstelle laut Blatt 01. */
  source: string
  /** `false`: Wert steht nicht in Anhang I (95 %). */
  inAnnex: boolean
}

/** Auswahllisten aus Blatt 01 („nicht ändern“). */
export interface ParameterLists {
  reliability: readonly string[]
  testType: readonly string[]
  yesNo: readonly string[]
  category: readonly number[]
  recalculation: readonly string[]
  article80: readonly string[]
  negativePopulation: readonly string[]
  methodSheets: readonly SheetId[]
}

/** Schlüssel einer Auswahlliste aus Blatt 01; `confidence` kommt aus der z-Tabelle. */
export type ListKey = keyof ParameterLists | 'confidence'

/** Parameter aus Blatt 01: z-Werte und Auswahllisten. */
export interface Parameters {
  zTable: readonly ZRow[]
  lists: ParameterLists
  /** Merksätze aus Blatt 01 (Zellen B16–B18), wörtlich. */
  notes: { materiality: string; minimumSize: string; limitedSize: string }
}

/**
 * Ergebnisübersicht eines Methodenblatts (feste Zellen N3–N11 der Vorlage).
 * Blatt 18 liest sie über den Kontext; das ersetzt den INDIRECT-Bezug.
 */
export interface MethodSummary {
  sheet: SheetId
  /** N3 */
  method: CellValue
  /** N4: Buchwert der Hochrechnungsbasis (BV). */
  bookValue: CellValue
  /** N5: Extrapolierter Fehler EE. */
  projectedError: CellValue
  /** N6: davon Fehler der umfassenden Schicht. */
  exhaustiveError: CellValue
  /** N7: Genauigkeit SE. */
  precision: CellValue
  /** N8: abgegrenzte systembedingte Fehler. */
  systemicErrors: CellValue
  /** N9: nicht berichtigte anomale Fehler. */
  anomalousErrors: CellValue
  /** N10: Stichprobenumfang gesamt. */
  sampleSize: CellValue
  /** N11: Gesamtfehlerquote (blattbezogen). */
  totalErrorRate: CellValue
}

/**
 * Alles, was ein Blatt von außerhalb braucht. Verweise zwischen Blättern
 * laufen ausdrücklich hierüber, es gibt keine Formel-Engine.
 */
export interface SheetContext {
  /** Blatt 01. */
  parameters: Parameters
  /** Ergebnisse anderer Blätter, auf die Verknüpfungen zeigen (z. B. `02_Grundgesamtheit`). */
  sheets: Readonly<Record<SheetId, CellMap>>
  /** Nur für Blatt 18: Ergebnisübersicht des gewählten Methodenblatts. */
  method?: MethodSummary
}

/** Rechenkern eines Blatts: reine Funktion ohne Seiteneffekte. */
export type Compute = (inputs: CellMap, context: SheetContext) => CellMap

/** Einstufung eines Prüfhinweises (✔ / ⚠ / ✖ / ohne Zeichen). */
export type Tone = 'success' | 'warning' | 'danger' | 'neutral'

/** Zusätzlicher Hinweis der Webfassung; verändert kein Rechenergebnis. */
export interface WebHint {
  /** Stabile Kennung, auch Schlüssel für Übersetzungen. */
  id: string
  tone: Tone
  text: string
}

/**
 * Begründete Abweichung vom Verhalten der Vorlage: Ist eine der Eingaben in
 * `whenEmpty` leer, liefert die Webfassung an `cell` `null` („Angabe fehlt“),
 * während die Vorlage mit 0 weiterrechnet. `whenEmpty` nennt genau die
 * Eingaben, von denen die Zelle abhängt und deren Fehlen sie leert.
 */
export interface Deviation {
  cell: CellAddress
  /** Zellen des Blatts oder, als `Blatt!Zelle`, eines anderen Blatts. */
  whenEmpty: readonly string[]
  /** Was die Vorlage in diesem Fall zeigt. */
  template: string
  reason: string
  /**
   * Gegenprobe im Golden-Abgleich: `zero` (Standard) – mit 0 statt der leeren
   * Eingaben muss der Rechenkern den Wert der Vorlage liefern; `none` – die
   * Vorlage zeigt den Wert aus einem anderen Grund (z. B. Textvergleich einer leeren Zelle).
   */
  check?: 'zero' | 'none'
}
