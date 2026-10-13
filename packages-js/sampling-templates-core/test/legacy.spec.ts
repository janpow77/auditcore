/**
 * Altvorlagen von 2017 (Blätter X1–X4 und die Tabelle X1a): Aufbau der
 * Definitionen, Hinweis der Vorlage, Hinweise der Webfassung, Schichtspalten
 * E–K von Blatt X3 und der Vollabgleich der Tabelle X1a mit der Arbeitsmappe
 * (läuft, sobald die Vorlage bereitliegt). Fehlende Angaben nach der
 * Richtlinie (`model/policy.ts`) prüft `legacy.missing.spec.ts`.
 */
import { createHash } from 'node:crypto'
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, fieldsOf, findField, inputCells, inputFields } from '../src/model/definition'
import { createContext, localizeSheet, type AvailableSheet } from '../src/model/sheet'
import { EXTRA_STRATA } from '../src/model/strata'
import type { CellValue } from '../src/model/types'
import { PARAMETERS } from '../src/sheets/01_Parameter/index'
import { sheet as x1 } from '../src/sheets/X1_KonsMUS_2017/index'
import { MANDATORY as mandatoryX1 } from '../src/sheets/X1_KonsMUS_2017/compute'
import { ERRORS_LABEL, RELIABILITY_FACTORS, RISK_LABEL, RISK_LEVELS, reliabilityFactor, sheet as x1a, table, tableCells } from '../src/sheets/X1a_RF_2017/index'
import { sheet as x2 } from '../src/sheets/X2_DiffSch_2017/index'
import { MANDATORY as mandatoryX2 } from '../src/sheets/X2_DiffSch_2017/compute'
import { sheet as x3 } from '../src/sheets/X3_DiffSch_S_2017/index'
import { MANDATORY as mandatoryX3, usedStrata } from '../src/sheets/X3_DiffSch_S_2017/compute'
import { sheet as x4 } from '../src/sheets/X4_DiffSch_2Z_2017/index'
import { MANDATORY as mandatoryX4 } from '../src/sheets/X4_DiffSch_2Z_2017/compute'
import { LEGACY_EXPANSION_FACTOR, LEGACY_LEGAL_BASIS, LEGACY_NOTICE, LEGACY_NOTICE_LABEL, LEGACY_RELIABILITY_FACTOR, LEGACY_STRATA, LEGACY_TEMPLATE_STRATA, LEGACY_Z, LegacyCells, atLeastMinimum, levelFactor } from '../src/sheets/shared/legacy'
import { buildSections, strataRows } from '../src/view/sheetView'
import { buildSummary } from '../src/view/summaryView'
import { openWorkspace } from '../src/workspace/open'
import { saveWorkspace } from '../src/workspace/save'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'
import { exportWorkbook, importWorkbook, readWorkbook, writeWorkbook } from '../src/xlsx/index'
import { loadGolden } from './golden'

const context = createContext()
const t = createTranslate()

const LEGACY: readonly { sheet: AvailableSheet; notice: string; mandatory: ReadonlySet<string>; primary: string }[] = [
  { sheet: x1, notice: 'G1', mandatory: mandatoryX1, primary: 'C11' },
  { sheet: x2, notice: 'E1', mandatory: mandatoryX2, primary: 'C11' },
  { sheet: x3, notice: 'M1', mandatory: mandatoryX3, primary: 'D15' },
  { sheet: x4, notice: 'F1', mandatory: mandatoryX4, primary: 'C16' },
]

/** Arbeitsmappe der Vorlage, falls sie bereitliegt (nie im Repository). */
function templateWorkbook(): string | null {
  const directory = process.env.AUDITCORE_SAMPLING_TEMPLATES_DIR ?? fileURLToPath(new URL('../.vorlage', import.meta.url))
  if (!existsSync(directory)) return null
  const name = readdirSync(directory)
    .filter((entry) => /^Stichprobenvorlagen_.*\.xlsx$/.test(entry))
    .sort()
    .at(-1)
  return name ? `${directory}/${name}` : null
}

