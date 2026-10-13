import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, defaultInputs, fieldsOf, findField, inputFields, named } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { TEMPLATE_POLICY } from '../src/model/policy'
import { SUMMARY_CELLS, createContext, summaryOf } from '../src/model/sheet'
import { STRATA_COLUMNS } from '../src/model/strata'
import type { CellValue, WebHint } from '../src/model/types'
import { en as shared } from '../src/sheets/01_Parameter/texts.en'
import { sheet } from '../src/sheets/09_SRS_1Z_S/index'
import { en } from '../src/sheets/09_SRS_1Z_S/texts.en'
import { strataRows } from '../src/view/sheetView'
import { buildSummary } from '../src/view/summaryView'
import { caseInputs, loadGolden } from './golden'

const context = createContext()
const t = createTranslate()
const sample = sheet.sample.inputs
/** Variante „wie die Vorlage“: Werte ohne Grundlage stehen wie in der Vorlage. */
const likeTemplate = createContext({ policy: TEMPLATE_POLICY })
/** Zeilen mit Eingaben je Schicht. */
const INPUT_ROWS = ['12', '13', '28', '45', '46', '47']

/** Dieselben Werte der ersten Schicht in eine andere Spalte verschoben. */
function moved(inputs: Readonly<Record<string, CellValue>>, from: string, to: string): Record<string, CellValue> {
  const result: Record<string, CellValue> = { ...inputs }
  for (const row of INPUT_ROWS) {
    result[`${to}${row}`] = inputs[`${from}${row}`] ?? null
    result[`${from}${row}`] = null
  }
  return result
}

