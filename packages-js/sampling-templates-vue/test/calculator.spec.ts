import type { DownloadFile } from '@auditcore/common'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { SamplingCalculator } from '../src/index'
import { FOUNDATION_SHEETS, pickVariant } from './sheets'

const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')
const delivered: DownloadFile[] = []

const mounted: VueWrapper[] = []

function mountCalculator(props: Record<string, unknown> = {}): VueWrapper {
  const wrapper = mount(SamplingCalculator, {
    attachTo: document.body,
    props: { sheets: FOUNDATION_SHEETS, localDraft: false, saveFile: (file: DownloadFile) => void delivered.push(file), ...props },
  })
  mounted.push(wrapper)
  return wrapper
}

/** Wartet auf Rechnen, Prüfsumme und den nachgeladenen Excel-Austausch. */
async function settle(): Promise<void> {
  for (let round = 0; round < 4; round += 1) {
    await flushPromises()
    await vi.dynamicImportSettled()
    if (!vi.isFakeTimers()) await new Promise((resolve) => setTimeout(resolve, 0))
  }
  await nextTick()
}

async function menu(wrapper: VueWrapper, action: string): Promise<void> {
  await wrapper.get('.fa-st__menu-wrap > button').trigger('click')
  await wrapper.get(`[data-action="${action}"]`).trigger('click')
  await settle()
}

async function withSample(props: Record<string, unknown> = {}): Promise<VueWrapper> {
  const wrapper = mountCalculator(props)
  await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
  await menu(wrapper, 'sample')
  return wrapper
}

async function openFile(wrapper: VueWrapper, file: File): Promise<void> {
  const input = wrapper.get('input[type="file"]')
  Object.defineProperty(input.element, 'files', { value: [file], configurable: true })
  await input.trigger('change')
  await settle()
  await settle()
}

const field = (wrapper: VueWrapper, cell: string) => wrapper.get(`[data-cell="${cell}"]`)
const valueOf = (wrapper: VueWrapper, cell: string): string => nbsp(field(wrapper, cell).get('.fa-st__value').text())
const inputOf = (wrapper: VueWrapper, cell: string) => field(wrapper, cell).get<HTMLInputElement>('input, select')

beforeEach(() => {
  delivered.length = 0
  localStorage.clear()
  sessionStorage.clear()
})
afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount()
  document.body.innerHTML = ''
})