describe('Gemeinsame Bausteine der Altvorlagen', () => {
  it('die fünf Stufen des Konfidenzniveaus decken sich mit der z-Tabelle aus Blatt 01', () => {
    expect(LEGACY_Z.map(([level]) => level)).toEqual(PARAMETERS.zTable.map((row) => row.confidence))
    expect(LEGACY_Z.map(([, z]) => z)).toEqual(PARAMETERS.zTable.map((row) => row.twoSided))
    for (const steps of [LEGACY_RELIABILITY_FACTOR, LEGACY_EXPANSION_FACTOR]) expect(steps.map(([level]) => level)).toEqual(LEGACY_Z.map(([level]) => level))
  })

  it('ohne zutreffende Stufe ist der Faktor 0 (FALSCH zählt in der Rechnung 0)', () => {
    expect(levelFactor(0.9, LEGACY_Z)).toBe(1.645)
    expect(levelFactor(0.9, LEGACY_RELIABILITY_FACTOR)).toBe(2.31)
    expect(levelFactor(0.95, LEGACY_EXPANSION_FACTOR)).toBe(1.6)
    expect(levelFactor(0.85, LEGACY_Z)).toBe(0)
    expect(levelFactor(null, LEGACY_Z)).toBe(0)
    expect(levelFactor('90 %', LEGACY_Z)).toBe(0)
  })

  it('Mindestumfang 30, auch für einen negativen rechnerischen Umfang', () => {
    expect([atLeastMinimum(29), atLeastMinimum(30), atLeastMinimum(31), atLeastMinimum(-400)]).toEqual([30, 30, 31, 30])
  })

  it('leere Pflichteingabe: Zelle bleibt offen; leere sonstige Eingabe zählt 0; Zelle ohne Wert ist ein Fehlerwert', () => {
    const cells: Record<string, CellValue> = { A1: 5, A2: null, A3: null, A4: 'Text' }
    const s = new LegacyCells(cells, new Set(['A2']))
    s.set('B1', ['A1', 'A3'], () => s.input('A1') + s.input('A3'))
    s.set('B2', ['A1', 'A2'], () => s.input('A1') + s.input('A2'))
    s.set('B3', ['B2'], () => s.value('B2') * 2)
    s.set('B4', ['A4'], () => s.input('A4') * 2)
    s.set('B5', ['B4'], () => s.value('B4') + 1)
    expect(cells).toMatchObject({ B1: 5, B2: null, B3: null, B4: null, B5: null })
    expect([s.isOpen('B2'), s.isOpen('B3'), s.isOpen('B4'), s.isOpen('B5'), s.isOpen('A3')]).toEqual([true, true, false, false, false])
  })
})

