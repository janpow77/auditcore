import type { DownloadFile } from '@auditcore/common'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { SamplingCalculator } from '../src/index'
import { FOUNDATION_SHEETS, pickVariant } from './sheets'

const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')
const [mounted, delivered]: [VueWrapper[], DownloadFile[]] = [[], []]

function mountCalculator(props: Record<string, unknown> = {}): VueWrapper {
  const wrapper = mount(SamplingCalculator, { attachTo: document.body, props: { sheets: FOUNDATION_SHEETS, localDraft: false, saveFile: (file: DownloadFile) => void delivered.push(file), ...props } })
  mounted.push(wrapper)
  return wrapper
}

async function settle(): Promise<void> {
  for (let round = 0; round < 4; round += 1) {
    await flushPromises()
    await vi.dynamicImportSettled()
    await new Promise((resolve) => setTimeout(resolve, 0))
  }
  await nextTick()
}

async function menu(wrapper: VueWrapper, action: string): Promise<void> {
  await wrapper.get('.fa-st__menu-wrap > button').trigger('click')
  await wrapper.get(`[data-action="${action}"]`).trigger('click')
  await settle()
}

const step = (wrapper: VueWrapper, id: string) => wrapper.get(`[data-step="${id}"]`).trigger('click')
const cell = (wrapper: VueWrapper, address: string) => wrapper.get(`[data-cell="${address}"]`)
const input = (wrapper: VueWrapper, address: string) => cell(wrapper, address).get<HTMLInputElement>('input, select')
const value = (wrapper: VueWrapper, address: string): string => nbsp(cell(wrapper, address).get('.fa-st__value').text())

afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount()
  document.body.innerHTML = ''
  delivered.length = 0
})

describe('Arbeitsschritte und Kontextfluss', () => {
  it('die Schritte sind umschaltbar; Schritte ohne Rechenkern sind gekennzeichnet', async () => {
    const wrapper = mountCalculator()
    expect(wrapper.findAll('[data-step]').map((button) => button.text())).toEqual(['1Grundgesamtheit', '2Verfahren', '3Unterstichproben', '4Gesamtfehlerquote · folgt', '5Bericht · folgt'])
    expect(wrapper.get('[data-substeps] [aria-current="step"]').text()).toBe('Verfahren wählen')
    expect(wrapper.get('[data-step="method"]').attributes('aria-current')).toBe('step')
    await step(wrapper, 'totalErrorRate')
    expect(wrapper.get('[data-step="method"]').attributes('aria-current')).toBe('step')
    await step(wrapper, 'population')
    expect(wrapper.get('[data-step="population"]').attributes('aria-current')).toBe('step')
    expect(wrapper.get('[data-sheet-view]').attributes('data-sheet-view')).toBe('02_Grundgesamtheit')
    expect(wrapper.findAll('.fa-st__section-title').map((title) => title.text().slice(0, 1))).toEqual(['A', 'B', 'C', 'D', 'E', 'F', 'G'])
    expect(input(wrapper, 'C49').element.value).toBe('keine betroffenen Einheiten')
    await step(wrapper, 'method')
    expect(wrapper.find('.fa-st__question').exists()).toBe(true)
  })

  it('BV und N aus Blatt 02 sind im Methodenblatt vorbelegt, überschreibbar und als überschrieben markiert', async () => {
    const wrapper = mountCalculator()
    await step(wrapper, 'population')
    await input(wrapper, 'C24').setValue('420')
    await input(wrapper, 'C25').setValue('48.500.000,00')
    expect(value(wrapper, 'C51')).toBe('48.500.000,00 €')
    expect(nbsp(wrapper.get('[data-result="primary"]').text())).toBe('48.500.000,00 €')
    await step(wrapper, 'method')
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    expect(input(wrapper, 'C7').element.value).toBe('48.500.000,00')
    expect(input(wrapper, 'C8').element.value).toBe('420')
    expect(cell(wrapper, 'C7').get('[data-link]').text()).toBe('aus Blatt 02_Grundgesamtheit vorbelegt')
    expect(value(wrapper, 'C16')).toBe('970.000,00 €')
    await input(wrapper, 'C7').setValue('40.000.000,00')
    expect(cell(wrapper, 'C7').get('[data-link]').text()).toBe('Vorbelegung überschrieben')
    expect(value(wrapper, 'C16')).toBe('800.000,00 €')
    await input(wrapper, 'C7').setValue('')
    await input(wrapper, 'C7').trigger('blur')
    await nextTick()
    expect(cell(wrapper, 'C7').get('[data-link]').text()).toBe('aus Blatt 02_Grundgesamtheit vorbelegt')
    expect(input(wrapper, 'C7').element.value).toBe('48.500.000,00')
  })

  it('der Wegweiser zeigt die Hinweise der Vorlage aus Blatt 02 und empfiehlt nichts', async () => {
    const wrapper = mountCalculator()
    expect(wrapper.get('[data-guide]').text()).toContain('empfiehlt kein Verfahren')
    expect(wrapper.findAll('[data-guide-item]')).toHaveLength(1)
    await step(wrapper, 'population')
    await input(wrapper, 'C24').setValue('251')
    await input(wrapper, 'C25').setValue('17.300.000,00')
    await step(wrapper, 'method')
    expect(nbsp(wrapper.get('[data-guide]').text())).toContain('Angepasste Grundgesamtheit: 251 Einheiten, 17.300.000,00 €.')
    expect(wrapper.findAll('[data-guide-item]').map((item) => item.text())).toEqual([
      '✔ weniger als 300 Einheiten: nichtstatistisches Verfahren zulässig (Art. 79 Abs. 2 VO (EU) 2021/1060)',
      'Mindestumfang bei nichtstatistischem Verfahren (10 % der Einheiten): 26 (Art. 6 Abs. 2 DelVO.)',
      'Begrenzter Stichprobenumfang: 50 Einheiten für Programme der Kategorie 1 oder 2 ohne Art. 83 (Art. 5 Abs. 7); 30 Einheiten bei Art. 83.',
    ])
  })
})