describe('Verfahrensauswahl', () => {
  it('grenzt das Verfahren über Methode, Zeiträume und Schichtung auf genau eine Variante ein', async () => {
    const wrapper = mountCalculator()
    expect(wrapper.findAll('[role="tab"]').map((tab) => tab.text())).toEqual([
      'MUS-Standardansatz',
      'Einfache Zufallsstichprobe',
      'Nichtstatistisch, gleiche Wahrscheinlichkeit',
      'Nichtstatistisch, PPS',
      'Weitere Methoden nach Art. 79',
    ])
    expect(wrapper.findAll('[data-periods]').map((button) => button.text())).toEqual(['1 Zeitraum', '2 Zeiträume', '3 Zeiträume'])
    expect(wrapper.text()).not.toMatch(/Blatt \d/)
    expect(wrapper.get('[data-sheet="03_MUS_1Z"]').attributes('aria-disabled')).toBeUndefined()
    await wrapper.get('[data-stratified="true"]').trigger('click')
    expect(wrapper.get('[data-sheet="04_MUS_1Z_S"]').attributes('aria-disabled')).toBeUndefined()
    await wrapper.get('[data-periods="2"]').trigger('click')
    await wrapper.get('[data-stratified="false"]').trigger('click')
    expect(wrapper.get('[data-sheet="05_MUS_2Z"]').attributes('aria-disabled')).toBe('true')
    expect(wrapper.get('[data-sheet="05_MUS_2Z"]').text()).toContain('noch nicht verfügbar')
    await wrapper.get('[data-periods="3"]').trigger('click')
    await wrapper.get('[data-stratified="true"]').trigger('click')
    expect(wrapper.find('[data-match] [data-sheet]').exists()).toBe(false)
    expect(wrapper.get('[data-gap]').text()).toContain('kein Blatt in der Vorlage')
  })

  it('erklärt MUS, PPS, Zufallsstichprobe und Startwert in aufklappbaren Kurztexten', () => {
    const wrapper = mountCalculator()
    expect(wrapper.findAll('[data-glossary] summary').map((item) => item.text())).toEqual(['MUS (Monetary Unit Sampling)', 'PPS (Probability Proportional to Size)', 'Einfache Zufallsstichprobe', 'Startwert'])
  })

  it('ist mit Pfeiltasten, Pos1 und Ende bedienbar', async () => {
    const wrapper = mountCalculator()
    const list = wrapper.get('[role="tablist"]')
    await list.trigger('keydown', { key: 'ArrowDown' })
    await nextTick()
    expect(wrapper.findAll('[role="tab"]')[1]?.attributes('aria-selected')).toBe('true')
    expect(document.activeElement?.textContent).toContain('Einfache Zufallsstichprobe')
    await list.trigger('keydown', { key: 'End' })
    expect(wrapper.get('[role="tabpanel"]').text()).toContain('Keine gebrauchsfertige Methode der DelVO')
    expect(wrapper.findAll('[role="tabpanel"] li')).toHaveLength(5)
    await list.trigger('keydown', { key: 'ArrowDown' })
    expect(wrapper.findAll('[role="tab"]')[0]?.attributes('aria-selected')).toBe('true')
  })

  it('eine Variante ohne Rechenkern lässt sich nicht wählen', async () => {
    const wrapper = mountCalculator()
    await pickVariant(wrapper, '05_MUS_2Z')
    expect(wrapper.find('.fa-st__form').exists()).toBe(false)
    await pickVariant(wrapper, '03_MUS_1Z')
    expect(wrapper.get('.fa-st__chip').text()).toContain('MUS')
    expect(wrapper.get('[data-substeps] [aria-current="step"]').text()).toBe('Parameter und Ergebnis')
    expect(wrapper.findAll('.fa-st__section-title').map((title) => title.text().slice(0, 1))).toEqual(['H', 'I', 'J', 'K', 'L', 'M'])
    await wrapper.get('.fa-st__chip button').trigger('click')
    expect(wrapper.get('[role="tab"][aria-selected="true"]').text()).toContain('MUS-Standardansatz')
  })

})

