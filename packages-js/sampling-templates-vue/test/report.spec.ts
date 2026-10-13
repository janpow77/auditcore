import { SHEETS, buildReport, computeWorkspace, contextFor, createTranslate, emptyWorkspace, findAvailableSheet, type CellMap, type ReportPage, type WorkspaceState } from '@auditcore/sampling-templates-core'
import { mount, type VueWrapper } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, describe, expect, it } from 'vitest'
import ReportView from '../src/components/ReportView.vue'

const t = createTranslate()
const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ').replaceAll(String.fromCharCode(8239), ' ')
const sheet = (id: string) => {
  const found = findAvailableSheet(id, SHEETS)
  if (!found) throw new Error(`Blatt ${id} fehlt`)
  return found
}

/** Arbeitsstand aus den Beispielwerten der Blätter 02, 03, 18 und 20. */
function sampleState(report: CellMap = {}, method: CellMap = {}): WorkspaceState {
  const sheets = Object.fromEntries(['02_Grundgesamtheit', '03_MUS_1Z', '18_GFQ_AnhIII', '20_Druck_KOM'].map((id) => [id, { ...sheet(id).sample.inputs }]))
  Object.assign(sheets['20_Druck_KOM']!, report)
  Object.assign(sheets['03_MUS_1Z']!, method)
  return { ...emptyWorkspace(), activeMethod: '03_MUS_1Z', sheets }
}

function pageOf(state: WorkspaceState): ReportPage {
  const results = computeWorkspace(state)
  return buildReport(sheet('20_Druck_KOM'), state.sheets['20_Druck_KOM'] as CellMap, results['20_Druck_KOM']!, contextFor('20_Druck_KOM', state, results), t)
}

const mounted: VueWrapper[] = []
function mountReport(state: WorkspaceState = sampleState()): VueWrapper {
  const wrapper = mount(ReportView, { attachTo: document.body, props: { report: pageOf(state), t } })
  mounted.push(wrapper)
  return wrapper
}

afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount()
  document.body.innerHTML = ''
})

