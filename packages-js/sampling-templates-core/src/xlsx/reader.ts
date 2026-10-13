/**
 * Liest Zellwerte aus einer `.xlsx`-Arbeitsmappe: Blattnamen, Zahlen, Texte
 * (gemeinsame und Inline-Strings), Formeltext und zuletzt berechneter Wert.
 * Gelesen wird in einem linearen Durchlauf mit festen Grenzen für Größe,
 * Zellenzahl und Zeit; entpackt wird nur, was gebraucht wird. DTDs und externe
 * Bezüge werden nicht ausgewertet.
 */
import { strFromU8, unzipSync } from 'fflate'
import { attributesOf, columnName, decodeText, tokenize, type XmlToken } from './xml'

/** Größte Arbeitsmappe (gepackt) und größter Einzelteil (entpackt), die gelesen werden. */
export const MAX_WORKBOOK_SIZE = 20 * 1024 * 1024
const MAX_PART_SIZE = 40 * 1024 * 1024
/** Höchstzahl der Zellen je Blatt und der gemeinsamen Zeichenketten. */
export const MAX_WORKBOOK_CELLS = 1_000_000
/** Zeitgrenze je gelesenem Teil in Millisekunden. */
const TIME_LIMIT_MS = 8000
const CHECK_EVERY = 4096
const NUMBER = /^-?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/

/** Lesefehler: keine oder eine beschädigte `.xlsx`-Datei, oder eine Grenze ist überschritten. */
export class WorkbookError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'WorkbookError'
  }
}

export interface WorkbookCellValue {
  value: number | string | boolean | null
  /** Die Zelle enthält eine Formel; `value` ist ihr zuletzt berechnetes Ergebnis. */
  formula: boolean
  /** Text der Formel ohne führendes `=`; leer ohne Formel. */
  formulaText: string
}

export interface ReadWorkbook {
  sheetNames: readonly string[]
  /** Zellen eines Blatts nach Adresse; unbekanntes Blatt ergibt eine leere Zuordnung. */
  cells(sheet: string): ReadonlyMap<string, WorkbookCellValue>
}

function part(data: Uint8Array, name: string): string | null {
  const files = unzipSync(data, { filter: (file) => file.name === name && file.originalSize <= MAX_PART_SIZE })
  const bytes = files[name]
  return bytes ? strFromU8(bytes) : null
}

/** Elemente eines Teils mit Zeitgrenze, damit eine präparierte Datei die Seite nicht blockiert. */
function* timed(xml: string): Generator<XmlToken> {
  const deadline = Date.now() + TIME_LIMIT_MS
  let seen = 0
  for (const token of tokenize(xml)) {
    seen += 1
    if (seen % CHECK_EVERY === 0 && Date.now() > deadline) throw new WorkbookError('Zeitgrenze beim Lesen überschritten')
    yield token
  }
}

/** Schachtelungstiefe eines Elements fortschreiben. */
const step = (token: XmlToken): number => (token.kind === 'open' ? 1 : token.kind === 'close' ? -1 : 0)

/** Gemeinsame Zeichenketten: je `<si>` ein Eintrag (auch leer), nur sichtbare Läufe, keine phonetischen Angaben. */
class StringReader {
  readonly strings: string[] = []
  private current: string | null = null
  private inText = false
  private phonetic = 0

  private push(text: string): void {
    this.strings.push(text)
    this.current = null
    if (this.strings.length > MAX_WORKBOOK_CELLS) throw new WorkbookError('Zu viele Zeichenketten')
  }

  private item(token: XmlToken): void {
    // Ein noch offener Eintrag (nicht geschlossenes Element) wird abgeschlossen, bevor der nächste beginnt.
    if (this.current !== null) this.push(this.current)
    if (token.kind === 'open') this.current = ''
    else if (token.kind === 'empty') this.push('')
  }

  read(token: XmlToken): void {
    if (token.name === 'si') this.item(token)
    else if (token.name === 'rPh') this.phonetic += step(token)
    else if (token.name === 't') this.inText = token.kind === 'open'
    else if (token.kind === 'text' && this.inText && this.phonetic <= 0 && this.current !== null) this.current += decodeText(token.text)
  }
}

function sharedStrings(xml: string | null): string[] {
  const reader = new StringReader()
  for (const token of timed(xml ?? '')) reader.read(token)
  reader.read({ kind: 'close', name: 'si', text: '' })
  return reader.strings
}

interface OpenCell {
  reference: string
  type: string | undefined
  raw: string | null
  inline: string
  formula: boolean
  formulaText: string
}

/** Wert je Zelltyp aus dem Rohtext von `<v>`; unbekannte Typen gelten als Zahl. */
const TYPED: Readonly<Record<string, (raw: string, strings: readonly string[]) => number | string | boolean | null>> = {
  s: (raw, strings) => (NUMBER.test(raw) ? (strings[Number(raw)] ?? null) : null),
  str: (raw) => decodeText(raw),
  b: (raw) => raw.trim() === '1',
  e: () => null,
}

function valueOf(cell: OpenCell, strings: readonly string[]): number | string | boolean | null {
  if (cell.type === 'inlineStr') return cell.inline
  const raw = cell.raw ?? ''
  if (raw.trim() === '') return null
  const typed = cell.type ? TYPED[cell.type] : undefined
  if (typed) return typed(cell.type === 'str' ? raw : raw.trim(), strings)
  return NUMBER.test(raw.trim()) ? Number(raw.trim()) : null
}

