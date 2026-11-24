// Reine Funktionen der Schwärzung: Gruppen gleicher Fundtexte, Seitenangaben,
// Auswahl und Geometrie eigener Bereiche (Anzeigekoordinaten 0…1).

import type { RedactionArea, RedactionBox, RedactionCandidate, RedactionPlan, RedactionSelection } from './types'

/** Gleiche Fundtexte derselben Quelle werden gemeinsam an- und abgewählt. */
export interface RedactionGroup {
  key: string
  source: string
  label: string
  text: string
  items: readonly RedactionCandidate[]
  pages: readonly number[]
  /** Mindestens eine Fundstelle liegt außerhalb des Seitentexts (Metadaten, Kommentar, …). */
  hidden: boolean
}

export type RedactionGroupState = 'all' | 'some' | 'none'

/** Mindestgröße eines Bereichs (Anteil der Seitenkante). */
export const REDACTION_MIN_SIZE = 0.004
/** Schritt der Pfeiltasten; mit Umschalt `REDACTION_KEY_STEP_LARGE`. */
export const REDACTION_KEY_STEP = 0.005
export const REDACTION_KEY_STEP_LARGE = 0.05
/** So viele Gruppen zeigt die Liste je Schritt („Weitere anzeigen“). */
export const REDACTION_GROUP_PAGE = 200
/** Ab dieser Gruppenzahl erscheint das Filterfeld. */
export const REDACTION_FILTER_FROM = 8
/** Höchstens so viele Seitenknöpfe „Seiten mit Fundstellen“. */
export const REDACTION_PAGE_BUTTONS = 60

export function normalizeRedactionText(text: string): string {
  return text.normalize('NFKC').replace(/\s+/g, ' ').trim().toLocaleLowerCase('de')
}

const groupCache = new WeakMap<readonly RedactionCandidate[], readonly RedactionGroup[]>()

/** Gruppen nach Häufigkeit, dann alphabetisch; je Kandidatenliste nur einmal berechnet. */
export function redactionGroups(candidates: readonly RedactionCandidate[]): readonly RedactionGroup[] {
  const cached = groupCache.get(candidates)
  if (cached) return cached
  const groups = new Map<string, { key: string; source: string; label: string; text: string; items: RedactionCandidate[]; pages: number[]; hidden: boolean }>()
  for (const candidate of candidates) {
    const key = `${candidate.source}\u001f${normalizeRedactionText(candidate.text)}`
    let group = groups.get(key)
    if (!group) {
      group = { key, source: candidate.source, label: candidate.label, text: candidate.text, items: [], pages: [], hidden: false }
      groups.set(key, group)
    }
    group.items.push(candidate)
    if (candidate.kind === 'hidden') group.hidden = true
    if (candidate.page && !group.pages.includes(candidate.page)) group.pages.push(candidate.page)
  }
  const sorted = [...groups.values()].sort((a, b) => b.items.length - a.items.length || a.text.localeCompare(b.text, 'de'))
  groupCache.set(candidates, sorted)
  return sorted
}

/** „1–3, 5“ aus Seitenzahlen. */
export function formatRedactionPages(pages: readonly number[]): string {
  const sorted = [...new Set(pages)].sort((a, b) => a - b)
  const parts: string[] = []
  let start = sorted[0]
  let previous = sorted[0]
  for (const page of [...sorted.slice(1), Number.NaN]) {
    if (previous !== undefined && page === previous + 1) {
      previous = page
      continue
    }
    if (start !== undefined) parts.push(start === previous ? `${start}` : `${start}–${previous}`)
    start = page
    previous = page
  }
  return parts.join(', ')
}

export function redactionGroupState(group: RedactionGroup, selected: ReadonlySet<string>): RedactionGroupState {
  const count = group.items.reduce((sum, item) => sum + (selected.has(item.id) ? 1 : 0), 0)
  return count === group.items.length ? 'all' : count === 0 ? 'none' : 'some'
}

/** Vorauswahl des Dienstes (`selected`). */
export function initialRedactionSelection(plan: RedactionPlan): ReadonlySet<string> {
  return new Set(plan.candidates.filter((candidate) => candidate.selected).map((candidate) => candidate.id))
}

/** Bestätigte Auswahl für `POST /apply` in Reihenfolge des Plans. */
export function redactionSelectionPayload(plan: RedactionPlan, selected: ReadonlySet<string>, areas: readonly RedactionArea[], sanitize: boolean): RedactionSelection {
  return {
    sha256: plan.sha256,
    criteria: plan.criteria,
    selected: plan.candidates.filter((candidate) => selected.has(candidate.id)).map((candidate) => candidate.id),
    areas: areas.map(({ page, rect }) => ({ page, rect: [rect[0], rect[1], rect[2], rect[3]] })),
    sanitize,
  }
}

