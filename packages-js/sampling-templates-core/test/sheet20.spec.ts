import { describe, expect, it } from 'vitest'
import { isBlank } from '../src/excel/index'
import { createTranslate, type Translate } from '../src/i18n/messages'
import { defaultInputs } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { TEMPLATE_POLICY } from '../src/model/policy'
import { createContext } from '../src/model/sheet'
import type { CellMap, MethodSummary, SheetContext } from '../src/model/types'
import { sheet as population } from '../src/sheets/02_Grundgesamtheit/index'
import { sheet as mus } from '../src/sheets/03_MUS_1Z/index'
import { sheet as total } from '../src/sheets/18_GFQ_AnhIII/index'
import { sheet } from '../src/sheets/20_Druck_KOM/index'
import { buildReport, type ReportBlock } from '../src/view/reportView'
import { computeWorkspace, contextFor } from '../src/workspace/compute'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'

const t = createTranslate()
const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ').replaceAll(String.fromCharCode(8239), ' ')
const defaults = defaultInputs(sheet.definition)
const summary: MethodSummary = { sheet: '08_SRS_1Z', method: 'Einfaches Zufallsstichprobenverfahren, 1 Zeitraum', bookValue: 10000000, projectedError: 120000, exhaustiveError: 20000, precision: 60000, systemicErrors: 5000, anomalousErrors: 1000, sampleSize: 60, totalErrorRate: 0.0126 }

/** Erfundene Ergebnisse der Blätter 02 und 18: Hochrechnungsbasis 10 Mio. €, Gesamtfehlerquote 1,26 %. */
function context(sheet18: CellMap = {}, sheet02: CellMap = {}, policy?: SheetContext['policy']): SheetContext {
  const sheets = {
    '02_Grundgesamtheit': { C9: '2021DE16RFPR000 (Beispiel)', C12: '2025/2026', C16: 10200000, C23: 432, C51: 10000000, C52: 420, C55: 12, C56: 0, ...sheet02 },
    '18_GFQ_AnhIII': { C4: '08_SRS_1Z', C14: 10000000, C24: 120000, C25: 60000, C26: 0.0126, C27: 128520, C28: 0.0186, C29: 0.02, ...sheet18 },
  }
  return createContext({ sheets, method: summary, policy })
}

const compute = (inputs: CellMap = {}, ctx: SheetContext = context()): CellMap => sheet.compute({ ...defaults, ...inputs }, ctx)

/** Arbeitsstand mit den Beispielwerten der Blätter 02, 03, 18 und 20. */
function workspace(changes: Partial<Record<string, CellMap>> = {}, activeMethod: string | null = mus.id): WorkspaceState {
  return { ...emptyWorkspace(), activeMethod, sheets: { [population.id]: population.sample.inputs, [mus.id]: mus.sample.inputs, [total.id]: total.sample.inputs, [sheet.id]: sheet.sample.inputs, ...changes } as WorkspaceState['sheets'] }
}

function report(state: WorkspaceState) {
  const results = computeWorkspace(state)
  return buildReport(sheet, state.sheets[sheet.id] as CellMap, results[sheet.id]!, contextFor(sheet.id, state, results), t)
}

