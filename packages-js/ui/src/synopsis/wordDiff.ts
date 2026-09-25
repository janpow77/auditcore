/**
 * Wortdifferenz für die Anzeige, ohne Vue. Bevorzugt die vom Server gelieferte
 * `difflib.ndiff`-Folge (`"  "` gleich, `"- "` entfallen, `"+ "` neu,
 * `"? "` Hinweis); fehlt sie (Gesetzessynopse), rechnet eine längste gemeinsame
 * Teilfolge über Wörter nach – wie `regulierung/frontend/src/lib/textDiff.ts`
 * mit einer Obergrenze, damit die Oberfläche nicht einfriert.
 */

export type SegmentKind = 'same' | 'removed' | 'added'
export type DiffSide = 'old' | 'new' | 'inline'

export interface DiffSegment {
  text: string
  kind: SegmentKind
}

/** Oberhalb dieser Wortzahl je Seite wird nicht wortweise verglichen. */
export const WORD_LIMIT = 1200

type Operation = readonly [SegmentKind, string]

function words(text: string): string[] {
  return text.split(/\s+/).filter(Boolean)
}

function pushWord(out: DiffSegment[], word: string, kind: SegmentKind): void {
  const last = out[out.length - 1]
  if (!last) {
    out.push({ text: word, kind })
    return
  }
  if (last.kind === kind) {
    last.text += ` ${word}`
    return
  }
  if (last.kind === 'same') {
    last.text += ' '
    out.push({ text: word, kind })
    return
  }
  if (kind === 'same') {
    out.push({ text: ` ${word}`, kind })
    return
  }
  out.push({ text: ' ', kind: 'same' }, { text: word, kind })
}

function visible(kind: SegmentKind, side: DiffSide): boolean {
  if (side === 'old') return kind !== 'added'
  if (side === 'new') return kind !== 'removed'
  return true
}

function toSegments(operations: readonly Operation[], side: DiffSide): DiffSegment[] {
  const out: DiffSegment[] = []
  for (const [kind, word] of operations) {
    if (visible(kind, side)) pushWord(out, word, kind)
  }
  return out
}

/** ndiff-Zeilen in Operationen übersetzen; Hinweiszeilen (`? `) entfallen. */
export function ndiffOperations(lines: readonly string[]): Operation[] {
  const operations: Operation[] = []
  for (const line of lines) {
    const prefix = line.slice(0, 2)
    const word = line.slice(2)
    if (prefix === '  ') operations.push(['same', word])
    else if (prefix === '- ') operations.push(['removed', word])
    else if (prefix === '+ ') operations.push(['added', word])
  }
  return operations
}

function lcsTable(a: readonly string[], b: readonly string[]): Int32Array {
  const width = b.length + 1
  const table = new Int32Array((a.length + 1) * width)
  for (let i = a.length - 1; i >= 0; i -= 1) {
    for (let j = b.length - 1; j >= 0; j -= 1) {
      const index = i * width + j
      table[index] =
        a[i] === b[j]
          ? (table[index + width + 1] ?? 0) + 1
          : Math.max(table[index + width] ?? 0, table[index + 1] ?? 0)
    }
  }
  return table
}

function walk(a: readonly string[], b: readonly string[], table: Int32Array): Operation[] {
  const width = b.length + 1
  const at = (i: number, j: number): number => table[i * width + j] ?? 0
  const operations: Operation[] = []
  let i = 0
  let j = 0
  while (i < a.length && j < b.length) {
    const left = a[i] as string
    const right = b[j] as string
    if (left === right) {
      operations.push(['same', left])
      i += 1
      j += 1
    } else if (at(i + 1, j) >= at(i, j + 1)) {
      operations.push(['removed', left])
      i += 1
    } else {
      operations.push(['added', right])
      j += 1
    }
  }
  for (const word of a.slice(i)) operations.push(['removed', word])
  for (const word of b.slice(j)) operations.push(['added', word])
  return operations
}

/** Längste gemeinsame Teilfolge über Wörter; `null` oberhalb von {@link WORD_LIMIT}. */
export function lcsOperations(oldText: string, newText: string): Operation[] | null {
  const a = words(oldText)
  const b = words(newText)
  if (a.length > WORD_LIMIT || b.length > WORD_LIMIT) return null
  return walk(a, b, lcsTable(a, b))
}

/**
 * Segmente einer Seite. `ndiff` hat Vorrang; ohne sie wird nachgerechnet.
 * Ist keine Wortdifferenz möglich, bleibt der Text unmarkiert (seitenweise)
 * bzw. erscheint inline als Streichung plus Einfügung.
 */
export function diffSegments(
  oldText: string,
  newText: string,
  side: DiffSide,
  ndiff?: readonly string[],
): DiffSegment[] {
  const operations = ndiff && ndiff.length > 0 ? ndiffOperations(ndiff) : lcsOperations(oldText, newText)
  if (operations) return toSegments(operations, side)
  if (side === 'old') return oldText ? [{ text: oldText, kind: 'same' }] : []
  if (side === 'new') return newText ? [{ text: newText, kind: 'same' }] : []
  return wholeSegments(oldText, newText)
}

/** Ganze Texte als Streichung und Einfügung (neue/entfallene Stellen, Rückfall). */
export function wholeSegments(oldText: string, newText: string): DiffSegment[] {
  const out: DiffSegment[] = []
  if (oldText) out.push({ text: oldText, kind: 'removed' })
  if (oldText && newText) out.push({ text: ' ', kind: 'same' })
  if (newText) out.push({ text: newText, kind: 'added' })
  return out
}

export function plainSegments(text: string): DiffSegment[] {
  return text ? [{ text, kind: 'same' }] : []
}

export function segmentsText(segments: readonly DiffSegment[]): string {
  return segments.map((segment) => segment.text).join('')
}
