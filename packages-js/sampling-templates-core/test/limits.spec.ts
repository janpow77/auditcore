/**
 * Einschränkungen eines Ergebnisses reisen vollständig mit (Auflage V2 der
 * Gesamtabnahme): Je Hinweisart ein Durchstich vom Verfahrensblatt über Blatt 18
 * und den Bericht (Bildschirm und Druck) bis in den Excel-Export. Dazu der
 * Export selbst: nur bearbeitete Blätter, andere Verfahren gekennzeichnet.
 */
import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { defaultInputs } from '../src/model/definition'
import type { AvailableSheet } from '../src/model/sheet'
import type { CellMap } from '../src/model/types'
import { findAvailableSheet } from '../src/sheets/registry'
import { buildReport } from '../src/view/reportView'
import { buildSections } from '../src/view/sheetView'
import { buildSummary } from '../src/view/summaryView'
import { computeWorkspace, contextFor } from '../src/workspace/compute'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'
import { exportWorkbook, readWorkbook } from '../src/xlsx/index'

const t = createTranslate()
const sheetOf = (id: string): AvailableSheet => {
  const sheet = findAvailableSheet(id)
  if (!sheet) throw new Error(`Blatt ${id} fehlt`)
  return sheet
}
const population = sheetOf('02_Grundgesamtheit')
const total = sheetOf('18_GFQ_AnhIII')
const report = sheetOf('20_Druck_KOM')

function stateWith(method: AvailableSheet, changes: CellMap = {}, clean = false): WorkspaceState {
  const inputs = clean ? { ...defaultInputs(method.definition), ...changes } : { ...method.sample.inputs, ...changes }
  return { ...emptyWorkspace(), activeMethod: method.id, sheets: { [population.id]: population.sample.inputs, [method.id]: inputs, [total.id]: total.sample.inputs, [report.id]: report.sample.inputs } }
}

/** Alle Stellen, an denen ein Hinweis des Verfahrens stehen muss. */
async function trace(state: WorkspaceState) {
  const results = computeWorkspace(state)
  const inputs = (id: string): CellMap => (state.sheets[id] as CellMap | undefined) ?? {}
  const summary = (sheet: AvailableSheet) => buildSummary(sheet, inputs(sheet.id), results[sheet.id] ?? {}, contextFor(sheet.id, state, results), t)
  const page = buildReport(report, inputs(report.id), results[report.id] ?? {}, contextFor(report.id, state, results), t)
  const workbook = readWorkbook((await exportWorkbook(state, { now: new Date('2026-10-13T09:30:00Z') })).data)
  const texts = (name: string): string[] => [...workbook.cells(name).values()].map((cell) => String(cell.value ?? ''))
  const assessment = buildSections(total, inputs(total.id), results[total.id] ?? {}, contextFor(total.id, state, results), t).flatMap((section) => section.rows).find((row) => row.cell === 'C30')
  return {
    method: summary(sheetOf(state.activeMethod ?? '')).hints.map((hint) => hint.text),
    sheet18: summary(total).hints,
    screen: page.hints.map((hint) => hint.text),
    print: page.hints.filter((hint) => hint.printed).map((hint) => hint.text),
    exportMethod: texts('Ergebnis'),
    export18: texts(total.id),
    exportReport: texts(report.id),
    assessmentTone: assessment?.tone,
    sheets: workbook.sheetNames,
  }
}

/** Der Text steht am Verfahren und – mit der Blattnummer davor – in Blatt 18, im Bericht (Bildschirm und Druck) und in jedem Exportblatt. */
function expectEverywhere(found: Awaited<ReturnType<typeof trace>>, text: string, number: string): void {
  const carried = `Blatt ${number}: ${text}`
  expect(found.method, 'Verfahrensblatt').toContain(text)
  expect(found.sheet18.map((hint) => hint.text), 'Blatt 18').toContain(carried)
  expect(found.screen, 'Bericht am Bildschirm').toContain(carried)
  expect(found.print, 'Bericht im Druck').toContain(carried)
  expect(found.exportMethod, 'Export des Verfahrens').toContain(text)
  expect(found.export18, 'Export Blatt 18').toContain(carried)
  expect(found.exportReport, 'Export Bericht').toContain(carried)
}

