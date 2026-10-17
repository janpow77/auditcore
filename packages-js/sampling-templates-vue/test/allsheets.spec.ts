import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { SHEETS, availableSheets, FAMILIES } from '@auditcore/sampling-templates-core'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { SamplingCalculator } from '../src/index'
import { pickVariant } from './sheets'

/** Oberfläche mit dem vollen Blattbestand: jedes Verfahren wählbar, Altvorlage X3, Datentabelle X1a, Übernahme je Schicht. */
const mounted: VueWrapper[] = []
const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')

function mountCalculator(): VueWrapper {
  const wrapper = mount(SamplingCalculator, { attachTo: document.body, props: { sheets: SHEETS, saveFile: () => undefined } })
  mounted.push(wrapper)
  return wrapper
}

async function settle(): Promise<void> {
  for (let round = 0; round < 3; round += 1) {
    await flushPromises()
    await vi.dynamicImportSettled()
  }
  await nextTick()
}

async function menu(wrapper: VueWrapper, action: string): Promise<void> {
  await wrapper.get('.fa-st__menu-wrap > button').trigger('click')
  await wrapper.get(`[data-action="${action}"]`).trigger('click')
  await settle()
}

/** Verfahren über die Auswahl öffnen: Familie, Zeiträume, Schichtung, dann übernehmen. */
async function choose(wrapper: VueWrapper, sheet: string): Promise<void> {
  await pickVariant(wrapper, sheet)
  await settle()
}

const input = (wrapper: VueWrapper, address: string) => wrapper.get(`[data-cell="${address}"]`).get<HTMLInputElement>('input, select')
const columns = (wrapper: VueWrapper): string[] => wrapper.get('[data-strata] thead').findAll('th').map((head) => head.text())
const STEP_SHEETS = ['02_Grundgesamtheit', '17_Unterstichprobe', '18_GFQ_AnhIII', '20_Druck_KOM']
const METHODS = availableSheets().filter((sheet) => !STEP_SHEETS.includes(sheet.id))

afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount()
  document.body.innerHTML = ''
})

describe('Voller Blattbestand', () => {
  it('jede Variante des Katalogs ist ein Verfahren mit Rechenkern oder eine Datentabelle', () => {
    const wrapper = mountCalculator()
    expect(METHODS).toHaveLength(18)
    expect(wrapper.text()).not.toContain('noch nicht verfügbar')
  })

  for (const sheet of METHODS) {
    it(`${sheet.id}: wählbar, Beispielwerte ergeben die Hauptgröße, leeres Formular zeigt „noch keine Angaben“`, async () => {
      const wrapper = mountCalculator()
      await choose(wrapper, sheet.id)
      expect(wrapper.get('[data-sheet-view]').attributes('data-sheet-view')).toBe(sheet.id)
      expect(wrapper.get('[data-result="primary"]').text()).toBe('noch keine Angaben')
      expect(wrapper.findAll('[data-hint]')).toHaveLength(0)
      await menu(wrapper, 'sample')
      expect(wrapper.get('[data-result="primary"]').text()).toMatch(/\d/)
      expect(wrapper.text()).not.toContain('NaN')
      expect(wrapper.text()).not.toContain('undefined')
    })
  }
})