describe('Blatt 20: Rechenkern', () => {
  it('Kopf, Kennzahlen aus Blatt 02, dem aktiven Verfahren und Blatt 18', () => {
    const c = compute({ J4: '13.10.2026', J6: 5300000 })
    // Ohne Bezeichnung des Programms beginnt die Kopfzeile mit der CCI-Nummer; ein fester Programmname steht nirgends.
    expect(c.A6).toBe('CCI 2021DE16RFPR000 · Geschäftsjahr 2025/2026 · vorläufig')
    expect(compute({ J5: null }).A6).toBe('CCI 2021DE16RFPR000 · Geschäftsjahr 2025/2026')
    expect(compute({ W4: 'Programm Musterland' }).A6).toBe('Programm Musterland · CCI 2021DE16RFPR000 · Geschäftsjahr 2025/2026 · vorläufig')
    expect(compute({ W5: 'Prüfbehörde Musterland', W7: 'Musterstadt' }).W8).toBe('Prüfbehörde Musterland, Musterstadt')
    expect(c.W8).toBeNull()
    expect(c).toMatchObject({ G6: '13.10.2026', F11: 432, G11: 10200000, F12: 420, G12: 10000000, F13: 12, G13: 0, F14: 60, G14: 5300000, D15: 'Einfaches Zufallsstichprobenverfahren, 1 Zeitraum' })
    expect(c).toMatchObject({ G32: 0.0126, G33: 120000, G34: 60000, G35: 0.0186, G36: 128520, A37: 'Die Gesamtfehlerquote liegt unter der Signifikanzschwelle.' })
    expect(compute({}, context({ C29: 0.01 })).A37).toBe('Die Gesamtfehlerquote liegt über der Signifikanzschwelle.')
  })

  it('im Arbeitsstand erhält auch Blatt 20 die Ergebnisübersicht des aktiven Verfahrens', () => {
    const state = workspace()
    const results = computeWorkspace(state)
    expect(results[sheet.id]).toMatchObject({ F14: results[mus.id]!.N10, D15: 'MUS-Standardansatz, 1 Zeitraum', G32: results[total.id]!.C26, G36: results[total.id]!.C27 })
    expect(contextFor(sheet.id, state, results).method?.sheet).toBe(mus.id)
  })

  it('nichtstatistisch: „nicht berechnet“; kein Verfahren oder Altvorlage: keine Übernahme', () => {
    expect(compute({}, context({ C25: 'n. a.', C28: 'n. a.' }))).toMatchObject({ G34: 'nicht berechnet', G35: 'nicht berechnet' })
    expect(compute({}, context({ C4: null }))).toMatchObject({ F14: null, D15: null })
    const legacy = computeWorkspace(workspace({}, 'X2_DiffSch_2017'))
    expect(legacy[sheet.id]).toMatchObject({ F14: null, D15: null, G32: null, A37: null })
    expect(legacy[total.id]!.C4).toBeNull()
  })

  it('Tabelle der Fehlerfälle: Quote je Fall, Summen, „davon vorläufig“ nach dem Anfang des Stands', () => {
    const c = compute({ C20: 250000, D20: 5000, G20: 'vorläufig', C21: 100000, D21: 1000, G21: 'Vorläufig – Anhörung', C22: 50000, D22: 500, G22: 'endgültig', C23: 80000, D24: 70, G24: ' vorläufig' })
    expect(c).toMatchObject({ E20: 0.02, E21: 0.01, E22: 0.01, E23: null, E24: null, C28: 480000, D28: 6570, F28: 'davon vorläufig: ', G28: 6000 })
    expect(compute()).toMatchObject({ C28: null, D28: null, G28: null })
    // Buchwert 0: Die Vorlage zeigt #DIV/0!, die Webfassung keinen Wert und einen Hinweis.
    const zero = compute({ C20: 0, D20: 100 })
    expect(zero.E20).toBeNull()
    expect(sheet.webHints?.({}, zero, context()).map((hint) => hint.id)).toEqual(['own-header', 'case-book-value-zero'])
  })

  it('Restfehlerquote nach der Logik der Kommissionsvorlage und Finanzkorrektur bis 2 %', () => {
    const c = compute({ J7: 1000000, J8: 50000 })
    expect(c).toMatchObject({ G40: 1000000, G41: 50000 })
    expect(c.G42).toBeCloseTo((0.0126 * 9000000 - 50000) / (9000000 - 50000), 12)
    expect(c.G43).toBe(0)
    const above = compute({}, context({ C26: 0.03 }))
    expect(above.G42).toBeCloseTo(0.03, 12)
    expect(above.G43).toBeCloseTo((0.03 * 10000000 - 0.02 * 10000000) / 0.98, 6)
    expect(compute()).toMatchObject({ G40: null, G41: null })
  })

  it('Restfehlerquote nicht bestimmbar: Der Betrag der Vorlage hat keine Grundlage und bleibt aus', () => {
    const inputs = { ...defaults, J7: 6000000, J8: 4000000 }
    expect(sheet.compute(inputs, context())).toMatchObject({ G42: null, G43: null })
    expect(sheet.compute(inputs, context({}, {}, TEMPLATE_POLICY)).G43).toBeCloseTo((0.0126 * 4000000 - 4000000) / 0.98, 6)
    expect(sheet.webHints?.(inputs, sheet.compute(inputs, context()), context()).map((hint) => hint.id)).toContain('residual-rate-undefined')
  })

  it('leeres Formular zeigt nur feste Texte der Vorlage, die Vorgabe und die freiwilligen Größen', () => {
    const results = computeWorkspace({ ...emptyWorkspace(), sheets: { [population.id]: defaultInputs(population.definition), [total.id]: defaultInputs(total.definition), [sheet.id]: defaults } })
    const shown = Object.fromEntries(Object.entries(results[sheet.id]!).filter(([, value]) => !isBlank(value)))
    // A6: Kopfzeile ohne Programm, CCI und Geschäftsjahr; F13/G13: negative Grundgesamtheit (leer = keine); F28: fester Text; J5: Vorgabe.
    expect(shown).toEqual({ A6: 'CCI  · Geschäftsjahr  · vorläufig', F13: 0, G13: 0, F28: 'davon vorläufig: ', J5: 'vorläufig' })
  })

  it('Pflichteingaben anderer Blätter: Angabe fehlt mit Nennung; wie die Vorlage mit 0 gerechnet', () => {
    const ctx = context({ C29: null }, { C23: null, C16: null })
    const current = evaluateSheet(sheet, defaults, ctx)
    expect(current.cells).toMatchObject({ F11: null, G11: null, A37: null })
    expect(current.lacking.get('F11')).toEqual(['02_Grundgesamtheit!C23'])
    expect(current.lacking.get('G11')).toEqual(['02_Grundgesamtheit!C16'])
    expect(current.lacking.get('A37')).toEqual(['18_GFQ_AnhIII!C29'])
    const template = evaluateSheet(sheet, defaults, context({ C29: null }, { C23: null, C16: null }, TEMPLATE_POLICY))
    expect(template.cells).toMatchObject({ F11: 0, G11: 0, A37: 'Die Gesamtfehlerquote liegt über der Signifikanzschwelle.' })
    expect(template.assumed.map((entry) => entry.input)).toEqual(['02_Grundgesamtheit!C23', '02_Grundgesamtheit!C16', '18_GFQ_AnhIII!C29'])
  })

  it('Wert ohne Grundlage: Ist Blatt 18 offen, weil dort eine Angabe fehlt, übernimmt der Bericht weder Zahl noch „nicht berechnet“; sind alle Angaben da, zeigt er wie die Vorlage „nicht berechnet“', () => {
    const open = { C24: null, C25: null, C26: null, C27: null, C28: null }
    // `sourceIncomplete`: Blatt 18 oder dem Verfahren fehlt eine Pflichteingabe (setzt `contextFor` im Arbeitsstand).
    expect(evaluateSheet(sheet, defaults, { ...context(open), sourceIncomplete: true }).cells).toMatchObject({ G32: null, G33: null, G34: null, G35: null, G36: null, A37: null, G42: null, G43: null })
    const complete = evaluateSheet(sheet, defaults, context(open))
    expect(complete.cells).toMatchObject({ G32: null, G33: null, G34: 'nicht berechnet', G35: 'nicht berechnet' })
    expect(complete.withoutBasis).toEqual(expect.arrayContaining(['G34', 'G35']))
    expect(sheet.compute(defaults, context({ C25: null, C28: null }, {}, TEMPLATE_POLICY))).toMatchObject({ G34: 'nicht berechnet', G35: 'nicht berechnet' })
  })
})

