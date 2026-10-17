import type { DownloadFile } from '@auditcore/common'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { SamplingCalculator } from '../src/index'
import { FOUNDATION_SHEETS } from './sheets'

const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')
const mounted: VueWrapper[] = []
const delivered: DownloadFile[] = []

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

const cell = (wrapper: VueWrapper, address: string) => wrapper.get(`[data-cell="${address}"]`)
const input = (wrapper: VueWrapper, address: string) => cell(wrapper, address).get<HTMLInputElement>('input, select')
const value = (wrapper: VueWrapper, address: string): string => nbsp(cell(wrapper, address).get('.fa-st__value').text())

afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount()
  document.body.innerHTML = ''
  delivered.length = 0
})

describe('Dateien: Vorschau, Fehlermeldungen, Entwurf', () => {
  async function chooseFile(wrapper: VueWrapper, file: File): Promise<void> {
    const field = wrapper.get('input[type="file"]')
    Object.defineProperty(field.element, 'files', { value: [file], configurable: true })
    await field.trigger('change')
    await settle()
  }

  async function templateFile(): Promise<File> {
    const { writeWorkbook } = await import('@auditcore/sampling-templates-core/workbook')
    const values: Record<number, number | string> = { 7: 48500000, 8: 420, 9: 'Mittel', 10: 0.7, 11: 'Einseitig', 14: 0.02, 17: 0.007, 20: '0,12', 22: 2, 23: 'NEIN', 24: 'ja', 27: 92, 38: 'k. A.' }
    const rows = Array.from({ length: 40 }, (_, index) => [null, null, values[index + 1] === undefined ? null : { value: values[index + 1]! }])
    return new File([writeWorkbook([{ name: '03_MUS_1Z', rows }]).slice().buffer], 'vorlage.xlsx')
  }

  it('eine ausgefüllte Vorlage wird erst nach einer Vorschau übernommen, die jede Umdeutung und Abweichung nennt', async () => {
    const wrapper = mountCalculator()
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await chooseFile(wrapper, await templateFile())
    const preview = document.querySelector('[data-import-preview]')!
    expect(preview.textContent).toContain('Aus „vorlage.xlsx“ werden 11 Eingaben übernommen (Blätter: 03_MUS_1Z)')
    const issues = [...preview.querySelectorAll('[data-import-issues] tbody tr')].map((row) => [...row.children].map((child) => child.textContent?.trim()))
    expect(issues).toEqual(expect.arrayContaining([
      ['03_MUS_1Z', expect.stringContaining('C9 ·'), 'Mittel', 'Schreibweise an die Auswahlliste angepasst', 'mittel'],
      ['03_MUS_1Z', expect.stringContaining('C24 ·'), 'ja', 'Schreibweise an die Auswahlliste angepasst', 'Ja'],
      ['03_MUS_1Z', expect.stringContaining('C20 ·'), '0,12', 'Zahl stand als Text in der Zelle', '0.12'],
      ['03_MUS_1Z', expect.stringContaining('C38 ·'), 'k. A.', 'keine lesbare Zahl', 'nicht übernommen'],
    ]))
    const differences = [...preview.querySelectorAll('[data-import-differences] tbody tr')].map((row) => [...row.children].map((child) => child.textContent?.trim()))
    expect(differences).toEqual([['03_MUS_1Z', expect.stringContaining('C27 ·'), '92', '30']])
    expect(inputOrNull(wrapper, 'C7')).toBe('')
    ;(document.querySelector('[data-action="import-apply"]') as HTMLButtonElement).click()
    await settle()
    expect(document.querySelector('[data-import-preview]')).toBeNull()
    expect(input(wrapper, 'C7').element.value).toBe('48.500.000,00')
    expect(input(wrapper, 'C24').element.value).toBe('Ja')
    expect(value(wrapper, 'C27')).toBe('30')
    expect(wrapper.get('[data-notice="info"]').text()).toContain('Eingaben aus der Excel-Vorlage „vorlage.xlsx“ übernommen')
    expect(wrapper.get('[data-status]').text()).toContain('geändert')
  })

  it('Abbrechen der Vorschau übernimmt nichts', async () => {
    const wrapper = mountCalculator()
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await chooseFile(wrapper, await templateFile())
    const buttons = [...document.querySelectorAll('[role="dialog"] footer button')] as HTMLButtonElement[]
    buttons[0]!.click()
    await settle()
    expect(document.querySelector('[data-import-preview]')).toBeNull()
    expect(input(wrapper, 'C7').element.value).toBe('')
  })

  it('ein Fehler beim Speichern oder Lesen erscheint als Meldung', async () => {
    const quiet = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    const wrapper = mountCalculator({ saveFile: () => Promise.reject(new Error('kein Speicherplatz')) })
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await menu(wrapper, 'save')
    expect(wrapper.get('[data-notice="danger"]').text()).toContain('Die Datei konnte nicht erzeugt werden')
    expect(wrapper.get('[data-status]').text()).not.toContain('gespeichert')
    await wrapper.get('[data-notice="danger"] button').trigger('click')
    const unreadable = new File(['{}'], 'gesperrt.json')
    Object.defineProperty(unreadable, 'text', { value: () => Promise.reject(new Error('gesperrt')) })
    await chooseFile(wrapper, unreadable)
    expect(wrapper.get('[data-notice="danger"]').text()).toContain('Die Datei „gesperrt.json“ konnte nicht verarbeitet werden')
    quiet.mockRestore()
  })

  it('der lokale Entwurf ist ohne Zutun der Anwendung aus und überschreibt keinen vorgegebenen Arbeitsstand', async () => {
    const plain = mount(SamplingCalculator, { attachTo: document.body, props: { sheets: FOUNDATION_SHEETS } })
    mounted.push(plain)
    expect(plain.find('[data-action="clearDraft"]').exists()).toBe(false)
    expect(plain.text()).not.toContain('lokalen Entwurf')
    localStorage.setItem('auditcore-sampling-templates:vorrang', JSON.stringify({ v: 1, data: 'kein Arbeitsstand' }))
    const initial = { header: { programm: '', cci: '', geschaeftsjahr: '', bearbeitung: '', aktenzeichen: '' }, activeMethod: '03_MUS_1Z', sheets: { '03_MUS_1Z': { C7: 1000, C14: 0.02 } } }
    const first = mountCalculator({ localDraft: true, draftKey: 'vorrang', initialState: initial })
    await input(first, 'C7').setValue('2.000,00')
    first.unmount()
    mounted.pop()
    await settle()
    expect(localStorage.getItem('auditcore-sampling-templates:vorrang')).toContain('flowaudit-stichprobe')
    const second = mountCalculator({ localDraft: true, draftKey: 'vorrang', initialState: initial })
    await settle()
    expect(input(second, 'C7').element.value).toBe('1.000,00')
    expect(second.find('[data-notice="info"]').exists()).toBe(false)
    localStorage.clear()
  })
})

function inputOrNull(wrapper: VueWrapper, address: string): string | null {
  const found = wrapper.find(`[data-cell="${address}"] input`)
  return found.exists() ? (found.element as HTMLInputElement).value : null
}
