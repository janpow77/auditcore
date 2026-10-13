/**
 * Einschränkungen eines Ergebnisses: alles, was am Verfahrensblatt die
 * Aussagekraft des Ergebnisses einschränkt – mit 0 gerechnete Eingaben, stille
 * Lücken (die Vorlage rechnet ohne eine Schicht, einen Zeitraum oder eine Größe
 * weiter), Werte der Vorlage ohne Grundlage, negative Ergebnisse, Hinweise der
 * Webfassung in Warnfarbe, Auslegungen der Vorlage und der Hinweis einer Altvorlage. Sie wandern mit dem Ergebnis in
 * Blatt 18, auf die Berichtsseite (auch im Druck) und in jeden Export; ein
 * bestandener Befund („✔“) erscheint daneben nicht uneingeschränkt grün.
 */
import { isBlank, isNumber, lt } from '../excel/index'
import type { Translate } from '../i18n/messages'
import { cellsOf, fieldsOf, findField, type FieldDefinition } from '../model/definition'
import { resultCellsOf } from '../model/dependence'
import { evaluateSheet } from '../model/evaluate'
import { createContext, type AvailableSheet, type SheetModule } from '../model/sheet'
import { translateValue } from '../model/texts'
import type { CellMap, SheetContext, SheetId, Tone } from '../model/types'
import { SHEETS, findAvailableSheet } from '../sheets/registry'

export type LimitationKind = 'zero' | 'missing' | 'withoutBasis' | 'negative' | 'range' | 'warning' | 'interpretation' | 'legacy'

export interface Limitation {
  id: string
  kind: LimitationKind
  tone: Tone
  text: string
}

/** Feld der Altvorlagen mit dem Hinweis, dass sie keine gebrauchsfertige Methode sind. */
const LEGACY_NOTICE = 'legacyNotice'
/** Blatt, über das die Blätter 18 und 20 das Verfahren beziehen, und das Blatt des Berichts. */
const TOTAL_ERROR_RATE_SHEET = '18_GFQ_AnhIII'
const REPORT_SHEET = '20_Druck_KOM'
const POPULATION_SHEET = '02_Grundgesamtheit'

/** Nummer der Schicht einer Schichtzelle (1 …) oder 0. */
function stratumOf(field: FieldDefinition | undefined, cell: string): number {
  return field?.columns && cell !== field.total ? field.columns.indexOf(cell.replace(/\d+$/, '')) + 1 : 0
}

/** Bezeichnung einer Eingabe für Hinweise: „Bezeichnung (Zelle)“, bei anderen Blättern „Blatt!Zelle“; mit `t` bei Schichtzellen mit der Schicht davor. */
export function inputName(sheet: AvailableSheet, reference: string, t?: Translate): string {
  const field = reference.includes('!') ? undefined : findField(sheet.definition, reference)
  const stratum = t ? stratumOf(field, reference) : 0
  return field ? `${stratum ? `${t!('stratum', { number: stratum })}: ` : ''}${field.label} (${reference})` : reference
}

/** Zufallsschicht: Stichprobenumfang abzüglich der hochwertigen Einheiten. */
const RANDOM_STRATUM = /randomstratumunits|stratumrandomunits|finalrandomunits/i
const INTERVAL = /interval/i

/** Berechnete Anzahlen des Blatts (Stichprobenumfänge, Einheiten), Schichtzellen und Summenzellen eingeschlossen. */
function countCells(sheet: AvailableSheet, alsoIntervals: boolean): string[] {
  const computed = fieldsOf(sheet.definition).filter((field) => (field.kind === 'formula' || field.kind === 'result') && (field.type === 'integer' || (alsoIntervals && INTERVAL.test(field.alias))))
  return computed.flatMap((field) => [...cellsOf(field), ...(field.total ? [field.total] : [])])
}