describe('Rechenblatt', () => {
  it('Beispielwerte ergeben die Größen des Gestaltungsprototyps', async () => {
    const wrapper = await withSample()
    expect(wrapper.get('[data-notice="sample"]').text()).toContain('stammen aus keiner Prüfung')
    expect(nbsp(wrapper.get('[data-result="primary"]').text())).toBe('92 Einheiten')
    const summary = Object.fromEntries(wrapper.findAll('.fa-st__kv dt').map((term, index) => [term.text(), nbsp(wrapper.findAll('.fa-st__kv dd')[index]!.text())]))
    expect(summary).toMatchObject({ Auswahlintervall: '480.681,82 €', 'Extrapolierter Fehler': '316.422,73 €', Gesamtfehlerquote: '0,652 %', 'Obere Fehlergrenze': '1,086 %' })
    expect(valueOf(wrapper, 'C27')).toBe('92')
    expect(inputOf(wrapper, 'C7').element.value).toBe('48.500.000,00')
    expect(inputOf(wrapper, 'C14').element.value).toBe('2')
    expect(wrapper.get('[data-status]').text()).toBe('Beispielwerte')
  })

  it('Prüfhinweise stehen als Text mit Einstufung in der Ergebnisspalte', async () => {
    const wrapper = await withSample()
    const hints = wrapper.findAll('.fa-st__hint-list li')
    expect(hints).toHaveLength(7)
    expect(hints[0]?.text()).toBe('erfüllt: ✔ mittel: Wert zwischen den Eckwerten')
    expect(hints[0]?.find('.fa-badge--success').exists()).toBe(true)
    expect(hints[3]?.text()).toBe('Hinweis: Nicht angewandt – Anh. I und II gelten')
  })

  it('deutsche Zahleneingabe: rechnet sofort, formatiert beim Verlassen, meldet Fehler mit Erklärung', async () => {
    const wrapper = await withSample()
    const sigma = inputOf(wrapper, 'C20')
    await sigma.setValue('0,24')
    expect(valueOf(wrapper, 'C21')).toBe('366')
    expect(wrapper.get('[data-status]').text()).toBe('Beispielwerte · geändert')
    const amount = inputOf(wrapper, 'C30')
    await amount.setValue('6200000')
    await amount.trigger('blur')
    await nextTick()
    expect(amount.element.value).toBe('6.200.000,00')
    await sigma.setValue('1.5')
    await sigma.trigger('blur')
    expect(sigma.attributes('aria-invalid')).toBe('true')
    expect(field(wrapper, 'C20').get('[role="alert"]').text()).toContain('mehrdeutig')
    expect(valueOf(wrapper, 'C21')).toBe('Angabe fehlt')
    expect(sigma.element.value).toBe('1.5')
  })

  it('Prozentfelder werden in Prozent eingegeben, Auswahlfelder behalten ihren Zahlenwert', async () => {
    const wrapper = await withSample()
    await inputOf(wrapper, 'C17').setValue('2,5')
    expect(field(wrapper, 'C19').text()).toContain('✖ TE ≤ AE: Stichprobenumfang nicht bestimmbar')
    expect(wrapper.get('[data-result="primary"]').text()).toBe('nicht bestimmbar (TE ≤ AE)')
    await inputOf(wrapper, 'C17').setValue('0,7')
    await inputOf(wrapper, 'C10').setValue('0.95')
    expect(valueOf(wrapper, 'C12')).toBe('1,960')
    const web = wrapper.findAll('[data-hint="web"]')
    expect(web).toHaveLength(1)
    expect(web[0]?.text()).toContain('Hinweis der Webfassung')
    expect(web[0]?.text()).toContain('Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I')
  })

  it('Ergebnisänderungen werden gedrosselt angesagt', async () => {
    vi.useFakeTimers()
    try {
      const wrapper = await withSample()
      const live = (): string => nbsp(wrapper.get('[data-live]').text())
      vi.advanceTimersByTime(1600)
      await nextTick()
      expect(live()).toContain('Anzuwendender Stichprobenumfang 92 Einheiten')
      await inputOf(wrapper, 'C20').setValue('0,24')
      await inputOf(wrapper, 'C20').setValue('0,3')
      expect(live()).toContain('92 Einheiten')
      vi.advanceTimersByTime(1600)
      await nextTick()
      expect(live()).toBe('Ergebnisse aktualisiert: Anzuwendender Stichprobenumfang 572 Einheiten, Gesamtfehlerquote 0,133 %, Obere Fehlergrenze 0,304 %')
      expect(wrapper.get('[data-live]').attributes('aria-live')).toBe('polite')
    } finally {
      vi.useRealTimers()
    }
  })
})