/** Begriffe aus dem Textfeld: eine Zeile je Begriff, leere Zeilen und Dubletten entfallen. */
export function redactionTerms(text: string): string[] {
  const seen = new Set<string>()
  const terms: string[] = []
  for (const line of text.split(/\r?\n/)) {
    const term = line.trim()
    if (term && !seen.has(term)) {
      seen.add(term)
      terms.push(term)
    }
  }
  return terms
}

const clamp = (value: number): number => Math.min(1, Math.max(0, value))
/** Auf sechs Nachkommastellen runden (keine Gleitkommareste in Anzeige und Auswahl). */
const round = (value: number): number => Math.round(value * 1e6) / 1e6
const rounded = (box: RedactionBox): RedactionBox => [round(box[0]), round(box[1]), round(box[2]), round(box[3])]

/** Rechteck aus zwei Punkten, auf die Seite begrenzt. */
export function redactionBoxFromPoints(a: readonly [number, number], b: readonly [number, number]): RedactionBox {
  const [ax, ay] = [clamp(a[0]), clamp(a[1])]
  const [bx, by] = [clamp(b[0]), clamp(b[1])]
  return rounded([Math.min(ax, bx), Math.min(ay, by), Math.max(ax, bx), Math.max(ay, by)])
}

export function redactionBoxIsTooSmall(box: RedactionBox): boolean {
  return box[2] - box[0] < REDACTION_MIN_SIZE || box[3] - box[1] < REDACTION_MIN_SIZE
}

/** Rechte untere Ecke auf `point` ziehen (Maus) – nie kleiner als die Mindestgröße. */
export function resizeRedactionBox(box: RedactionBox, point: readonly [number, number]): RedactionBox {
  const x1 = Math.min(1, Math.max(box[0] + REDACTION_MIN_SIZE, point[0]))
  const y1 = Math.min(1, Math.max(box[1] + REDACTION_MIN_SIZE, point[1]))
  return rounded([box[0], box[1], x1, y1])
}

export type RedactionArrow = 'ArrowLeft' | 'ArrowRight' | 'ArrowUp' | 'ArrowDown'

const ARROWS: Readonly<Record<RedactionArrow, readonly [number, number]>> = {
  ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowDown: [0, 1], ArrowUp: [0, -1],
}

export function isRedactionArrow(key: string): key is RedactionArrow {
  return Object.prototype.hasOwnProperty.call(ARROWS, key)
}

/** Tastatur: Größe (rechte untere Ecke) oder Lage des ganzen Bereichs ändern. */
export function nudgeRedactionBox(box: RedactionBox, key: RedactionArrow, mode: 'resize' | 'move', large: boolean): RedactionBox {
  const [dx, dy] = ARROWS[key]
  const step = large ? REDACTION_KEY_STEP_LARGE : REDACTION_KEY_STEP
  if (mode === 'resize') return resizeRedactionBox(box, [box[2] + dx * step, box[3] + dy * step])
  const width = box[2] - box[0]
  const height = box[3] - box[1]
  const x0 = Math.min(1 - width, Math.max(0, box[0] + dx * step))
  const y0 = Math.min(1 - height, Math.max(0, box[1] + dy * step))
  return rounded([x0, y0, x0 + width, y0 + height])
}

/** Bereich, den die Schaltfläche „Bereich hinzufügen“ anlegt (Seitenmitte, je weiterem Bereich versetzt). */
export function defaultRedactionBox(existing: number): RedactionBox {
  const offset = (existing % 8) * 0.03
  return rounded([0.3 + offset, 0.4 + offset, 0.6 + offset, 0.48 + offset])
}

/** Lage als CSS-Eigenschaften in Prozent der Seite (Vue und React identisch). */
export function redactionBoxStyle(box: RedactionBox): Record<'left' | 'top' | 'width' | 'height', string> {
  const percent = (value: number): string => `${Math.round(value * 100000) / 1000}%`
  return {
    left: percent(box[0]),
    top: percent(box[1]),
    width: percent(Math.max(0, box[2] - box[0])),
    height: percent(Math.max(0, box[3] - box[1])),
  }
}

/** Zeigerposition relativ zur Seitenfläche als Anteile 0…1 (außerhalb begrenzt). */
export function redactionPoint(bounds: { left: number; top: number; width: number; height: number }, x: number, y: number): [number, number] {
  if (!bounds.width || !bounds.height) return [0, 0]
  return [clamp((x - bounds.left) / bounds.width), clamp((y - bounds.top) / bounds.height)]
}