describe('Hinweise reisen vom Verfahren über Blatt 18 und den Bericht bis in den Export', () => {
  const mus = sheetOf('03_MUS_1Z')

  it('„Keine Angabe, daher mit 0 berechnet“ (fehlende Standardabweichung der Stichprobe)', async () => {
    const found = await trace(stateWith(mus, { C39: null }))
    expectEverywhere(found, 'Keine Angabe, daher mit 0 berechnet: Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r) (C39)', '03')
    // Blatt 18 würdigt „✔“, zeigt es wegen des Hinweises aber nicht uneingeschränkt grün.
    expect(found.assessmentTone).toBe('warning')
    expect(found.sheet18.find((hint) => hint.id === 'C30')?.text).toMatch(/^✔ .* – Nicht uneingeschränkt: siehe Hinweise der Webfassung$/)
  })

  it('Hinweis der Webfassung in Warnfarbe (Stichprobenumfang übersteigt die Anzahl der Einheiten)', async () => {
    expectEverywhere(await trace(stateWith(mus, { C8: 50 })), 'Stichprobenumfang übersteigt die Anzahl der Einheiten der Grundgesamtheit', '03')
  })

  it('stille Lücke: Fehlersumme der hochwertigen Einheiten fehlt, obwohl Anzahl und Buchwert eingetragen sind', async () => {
    const found = await trace(stateWith(mus, { C37: null }))
    const text = found.method.find((entry) => entry.startsWith('Angabe fehlt: Summe der Fehler in den hochwertigen Einheiten'))
    expect(text).toBeDefined()
    expectEverywhere(found, text ?? '', '03')
  })

  it('negatives Ergebnis: mehr hochwertige Einheiten als Stichprobenumfang (Blatt 15)', async () => {
    const pps = sheetOf('15_NS_PPS')
    const found = await trace(stateWith(pps, { C10: 8, C14: 79 }))
    expectEverywhere(found, 'Mehr hochwertige Einheiten als Stichprobenumfang: Die Zufallsschicht ist negativ – das Ergebnis ist nicht belastbar', '15')
    expect(found.method.some((entry) => entry.startsWith('Negativer Wert wie in der Vorlage:'))).toBe(true)
  })

  it('Auslegung der Vorlage (Erhöhung bei begrenztem Umfang, Blatt 05)', async () => {
    const found = await trace(stateWith(sheetOf('05_MUS_2Z')))
    const carried = found.sheet18.map((hint) => hint.text).filter((entry) => entry.startsWith('Blatt 05: Auslegung der Vorlage'))
    expect(carried.length).toBeGreaterThan(0)
    for (const text of carried) {
      expect(found.print).toContain(text)
      expect(found.export18).toContain(text)
      expect(found.exportReport).toContain(text)
    }
  })

  it('Altvorlage: Der Hinweis steht in Blatt 18 auch bei sonst leerem Formular, im Bericht und im Export', async () => {
    const legacy = sheetOf('X2_DiffSch_2017')
    const state: WorkspaceState = { ...emptyWorkspace(), activeMethod: legacy.id, sheets: { [legacy.id]: legacy.sample.inputs, [total.id]: defaultInputs(total.definition), [report.id]: defaultInputs(report.definition) } }
    const found = await trace(state)
    const hints = found.sheet18.map((hint) => hint.text)
    expect(hints.some((entry) => entry.startsWith('Blatt X2: '))).toBe(true)
    expect(hints.some((entry) => entry.includes('hat keine Ergebnisübersicht'))).toBe(true)
    const legacyNote = hints.find((entry) => entry.startsWith('Blatt X2: ')) ?? ''
    expect(found.print).toContain(legacyNote)
    expect(found.export18).toContain(legacyNote)
  })
})

describe('Export: nur bearbeitete Blätter, andere Verfahren gekennzeichnet', () => {
  const mus = sheetOf('03_MUS_1Z')
  const srs = sheetOf('08_SRS_1Z')
  const NOT_ACTIVE = 'Nicht das gewählte Verfahren: Dieses Blatt fließt nicht in Blatt 18 und den Bericht ein.'

  it('Blätter nur mit den Vorgaben der Vorlage stehen nicht im Export', async () => {
    const state: WorkspaceState = { ...stateWith(mus), sheets: { ...stateWith(mus).sheets, [srs.id]: defaultInputs(srs.definition), '09_SRS_1Z_S': defaultInputs(sheetOf('09_SRS_1Z_S').definition) } }
    expect((await trace(state)).sheets).toEqual(['Ergebnis', population.id, total.id, report.id, '_Arbeitsstand'])
  })

  it('ein früher bearbeitetes anderes Verfahren ist im Kopf seines Blatts gekennzeichnet, das gewählte nicht', async () => {
    const state: WorkspaceState = { ...stateWith(mus), sheets: { ...stateWith(mus).sheets, [srs.id]: srs.sample.inputs } }
    const workbook = readWorkbook((await exportWorkbook(state, { now: new Date('2026-10-13T09:30:00Z') })).data)
    const texts = (name: string): string[] => [...workbook.cells(name).values()].map((cell) => String(cell.value ?? ''))
    expect(workbook.sheetNames).toContain(srs.id)
    expect(texts(srs.id)).toContain(NOT_ACTIVE)
    expect(texts('Ergebnis')).not.toContain(NOT_ACTIVE)
    expect(texts(total.id)).not.toContain(NOT_ACTIVE)
  })
})