/** Berechnete Zellen, in denen ein negativer Wert das Ergebnis entwertet: Anzahlen, Auswahlintervalle und die Größen der Ergebnisspalte. */
function negativeCells(sheet: AvailableSheet, results: CellMap): { field: FieldDefinition | undefined; cell: string }[] {
  return [...new Set([...countCells(sheet, true), ...resultCellsOf(sheet)])]
    .filter((cell) => {
      const value = results[cell]
      return isNumber(value) && lt(value, 0)
    })
    .map((cell) => ({ field: findField(sheet.definition, cell), cell }))
}

/** Ab dieser Größe einer Anzahl ist die Webfassung nicht mehr gegen die Vorlage geprüft (TE − AE ist dort nur noch Rundungsrauschen). */
const TESTED_RANGE = 1e15

/** Anzahlen jenseits des geprüften Zahlenbereichs: gezeigt wie gerechnet, aber als nicht belastbar ausgewiesen. */
function beyondRange(sheet: AvailableSheet, results: CellMap, t: Translate): Limitation[] {
  const found = countCells(sheet, false).some((cell) => {
    const value = results[cell]
    return isNumber(value) && Math.abs(value) >= TESTED_RANGE
  })
  return found ? [{ id: 'beyond-tested-range', kind: 'range', tone: 'warning', text: t('beyondTestedRange') }] : []
}

/**
 * Negative Ergebnisse: Die Vorlage sperrt sie nicht (mehr hochwertige Einheiten
 * als Stichprobenumfang ergeben eine negative Zufallsschicht, eine negative
 * Fehlerquote wird „✔“ gewürdigt). Die Webfassung zeigt dieselben Werte und
 * weist sie aus.
 */
function negatives(sheet: AvailableSheet, results: CellMap, t: Translate): Limitation[] {
  const found = negativeCells(sheet, results)
  if (found.length === 0) return []
  const random = found.filter((entry) => entry.field && RANDOM_STRATUM.test(entry.field.alias))
  // Je Feld einmal genannt; bei Schichtzeilen mit den betroffenen Schichten statt jeder Zelle.
  const strata = (field: FieldDefinition): string => {
    const numbers = found.filter((entry) => entry.field === field).map((entry) => stratumOf(field, entry.cell)).filter((number) => number > 0)
    return numbers.length ? ` (${t('stratum', { number: numbers.join(', ') })})` : ''
  }
  const fields = [...new Set(found.flatMap((entry) => entry.field ?? []))].map((field) => `${field.label}${strata(field)}`).join('; ')
  return [
    ...(random.length ? [{ id: 'negative-random-stratum', kind: 'negative' as const, tone: 'warning' as const, text: t('negativeRandomStratum') }] : []),
    { id: 'negative-result', kind: 'negative', tone: 'warning', text: t('negativeResult', { fields }) },
  ]
}

function interpretations(sheet: AvailableSheet, results: CellMap, t: Translate): Limitation[] {
  return fieldsOf(sheet.definition)
    .filter((field) => field.interpretation && !isBlank(results[field.cell] ?? (field.total ? results[field.total] : null)))
    .map((field) => ({ id: `interpretation-${field.cell}`, kind: 'interpretation' as const, tone: 'neutral' as const, text: `${t('interpretation')} – ${field.label}: ${field.interpretation}` }))
}

function legacy(sheet: AvailableSheet, results: CellMap): Limitation[] {
  const field = fieldsOf(sheet.definition).find((entry) => entry.alias === LEGACY_NOTICE)
  const notice = field ? results[field.cell] : null
  return typeof notice === 'string' && notice ? [{ id: 'legacy', kind: 'legacy', tone: 'warning', text: translateValue(sheet.texts, notice) }] : []
}

/** Höchstzahl der Bezeichnungen, die ein Hinweis aufzählt; weitere werden gezählt. */
const NAMED_FIELDS = 6