describe.each(LEGACY)('Altvorlage $sheet.id', ({ sheet, notice, mandatory, primary }) => {
  const results = sheet.compute(sheet.sample.inputs, context)

  it('jede Zelle und jeder Alias kommt genau einmal vor; der Rechenkern füllt jede Zelle der Definition', () => {
    const fields = fieldsOf(sheet.definition)
    const cells = fields.flatMap(cellsOf)
    expect(new Set(cells).size).toBe(cells.length)
    expect(new Set(fields.map((field) => field.alias)).size).toBe(fields.length)
    for (const field of fields) expect(field.alias).toMatch(/^[a-z][A-Za-z0-9]*$/)
    for (const cell of cells) expect(Object.keys(results)).toContain(cell)
  })

  it('trägt den Hinweis der Vorlage wortgleich als erste Zeile und unter den Prüfhinweisen', () => {
    expect(sheet.definition.sections[0]?.fields[0]).toMatchObject({ cell: notice, type: 'check', kind: 'formula' })
    expect(results[notice]).toBe(LEGACY_NOTICE)
    expect(sheet.compute({}, context)[notice]).toBe(LEGACY_NOTICE)
    expect(LEGACY_NOTICE).toContain('Keine gebrauchsfertige Methode im Sinne der DelVO (EU) 2023/67')
    expect(LEGACY_NOTICE).toContain('ErwG 15 DelVO')
    expect(sheet.definition.legalBasis).toBe(LEGACY_LEGAL_BASIS)
    const hints = buildSummary(sheet, sheet.sample.inputs, results, context, t).hints
    expect(hints[0]).toMatchObject({ id: notice, text: LEGACY_NOTICE, source: 'template' })
    expect(buildSections(sheet, sheet.sample.inputs, results, context, t)[0]?.rows[0]).toMatchObject({ cell: notice, display: LEGACY_NOTICE })
  })

  it('Beispielwerte ergeben ein vollständiges Ergebnis; Hinweis der Webfassung nur zur Rundung der Schichtumfänge (X3)', () => {
    const open = fieldsOf(sheet.definition)
      .filter((field) => field.kind === 'formula' && !field.columns)
      .filter((field) => results[field.cell] === null)
    expect(open.map((field) => field.cell)).toEqual([])
    expect(results[primary]).toBeGreaterThanOrEqual(30)
    // X3: 42 + 30 + 12 = 84 Einheiten bei n = 83 – die Fußnote der Vorlage beschreibt genau das.
    expect((sheet.webHints?.(sheet.sample.inputs, results, context) ?? []).map((hint) => hint.id)).toEqual(sheet === x3 ? ['strata-sum-exceeds-size'] : [])
    expect(sheet.zeroAssumed?.(results) ?? []).toEqual([])
  })

  it('Pflichteingaben sind Eingabezellen der Definition; Abweichungen nennen nur Pflichteingaben', () => {
    const inputs = new Set(inputCells(sheet.definition))
    for (const cell of mandatory) expect(inputs.has(cell), cell).toBe(true)
    // Pflichteingabe fehlt: Die Abweichung nennt nur Pflichteingaben. Wert ohne Grundlage: Sie nennt die fehlende Größe, eine Formelzelle.
    const formulas = new Set(fieldsOf(sheet.definition).filter((field) => field.kind === 'formula').flatMap(cellsOf))
    for (const deviation of sheet.deviations) {
      const allowed = deviation.kind === 'withoutBasis' ? formulas : mandatory
      for (const cell of deviation.whenEmpty) expect(allowed.has(cell), `${deviation.cell} ← ${cell}`).toBe(true)
    }
    expect(sheet.deviations.filter((deviation) => deviation.check !== undefined)).toEqual([])
  })

  it('das Konfidenzniveau ist eine Auswahl der fünf Stufen; ohne Auswahl bleiben Faktor und Umfang offen', () => {
    const level = inputFields(sheet.definition).find((field) => field.alias === 'confidenceLevel')!
    expect(level).toMatchObject({ type: 'choice', list: 'confidence' })
    const without = sheet.compute({ ...sheet.sample.inputs, [level.cell]: null }, context)
    expect(without[primary]).toBeNull()
    const outside = sheet.compute({ ...sheet.sample.inputs, [level.cell]: 0.85 }, context)
    expect(outside[primary]).toBe(sheet.id.startsWith('X4') ? 0 : 30)
  })

  it('Golden-Fälle: mindestens 12 benannte Fälle und 100 vollständige Zufallsbelegungen', () => {
    const cases = loadGolden(sheet.id)
    const random = cases.filter((entry) => entry.name.startsWith('Zufallsbelegung'))
    expect(random.length).toBeGreaterThanOrEqual(100)
    expect(cases.length - random.length).toBeGreaterThanOrEqual(12)
    for (const entry of random) for (const cell of mandatory) if (!/^(?:[E-K]|A[A-M])\d+$/.test(cell)) expect(entry.eingaben[cell], `${entry.name} ${cell}`).not.toBeUndefined()
  })

  it('Arbeitsstand und Excel-Export: Eingaben und Ergebnisse bleiben erhalten', async () => {
    const state: WorkspaceState = { ...emptyWorkspace(), activeMethod: sheet.id, sheets: { [sheet.id]: sheet.sample.inputs } }
    const opened = await openWorkspace((await saveWorkspace(state)).text)
    expect(opened).toMatchObject({ ok: true, notices: [] })
    expect(opened.ok && opened.state.sheets[sheet.id]).toEqual(sheet.sample.inputs)
    const exported = await exportWorkbook(state)
    const imported = importWorkbook(exported.data)
    const reopened = imported.kind === 'workspace' ? await openWorkspace(imported.text) : null
    expect(reopened?.ok && reopened.state).toEqual(state)
    const texts = [...readWorkbook(exported.data).cells('Ergebnis').values()].map((cell) => cell.value)
    expect(texts).toContain(LEGACY_NOTICE)
    expect(texts).toContain(results[primary])
  })

  it('englische Oberfläche: Titel und Hinweis übersetzt, Zellen und Werte unverändert', () => {
    const localized = localizeSheet(sheet, 'en')
    expect(localized.compute(sheet.sample.inputs, context)).toEqual(results)
    expect(localized.definition.title).not.toBe(sheet.definition.title)
    const rows = buildSections(localized, sheet.sample.inputs, results, context, createTranslate(undefined, 'en'))[0]?.rows
    expect(rows?.[0]?.display).toContain('Not an off-the-shelf sampling methodology')
    expect(rows?.[1]?.label).toBe(sheet.definition.sections[0]?.fields[1]?.label)
  })
})