const COLLECTED: ReadonlySet<string> = new Set(['v', 't', 'f'])

/** Zustand beim Lesen eines Blatts: aktuelle Zelle, Lage in der Zeile, was gerade gesammelt wird. */
class SheetReader {
  readonly cells = new Map<string, WorkbookCellValue>()
  private cell: OpenCell | null = null
  private collecting: 'v' | 't' | 'f' | null = null
  private phonetic = 0
  private row = 0
  private column = 0

  constructor(private readonly strings: readonly string[]) {}

  private finish(): void {
    if (!this.cell) return
    this.cells.set(this.cell.reference, { value: valueOf(this.cell, this.strings), formula: this.cell.formula, formulaText: this.cell.formulaText })
    this.cell = null
    this.collecting = null
    if (this.cells.size > MAX_WORKBOOK_CELLS) throw new WorkbookError('Zu viele Zellen')
  }

  private startRow(token: XmlToken): void {
    this.finish()
    const number = Number(attributesOf(token.text).r)
    this.row = Number.isInteger(number) && number > 0 ? number : this.row + 1
    this.column = 0
  }

  private startCell(token: XmlToken): void {
    this.finish()
    const attributes = attributesOf(token.text)
    this.column += 1
    const reference = /^[A-Z]{1,3}[0-9]{1,7}$/.test(attributes.r ?? '') ? attributes.r! : `${columnName(this.column)}${Math.max(1, this.row)}`
    this.cell = { reference, type: attributes.t, raw: null, inline: '', formula: false, formulaText: '' }
    if (token.kind === 'empty') this.finish()
  }

  private text(token: XmlToken): void {
    if (!this.cell) return
    if (this.collecting === 'v') this.cell.raw = (this.cell.raw ?? '') + token.text
    else if (this.collecting === 'f') this.cell.formulaText += decodeText(token.text)
    else if (this.collecting === 't' && this.phonetic <= 0) this.cell.inline += decodeText(token.text)
  }

  private element(token: XmlToken): void {
    if (!this.cell) return
    if (token.name === 'rPh') this.phonetic += step(token)
    if (token.name === 'f' && token.kind !== 'close') this.cell.formula = true
    if (COLLECTED.has(token.name)) this.collecting = token.kind === 'open' ? (token.name as 'v' | 't' | 'f') : null
  }

  read(token: XmlToken): void {
    if (token.kind === 'text') this.text(token)
    else if (token.name === 'row' && token.kind !== 'close') this.startRow(token)
    else if (token.name === 'row') this.finish()
    else if (token.name === 'c' && token.kind !== 'close') this.startCell(token)
    else if (token.name === 'c' || token.name === 'sheetData') this.finish()
    else this.element(token)
  }
}

function sheetCells(xml: string, strings: readonly string[]): Map<string, WorkbookCellValue> {
  const reader = new SheetReader(strings)
  for (const token of timed(xml)) reader.read(token)
  reader.read({ kind: 'close', name: 'sheetData', text: '' })
  return reader.cells
}

/** Beziehungskennung → Pfad im Archiv. */
function relationTargets(relations: string): Map<string, string> {
  const targets = new Map<string, string>()
  for (const token of timed(relations)) {
    if (token.name !== 'Relationship') continue
    const { Id, Target } = attributesOf(token.text)
    if (Id && Target) targets.set(Id, Target.startsWith('/') ? Target.slice(1) : `xl/${Target}`)
  }
  return targets
}

/** Blattname → Pfad des Blatts im Archiv. */
function sheetPaths(workbook: string, relations: string): Map<string, string> {
  const targets = relationTargets(relations)
  const paths = new Map<string, string>()
  for (const token of timed(workbook)) {
    if (token.name !== 'sheet' || token.kind === 'close') continue
    const { name, id } = attributesOf(token.text)
    const target = id ? targets.get(id) : undefined
    if (name && target) paths.set(name, target)
  }
  return paths
}

/** Fremde Fehler (beschädigtes Archiv, ungültige Zeichen) werden zu `WorkbookError`. */
function guarded<T>(read: () => T): T {
  try {
    return read()
  } catch (error) {
    throw error instanceof WorkbookError ? error : new WorkbookError('Datei ist keine lesbare .xlsx-Arbeitsmappe')
  }
}

/** Arbeitsmappe öffnen; Blätter werden erst beim Zugriff entpackt. */
export function readWorkbook(data: Uint8Array): ReadWorkbook {
  if (data.length > MAX_WORKBOOK_SIZE) throw new WorkbookError('Arbeitsmappe zu groß')
  const { paths, strings } = guarded(() => {
    const workbook = part(data, 'xl/workbook.xml')
    const relations = part(data, 'xl/_rels/workbook.xml.rels')
    if (!workbook || !relations) throw new WorkbookError('Keine Arbeitsmappe')
    return { paths: sheetPaths(workbook, relations), strings: sharedStrings(part(data, 'xl/sharedStrings.xml')) }
  })
  const cache = new Map<string, Map<string, WorkbookCellValue>>()
  return {
    sheetNames: [...paths.keys()],
    cells(sheet) {
      const cached = cache.get(sheet)
      if (cached) return cached
      const path = paths.get(sheet)
      const cells = guarded(() => {
        const xml = path ? part(data, path) : null
        return xml ? sheetCells(xml, strings) : new Map<string, WorkbookCellValue>()
      })
      cache.set(sheet, cells)
      return cells
    },
  }
}
