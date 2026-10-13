/**
 * Arbeitsstand: alle Eingaben einer Sitzung als Datei, die die Prüfbehörde
 * selbst speichert und später wieder öffnet. Die Schlüssel der Datei sind
 * deutsch und fest (Dateiformat); Eingaben tragen die Zelladressen der Vorlage.
 */
import type { CellAddress, CellMap, CellValue, SheetId } from '../model/types'

/** Formatkennung der Arbeitsstandsdatei. */
export const WORKSPACE_FORMAT = 'flowaudit-stichprobe'
/** Aktuelle Fassung des Dateiformats; ältere werden angehoben, neuere abgelehnt. */
export const WORKSPACE_FORMAT_VERSION = 1
/** Fassung des Rechenkerns (gleich der Paketversion); steht in jeder Datei. */
export const ENGINE_VERSION = '0.1.1'
/** Nachgebildete Vorlage. */
export const TEMPLATE_NAME = 'Stichprobenvorlagen 2021–2027, Fassung 4'
/** Rechtsstand der Vorlage. */
export const LEGAL_STATE = 'DelVO (EU) 2023/67'
/** Größte Datei, die geöffnet wird (Zeichen der JSON-Datei). */
export const MAX_WORKSPACE_SIZE = 2 * 1024 * 1024

/** Kopfangaben der Datei (Schlüssel wie im Dateiformat). */
export interface WorkspaceHeader {
  programm: string
  cci: string
  geschaeftsjahr: string
  bearbeitung: string
  aktenzeichen: string
}

/** Eingaben eines Blatts: Zellwerte, bei Blatt 17 eine Liste von Stichprobeneinheiten. */
export type SheetInputs = CellMap | readonly CellMap[]

/** Arbeitsstand im Speicher. */
export interface WorkspaceState {
  header: WorkspaceHeader
  /** Gewähltes Methodenblatt. */
  activeMethod: SheetId | null
  /** Eingaben je Blatt; Schlüssel sind Zelladressen der Vorlage. */
  sheets: Readonly<Record<SheetId, SheetInputs>>
}

/** Arbeitsstandsdatei (`.json`), beschrieben durch `schema/arbeitsstand.schema.json`. */
export interface WorkspaceFile {
  format: typeof WORKSPACE_FORMAT
  formatVersion: number
  rechenkern: string
  vorlage: string
  rechtsstand: string
  /** Zeitpunkt des Speicherns (ISO 8601, UTC). */
  gespeichertAm: string
  kopf: WorkspaceHeader
  aktiveMethode: SheetId | null
  blaetter: Record<SheetId, SheetInputs>
  /** Informativ: beim Öffnen wird immer neu gerechnet. */
  ergebnisse: Record<SheetId, CellMap>
  /**
   * Informativ: Hinweise der Webfassung zum Zeitpunkt des Speicherns je Blatt,
   * darunter „Keine Angabe, daher mit 0 berechnet“. Beim Öffnen neu ermittelt.
   */
  hinweise: Record<SheetId, readonly { id: string; text: string }[]>
  /** `sha256:` + Hexadezimalwert über die kanonisch sortierten Eingaben. */
  pruefsumme: string
}

/** Abweichung zwischen gespeichertem und neu berechnetem Ergebnis. */
export interface ResultDifference {
  sheet: SheetId
  cell: CellAddress
  /** Bezeichnung der Größe laut Methodendefinition. */
  label: string
  stored: CellValue
  computed: CellValue
}

/** Hinweis beim Öffnen; die Oberfläche formuliert daraus den Text. */
export type OpenNotice =
  | { kind: 'checksum-mismatch' }
  | { kind: 'results-differ'; differences: readonly ResultDifference[]; storedEngine: string; currentEngine: string }
  | { kind: 'unknown-fields'; fields: readonly string[] }
  | { kind: 'migrated'; from: number; to: number }

export type OpenErrorCode = 'too-large' | 'invalid-json' | 'unsafe-key' | 'not-a-workspace' | 'newer-version' | 'invalid-structure'

/** Grund, aus dem eine Datei nicht geöffnet wird. */
export interface OpenError {
  code: OpenErrorCode
  /** Stelle in der Datei bzw. Fassungsnummer. */
  detail?: string
}

export type OpenResult =
  | { ok: true; state: WorkspaceState; savedAt: string | null; engine: string | null; notices: readonly OpenNotice[] }
  | { ok: false; error: OpenError }

/** Leerer Arbeitsstand. */
export function emptyWorkspace(): WorkspaceState {
  return { header: { programm: '', cci: '', geschaeftsjahr: '', bearbeitung: '', aktenzeichen: '' }, activeMethod: null, sheets: {} }
}