describe('Hinweise der Webfassung zu den Altvorlagen', () => {
  const ids = (sheet: AvailableSheet, inputs: Record<string, CellValue>): string[] => (sheet.webHints?.(inputs, sheet.compute(inputs, context), context) ?? []).map((hint) => hint.id)

  it('TE ≤ AE bzw. TE ≤ AE × EF', () => {
    expect(ids(x1, { ...x1.sample.inputs, C4: 0.95, C7: 0.0126 })).toEqual(['tolerable-error-not-above-anticipated'])
    expect(ids(x2, { ...x2.sample.inputs, C7: 0.02 })).toEqual(['tolerable-error-not-above-anticipated'])
    expect(ids(x3, { ...x3.sample.inputs, D11: 0.0201 })).toContain('tolerable-error-not-above-anticipated')
    expect(ids(x4, { ...x4.sample.inputs, C12: 0.025 })).toContain('tolerable-error-not-above-anticipated-1')
    expect(ids(x4, { ...x4.sample.inputs, C27: 0.02 })).toContain('tolerable-error-not-above-anticipated-2')
  })

  it('X4: negativer Nenner bei der Neuberechnung ergibt wie in der Vorlage einen negativen Umfang – mit Hinweis', () => {
    const inputs = { ...x4.sample.inputs, C22: 21000 }
    expect(x4.compute(inputs, context).C31).toBe(-11)
    expect(ids(x4, inputs)).toEqual(expect.arrayContaining(['negative-denominator', 'below-three-units']))
  })

  it('Stichprobenumfang über der Anzahl der Einheiten; X3: Summe der Schichtumfänge über dem Gesamtumfang', () => {
    expect(ids(x2, { ...x2.sample.inputs, C3: 25, C4: 900000 })).toContain('size-exceeds-population')
    expect(ids(x3, { ...x3.sample.inputs, D11: 0.0129 })).toContain('strata-sum-exceeds-size')
  })
})

