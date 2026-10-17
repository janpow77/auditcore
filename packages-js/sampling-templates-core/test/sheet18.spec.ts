import { describe, expect, it } from 'vitest'
import { isBlank } from '../src/excel/index'
import { defaultInputs } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { TEMPLATE_POLICY } from '../src/model/policy'
import { createContext } from '../src/model/sheet'
import type { CellMap, MethodSummary, SheetContext } from '../src/model/types'
import { sheet as population } from '../src/sheets/02_Grundgesamtheit/index'
import { sheet as mus } from '../src/sheets/03_MUS_1Z/index'
import { sheet } from '../src/sheets/18_GFQ_AnhIII/index'
import { computeWorkspace, contextFor } from '../src/workspace/compute'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'

const defaults = defaultInputs(sheet.definition)

/** Erfundene Ergebnisübersicht eines statistischen Verfahrens. */
const summary: MethodSummary = { sheet: '08_SRS_1Z', method: 'Einfaches Zufallsstichprobenverfahren, 1 Zeitraum', bookValue: 10000000, projectedError: 120000, exhaustiveError: 20000, precision: 60000, systemicErrors: 5000, anomalousErrors: 1000, sampleSize: 60, totalErrorRate: 0.0126 }

/** Blatt 02 als Ergebnis: zu prüfende Grundgesamtheit 10,2 Mio. € einschließlich 200.000 € TH-Pauschale. */
function context(method: Partial<MethodSummary> | null = {}, sheet02: CellMap = {}, policy?: SheetContext['policy']): SheetContext {
  const sheets = { '02_Grundgesamtheit': { C39: 10200000, C20: 200000, C48: 0, C49: 'keine betroffenen Einheiten', ...sheet02 } }
  return createContext({ sheets, method: method === null ? undefined : { ...summary, ...method }, policy })
}

const compute = (inputs: CellMap = {}, ctx: SheetContext = context()): CellMap => sheet.compute({ ...defaults, ...inputs }, ctx)
const hintIds = (inputs: CellMap, ctx: SheetContext): string[] => (sheet.webHints?.(inputs, sheet.compute({ ...defaults, ...inputs }, ctx), ctx) ?? []).map((hint) => hint.id)