describe('Blatt 09_SRS_1Z_S', () => {
  it('Beispielwerte mit drei Schichten ergeben ein vollständiges Ergebnis', () => {
    const results = sheet.compute(sample, context)
    const result = named(sheet.definition, results)
    expect(results.C12).toBe(416)
    expect(results.C13).toBe(42300000)
    expect(result.bookValue).toBe(48500000)
    expect(result.sampleSize).toBeGreaterThanOrEqual(30)
    expect(results.C41).toBeGreaterThanOrEqual(results.C39 as number)
    expect(results.G41).toBeNull()
    expect(results.G49).toBe(0)
    expect(result.assessment).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
    expect(results.N3).toBe('Einfaches Zufallsstichprobenverfahren, 1 Zeitraum, geschichtet')
    expect(results.N10).toBe((results.C41 as number) + 4)
  })

  it('jede Zelle und jeder Alias kommt genau einmal vor; Schichtzeilen lösen sich in 20 Zellen auf', () => {
    const fields = fieldsOf(sheet.definition)
    expect(new Set(fields.map((field) => field.cell)).size).toBe(fields.length)
    expect(new Set(fields.map((field) => field.alias)).size).toBe(fields.length)
    for (const field of fields) expect(field.alias).toMatch(/^[a-z][A-Za-z0-9]*$/)
    expect(cellsOf(findField(sheet.definition, 'D12')!)).toHaveLength(20)
    expect(findField(sheet.definition, 'C12')?.alias).toBe('stratumUnits')
    expect(strataRows(sheet)).toEqual(INPUT_ROWS)
  })

  it('der Rechenkern füllt jede Zelle der Definition, die Summenzellen und die Ergebnisübersicht', () => {
    const cells = Object.keys(sheet.compute(sample, context))
    for (const field of fieldsOf(sheet.definition)) {
      for (const cell of cellsOf(field)) expect(cells).toContain(cell)
      if (field.total) expect(cells).toContain(field.total)
    }
    for (const cell of Object.values(SUMMARY_CELLS)) expect(cells).toContain(cell)
  })

  it('Vorgaben der Vorlage und Beispielwerte nur in Eingabezellen', () => {
    expect(defaultInputs(sheet.definition)).toEqual({ C18: 'zweiseitig', C21: 0.02, C33: 'Nein', C34: 'Nein' })
    const cells = inputFields(sheet.definition).flatMap(cellsOf)
    for (const cell of Object.keys(sample)) expect(cells).toContain(cell)
  })

  it('Abgleich mit der angepassten Grundgesamtheit aus Blatt 02', () => {
    expect(sheet.compute(sample, context).C15).toBeNull()
    expect(sheet.compute(sample, createContext({ sheets: { '02_Grundgesamtheit': { C51: 48000000 } } })).C15).toBe(500000)
  })

  it('die Ergebnisübersicht für Blatt 18 liest die festen Zellen N3–N11', () => {
    const results = sheet.compute(sample, context)
    expect(summaryOf(sheet.id, results)).toMatchObject({ sheet: '09_SRS_1Z_S', bookValue: 48500000, exhaustiveError: 18400, projectedError: results.C52, precision: results.C53, totalErrorRate: results.C60 })
  })

  it('dieselben Werte in Spalte D und in Spalte AA ergeben dieselben Ergebnisse', () => {
    const base = sheet.compute(sample, context)
    const shifted = sheet.compute(moved(sample, 'D', 'AA'), context)
    for (const row of ['29', '41', '42', '49', '50']) expect(shifted[`AA${row}`], `Zeile ${row}`).toEqual(base[`D${row}`])
    for (const cell of ['C12', 'C13', 'C14', 'C29', 'C30', 'C31', 'C39', 'C41', 'C45', 'C46', 'C49', 'C50', 'C52', 'C53', 'C56', 'C57', 'C60', 'C61', 'C62', 'N10']) {
      expect(shifted[cell], cell).toEqual(base[cell])
    }
    expect(shifted.D41).toBeNull()
  })

  it('die achte Schicht rechnet mit und ist als Hinweis der Webfassung gekennzeichnet', () => {
    const eight = { ...sample, G12: 40, H12: 40, I12: 40, J12: 40, AA12: 80, G13: 3e6, H13: 3e6, I13: 3e6, J13: 3e6, AA13: 6e6, G28: 9000, H28: 9000, I28: 9000, J28: 9000, AA28: 9000, AA45: 600000, AA46: 3000, AA47: 2000 }
    const results = sheet.compute(eight, context)
    expect(results.C12).toBe(656)
    expect(results.AA41).toBeGreaterThan(0)
    expect(results.C41).toBe(STRATA_COLUMNS.reduce((total, column) => total + ((results[`${column}41`] as number | null) ?? 0), 0))
    expect(sheet.webHints?.(eight, results, context).map((hint) => hint.id)).toContain('strata-beyond-template')
    expect(sheet.webHints?.(sample, sheet.compute(sample, context), context)).toEqual([{ id: 'strata-sum-exceeds-size', tone: 'warning', text: 'Summe der aufgerundeten Schichtumfänge ist größer als der anzuwendende Stichprobenumfang' }])
  })

  it('fehlt die Standardabweichung einer belegten Schicht, bleiben Umfang und Folgegrößen offen', () => {
    const results = sheet.compute({ ...sample, E28: null }, context)
    expect([results.E29, results.C29, results.C30, results.C31, results.C39, results.E41, results.C41, results.C53, results.C56, results.C61, results.C62, results.N10]).toEqual(Array.from({ length: 12 }, () => null))
    expect(results.C52).toBeCloseTo(sheet.compute(sample, context).C52 as number, 6)
    expect(isFinite(results.C60 as number)).toBe(true)
  })

  it('fehlt der Buchwert einer belegten Schicht, bleibt die Hochrechnung offen', () => {
    const results = sheet.compute({ ...sample, F13: null }, context)
    expect([results.F49, results.C49, results.C52, results.C56, results.C60, results.C62]).toEqual([null, null, null, null, null, null])
    expect(results.D49).toBeGreaterThan(0)
  })

  it('fehlt die Standardabweichung der Variablen q einer Schicht, ist ihr Beitrag 0 und wird ausgewiesen', () => {
    const results = sheet.compute({ ...sample, E47: null }, context)
    expect(results.E50).toBe(0)
    expect(results.C53).toBeGreaterThan(0)
    expect(sheet.zeroAssumed?.(results)).toEqual([{ input: 'E47', cells: ['E50', 'C50', 'C53', 'C56', 'C57', 'C58', 'C61', 'C62'] }])
    expect(sheet.zeroAssumed?.(sheet.compute(sample, context))).toEqual([])
    const all = sheet.compute({ ...sample, D47: null, E47: null, F47: null }, context)
    expect(sheet.zeroAssumed?.(all).map((entry) => entry.input)).toEqual(['D47', 'E47', 'F47'])
    expect(all.C53).toBe(0)
    expect(sheet.zeroAssumed?.(sheet.compute({ ...sample, AA12: 30, AA13: 2e6, AA28: 9000, AA45: 300000, AA46: 0 }, context)).map((entry) => entry.input)).toEqual(['AA47'])
  })

  it('Prüfhinweise je Schicht: ein gemeinsamer Hinweis oder die Schichten mit Befund', () => {
    const fine = buildSummary(sheet, sample, sheet.compute(sample, context), context, t)
    expect(fine.hints.map((hint) => hint.text)).toContain('Mindestens drei Einheiten je Zufallsschicht: ✔ ≥ 3')
    const inputs = { ...sample, G12: 5, G13: 300000, G28: 4000 }
    const short = buildSummary(sheet, inputs, sheet.compute(inputs, context), context, t)
    expect(short.hints).toContainEqual(expect.objectContaining({ id: 'G42', text: 'Schicht 4: ✖ < 3', tone: 'danger' }))
  })
})