describe('Beispielwerte', () => {
  it('im Schritt Grundgesamtheit geladen, bleibt der Schritt stehen; mit Blattangabe öffnet die Methode das Verfahren', async () => {
    const wrapper = mountCalculator()
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await step(wrapper, 'population')
    await menu(wrapper, 'sample')
    expect(wrapper.get('[data-sheet-view]').attributes('data-sheet-view')).toBe('02_Grundgesamtheit')
    expect(wrapper.get('[data-step="population"]').attributes('aria-current')).toBe('step')
    ;(wrapper.vm as unknown as { loadSample: (sheet?: string) => void }).loadSample('04_MUS_1Z_S')
    await settle()
    expect(wrapper.get('[data-sheet-view]').attributes('data-sheet-view')).toBe('04_MUS_1Z_S')
    expect(wrapper.get('[data-result="primary"]').text()).toMatch(/\d/)
  })
})

describe('Schichttabelle (Blatt 04)', () => {
  async function stratified(): Promise<VueWrapper> {
    const wrapper = mountCalculator()
    await pickVariant(wrapper, '04_MUS_1Z_S')
    await menu(wrapper, 'sample')
    return wrapper
  }
  const columns = (wrapper: VueWrapper): string[] => wrapper.get('[data-strata] thead').findAll('th').map((head) => head.text())

  it('zeigt Schichtzeilen als Tabelle mit Summenspalte in einem eigenen Rollbereich', async () => {
    const wrapper = await stratified()
    expect(columns(wrapper)).toEqual(['Gesamt', 'Schicht 1', 'Schicht 2', 'Schicht 3'])
    const region = wrapper.get('[data-strata] [role="region"]')
    expect(region.attributes('tabindex')).toBe('0')
    expect(region.attributes('aria-label')).toBe('Schichttabelle, waagerecht rollbar')
    expect(nbsp(cell(wrapper, 'C9').text())).toBe('48.500.000,00 €')
    expect(input(wrapper, 'E9').element.value).toBe('16.500.000,00')
    expect(input(wrapper, 'E9').attributes('aria-label')).toBe('Buchwert je Schicht (BV_h) – Schicht 2')
    expect(cell(wrapper, 'D41').text()).toBe('✔ ≥ 3')
    expect(wrapper.findAll('[data-strata]').length).toBeGreaterThan(3)
  })

  it('Schichten hinzufügen und entfernen; ab der achten steht der Hinweis der Webfassung', async () => {
    const wrapper = await stratified()
    await wrapper.get('[data-action="strata-add"]').trigger('click')
    expect(columns(wrapper)).toHaveLength(5)
    await input(wrapper, 'G9').setValue('2.000.000,00')
    expect(nbsp(cell(wrapper, 'C9').text())).toBe('50.500.000,00 €')
    expect(wrapper.find('[data-strata-note]').exists()).toBe(false)
    for (let count = 4; count < 8; count += 1) await wrapper.get('[data-action="strata-add"]').trigger('click')
    expect(columns(wrapper).at(-1)).toBe('Schicht 8')
    expect(wrapper.get('[data-strata-note]').text()).toContain('Hinweis der Webfassung')
    await input(wrapper, 'AA9').setValue('1.000.000,00')
    expect(nbsp(cell(wrapper, 'C9').text())).toBe('51.500.000,00 €')
    expect(wrapper.findAll('[data-hint="web"]').map((hint) => hint.text()).join(' ')).toContain('Mehr als sieben Schichten')
    await wrapper.get('[data-action="strata-remove"]').trigger('click').then(settle)
    ;(document.querySelector('[data-action="discard"]') as HTMLButtonElement).click() // Schicht 8 trägt eine Eingabe: Rückfrage
    expect((await settle(), columns(wrapper).at(-1))).toBe('Schicht 7')
    expect(nbsp(cell(wrapper, 'C9').text())).toBe('50.500.000,00 €')
  })

  it('höchstens 20 Schichten, mindestens eine', async () => {
    const wrapper = await stratified()
    for (let count = 3; count < 22; count += 1) await wrapper.get('[data-action="strata-add"]').trigger('click')
    expect(columns(wrapper)).toHaveLength(21)
    expect(wrapper.get('[data-action="strata-add"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-strata] [role="status"]').text()).toBe('20 von höchstens 20 Schichten')
  })
})