describe('Arbeitsstand', () => {
  it('Rundlauf Speichern → Neu → Öffnen ergibt dieselben Eingaben und Ergebnisse', async () => {
    const wrapper = await withSample()
    await inputOf(wrapper, 'C20').setValue('0,24')
    await menu(wrapper, 'save')
    expect(delivered).toHaveLength(1)
    expect(delivered[0]?.filename).toBe('Stichprobe_03_MUS_1Z_2025_2026_Arbeitsstand.json')
    expect(wrapper.get('[data-status]').text()).toBe('Stichprobe_03_MUS_1Z_2025_2026_Arbeitsstand.json · gespeichert')
    expect(wrapper.emitted('saved')).toHaveLength(1)
    await menu(wrapper, 'new')
    expect(inputOf(wrapper, 'C7').element.value).toBe('')
    expect(inputOf(wrapper, 'C14').element.value).toBe('2')
    expect(wrapper.get('[data-status]').text()).toBe('Neuer Arbeitsstand')
    await openFile(wrapper, new File([await delivered[0]!.blob.text()], 'stand.json', { type: 'application/json' }))
    expect(inputOf(wrapper, 'C20').element.value).toBe('0,24')
    expect(valueOf(wrapper, 'C21')).toBe('366')
    expect(wrapper.findAll('[data-notice]')).toHaveLength(0)
    expect(wrapper.get('[data-status]').text()).toBe('stand.json · gespeichert')
    expect(wrapper.get('[data-flash]').text()).toContain('Arbeitsstand geöffnet (gespeichert am')
  })

  it('eine außerhalb veränderte Datei löst den Prüfsummenhinweis aus', async () => {
    const wrapper = await withSample()
    await menu(wrapper, 'save')
    const tampered = (await delivered[0]!.blob.text()).replace('"C7": 48500000', '"C7": 58500000')
    await openFile(wrapper, new File([tampered], 'veraendert.json'))
    expect(wrapper.get('[data-notice="warning"]').text()).toContain('Die Prüfsumme stimmt nicht')
    expect(inputOf(wrapper, 'C7').element.value).toBe('58.500.000,00')
  })

  it('Excel-Export lässt sich wieder öffnen', async () => {
    const wrapper = await withSample()
    await wrapper.get('[data-action="export"]').trigger('click')
    await settle()
    await settle()
    expect(delivered[0]?.filename).toBe('Stichprobe_03_MUS_1Z_2025_2026_Ergebnis.xlsx')
    expect(wrapper.emitted('exported')).toHaveLength(1)
    await menu(wrapper, 'new')
    await openFile(wrapper, new File([await delivered[0]!.blob.arrayBuffer()], 'ergebnis.xlsx'))
    expect(valueOf(wrapper, 'C27')).toBe('92')
    expect(wrapper.findAll('[data-notice]')).toHaveLength(0)
  })

  it('fremde Dateien werden mit Erklärung abgelehnt', async () => {
    const wrapper = await withSample()
    await openFile(wrapper, new File(['{"format":"anders"}'], 'fremd.json'))
    expect(wrapper.get('[data-notice="danger"]').text()).toBe('Die Datei ist kein Arbeitsstand dieses Rechners.Schließen')
    await wrapper.get('[data-notice="danger"] button').trigger('click')
    await openFile(wrapper, new File(['x'], 'bild.png'))
    expect(wrapper.get('[data-notice="danger"]').text()).toContain('Dateityp wird nicht unterstützt')
    await wrapper.get('[data-notice="danger"] button').trigger('click')
    await openFile(wrapper, new File(['kein zip'], 'kaputt.xlsx'))
    expect(wrapper.get('[data-notice="danger"]').text()).toContain('konnte nicht gelesen werden')
    expect(valueOf(wrapper, 'C27')).toBe('92')
  })

  it('ungespeicherte Änderungen werden nur nach Bestätigung verworfen', async () => {
    const wrapper = await withSample()
    await inputOf(wrapper, 'C20').setValue('0,24')
    await menu(wrapper, 'new')
    expect(document.querySelector('[role="dialog"]')?.textContent).toContain('Ungespeicherte Änderungen')
    expect(inputOf(wrapper, 'C20').element.value).toBe('0,24')
    ;(document.querySelector('[data-action="discard"]') as HTMLButtonElement).click()
    await settle()
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(inputOf(wrapper, 'C20').element.value).toBe('')
  })

  it('warnt beim Verlassen der Seite nur bei ungespeicherten Änderungen', async () => {
    const wrapper = await withSample()
    const leave = (): Event => {
      const event = new Event('beforeunload', { cancelable: true })
      window.dispatchEvent(event)
      return event
    }
    expect(leave().defaultPrevented).toBe(false)
    await inputOf(wrapper, 'C20').setValue('0,24')
    expect(leave().defaultPrevented).toBe(true)
    await menu(wrapper, 'save')
    expect(leave().defaultPrevented).toBe(false)
  })

  it('eine abgelegte Datei wird geöffnet', async () => {
    const wrapper = await withSample()
    await menu(wrapper, 'save')
    await menu(wrapper, 'new')
    const file = new File([await delivered[0]!.blob.text()], 'abgelegt.json')
    const dataTransfer = { types: ['Files'], files: [file] }
    await wrapper.trigger('dragenter', { dataTransfer })
    expect(wrapper.get('.fa-st__drop').text()).toContain('Datei hier ablegen')
    await wrapper.trigger('drop', { dataTransfer })
    await settle()
    await settle()
    expect(wrapper.find('.fa-st__drop').exists()).toBe(false)
    expect(valueOf(wrapper, 'C27')).toBe('92')
    expect(wrapper.get('[data-status]').text()).toBe('abgelegt.json · gespeichert')
  })
})