describe('Blatt 09_SRS_1Z_S: Richtlinie für fehlende Angaben', () => {
  /** Zellen, die das leere Formular zeigen darf – alles andere wäre ein Wert ohne Eingabe. */
  const ALLOWED_WHEN_EMPTY: Record<string, CellValue> = {
    N3: 'Einfaches Zufallsstichprobenverfahren, 1 Zeitraum, geschichtet', // fester Text
    C22: '✔ ≤ 2 %', // Prüfhinweis zur Vorgabe 2 %
    C35: 'Nicht angewandt – Anh. I und II gelten', // Vorgabe „Nein“
    C37: 30, // Mindestumfang der Verordnung; das Feld bezeichnet die Untergrenze selbst
    C51: 0, N6: 0, N8: 0, N9: 0, // freiwillige Einzelbeträge: leer heißt „keine“
  }
  /** Zeilen, die für nicht belegte Schichten wie in der Vorlage 0 tragen (Hilfszeilen und Hochrechnung je Schicht). */
  const ZERO_ROWS = ['29=0', '49=0', '50=0']
  const LACKING_WHEN_EMPTY: string[] = []

  it('leeres Formular: kein Umfang, kein Ergebnis und kein Prüfhinweis ohne Eingabe', () => {
    const inputs = defaultInputs(sheet.definition)
    const evaluation = evaluateSheet(sheet, inputs, context)
    const shown = Object.entries(evaluation.cells).filter(([cell, value]) => value !== null && !(cell in inputs))
    expect(Object.fromEntries(shown.filter(([cell]) => /^[CN]\d+$/.test(cell)))).toEqual(ALLOWED_WHEN_EMPTY)
    expect(shown.filter(([cell]) => !/^[CN]\d+$/.test(cell)).map(([cell, value]) => `${cell.replace(/^[A-Z]+/, '')}=${String(value)}`).filter((entry, index, all) => all.indexOf(entry) === index)).toEqual(ZERO_ROWS)
    expect(evaluation.assumed).toEqual([])
    expect([...evaluation.lacking.keys()]).toEqual(LACKING_WHEN_EMPTY)
  })

  it('leeres Formular: Die Ergebnisspalte zeigt keine Hauptgröße; die Vorlage zeigt 0 Einheiten und Summen 0', () => {
    const inputs = defaultInputs(sheet.definition)
    expect(buildSummary(sheet, inputs, sheet.compute(inputs, context), context, t)).toMatchObject({ primaryValue: '', primaryUnit: '' })
    expect(sheet.compute(inputs, likeTemplate)).toMatchObject({ C12: 0, C13: 0, C14: 0, C23: 0, C41: 0, C49: 0, N4: 0, N10: 0 })
  })

  it('Pflichteingabe (requiredInput): „Angabe fehlt“ mit Nennung der Eingabe, auch ab der achten Schicht', () => {
    const current = evaluateSheet(sheet, { ...sample, E28: null }, context)
    expect([current.cells.E29, current.cells.C31, current.cells.C39, current.cells.N10]).toEqual([null, null, null, null])
    expect(current.lacking.get('E29')).toEqual(['E28'])
    expect(current.lacking.get('C31')).toContain('E28')
    const shown = evaluateSheet(sheet, { ...sample, E28: null }, likeTemplate)
    expect(shown.cells.E29).toBe(0)
    expect(shown.cells.C39).toBeGreaterThanOrEqual(26)
    expect(shown.assumed.find((entry) => entry.input === 'E28')?.cells).toContain('C31')
    const eighth = evaluateSheet(sheet, { ...moved(sample, 'D', 'AA'), AA28: null }, context)
    expect([eighth.cells.AA29, eighth.cells.C31, eighth.cells.AA41, eighth.cells.AA42]).toEqual([null, null, null, null])
    expect(eighth.lacking.get('AA29')).toEqual(['AA28'])
    expect(eighth.lacking.get('AA41')).toContain('AA28')
  })

  it('Standardabweichung der Stichprobe (sampleDeviation): mit 0 gerechnet und ausgewiesen', () => {
    const current = evaluateSheet(sheet, { ...sample, E47: null }, context)
    expect(current.cells.C53).toBeGreaterThan(0)
    expect(current.assumed).toEqual([{ input: 'E47', cells: ['E50', 'C50', 'C53', 'C56', 'C57', 'C58', 'C61', 'C62'] }])
  })

  it('Fehlersumme einer Schicht fehlt, eine andere trägt eine (partialErrorSum): Ergebnis wie die Vorlage, ausgewiesen', () => {
    const inputs = { ...sample, E46: null }
    const current = evaluateSheet(sheet, inputs, context)
    expect(current.cells.E49).toBe(0)
    expect(current.cells.C52).toBeCloseTo(164671.43, 2)
    expect(current.assumed).toEqual([{ input: 'E46', cells: ['E49', 'C49', 'C52', 'C56', 'C57', 'C59', 'C60', 'C61', 'C62', 'N5', 'N11'], kind: 'partialErrorSum' }])
    // Bis auf den Abgleich mit dem (hier leeren) Blatt 02 zeigt die Webfassung jede Zelle wie die Vorlage.
    expect({ ...current.cells, C15: null }).toEqual({ ...evaluateSheet(sheet, inputs, likeTemplate).cells, C15: null })
    // Trägt keine Schicht eine Fehlersumme, gibt es kein Ergebnis und nichts auszuweisen; die Vorlage zeigt 0 € je Schicht.
    const none = { ...sample, D46: null, E46: null, F46: null }
    const empty = evaluateSheet(sheet, none, context)
    expect([empty.cells.D49, empty.cells.C46, empty.cells.C49, empty.cells.C52]).toEqual([null, null, null, null])
    expect(empty.assumed).toEqual([])
    expect(sheet.compute(none, likeTemplate)).toMatchObject({ D49: 0, C46: 0, C49: 0, C52: null })
  })

  it('Wert ohne Grundlage (withoutBasis): offen ohne „Angabe fehlt“; wie die Vorlage gezeigt', () => {
    const inputs = { ...sample, C24: 0.025 }
    const current = evaluateSheet(sheet, inputs, context)
    expect([current.cells.C31, current.cells.C39, current.cells.D41, current.cells.C41, current.cells.D42, current.cells.N10]).toEqual(['TE ≤ AE', null, null, null, null, null])
    expect(current.lacking.has('D42')).toBe(false)
    expect(current.assumed).toEqual([])
    expect(sheet.compute(inputs, likeTemplate)).toMatchObject({ C31: 'TE ≤ AE', C41: 0, D41: null, D42: '✔ ≥ 3', N10: 4 })
    // Ohne Buchwert einer Zufallsschicht baute der Buchwert der Grundgesamtheit nur auf der umfassenden Schicht auf.
    const noBookValues = { ...sample, D13: null, E13: null, F13: null }
    const open = sheet.compute(noBookValues, context)
    expect([open.C13, open.C14, open.C23, open.C31, open.C39, open.N4]).toEqual([null, null, null, null, null, null])
    expect(sheet.compute(noBookValues, likeTemplate)).toMatchObject({ C13: 0, C14: 6200000, C23: 124000, C31: 2526, C39: 2526, N4: 6200000 })
  })
})