describe('Unterstichproben (Blatt 17)', () => {
  async function units(): Promise<VueWrapper> {
    const wrapper = mountCalculator()
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await menu(wrapper, 'sample')
    await step(wrapper, 'subsamples')
    return wrapper
  }

  it('Liste mit Beispieleinheit, Einheit hinzufügen, bearbeiten und entfernen', async () => {
    const wrapper = await units()
    expect(wrapper.findAll('[data-unit]')).toHaveLength(1)
    expect(nbsp(wrapper.get('[data-unit="0"]').text())).toContain('Beispiel-Vorhaben 17')
    await wrapper.get('[data-action="unit-add"]').trigger('click')
    expect(wrapper.findAll('[data-unit]')).toHaveLength(2)
    expect(wrapper.get('[data-unit="1"]').attributes('aria-current')).toBe('true')
    await input(wrapper, 'C5').setValue('V-2')
    await input(wrapper, 'C6').setValue('900.000,00')
    await input(wrapper, 'C10').setValue('20')
    await input(wrapper, 'C11').setValue('50.000,00')
    await input(wrapper, 'C12').setValue('500,00')
    await input(wrapper, 'W5').setValue('hochwertige Einheit')
    expect(nbsp(wrapper.get('[data-unit="1"]').text())).toContain('9.000,00 €')
    expect(nbsp(wrapper.get('[data-result="primary"]').text())).toBe('9.000,00 €')
    await wrapper.get('[data-unit="0"] button').trigger('click')
    expect(input(wrapper, 'C5').element.value).toBe('Beispiel-Vorhaben 17')
    await wrapper.get('[data-unit="0"] td:last-child button').trigger('click')
    expect(wrapper.findAll('[data-unit]')).toHaveLength(1)
    expect(input(wrapper, 'C5').element.value).toBe('V-2')
  })

  it('Einfügen aus Zwischenablage oder CSV und Übernahme der Summen in das Methodenblatt', async () => {
    const wrapper = await units()
    await wrapper.get('[data-action="unit-paste"]').trigger('click')
    await nextTick()
    const dialog = document.querySelector('[role="dialog"]')!
    expect(dialog.textContent).toContain('Buchwert der Stichprobeneinheit (BV_i) (C6)')
    const area = dialog.querySelector('textarea')!
    area.value = 'C5;C6;C10;C11;C12;W5\nV-3;900.000,00;20;50.000,00;500,00;hochwertige Einheit\nV-4;1.5;x;;;Zufallsschicht'
    area.dispatchEvent(new Event('input'))
    await nextTick()
    ;(dialog.querySelector('[data-action="unit-paste-apply"]') as HTMLButtonElement).click()
    await settle()
    expect(wrapper.findAll('[data-unit]')).toHaveLength(3)
    expect(wrapper.get('[data-flash]').text()).toBe('2 Einheiten eingefügt.')
    expect(wrapper.get('[data-notice="warning"]').text()).toContain('2 Zellen waren nicht lesbar')
    expect(nbsp(wrapper.get('[data-total="highValueErrors"]').text())).toBe('9.000,00 €')
    expect(wrapper.get('[data-total="errorRateSum"]').text()).toBe('0,0150')
    expect(wrapper.get('[data-totals]').text()).toContain('1 Einheiten ohne bestimmbaren Fehler')
    expect(wrapper.get('[data-totals]').text()).toContain('Hinweis der Webfassung')
    await wrapper.get('[data-action="unit-transfer"]').trigger('click')
    expect(wrapper.get('[data-flash]').text()).toBe('Übernommen in Blatt 03: C37, C38.')
    await step(wrapper, 'method')
    expect(input(wrapper, 'C37').element.value).toBe('9.000,00')
    expect(input(wrapper, 'C38').element.value).toBe('0,015')
    expect(wrapper.get('[data-status]').text()).toContain('geändert')
  })

  it('Rundlauf mit Grundgesamtheit, Schichten und Einheiten', async () => {
    const wrapper = await units()
    await wrapper.get('[data-action="unit-add"]').trigger('click')
    await input(wrapper, 'C5').setValue('V-2')
    await menu(wrapper, 'save')
    const text = await delivered[0]!.blob.text()
    expect(Object.keys((JSON.parse(text) as { blaetter: object }).blaetter)).toEqual(expect.arrayContaining(['02_Grundgesamtheit', '03_MUS_1Z', '17_Unterstichprobe']))
    await menu(wrapper, 'new')
    await step(wrapper, 'subsamples')
    expect(wrapper.findAll('[data-unit]')).toHaveLength(0)
    const file = wrapper.get('input[type="file"]')
    Object.defineProperty(file.element, 'files', { value: [new File([text], 'stand.json')], configurable: true })
    await file.trigger('change')
    await settle()
    expect(wrapper.findAll('[data-notice]')).toHaveLength(0)
    await step(wrapper, 'subsamples')
    expect(wrapper.findAll('[data-unit]')).toHaveLength(2)
    await step(wrapper, 'population')
    expect(value(wrapper, 'C52')).toBe('420')
  })
})

