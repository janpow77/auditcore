import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, defaultInputs, fieldsOf, inputFields, named } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { TEMPLATE_POLICY } from '../src/model/policy'
import { SUMMARY_CELLS, createContext, summaryOf } from '../src/model/sheet'
import { subsampleTargets } from '../src/model/list'
import type { CellMap, CellValue, WebHint } from '../src/model/types'
import { en as shared } from '../src/sheets/01_Parameter/texts.en'
import { sheet } from '../src/sheets/08_SRS_1Z/index'
import { en } from '../src/sheets/08_SRS_1Z/texts.en'
import { isQualified, limitationsOf } from '../src/view/limits'
import { caseInputs, loadGolden } from './golden'

const context = createContext()
const sample = sheet.sample.inputs
/** Variante „wie die Vorlage“: Werte ohne Grundlage stehen wie in der Vorlage. */
const likeTemplate = createContext({ policy: TEMPLATE_POLICY })
const t = createTranslate()

/** Hinweis „wie in der Vorlage gezeigt, obwohl die Grundlage fehlt“ zu den Eingaben – in Warnfarbe, die Würdigung ist dann nicht uneingeschränkt grün. */
function withoutBasisHint(inputs: CellMap): { tone?: string; qualified: boolean } {
  const limitations = limitationsOf(sheet, inputs, evaluateSheet(sheet, inputs, context).cells, context, t)
  return { tone: limitations.find((entry) => entry.kind === 'withoutBasis')?.tone, qualified: isQualified(limitations) }
}