describe('Blatt X3: Schichten in den Spalten E–K', () => {
  /** Die Beispielschicht aus Spalte E in eine andere Spalte gelegt. */
  const moved = (column: string): Record<string, CellValue> => ({ D9: 0.9, D11: 0.005, [`${column}6`]: 24000000, [`${column}7`]: 210, [`${column}8`]: 9000, [`${column}19`]: 15000, [`${column}21`]: 2800 })
  const scalars = ['D1', 'D3', 'D4', 'D15', 'D23', 'D24', 'D25', 'D26', 'D27', 'D28', 'D29', 'D30']

  it('sieben Spalten der Vorlage (E–K), dreizehn weitere der Webfassung (AA–AM)', () => {
    expect(LEGACY_TEMPLATE_STRATA).toEqual(['E', 'F', 'G', 'H', 'I', 'J', 'K'])
    expect(LEGACY_STRATA).toEqual([...LEGACY_TEMPLATE_STRATA, ...EXTRA_STRATA])
    const field = findField(x3.definition, 'E6')!
    expect(cellsOf(field)).toHaveLength(20)
    expect(field.total).toBeUndefined()
    expect(findField(x3.definition, 'K21')?.alias).toBe('stratumSampleDeviation')
    expect(findField(x3.definition, 'AM19')?.alias).toBe('stratumSampleError')
    expect(findField(x3.definition, 'D6')).toBeUndefined()
    expect(strataRows(x3)).toEqual(['6', '7', '8', '18', '19', '21'])
  })

  it('dieselben Werte in Spalte E, K und AA ergeben dieselben Ergebnisse', () => {
    const inE = x3.compute(moved('E'), context)
    for (const column of ['K', 'AA', 'AM']) {
      const other = x3.compute(moved(column), context)
      for (const cell of scalars) expect(other[cell], `${column} ${cell}`).toBe(inE[cell])
      for (const line of [17, 20, 22]) expect(other[`${column}${line}`], `${column}${line}`).toBe(inE[`E${line}`])
    }
    expect(inE.D15).toBeGreaterThanOrEqual(30)
  })

  it('die achte Schicht rechnet mit und ist als Hinweis der Webfassung gekennzeichnet', () => {
    const eight = { ...x3.sample.inputs, AA6: 2000000, AA7: 40, AA8: 6000, AA19: 900, AA21: 1500 }
    const results = x3.compute(eight, context)
    expect(results.D1).toBe(50500000)
    expect(results.D3).toBe(460)
    expect(results.AA17).toBeGreaterThan(0)
    expect(usedStrata(eight)).toEqual(['E', 'F', 'G', 'AA'])
    expect(x3.webHints?.(eight, results, context).map((hint) => hint.id)).toContain('strata-beyond-template')
  })

  it('leere Schicht zwischen belegten wird als Hinweis der Webfassung genannt', () => {
    const inputs = { ...moved('E'), ...moved('K') }
    const hints = x3.webHints?.(inputs, x3.compute(inputs, context), context) ?? []
    expect(hints).toContainEqual({ id: 'strata-gap', tone: 'neutral', text: 'Leere Schicht zwischen belegten Schichten: Belegt sind die Schichten 1, 7' })
    expect((x3.webHints?.(x3.sample.inputs, x3.compute(x3.sample.inputs, context), context) ?? []).map((hint) => hint.id)).not.toContain('strata-gap')
  })

  it('nicht belegte Schicht: Umfang 0 wie in der Vorlage, sonst kein Wert', () => {
    const results = x3.compute(x3.sample.inputs, context)
    expect([results.H17, results.H20, results.H22]).toEqual([0, null, null])
    expect([results.E17, results.F17, results.G17]).toEqual([42, 30, 12])
  })

  it('belegte Schicht ohne Umfang: Summen und Folgegrößen bleiben offen', () => {
    const results = x3.compute({ ...x3.sample.inputs, H6: 2000000 }, context)
    expect(results.D1).toBe(50500000)
    expect([results.D3, results.D4, results.D15, results.E17, results.D23]).toEqual([null, null, null, null, null])
  })

  it('Anzeigemodell: Schichtzeilen ohne Summenzelle, je Schicht eine Zelle ab Spalte E', () => {
    const rows = buildSections(x3, x3.sample.inputs, x3.compute(x3.sample.inputs, context), context, t).flatMap((section) => [...section.rows])
    const bookValue = rows.find((row) => row.cell === 'E6')!
    expect(bookValue.strata?.total).toBeNull()
    expect(bookValue.strata?.cells.slice(0, 8).map((cell) => cell.cell)).toEqual(['E6', 'F6', 'G6', 'H6', 'I6', 'J6', 'K6', 'AA6'])
    expect(rows.find((row) => row.cell === 'E17')?.strata?.cells[1]).toMatchObject({ cell: 'F17', display: '30' })
  })

  it('Import der ausgefüllten Vorlage liest die Schichtspalten E–K', () => {
    const line = (values: readonly (number | null)[]): ({ value: number } | null)[] => [null, null, null, null, ...values.map((value) => (value === null ? null : { value }))]
    const rows = Array.from({ length: 8 }, (_, index) => (index === 5 ? line([100, 200, null, null, null, null, 300]) : index === 6 ? line([10, 20, null, null, null, null, 30]) : []))
    const imported = importWorkbook(writeWorkbook([{ name: 'X3_DiffSch_S_2017', rows }]))
    expect(imported).toMatchObject({ kind: 'template', sheets: { X3_DiffSch_S_2017: { E6: 100, F6: 200, K6: 300, E7: 10, K7: 30 } } })
  })
})

