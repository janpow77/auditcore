/**
 * Zellen, an denen die Webfassung bewusst nach der DelVO (EU) 2023/67 rechnet
 * (Entscheidung des Inhabers vom 17.10.2026, `docs/abweichungen.md` Nr. 16).
 * Die Sollwerte rechnet `scripts/delvo_soll.py` unabhängig vom Rechenkern aus
 * den Excel-Sollwerten nach (`test/golden-delvo/*.delvo.json`): `cells` nennt
 * je Fall den DelVO-Wert einer Zelle, `others` (falls vorhanden) verlangt, dass
 * jede weitere abweichende Zelle des Falls leer ist („—“, Folgegröße).
 */
import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import type { CellValue } from '../src/model/types'

export interface DelvoEntry {
  position: number
  name: string
  cells: Record<string, CellValue>
  others?: null
  rule: string
}

/** Texte der Vorlage für „kein Wert“ in Blatt 18 und im Bericht; als Folgegröße gleichwertig mit „—“. */
const NO_VALUE: ReadonlySet<string> = new Set(['n. a.', 'nicht berechnet'])

const DIRECTORY = fileURLToPath(new URL('./golden-delvo/', import.meta.url))

/** DelVO-Sollwerte einer Golden-Datei je Position des Falls. */
export function delvoEntries(goldenFile: string): Map<number, DelvoEntry> {
  const path = `${DIRECTORY}${goldenFile.replace(/\.golden\.json$/, '.delvo.json')}`
  if (!existsSync(path)) return new Map()
  return new Map((JSON.parse(readFileSync(path, 'utf8')) as DelvoEntry[]).map((entry) => [entry.position, entry]))
}

/**
 * Urteil zu einer Zelle eines Falls mit DelVO-Sollwerten: `delvo` – die
 * Webfassung zeigt den DelVO-Wert (bzw. als Folgegröße keinen Wert);
 * `wrong` – eine Zelle mit DelVO-Sollwert weicht davon ab; `none` – die Zelle
 * ist nicht betroffen.
 */
export function delvoVerdict(entry: DelvoEntry | undefined, cell: string, actual: CellValue, same: (expected: CellValue, actual: CellValue) => boolean): 'delvo' | 'wrong' | 'none' {
  if (!entry) return 'none'
  if (cell in entry.cells) return same(entry.cells[cell] ?? null, actual) ? 'delvo' : 'wrong'
  return 'others' in entry && (actual === null || NO_VALUE.has(String(actual))) ? 'delvo' : 'none'
}