describe('Altvorlage X3: Schichten in den Spalten E–K', () => {
  it('„Letzte Schicht entfernen“ entfernt die letzte Schicht und lässt die übrigen Eingaben stehen', async () => {
    const wrapper = mountCalculator()
    await choose(wrapper, 'X3_DiffSch_S_2017')
    await menu(wrapper, 'sample')
    expect(columns(wrapper).filter((name) => name.startsWith('Schicht'))).toEqual(['Schicht 1', 'Schicht 2', 'Schicht 3'])
    const before = ['E6', 'F6', 'G6'].map((cell) => input(wrapper, cell).element.value)
    expect(before.every((value) => value !== '')).toBe(true)
    await wrapper.get('[data-action="strata-remove"]').trigger('click')
    await settle()
    // Die Schicht trägt Eingaben: Erst nach der Rückfrage wird sie entfernt.
    expect(columns(wrapper).filter((name) => name.startsWith('Schicht'))).toHaveLength(3)
    expect(document.body.textContent).toContain('Die letzte Schicht enthält Eingaben. Wenn Sie fortfahren, werden sie gelöscht.')
    ;(document.querySelector('[data-action="discard"]') as HTMLButtonElement).click()
    await settle()
    expect(columns(wrapper).filter((name) => name.startsWith('Schicht'))).toEqual(['Schicht 1', 'Schicht 2'])
    expect(['E6', 'F6'].map((cell) => input(wrapper, cell).element.value)).toEqual(before.slice(0, 2))
    // Die dritte Schicht (Spalte G) ist geleert: wieder hinzugefügt, ist sie leer.
    await wrapper.get('[data-action="strata-add"]').trigger('click')
    await settle()
    expect(input(wrapper, 'G6').element.value).toBe('')
  })

  it('eine belegte siebte Schicht (Spalte K) ist sichtbar', async () => {
    const wrapper = mountCalculator()
    await choose(wrapper, 'X3_DiffSch_S_2017')
    await menu(wrapper, 'sample')
    for (let count = 3; count < 7; count += 1) await wrapper.get('[data-action="strata-add"]').trigger('click')
    await input(wrapper, 'K6').setValue('900.000')
    await settle()
    expect(columns(wrapper).at(-1)).toBe('Schicht 7')
    expect(wrapper.find('[data-strata-note]').exists()).toBe(false)
    expect(nbsp(input(wrapper, 'K6').element.value)).not.toBe('')
  })
})

describe('Datentabelle X1a', () => {
  it('die Kachel öffnet die Tabelle; als Verfahren wählbar ist sie nicht', async () => {
    const wrapper = mountCalculator()
    const family = FAMILIES.findIndex((entry) => entry.variants.some((variant) => variant.sheet === 'X1a_RF_2017'))
    await wrapper.findAll('[role="tab"]')[family]!.trigger('click')
    const tile = wrapper.get('[data-table-sheet="X1a_RF_2017"]')
    expect(tile.text()).toContain('Datentabelle')
    await tile.trigger('click')
    await settle()
    const dialog = document.querySelector('[role="dialog"]')
    expect(dialog?.textContent).toContain('Zuverlässigkeitsfaktoren')
    expect(dialog?.querySelectorAll('tbody tr')).toHaveLength(51)
    expect(dialog?.querySelector('[role="region"]')?.getAttribute('tabindex')).toBe('0')
    expect(wrapper.find('[data-sheet-view]').exists()).toBe(false)
  })

  it('aus dem Verfahren X1 heraus erreichbar', async () => {
    const wrapper = mountCalculator()
    await choose(wrapper, 'X1_KonsMUS_2017')
    await wrapper.get('[data-action="table-X1a_RF_2017"]').trigger('click')
    await settle()
    expect(document.querySelector('[role="dialog"] [data-table]')).not.toBeNull()
  })
})

describe('Unterstichproben in einem geschichteten Verfahren', () => {
  it('Übernahme je Schicht; Einheiten ohne Schichtnummer werden genannt', async () => {
    const wrapper = mountCalculator()
    await choose(wrapper, '04_MUS_1Z_S')
    await menu(wrapper, 'sample')
    await wrapper.get('[data-step="subsamples"]').trigger('click')
    await wrapper.get('[data-action="unit-add"]').trigger('click')
    for (const [cell, value] of [['C5', 'V-1'], ['C6', '100.000,00'], ['C10', '10'], ['C11', '50.000,00'], ['C12', '500,00'], ['W9', '2']] as const) await input(wrapper, cell).setValue(value)
    await wrapper.get('[data-action="unit-add"]').trigger('click')
    for (const [cell, value] of [['C5', 'V-2'], ['C6', '100.000,00'], ['C10', '10'], ['C11', '50.000,00'], ['C12', '500,00']] as const) await input(wrapper, cell).setValue(value)
    await settle()
    // Die Beispielwerte bringen eine Einheit ohne Schichtnummer mit; dazu kommt V-2.
    expect(wrapper.get('[data-unassigned]').text()).toContain('2 Einheiten ohne Schicht')
    await wrapper.get('[data-action="unit-transfer"]').trigger('click')
    expect(wrapper.get('[data-flash]').text()).toBe('Übernommen in Blatt 04: E46.')
    await wrapper.get('[data-step="method"]').trigger('click')
    expect(input(wrapper, 'E46').element.value).toBe('0,01')
  })
})