describe('Blatt 20: Berichtsansicht', () => {
  const tables = (blocks: readonly ReportBlock[]) => blocks.filter((block): block is Extract<ReportBlock, { kind: 'table' }> => block.kind === 'table')

  it('liefert die Druckseite als Daten: Kopf, vier Abschnitte, Tabellen, Freitexte, Fußzeile', () => {
    const page = report(workspace())
    expect(page).toMatchObject({ title: 'Vorhabenprüfungen – Stichprobe und Ergebnisse', cofinanced: ['Kofinanziert von der', 'Europäischen Union'], asOf: 'Stand 13.10.2026', footer: 'Prüfbehörde Musterland (Beispiel), Referat Beispiel, Musterstadt', footerPlaceholder: '', programmePlaceholder: '' })
    expect(page.subtitle).toBe('Beispielprogramm EFRE Musterland 2021–2027 · CCI 2021DE16RFPR000 · Geschäftsjahr 01.07.2025–30.06.2026 · vorläufig')
    expect(page.sections.map((section) => section.title)).toEqual(['1. Grundgesamtheit und Stichprobe', '2. Ergebnisse der Vorhabenprüfungen', '3. Hochrechnung und Gesamtfehlerquote', '4. Restfehlerquote und weiteres Vorgehen'])
    expect(page.sections.map((section) => section.blocks.map((block) => block.kind))).toEqual([['text', 'table'], ['text', 'table'], ['text', 'table', 'statement'], ['table', 'text']])
    expect(page.labels).toEqual({ report: 'Bericht', print: 'Drucken / als PDF sichern', hints: 'Hinweis der Webfassung' })
    expect(page.notes).toEqual([t('disclaimer'), t('templateStatus')])
    expect(page.controls.title).toBe('Steuerfelder (werden nicht gedruckt)')
    expect(page.controls.fields.map((field) => `${field.cell} ${field.label} ${field.control}`)).toEqual(['W4 Bezeichnung des Programms (Kopfzeile) text', 'W5 Prüfbehörde (Fußzeile) text', 'W6 Organisationseinheit (Fußzeile, freiwillig) text', 'W7 Ort (Fußzeile, freiwillig) text', 'J4 Stand text', 'J5 Status text', 'J6 Geprüfte Ausgaben der Stichprobe number', 'J7 Beträge nach Artikel 98 Absatz 6 (E) number', 'J8 Finanzkorrekturen (H) number'])
  })

  it('Tabellen: Spaltenköpfe, Zeilenbeschriftungen und Werte im Zahlenformat der Vorlage', () => {
    const page = report(workspace())
    const [first] = tables(page.sections[0]!.blocks)
    expect(first!.columns).toEqual([{ label: '', numeric: false }, { label: 'Datensätze', numeric: true }, { label: 'Ausgaben', numeric: true }])
    expect(first!.rows.map((row) => `${row.header}: ${row.cells.map((cell) => nbsp(cell.text)).join(' | ')}`)).toEqual([
      'Zahlungsanträge insgesamt (SFC2021): 432 | 49.200.000,00 €',
      'Positive Grundgesamtheit (Artikel 3 Absatz 4 DelVO): 420 | 48.500.000,00 €',
      'Negative Werte und Nullwerte: 12 | 0,00 €',
      'Stichprobe (Einheiten / geprüfte Ausgaben): 92 | 5.300.000,00 €',
      'Stichprobenverfahren: MUS-Standardansatz, 1 Zeitraum',
    ])
    expect(first!.rows[4]!.cells[0]!.span).toBe(2)
    const [cases] = tables(page.sections[1]!.blocks)
    expect(cases!.columns.map((column) => column.label)).toEqual(['VP', 'FÖPG', 'Buchwert', 'Fehler', 'Quote', 'Art des Fehlers', 'Stand'])
    expect(cases!.rows).toHaveLength(8)
    expect(cases!.rows[0]!.cells.map((cell) => (cell.input ? 'Eingabe' : nbsp(cell.text)))).toEqual(['Eingabe', 'Eingabe', 'Eingabe', 'Eingabe', '1,7 %', 'Eingabe', 'Eingabe'])
    expect(cases!.rows[0]!.cells[2]!.input).toMatchObject({ cell: 'C20', label: 'Buchwert 1', control: 'number', inputText: '250.000,00' })
    expect(`${cases!.foot!.header}: ${cases!.foot!.cells.map((cell) => nbsp(cell.text)).join(' | ')}`).toBe('Summe:  | 730.000,00 € | 5.350,00 € |  | davon vorläufig:  | 4.200,00 €')
    const [figures] = tables(page.sections[2]!.blocks)
    expect(figures!.columns).toEqual([])
    expect(nbsp(figures!.rows[0]!.cells[0]!.text)).toMatch(/^0,\d\d %$/)
    const [residual] = tables(page.sections[3]!.blocks)
    expect(residual!.rows.map((row) => row.header)).toEqual(['Beträge nach Artikel 98 Absatz 6 VO (EU) 2021/1060 (E)', 'Finanzkorrekturen (H)', 'Restfehlerquote nach Finanzkorrekturen', 'Hochgerechnete Finanzkorrektur bis zur Signifikanzschwelle von 2 %'])
    // Zahlenformat der Vorlage für 0: „nicht erforderlich“.
    expect(residual!.rows[3]!.cells[0]!.text).toBe('nicht erforderlich')
  })

  it('Freitexte tragen den Platzhalter der Vorlage in eckigen Klammern; der Stand kann als Datumszahl vorliegen', () => {
    const page = report(workspace({ [sheet.id]: { ...sheet.sample.inputs, A9: 'Zahlungsantrag Nr. 4 (Beispiel).', J4: 46308 } }))
    const text = page.sections[0]!.blocks[0]!
    expect(text).toMatchObject({ kind: 'text', text: 'Zahlungsantrag Nr. 4 (Beispiel).', field: { cell: 'A9', control: 'text' } })
    expect(text.kind === 'text' && text.placeholder).toMatch(/^\[Zahlungsanträge mit Nummer und Datum\..*\]$/)
    expect(page.sections[3]!.blocks[1]).toMatchObject({ kind: 'text', text: '', placeholder: '[Bewertung der Ergebnisse, systembedingte oder anomale Fehler, vorgesehene Korrekturen und weiteres Vorgehen.]' })
    expect(page.asOf).toBe('Stand 13.10.2026')
    expect(report(workspace({ [sheet.id]: { ...sheet.sample.inputs, J4: null } })).asOf).toBe('')
  })

  it('Hinweise auf dem Ausdruck: jede mit 0 gerechnete Eingabe des Verfahrens, Hinweise zu Blatt 18; Hinweise zu Blatt 20 nur am Bildschirm', () => {
    const complete = report(workspace())
    // Die Auslegung der Vorlage in Blatt 18 (C24) reist mit auf den Ausdruck; allgemeine Auslegungen (Aufrunden, Würdigung, n_s) bleiben am Blatt.
    // Der Hinweis zu Kopf- und Fußzeile steht nur am Bildschirm.
    expect(complete.hints).toEqual([expect.objectContaining({ id: '18_GFQ_AnhIII-interpretation-C24', printed: true, tone: 'neutral' }), expect.objectContaining({ id: 'own-header', printed: false })])
    // Hinweise in Warnfarbe auf dem Ausdruck (die Auslegung der Vorlage ist neutral und steht immer dabei).
    const warned = (hint: { printed: boolean; tone: string }): boolean => hint.printed && hint.tone === 'warning'
    const page = report(workspace({ [mus.id]: { ...mus.sample.inputs, C39: null } }))
    expect(page.hints.filter(warned)).toEqual([
      { id: '03_MUS_1Z-zero-C39', tone: 'warning', printed: true, text: `Blatt 03: Keine Angabe, daher mit 0 berechnet: ${mus.definition.sections.flatMap((section) => [...section.fields]).find((field) => field.cell === 'C39')!.label} (C39)` },
    ])
    const none = report(workspace({}, null))
    expect(none.hints.filter(warned).map((hint) => hint.id)).toEqual(['18_GFQ_AnhIII-no-method'])
    expect(none.hints.find(warned)!.text).toMatch(/^Blatt 18: Kein Verfahren gewählt/)
    const legacy = report(workspace({}, 'X2_DiffSch_2017'))
    expect(legacy.hints.filter(warned).map((hint) => hint.id)).toEqual(['X2_DiffSch_2017-legacy', '18_GFQ_AnhIII-method-without-summary'])
  })

  it('„Angabe fehlt“ steht in der Zelle, wenn die Vorlage dort mit 0 gerechnet hätte', () => {
    const page = report(workspace({ [population.id]: { ...population.sample.inputs, C23: null } }))
    const cell = tables(page.sections[0]!.blocks)[0]!.rows[0]!.cells[0]!
    expect(cell).toMatchObject({ cell: 'F11', text: 'Angabe fehlt', missing: true })
  })

  it('die Schaltfläche zum Drucken trägt den Text der Oberfläche, deutsch und englisch', () => {
    const state = workspace()
    const results = computeWorkspace(state)
    const report = (t: Translate) => buildReport(sheet, state.sheets[sheet.id] as CellMap, results[sheet.id]!, contextFor(sheet.id, state, results), t)
    expect(report(createTranslate()).labels.print).toBe('Drucken / als PDF sichern')
    expect(report(createTranslate(undefined, 'en')).labels.print).toBe('Print / save as PDF')
  })
})