/** Bezeichnungen der Zellen für einen Hinweis: ohne Zellen der Ergebnisübersicht (sie wiederholen Felder des Blatts), gekürzt auf wenige. */
function namesOf(sheet: AvailableSheet, cells: readonly string[], t: Translate): string {
  const labels = [...new Set(cells.flatMap((cell) => findField(sheet.definition, cell)?.label ?? []))]
  const shown = labels.slice(0, NAMED_FIELDS).join('; ')
  return labels.length > NAMED_FIELDS ? `${shown}; ${t('andMore', { count: labels.length - NAMED_FIELDS })}` : shown || cells.slice(0, NAMED_FIELDS).join(', ')
}

/** Einschränkungen des Blatts selbst, in der Reihenfolge: mit 0 gerechnet, stille Lücken, ohne Grundlage, negative Ergebnisse, Warnhinweise, Auslegung, Altvorlage. */
export function limitationsOf(sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext, t: Translate): Limitation[] {
  const evaluation = evaluateSheet(sheet, inputs, context)
  const zero = evaluation.assumed.map((entry): Limitation => ({ id: `zero-${entry.input}`, kind: 'zero', tone: 'warning', text: t('zeroAssumedInput', { input: inputName(sheet, entry.input) }) }))
  const unfounded: Limitation[] = evaluation.withoutBasis.length ? [{ id: 'without-basis', kind: 'withoutBasis', tone: 'warning', text: t('withoutBasisHint', { fields: namesOf(sheet, evaluation.withoutBasis, t) }) }] : []
  const silent = evaluation.silent.map((input): Limitation => ({ id: `missing-${input}`, kind: 'missing', tone: 'warning', text: t('silentInput', { input: inputName(sheet, input, t) }) }))
  const warnings = (sheet.webHints?.(inputs, results, context) ?? [])
    .filter((hint) => hint.tone === 'warning' || hint.tone === 'danger')
    .map((hint): Limitation => ({ id: hint.id, kind: 'warning', tone: hint.tone, text: sheet.texts?.webHints?.[hint.id] ?? hint.text }))
  return [...zero, ...silent, ...unfounded, ...negatives(sheet, results, t), ...beyondRange(sheet, results, t), ...warnings, ...interpretations(sheet, results, t), ...legacy(sheet, results)]
}

/** Blätter, deren Einschränkungen ein Blatt mitführt: Blatt 18 die des Blatts 02 und des gewählten Verfahrens, der Bericht zusätzlich die des Blatts 18. */
function sourcesOf(sheet: SheetId, context: SheetContext): SheetId[] {
  const sources = [POPULATION_SHEET, ...(context.method ? [context.method.sheet] : [])]
  if (sheet === TOTAL_ERROR_RATE_SHEET) return sources
  if (sheet === REPORT_SHEET) return [...sources, TOTAL_ERROR_RATE_SHEET]
  return []
}

/**
 * Einschränkungen, die ein Blatt von den Blättern übernimmt, aus denen es sein
 * Ergebnis bezieht – je mit der Blattnummer davor („Blatt 03: …“). Die
 * liefernden Blätter werden dafür auf ihren Zellwerten aus dem Kontext gerechnet.
 */
export function carriedLimitations(sheet: AvailableSheet, context: SheetContext, t: Translate, sheets: readonly SheetModule[] = SHEETS): Limitation[] {
  return sourcesOf(sheet.id, context).flatMap((id) => {
    const source = findAvailableSheet(id, sheets)
    const cells = context.sheets[id]
    if (!source || !cells) return []
    const own = createContext({ parameters: context.parameters, sheets: context.sheets, policy: context.policy, ...(id === TOTAL_ERROR_RATE_SHEET ? { method: context.method } : {}) })
    const prefix = t('sheetNumber', { number: source.definition.number })
    return limitationsOf(source, cells, cells, own, t).map((entry) => ({ ...entry, id: `${id}-${entry.id}`, text: `${prefix}: ${entry.text}` }))
  })
}

/** Schränkt etwas das Ergebnis ein (Warnfarbe)? Dann erscheint ein bestandener Befund nicht uneingeschränkt grün. */
export function isQualified(limitations: readonly Limitation[]): boolean {
  return limitations.some((entry) => entry.tone === 'warning' || entry.tone === 'danger')
}