describe('Blatt X1a: Tabelle der Zuverlässigkeitsfaktoren', () => {
  const cells = tableCells()

  it('bleibt ohne Bedienblatt im Register und liefert die Tabelle als Daten', () => {
    expect(x1a.available).toBe(false)
    expect(RISK_LEVELS).toEqual([0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.37, 0.4, 0.5])
    expect(RELIABILITY_FACTORS).toHaveLength(51)
    for (const factors of RELIABILITY_FACTORS) expect(factors).toHaveLength(10)
    expect(reliabilityFactor(0, 0.05)).toBe(3)
    expect(reliabilityFactor(1, 0.1)).toBe(3.89)
    expect(reliabilityFactor(50, 0.5)).toBe(50.67)
    expect(() => reliabilityFactor(51, 0.05)).toThrow()
    expect(() => reliabilityFactor(1, 0.12)).toThrow()
    expect(() => reliabilityFactor(1.5, 0.05)).toThrow()
  })

  it('als Nachschlagetabelle: Überschrift, Quelle, Spalten und 51 Zeilen mit Zahlen – ohne Kenntnis des Blatts anzeigbar', () => {
    expect(table.title).toBe('Zuverlässigkeitsfaktoren')
    expect(table.source).toBe(LEGACY_NOTICE_LABEL)
    expect(LEGACY_NOTICE.startsWith(table.source)).toBe(true)
    expect(table.notes).toEqual([LEGACY_NOTICE])
    expect(table.columns).toHaveLength(11)
    expect(table.columns[0]).toEqual({ key: 'A', label: ERRORS_LABEL, format: '0' })
    expect(table.columns[2]).toEqual({ key: 'C', label: '5 %', value: 0.05, group: RISK_LABEL, format: '0.00' })
    expect(table.columns.slice(1).map((column) => column.value)).toEqual(RISK_LEVELS)
    expect(table.columns.map((column) => column.label).slice(1)).toEqual(['1 %', '5 %', '10 %', '15 %', '20 %', '25 %', '30 %', '37 %', '40 %', '50 %'])
    expect(table.rows).toHaveLength(51)
    for (const row of table.rows) {
      expect(row).toHaveLength(table.columns.length)
      for (const value of row) expect(typeof value).toBe('number')
    }
    expect(table.rows[0]).toEqual([0, 4.61, 3, 2.3, 1.9, 1.61, 1.39, 1.2, 0.99, 0.92, 0.69])
    expect(table.rows[50]?.[0]).toBe(50)
    // Jede Zelle der Tabelle steht an ihrer Adresse in der Vorlage (Spalte = key, Zeile = 3 + Index).
    table.rows.forEach((row, index) => row.forEach((value, column) => expect(cells[`${table.columns[column]!.key}${3 + index}`]).toBe(value)))
  })

  it('X1 liest die Tabelle nicht: feste Stufen 1,21 und 2,31 statt 1,2 und 2,3 der Tabelle (Zeile „0 Fehler“)', () => {
    const fixed = LEGACY_RELIABILITY_FACTOR.map(([level, factor]) => [factor, reliabilityFactor(0, Number((1 - level).toFixed(2)))])
    expect(fixed).toEqual([[0.92, 0.92], [1.21, 1.2], [1.61, 1.61], [2.31, 2.3], [3, 3]])
  })

  it('574 Zellen; die Faktoren steigen mit der Fehlerzahl und fallen mit dem Risiko', () => {
    expect(Object.keys(cells)).toHaveLength(574)
    expect(cells.M1).toBe(LEGACY_NOTICE)
    for (let errors = 0; errors < RELIABILITY_FACTORS.length; errors += 1) {
      const factors = RELIABILITY_FACTORS[errors]!
      for (let index = 1; index < factors.length; index += 1) expect(factors[index]!).toBeLessThan(factors[index - 1]!)
      if (errors > 0) for (let index = 0; index < factors.length; index += 1) expect(factors[index]!).toBeGreaterThan(RELIABILITY_FACTORS[errors - 1]![index]!)
    }
  })

  it('Prüfsumme der Tabelle (ändert sich nur mit den Daten)', () => {
    const canonical = JSON.stringify(Object.entries(cells).sort(([left], [right]) => (left < right ? -1 : 1)))
    expect(createHash('sha256').update(canonical).digest('hex')).toBe('90aae795eb7ccbaff38246299e284119987a54ac3f9751e56ca19c6f7a6d58bd')
  })

  const workbook = templateWorkbook()
  it.skipIf(!workbook)('Vollabgleich aller 574 Zellen mit der Arbeitsmappe der Vorlage', () => {
    const read = readWorkbook(new Uint8Array(readFileSync(workbook!))).cells('X1a_RF_2017')
    const found = Object.fromEntries([...read.entries()].filter(([, cell]) => cell.value !== null && cell.value !== '').map(([address, cell]) => [address, cell.value]))
    expect(Object.keys(found)).toHaveLength(574)
    expect([...read.values()].filter((cell) => cell.formula)).toEqual([])
    expect(found).toEqual(cells)
  })
})