describe('Blatt 09_SRS_1Z_S: englische Arbeitsübersetzung', () => {
  /** Texte des Rechenkerns und Hinweise der Webfassung, für die eine Übersetzung fehlt. */
  function untranslated(results: Readonly<Record<string, CellValue>>, hints: readonly WebHint[], inputCells: ReadonlySet<string>): string[] {
    const texts = Object.entries(results).flatMap(([cell, value]) => (typeof value === 'string' && !inputCells.has(cell) ? [value] : []))
    const known = { ...shared, ...en.values }
    return [...texts.filter((text) => !(text in known)), ...hints.map((hint) => hint.id).filter((id) => !en.webHints?.[id])]
  }

  it('jede Feldzelle, jeder Abschnitt und die Ergebnisspalte sind übersetzt', () => {
    for (const section of sheet.definition.sections) expect(en.sections?.[section.id]?.title, section.id).toBeTruthy()
    for (const field of fieldsOf(sheet.definition)) {
      const texts = en.fields?.[field.cell]
      for (const key of ['label', 'hint', 'formula', 'interpretation'] as const) expect(Boolean(texts?.[key]), `${field.cell} ${key}`).toBe(Boolean(field[key]))
    }
    expect([en.title, en.shortTitle, en.legalBasis, en.summary?.primary, en.summary?.unit].every(Boolean)).toBe(true)
    expect(Object.keys(en.summary?.rows ?? {})).toEqual(sheet.definition.summary.rows.map((row) => row.cell))
  })

  it('jeder Text, den der Rechenkern in den Golden-Fällen liefert, und jeder Hinweis der Webfassung ist übersetzt', () => {
    const inputCells = new Set(inputFields(sheet.definition).flatMap(cellsOf))
    const missing = new Set<string>()
    for (const golden of loadGolden(sheet.id)) {
      const inputs = caseInputs(sheet, golden)
      for (const policy of [context, likeTemplate]) {
        const results = sheet.compute(inputs, policy)
        for (const text of untranslated(results, sheet.webHints?.(inputs, results, policy) ?? [], inputCells)) missing.add(text)
      }
    }
    expect([...missing]).toEqual([])
  })
})