describe('Blatt 18: Gesamtfehlerquote nach Anhang III', () => {
  it('übernimmt das aktive Verfahren und rechnet die Gesamtfehlerquote ohne TH-Pauschale', () => {
    const c = compute()
    expect(c).toMatchObject({ C4: '08_SRS_1Z', C5: 10000000, C6: 120000, C7: 20000, C8: 60000, C9: 5000, C10: 1000, C11: 'Tabelle 2 (SRS/gleiche Wahrscheinlichkeit)' })
    expect(c).toMatchObject({ C12: 10200000, C13: 200000, C14: 10000000, C16: 0, C17: 10000000, C18: 1, C19: '✔ Basis stimmt mit der erwarteten Grundgesamtheit überein' })
    expect(c.C24).toBe(120000)
    expect(c.C25).toBe(60000)
    expect(c.C26).toBeCloseTo(126000 / 10000000, 12)
    expect(c.C27).toBeCloseTo(0.0126 * 10200000, 6)
    expect(c.C28).toBeCloseTo(186000 / 10000000, 12)
    expect(c.C30).toBe('✔ unter der Wesentlichkeitsschwelle')
  })

  it('im Arbeitsstand: C4 zeigt das gewählte Verfahren, die Werte kommen aus dessen Ergebnisübersicht N3–N11', () => {
    const state: WorkspaceState = { ...emptyWorkspace(), activeMethod: mus.id, sheets: { [population.id]: population.sample.inputs, [mus.id]: mus.sample.inputs, [sheet.id]: sheet.sample.inputs } }
    const results = computeWorkspace(state)
    const own = results[sheet.id]!
    const method = results[mus.id]!
    expect(own).toMatchObject({ C4: '03_MUS_1Z', C5: method.N4, C6: method.N5, C7: method.N6, C8: method.N7, C9: method.N8, C10: method.N9, C11: 'Tabelle 1 (MUS/PPS)' })
    expect(own.C12).toBe(results[population.id]!.C39)
    expect(own.C26).toBeCloseTo(((method.N5 as number) + 0 + 0) / (own.C14 as number), 12)
    expect(contextFor(sheet.id, state, results).method?.sheet).toBe('03_MUS_1Z')
  })

  it('Ausschluss skaliert Fehler und Genauigkeit mit BV_u / BV_r; Ersetzung lässt beide unverändert', () => {
    const excluded = compute({}, context({}, { C48: 500000, C49: 'Ausschluss (Art. 3 Abs. 6 Buchst. b)' }))
    expect(excluded.C17).toBe(9500000)
    expect(excluded.C18).toBeCloseTo(10000000 / 9500000, 12)
    expect(excluded.C24).toBeCloseTo((120000 * 10000000) / 9500000, 6)
    expect(excluded.C25).toBeCloseTo((60000 * 10000000) / 9500000, 6)
    expect(excluded.C19).toBe('⚠ Basis weicht ab – Ausschluss: reduzierte, Ersetzung/keine: ursprüngliche Grundgesamtheit')
    const replaced = compute({}, context({}, { C48: 500000, C49: 'Ersetzung (Anh. III)' }))
    expect(replaced).toMatchObject({ C24: 120000, C19: '✔ Basis stimmt mit der erwarteten Grundgesamtheit überein' })
  })

  it('Ersetzung bei Tabelle 2: wie die Vorlage ohne Anpassung der Genauigkeit, mit Hinweis der Webfassung', () => {
    const ctx = context({}, { C48: 500000, C49: 'Ersetzung (Anh. III)' })
    expect(compute({}, ctx).C25).toBe(60000)
    expect(hintIds({}, ctx)).toContain('replacement-precision-not-scaled')
    expect(hintIds({}, context({ sheet: '03_MUS_1Z' }, { C48: 500000, C49: 'Ersetzung (Anh. III)' }))).not.toContain('replacement-precision-not-scaled')
  })

  it('Anpassung der hochwertigen Schicht: nur der Zufallsteil wird skaliert, EE_e wird hochgerechnet', () => {
    const c = compute({ C20: 'Ja', C21: 3000000, C22: 2000000 }, context({}, { C48: 500000, C49: 'Ausschluss (Art. 3 Abs. 6 Buchst. b)' }))
    expect(c.C23).toBe(30000)
    expect(c.C24).toBeCloseTo(((120000 - 20000) * 10000000) / 9500000 + 30000, 6)
    expect(compute({ C20: 'Nein', C21: 3000000, C22: 2000000 }).C24).toBe(120000)
  })

  it('nichtstatistisches Verfahren: Der Text in N7 bleibt Text, Genauigkeit und obere Fehlergrenze sind „n. a.“', () => {
    const c = compute({}, context({ sheet: '13_NS_GW', precision: 'n. a. (Art. 8 Abs. 2)' }))
    expect(c).toMatchObject({ C8: 'n. a. (Art. 8 Abs. 2)', C25: 'n. a.', C28: 'n. a.', C30: '✔ unter der Wesentlichkeitsschwelle', C11: 'Tabelle 2 (SRS/gleiche Wahrscheinlichkeit)' })
    expect(compute({}, context({ sheet: '15_NS_PPS' })).C11).toBe('Tabelle 1 (MUS/PPS)')
  })

  it('Würdigung: über der Schwelle, obere Fehlergrenze über der Schwelle, unter der Schwelle', () => {
    expect(compute({ C29: 0.01 }).C30).toBe('✖ Gesamtfehlerquote über der Wesentlichkeitsschwelle')
    expect(compute({ C29: 0.015 }).C30).toBe('⚠ GFQ unter, obere Fehlergrenze über der Schwelle')
    expect(compute({ C29: 0.02 }).C30).toBe('✔ unter der Wesentlichkeitsschwelle')
  })

  it('kein Verfahren, Altvorlage oder Blatt 17 aktiv: keine Übernahme, C4–C11 leer, Hinweis der Webfassung', () => {
    for (const [method, hint] of [[null, 'no-method'], [{ sheet: 'X2_DiffSch_2017' }, 'method-without-summary'], [{ sheet: '17_Unterstichprobe' }, 'method-without-summary']] as const) {
      const ctx = context(method)
      const c = compute({}, ctx)
      for (const cell of ['C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C19', 'C24', 'C26', 'C30']) expect(c[cell], cell).toBeNull()
      expect(hintIds({}, ctx)).toEqual([hint])
    }
    const state: WorkspaceState = { ...emptyWorkspace(), activeMethod: 'X2_DiffSch_2017', sheets: { [population.id]: population.sample.inputs } }
    expect(computeWorkspace(state)[sheet.id]).toMatchObject({ C4: null, C5: null, C12: 49200000 })
  })

  it('leeres Formular zeigt nur Vorgaben und freiwillige Beträge', () => {
    const results = computeWorkspace({ ...emptyWorkspace(), sheets: { [population.id]: defaultInputs(population.definition), [sheet.id]: defaults } })
    const shown = Object.entries(results[sheet.id]!).filter(([, value]) => !isBlank(value))
    // C13/C16: TH-Pauschale und nicht prüfbare Einheiten sind freiwillige Beträge (leer = keine); C15, C20, C29: Vorgaben der Vorlage.
    expect(Object.fromEntries(shown)).toEqual({ C13: 0, C15: 'keine betroffenen Einheiten', C16: 0, C20: 'Nein', C29: 0.02 })
  })

  it('Pflichteingabe BV_e,u fehlt bei „Ja“: Angabe fehlt mit Nennung der Eingabe; wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    const inputs = { ...defaults, C20: 'Ja', C22: 2000000 }
    const current = evaluateSheet(sheet, inputs, context())
    for (const cell of ['C23', 'C24', 'C26', 'C27', 'C28', 'C30']) {
      expect(current.cells[cell], cell).toBeNull()
      expect(current.lacking.get(cell), cell).toEqual(['C21'])
    }
    const template = evaluateSheet(sheet, inputs, context({}, {}, TEMPLATE_POLICY))
    expect(template.cells).toMatchObject({ C23: 0, C24: 100000 })
    expect(template.assumed).toEqual([{ input: 'C21', cells: expect.arrayContaining(['C23', 'C24', 'C26', 'C27', 'C28', 'C30']), kind: 'requiredInput' }])
    expect(hintIds(inputs, context())).toContain('high-value-incomplete')
  })

  it('Wesentlichkeitsschwelle fehlt: Würdigung offen; die Vorlage vergliche gegen 0 %', () => {
    const inputs = { ...defaults, C29: null }
    const current = evaluateSheet(sheet, inputs, context())
    expect(current.cells.C30).toBeNull()
    // Die Abweichungen kennen keine Bedingung: BV_e,u (nur bei „Ja“ nötig) wird mitgenannt, solange es leer ist.
    expect(current.lacking.get('C30')).toEqual(['C29', 'C21'])
    expect(evaluateSheet(sheet, { ...inputs, C21: 3000000 }, context()).lacking.get('C30')).toEqual(['C29'])
    expect(evaluateSheet(sheet, inputs, context({}, {}, TEMPLATE_POLICY)).cells.C30).toBe('✖ Gesamtfehlerquote über der Wesentlichkeitsschwelle')
  })

  it('Wert ohne Grundlage: Liefert das Methodenblatt keine Genauigkeit, bleiben „n. a.“ und der bestandene Hinweis aus', () => {
    const ctx = context({ precision: null })
    const current = evaluateSheet(sheet, defaults, ctx)
    expect(current.cells).toMatchObject({ C25: null, C28: null, C30: null })
    expect(current.cells.C26).toBeCloseTo(0.0126, 12)
    expect(current.assumed).toEqual([])
    expect(hintIds(defaults, ctx)).toEqual(['method-incomplete'])
    expect(evaluateSheet(sheet, defaults, context({ precision: null }, {}, TEMPLATE_POLICY)).cells).toMatchObject({ C25: 'n. a.', C28: 'n. a.', C30: '✔ unter der Wesentlichkeitsschwelle' })
    // Über der Schwelle steht die Würdigung auch ohne obere Fehlergrenze fest.
    expect(evaluateSheet(sheet, { ...defaults, C29: 0.01 }, ctx).cells.C30).toBe('✖ Gesamtfehlerquote über der Wesentlichkeitsschwelle')
  })

  it('Blatt 02 leer oder ohne Behandlung nach Art. 80 Abs. 3: nichts wird mit 0 gerechnet, Hinweise der Webfassung', () => {
    const empty = createContext({ sheets: { '02_Grundgesamtheit': population.compute(defaultInputs(population.definition), createContext()) }, method: summary })
    const c = sheet.compute(defaults, empty)
    for (const cell of ['C12', 'C14', 'C17', 'C18', 'C19', 'C26', 'C27', 'C28', 'C30']) expect(c[cell], cell).toBeNull()
    expect(c).toMatchObject({ C13: 0, C16: 0, C24: 120000, C25: 60000 })
    expect(hintIds(defaults, empty)).toEqual(['population-missing'])
    const cleared = context({}, { C49: null })
    expect(compute({}, cleared)).toMatchObject({ C15: null, C24: 120000 })
    expect(evaluateSheet(sheet, defaults, cleared).lacking.get('C15')).toEqual(['02_Grundgesamtheit!C49'])
    expect(hintIds(defaults, cleared)).toEqual(['treatment-missing'])
    expect(hintIds(defaults, context({}, { C48: 12000000, C49: 'Ausschluss (Art. 3 Abs. 6 Buchst. b)' }))).toContain('reduced-population-not-positive')
  })
})