describe('Blatt 08_SRS_1Z', () => {
  it('Beispielwerte ergeben ein vollständiges Ergebnis', () => {
    const result = named(sheet.definition, sheet.compute(sample, context))
    expect(result.randomStratumPopulation).toBe(416)
    expect(result.computedSampleSize).toBe(38)
    expect(result.sampleSize).toBe(38)
    expect(result.totalSampleSize).toBe(42)
    expect(result.projectedError).toBeCloseTo(246169.23, 2)
    expect(result.precision).toBeCloseTo(167792.49, 2)
    expect(result.totalErrorRate).toBeCloseTo(0.005076, 6)
    expect(result.assessment).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
  })

  it('jede Zelle und jeder Alias kommt genau einmal vor', () => {
    const fields = fieldsOf(sheet.definition)
    expect(new Set(fields.map((field) => field.cell)).size).toBe(fields.length)
    expect(new Set(fields.map((field) => field.alias)).size).toBe(fields.length)
    for (const field of fields) expect(field.alias).toMatch(/^[a-z][A-Za-z0-9]*$/)
  })

  it('der Rechenkern füllt jede Zelle der Definition und die Ergebnisübersicht', () => {
    const cells = Object.keys(sheet.compute(sample, context))
    for (const field of fieldsOf(sheet.definition)) expect(cells).toContain(field.cell)
    for (const cell of Object.values(SUMMARY_CELLS)) expect(cells).toContain(cell)
  })

  it('Vorgaben der Vorlage: zweiseitig, 2 %, Nein, Nein', () => {
    expect(defaultInputs(sheet.definition)).toEqual({ C16: 'zweiseitig', C19: 0.02, C28: 'Nein', C29: 'Nein' })
  })

  it('Beispielwerte belegen nur Eingabezellen', () => {
    const cells = inputFields(sheet.definition).map((field) => field.cell)
    for (const cell of Object.keys(sample)) expect(cells).toContain(cell)
  })

  it('Buchwert und Anzahl kommen aus Blatt 02, solange sie nicht überschrieben sind', () => {
    const linked = createContext({ sheets: { '02_Grundgesamtheit': { C51: 1000, C52: 40 } } })
    expect(sheet.compute(defaultInputs(sheet.definition), linked)).toMatchObject({ C7: 1000, C8: 40, C12: 1000, C13: 40, C21: 20 })
    expect(sheet.compute({ ...defaultInputs(sheet.definition), C7: 500 }, linked)).toMatchObject({ C7: 500, C8: 40, C21: 10 })
  })

  it('die Ergebnisübersicht für Blatt 18 liest die festen Zellen N3–N11', () => {
    const summary = summaryOf(sheet.id, sheet.compute(sample, context))
    expect(summary).toMatchObject({ sheet: '08_SRS_1Z', method: 'Einfaches Zufallsstichprobenverfahren, 1 Zeitraum', bookValue: 48500000, exhaustiveError: 18400, sampleSize: 42, systemicErrors: 0 })
  })

  it('fehlt die Standardabweichung der Variablen q, wird mit 0 gerechnet und ausgewiesen', () => {
    const results = sheet.compute({ ...sample, C39: null }, context)
    expect(results.C44).toBe(0)
    expect(results.C53).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
    expect(sheet.zeroAssumed?.(results)).toEqual([{ input: 'C39', cells: ['C44', 'C47', 'C48', 'C49', 'C52', 'C53'] }])
    expect(sheet.zeroAssumed?.(sheet.compute(sample, context))).toEqual([])
    expect(sheet.zeroAssumed?.(sheet.compute({ ...sample, C39: null, C25: null }, context))).toEqual([])
  })

  it('fehlt die voraussichtliche Standardabweichung, bleiben Umfang, Genauigkeit und Würdigung offen', () => {
    const results = sheet.compute({ ...sample, C25: null }, context)
    expect([results.C26, results.C34, results.C35, results.C44, results.C47, results.C52, results.C53]).toEqual([null, null, null, null, null, null, null])
    expect(results.C43).toBeCloseTo(246169.23, 2)
    expect(results.C51).toBeCloseTo(0.005076, 6)
  })

  it('eine Gesamtfehlerquote über der Schwelle wird auch bei offener Genauigkeit gewürdigt', () => {
    expect(sheet.compute({ ...sample, C25: null, C37: 96000 }, context).C53).toBe('✖ Gesamtfehlerquote über der Wesentlichkeitsschwelle')
  })

  it('Summen aus den Unterstichproben: Buchwerte, Fehler und Fehler der umfassenden Schicht', () => {
    expect(subsampleTargets(sheet.definition).map((field) => [field.cell, field.subsample])).toEqual([['C36', 'bookValueSum'], ['C37', 'errorSum'], ['C40', 'highValueErrors']])
  })

  it('Hinweise der Webfassung verändern kein Ergebnis', () => {
    const inputs = { ...sample, C8: 30, C15: 0.95, C25: 90000 }
    const results = sheet.compute(inputs, context)
    expect(sheet.webHints?.(inputs, results, context).map((hint) => hint.id)).toEqual(['size-exceeds-population', 'confidence-outside-annex'])
    expect(sheet.webHints?.(sample, sheet.compute(sample, context), context)).toEqual([])
  })
})