describe('Bericht (Blatt 20)', () => {
  it('zeigt die Seite mit Kopf, vier Abschnitten und Fußzeile', () => {
    const page = mountReport().get('[data-report-page]')
    expect(page.get('h3').text()).toBe('Vorhabenprüfungen – Stichprobe und Ergebnisse')
    expect(page.get('[data-report-subtitle]').text()).toBe('EFRE-Programm Hessen 2021–2027 · CCI 2021DE16RFPR000 · Geschäftsjahr 01.07.2025–30.06.2026 · vorläufig')
    expect(page.get('[data-report-as-of]').text()).toBe('Stand 13.10.2026')
    expect(page.findAll('h4').map((heading) => heading.text())).toEqual(['1. Grundgesamtheit und Stichprobe', '2. Ergebnisse der Vorhabenprüfungen', '3. Hochrechnung und Gesamtfehlerquote', '4. Restfehlerquote und weiteres Vorgehen', 'Hinweis der Webfassung'])
    expect(page.get('footer').text()).toBe('EFRE-Prüfbehörde, Referat Z 6, HMWVW, Wiesbaden')
    expect(page.text()).toContain(t('disclaimer'))
    expect(page.text()).toContain(t('templateStatus'))
    expect(page.get('[data-report-statement]').text()).toBe('Die Gesamtfehlerquote liegt unter der Wesentlichkeitsschwelle.')
  })

  it('Tabellen sind zugänglich: Beschriftung, Spalten- und Zeilenköpfe mit scope', () => {
    const tables = mountReport().findAll('[data-report-page] table')
    expect(tables).toHaveLength(4)
    for (const table of tables) expect(table.find('caption').exists()).toBe(true)
    expect(tables[0]!.findAll('th[scope="col"]').map((cell) => cell.text())).toEqual(['Datensätze', 'Ausgaben'])
    expect(tables[0]!.findAll('th[scope="row"]').map((cell) => cell.text())).toContain('Positive Grundgesamtheit (Artikel 3 Absatz 4 DelVO)')
    expect(tables[1]!.findAll('th[scope="col"]').map((cell) => cell.text())).toEqual(['VP', 'FÖPG', 'Buchwert', 'Fehler', 'Quote', 'Art des Fehlers', 'Stand'])
    expect(tables[1]!.get('tfoot th[scope="row"]').text()).toBe('Summe')
    expect(nbsp(tables[0]!.get('[data-cell="G12"]').text())).toBe('48.500.000,00 €')
    expect(tables[0]!.get('[data-cell="D15"]').attributes('colspan')).toBe('2')
    expect(tables[2]!.findAll('th[scope="row"]')).toHaveLength(5)
    expect(tables[3]!.get('[data-cell="G43"]').text()).toBe('nicht erforderlich')
  })

  it('Freitexte und Fehlerfälle sind bearbeitbar und melden die Eingabe mit der Zelle der Vorlage', async () => {
    const wrapper = mountReport()
    const free = wrapper.get('[data-cell="A9"] textarea')
    expect(free.attributes('placeholder')).toMatch(/^\[Zahlungsanträge mit Nummer und Datum\./)
    expect(free.attributes('aria-label')).toBe('1. Grundgesamtheit und Stichprobe')
    await free.setValue('Zahlungsantrag Nr. 4 (Beispiel) ')
    await wrapper.get('[data-cell="A9"] textarea').setValue('   ')
    const amount = wrapper.get('[data-cell="C22"] input')
    expect(amount.attributes('aria-label')).toBe('Buchwert 3')
    await amount.setValue('96.000,50')
    await wrapper.get('[data-cell="G22"] input').setValue('vorläufig')
    expect(wrapper.emitted('update')).toEqual([['A9', 'Zahlungsantrag Nr. 4 (Beispiel) '], ['A9', null], ['C22', 96000.5], ['G22', 'vorläufig']])
    // Für den Druck steht der Wert als Text daneben; ein leerer Freitext druckt den Platzhalter der Vorlage.
    expect(nbsp(wrapper.get('[data-cell="C20"] .fa-st__report-print').text())).toBe('250.000,00 €')
    expect(wrapper.get('[data-cell="A45"] .fa-st__report-print').text()).toBe('[Bewertung der Ergebnisse, systembedingte oder anomale Fehler, vorgesehene Korrekturen und weiteres Vorgehen.]')
  })

  it('Steuerfelder stehen neben der Seite und sind bearbeitbar', async () => {
    const wrapper = mountReport()
    const controls = wrapper.get('[data-report-controls]')
    expect(controls.get('h3').text()).toBe('Steuerfelder (werden nicht gedruckt)')
    expect(controls.findAll('label').map((label) => label.text())).toEqual(['Stand', 'Status', 'Geprüfte Ausgaben der Stichprobe', 'Beträge nach Artikel 98 Absatz 6 (E)', 'Finanzkorrekturen (H)'])
    expect(wrapper.find('[data-report-page] [data-cell="J8"]').exists()).toBe(false)
    await controls.get('[data-cell="J8"] input').setValue('150.000,00')
    await controls.get('[data-cell="J5"] input').setValue('endgültig')
    expect(wrapper.emitted('update')).toEqual([['J8', 150000], ['J5', 'endgültig']])
    expect(controls.get('[data-report-screen-hints]').text()).toContain('EFRE-Programm Hessen 2021–2027')
  })

  it('die Schaltfläche meldet nur den Druckwunsch', async () => {
    const wrapper = mountReport()
    const button = wrapper.get('[data-action="print"]')
    expect(button.text()).toBe('Drucken / als PDF sichern')
    await button.trigger('click')
    expect(wrapper.emitted('print')).toHaveLength(1)
  })

  it('mit 0 gerechnete Eingaben stehen als Hinweis auf der Seite', () => {
    expect(mountReport().find('[data-report-hints]').exists()).toBe(false)
    const hints = mountReport(sampleState({}, { C39: null })).get('[data-report-page] [data-report-hints]')
    expect(hints.findAll('li')).toHaveLength(1)
    expect(hints.text()).toMatch(/^Blatt 03: Keine Angabe, daher mit 0 berechnet: .*\(C39\)$/)
  })

  it('kommt ohne Inline-Stile aus; das Druck-Stylesheet zeigt nur die Seite und blendet Bedienelemente aus', () => {
    const wrapper = mountReport()
    expect(wrapper.findAll('[style]')).toHaveLength(0)
    const css = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), '../../sampling-templates-core/styles/report.css'), 'utf8')
    const print = css.slice(css.indexOf('@media print'))
    expect(print).toMatch(/@page \{ size: A4 portrait; margin: [^}]+\}/)
    expect(print).toContain('.fa-st__report-screen { display: none !important; }')
    expect(print).toContain(':not(:has(.fa-st__report-page))')
    // Farben nur über die Designtoken; im Druck Schwarz auf Weiß.
    expect(css.replace(/--fa-[\w-]+: (black|white);/g, '')).not.toMatch(/#[0-9a-f]{3,8}\b|rgb\(|hsl\(|(?<![-\w])(black|white)(?![-\w])/i)
    for (const selector of css.matchAll(/\.fa-st__[\w-]+/g)) expect(selector[0].startsWith('.fa-st__report') || ['.fa-st__row', '.fa-st__input', '.fa-st__note', '.fa-st__error'].includes(selector[0]), selector[0]).toBe(true)
  })
})