describe('Texte', () => {
  it('eine Anwendung kann Texte überschreiben und Englisch liefern', () => {
    const wrapper = mountCalculator({ locale: 'en', messages: { en: { exportResult: 'Export result', pickerQuestion: 'Which sampling method do you apply?' } } })
    expect(wrapper.get('[data-action="export"]').text()).toBe('Export result')
    expect(wrapper.get('.fa-st__question').text()).toBe('Which sampling method do you apply?')
    expect(wrapper.get('.fa-st__menu-wrap > button').text()).toBe('Working file')
    expect(wrapper.get('[data-translation-note]').text()).toContain('Working translation')
  })
})

describe('Einbindung in eine Anwendung', () => {
  it('zeigt den Hinweis des Fachrahmens und den Stand der Vorlage', () => {
    const wrapper = mountCalculator()
    expect(wrapper.get('[data-disclaimer]').text()).toBe('Die Berechnung bildet die Stichprobenvorlagen 2021–2027 nach. Sie ersetzt nicht die fachliche Würdigung der Prüfbehörde und ist kein Dokument der Europäischen Kommission.')
    expect(wrapper.get('[data-template-status]').text()).toContain('Fassung 4, Stand Oktober 2026')
    expect(wrapper.get('[data-template-status]').text()).toContain('keine amtliche Fassung')
    expect(wrapper.find('[data-mark]').exists()).toBe(false)
  })

  it('nimmt die Datenmarke der Anwendung als Text oder als Slot', () => {
    expect(mountCalculator({ dataMark: 'Daten bleiben im Browser' }).get('[data-mark]').text()).toBe('Daten bleiben im Browser')
    const wrapper = mount(SamplingCalculator, { props: { sheets: FOUNDATION_SHEETS }, slots: { mark: '<span class="eco-datamark">Browser</span>' } })
    mounted.push(wrapper)
    expect(wrapper.get('[data-mark] .eco-datamark').text()).toBe('Browser')
  })

  it('gibt den Dateien den Vorsatz der Anwendung', async () => {
    const wrapper = await withSample({ filePrefix: 'ECOHESION' })
    await menu(wrapper, 'save')
    await wrapper.get('[data-action="export"]').trigger('click')
    await settle()
    expect(delivered.map((file) => file.filename)).toEqual(['ECOHESION_03_MUS_1Z_2025_2026_Arbeitsstand.json', 'ECOHESION_03_MUS_1Z_2025_2026_Ergebnis.xlsx'])
  })
})