describe('Englische Arbeitsübersetzung', () => {
  it('Oberfläche, Katalog, Bezeichnungen, Listen und Prüfhinweise erscheinen englisch; die Werte bleiben', async () => {
    const wrapper = mountCalculator({ locale: 'en' })
    expect(wrapper.get('[role="tab"]').text()).toContain('MUS standard approach')
    expect(wrapper.get('[data-match]').text()).toContain('MUS standard approach')
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await menu(wrapper, 'sample')
    expect(cell(wrapper, 'C27').get('.fa-st__label-text').text()).toBe('Sample size to be applied (at least 30; capped where applicable)')
    expect(cell(wrapper, 'C13').text()).toContain('✔ average: value between the two minimum levels')
    expect(input(wrapper, 'C9').element.value).toBe('mittel')
    expect(cell(wrapper, 'C9').findAll('option').map((option) => option.text())).toEqual(['– please select –', 'high', 'average', 'low'])
    expect(nbsp(wrapper.get('[data-result="primary"]').text())).toBe('92 units')
    expect(wrapper.get('[data-translation-note]').text()).toContain('German wording of the template is authoritative')
    await menu(wrapper, 'save')
    expect(JSON.parse(await delivered[0]!.blob.text())).toMatchObject({ blaetter: { '03_MUS_1Z': { C9: 'mittel' } }, ergebnisse: { '03_MUS_1Z': { C13: '✔ mittel: Wert zwischen den Eckwerten' } } })
  })
})