describe('Blatt 08_SRS_1Z: Richtlinie für fehlende Angaben', () => {
  /** Zellen, die das leere Formular zeigen darf – alles andere wäre ein Wert ohne Eingabe. */
  const ALLOWED_WHEN_EMPTY: Record<string, CellValue> = {
    N3: 'Einfaches Zufallsstichprobenverfahren, 1 Zeitraum', // fester Text
    C20: '✔ ≤ 2 %', // Prüfhinweis zur Vorgabe 2 %
    C30: 'Nicht angewandt – Anh. I und II gelten', // Vorgabe „Nein“
    C32: 30, // Mindestumfang der Verordnung; das Feld bezeichnet die Untergrenze selbst
    C41: 0, N6: 0, N8: 0, N9: 0, // freiwillige Einzelbeträge: leer heißt „keine“
  }
  const ZERO_ROWS: string[] = []
  /** „Angabe fehlt“ statt der 0 der Vorlage: Buchwert und Anzahl (Verknüpfung auf das leere Blatt 02) und was unmittelbar daraus folgt. */
  const LACKING_WHEN_EMPTY = ['C7', 'N4', 'C8', 'C12', 'C13', 'C21', 'C23']

  it('leeres Formular: kein Umfang, kein Ergebnis und kein Prüfhinweis ohne Eingabe', () => {
    const inputs = defaultInputs(sheet.definition)
    const evaluation = evaluateSheet(sheet, inputs, context)
    const shown = Object.entries(evaluation.cells).filter(([cell, value]) => value !== null && !(cell in inputs))
    expect(Object.fromEntries(shown.filter(([cell]) => /^[CN]\d+$/.test(cell)))).toEqual(ALLOWED_WHEN_EMPTY)
    expect(shown.filter(([cell]) => !/^[CN]\d+$/.test(cell)).map(([cell, value]) => `${cell.replace(/^[A-Z]+/, '')}=${String(value)}`).filter((entry, index, all) => all.indexOf(entry) === index)).toEqual(ZERO_ROWS)
    expect(evaluation.assumed).toEqual([])
    expect([...evaluation.lacking.keys()]).toEqual(LACKING_WHEN_EMPTY)
  })

  it('Pflichteingabe (requiredInput): „Angabe fehlt“ mit Nennung der Eingabe; wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    const inputs = { ...sample, C25: null }
    const current = evaluateSheet(sheet, inputs, context)
    expect([current.cells.C26, current.cells.C34, current.cells.C35, current.cells.N10]).toEqual([null, null, null, null])
    expect(current.lacking.get('C34')).toEqual(['C25'])
    expect(current.assumed).toEqual([])
    const shown = evaluateSheet(sheet, inputs, likeTemplate)
    expect([shown.cells.C26, shown.cells.C34, shown.cells.C35]).toEqual([0, 26, 30])
    expect(shown.lacking.size).toBe(0)
    expect(shown.assumed.find((entry) => entry.input === 'C25')?.cells).toContain('C34')
  })

  it('Standardabweichung der Stichprobe (sampleDeviation): mit 0 gerechnet und ausgewiesen', () => {
    const current = evaluateSheet(sheet, { ...sample, C39: null }, context)
    expect(current.cells.C44).toBe(0)
    expect(current.assumed).toEqual([{ input: 'C39', cells: ['C44', 'C47', 'C48', 'C49', 'C52', 'C53'] }])
    expect(current.lacking.size).toBe(0)
  })

  it('Wert ohne Grundlage (withoutBasis): Hochrechnung 0 € ohne Fehlersumme wie die Vorlage gezeigt und ausgewiesen; offen, solange eine Pflichteingabe fehlt', () => {
    const inputs = { ...sample, C37: null }
    // Alle Pflichteingaben liegen vor: Die Webfassung zeigt, was die Vorlage zeigt, und weist den Wert aus.
    const current = evaluateSheet(sheet, inputs, context)
    expect(current.complete).toBe(true)
    expect([current.cells.C42, current.cells.C43, current.cells.C51, current.cells.C53, current.cells.N5]).toEqual([0, null, null, null, null])
    expect(current.withoutBasis).toEqual(['C42'])
    // Die Genauigkeit hängt nicht an der Fehlersumme.
    expect(current.cells.C44).toBeCloseTo(167792.49, 2)
    expect(current.lacking.size).toBe(0)
    expect(current.assumed).toEqual([])
    expect(current.cells).toEqual(evaluateSheet(sheet, inputs, likeTemplate).cells)
    expect(withoutBasisHint(inputs)).toEqual({ tone: 'warning', qualified: true })
    // Fehlt dazu eine Pflichteingabe (voraussichtliche Standardabweichung), bleibt der Wert ohne Grundlage offen.
    const incomplete = evaluateSheet(sheet, { ...inputs, C25: null }, context)
    expect(incomplete.complete).toBe(false)
    expect([incomplete.cells.C42, incomplete.cells.C43]).toEqual([null, null])
    expect(incomplete.withoutBasis).toEqual([])
    expect(incomplete.lacking.has('C42')).toBe(false)
    expect(withoutBasisHint({ ...inputs, C25: null }).tone).toBeUndefined()
    // Eine eingetragene Fehlersumme 0 ist ein Prüfergebnis.
    expect(sheet.compute({ ...sample, C37: 0 }, context)).toMatchObject({ C42: 0, C43: 18400 })
    expect(evaluateSheet(sheet, { ...sample, C37: 0 }, context).withoutBasis).toEqual([])
  })
})

describe('Blatt 08_SRS_1Z: englische Arbeitsübersetzung', () => {
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