describe('Fehlende Angaben', () => {
  async function sample(): Promise<VueWrapper> {
    const wrapper = mountCalculator()
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await menu(wrapper, 'sample')
    return wrapper
  }

  it('„Angabe fehlt“ nennt die fehlende Eingabe, auch in der Ergebnisspalte', async () => {
    const wrapper = await sample()
    await input(wrapper, 'C20').setValue('')
    expect(value(wrapper, 'C27')).toBe('Angabe fehlt')
    expect(cell(wrapper, 'C27').get('[data-missing-note]').text()).toBe('Es fehlt: Voraussichtliche Standardabweichung der Fehlerquoten (σ_r) (C20)')
    expect(wrapper.get('[data-result="primary"]').text()).toBe('Angabe fehlt. Es fehlt: Voraussichtliche Standardabweichung der Fehlerquoten (σ_r) (C20)')
    expect(cell(wrapper, 'C12').find('[data-missing-note]').exists()).toBe(false)
  })

  it('fehlt die Standardabweichung der Stichprobe, wird wie in der Vorlage mit 0 gerechnet und das ausgewiesen', async () => {
    const wrapper = await sample()
    expect(wrapper.find('[data-zero-note]').exists()).toBe(false)
    await input(wrapper, 'C39').setValue('')
    expect(value(wrapper, 'C43')).toBe('0,00 €')
    const note = 'Hinweis der Webfassung: Keine Angabe, daher mit 0 berechnet: Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r) (C39)'
    for (const address of ['C43', 'C46', 'C47', 'C48', 'C51', 'C52']) expect(cell(wrapper, address).get('[data-zero-note]').text(), address).toBe(note)
    expect(cell(wrapper, 'C42').find('[data-zero-note]').exists()).toBe(false)
    expect(cell(wrapper, 'C52').text()).toContain('✔ GFQ und obere Fehlergrenze unter der Schwelle')
    const hints = wrapper.findAll('.fa-st__hint-list li')
    const warning = hints.find((hint) => hint.text().includes('Keine Angabe, daher mit 0 berechnet'))
    expect(warning?.attributes('data-hint')).toBe('web')
    expect(warning?.find('.fa-badge--warning').exists()).toBe(true)
    expect(warning?.text()).toContain('Hinweis der Webfassung')
    await menu(wrapper, 'save')
    const file = JSON.parse(await delivered[0]!.blob.text()) as { hinweise: Record<string, { id: string; text: string }[]> }
    expect(file.hinweise['03_MUS_1Z']).toEqual([{ id: 'zero-C39', text: 'Keine Angabe, daher mit 0 berechnet: Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r) (C39)' }])
  })

  it('ein Ganzzahlfeld lehnt „0.045“ mit Erklärung ab', async () => {
    const wrapper = await sample()
    await input(wrapper, 'C29').setValue('0.045')
    await input(wrapper, 'C29').trigger('blur')
    expect(input(wrapper, 'C29').attributes('aria-invalid')).toBe('true')
    expect(cell(wrapper, 'C29').get('[role="alert"]').text()).toContain('mehrdeutig')
    expect(input(wrapper, 'C29').element.value).toBe('0.045')
  })
})
