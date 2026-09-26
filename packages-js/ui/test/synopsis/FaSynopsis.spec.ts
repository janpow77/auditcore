import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineFlowauditElements } from '../../src/elements'
import FaSynopsis from '../../src/synopsis/FaSynopsis.vue'
import type { SynopsisPort } from '@auditcore/ui-core'
import type { ExportPayload, RowUpdate } from '@auditcore/ui-core'
import { article, checklist, standard } from '../../../ui-core/test/synopsis/fixtures'

afterEach(() => {
  document.body.innerHTML = ''
  vi.restoreAllMocks()
})

function rowTitles(wrapper: ReturnType<typeof mount>): string[] {
  return wrapper.findAll('.fa-synopsis-row__title').map((node) => node.text().replace(/, [^,]+$/, ''))
}

describe('FaSynopsis', () => {
  it('zeigt Kopf, Hinweise und nur Änderungen nebeneinander mit del/ins', () => {
    const wrapper = mount(FaSynopsis, { props: { comparison: standard } })
    expect(wrapper.find('h2').text()).toBe(standard.title)
    expect(wrapper.text()).toContain('3 geändert · 2 entfallen · 3 neu')
    expect(wrapper.text()).toContain('keine Prüfungsentscheidung')
    expect(wrapper.findAll('article')).toHaveLength(8)
    const first = wrapper.find('article')
    expect(first.attributes('aria-labelledby')).toBeTruthy()
    expect(first.findAll('h4').map((node) => node.text())).toEqual(['Bisherige Fassung', 'Neue Fassung'])
    expect(first.find('ins').text()).toContain('Unternehmen in Hessen.')
    expect(first.find('ins .fa-sr-only').text()).toBe('eingefügt:')
  })

  it('wechselt auf die Inline-Ansicht und filtert nach Art und Suchbegriff', async () => {
    const wrapper = mount(FaSynopsis, { props: { comparison: standard } })
    const [sideBySide, inline] = wrapper.findAll('[role="group"] button')
    expect(sideBySide?.attributes('aria-pressed')).toBe('true')
    await inline?.trigger('click')
    expect(wrapper.emitted('update:layout')?.[0]).toEqual(['inline'])
    await wrapper.setProps({ layout: 'inline' })
    expect(wrapper.find('.fa-synopsis-row__inline').exists()).toBe(true)
    expect(wrapper.find('.fa-synopsis-row__inline del').exists()).toBe(true)

    const boxes = wrapper.findAll('fieldset input[type="checkbox"]')
    await boxes[5]?.setValue(true) // unverändert
    expect(wrapper.findAll('article')).toHaveLength(11)
    await wrapper.find('input[type="search"]').setValue('Umsatzsteuer')
    expect(rowTitles(wrapper)).toEqual(['§ 2 Förderfähige Ausgaben, Absatz 3'])
    await wrapper.find('input[type="search"]').setValue('gibt es nicht')
    expect(wrapper.text()).toContain('Keine passenden Unterschiede')
  })

  it('navigiert per Taste und Schaltfläche und meldet die Position', async () => {
    const wrapper = mount(FaSynopsis, { props: { comparison: standard }, attachTo: document.body })
    const status = wrapper.find('[role="status"]')
    expect(status.attributes('aria-live')).toBe('polite')
    expect(status.text()).toBe('8 Änderungen in dieser Ansicht')
    await wrapper.find('section').trigger('keydown', { key: 'n' })
    expect(status.text()).toBe('Änderung 1 von 8')
    expect(document.activeElement?.getAttribute('data-row-id')).toBe(standard.result.rows[0]?.row_id)
    await wrapper.find('section').trigger('keydown', { key: 'j' })
    await wrapper.find('section').trigger('keydown', { key: 'k' })
    expect(status.text()).toBe('Änderung 1 von 8')
    const next = wrapper.findAll('button').find((button) => button.text() === 'Nächste Änderung')
    await next?.trigger('click')
    expect(status.text()).toBe('Änderung 2 von 8')
    expect(wrapper.emitted('navigate')).toHaveLength(4)
    expect(wrapper.find('[aria-current="true"]').attributes('data-row-id')).toBe(standard.result.rows[1]?.row_id)
    await wrapper.find('input[type="search"]').trigger('keydown', { key: 'n' })
    expect(status.text()).toBe('Änderung 2 von 8')
    wrapper.unmount()
  })

  it('bearbeitet Auswahl und Grund und speichert über den Port', async () => {
    const updateRows = vi.fn<NonNullable<SynopsisPort['updateRows']>>(async () => checklist)
    const port: SynopsisPort = { load: async () => checklist, updateRows, exportUrl: (id, format) => `/x/${id}/${format}` }
    const wrapper = mount(FaSynopsis, { props: { comparison: checklist, editable: true, port } })
    expect(wrapper.text()).toContain('5 von 6 Zeilen für die Ausgabe ausgewählt') // unveränderte Zeile ist abgewählt
    await wrapper.find('.fa-synopsis-row__include input').setValue(false)
    await flushPromises()
    const rowId = checklist.result.rows[0]?.row_id ?? ''
    expect(wrapper.emitted('row-update')?.[0]).toEqual([{ row_id: rowId, selected: false } satisfies RowUpdate])
    expect(updateRows).toHaveBeenCalledWith(checklist.id, [{ row_id: rowId, selected: false }])
    expect(wrapper.text()).toContain('4 von 6 Zeilen')
    await wrapper.find('textarea').setValue('redaktionell')
    await flushPromises()
    expect(updateRows).toHaveBeenLastCalledWith(checklist.id, [{ row_id: rowId, reason: 'redaktionell' }])
    expect(wrapper.findAll('a[download]').map((link) => link.attributes('href'))).toEqual([
      `/x/${checklist.id}/docx`,
      `/x/${checklist.id}/pdf`,
      `/x/${checklist.id}/json`,
    ])
    updateRows.mockRejectedValueOnce(new Error('offline'))
    await wrapper.find('textarea').setValue('neu')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toBe('Die Änderung konnte nicht gespeichert werden.')
  })

  it('lädt über den Port und meldet Ladefehler', async () => {
    const port: SynopsisPort = { load: vi.fn(async () => article) }
    const wrapper = mount(FaSynopsis, { props: { comparisonId: article.id, port } })
    expect(wrapper.text()).toContain('Vergleich wird geladen')
    await flushPromises()
    expect(wrapper.find('h2').text()).toBe(article.title)
    expect(wrapper.text()).toContain('Änderungsbefehle erkannt')
    expect(wrapper.find('details summary').text()).toBe('Konsolidierte Arbeitsfassung')
    expect(wrapper.findAll('h4').map((node) => node.text())).toContain('Fassung nach dem Entwurf')
    const failing = mount(FaSynopsis, { props: { comparisonId: 'x', port: { load: async () => Promise.reject(new Error('404')) } } })
    await flushPromises()
    expect(failing.find('[role="alert"]').text()).toBe('Der Vergleich konnte nicht geladen werden.')
  })

  it('exportiert HTML und Markdown als Ereignis und Datei', async () => {
    const createObjectURL = vi.fn(() => 'blob:x')
    Object.assign(URL, { createObjectURL, revokeObjectURL: vi.fn() })
    const wrapper = mount(FaSynopsis, { props: { comparison: standard } })
    const button = (label: string) => wrapper.findAll('button').find((node) => node.text() === label)
    await button('Markdown')?.trigger('click')
    await button('HTML')?.trigger('click')
    const payloads = wrapper.emitted('export')?.map(([payload]) => payload as ExportPayload) ?? []
    expect(payloads.map((payload) => [payload.format, payload.filename])).toEqual([
      ['markdown', 'Förderrichtlinie_Mittelstand_Fassung_2025_und_2026.md'],
      ['html', 'Förderrichtlinie_Mittelstand_Fassung_2025_und_2026.html'],
    ])
    expect(payloads[0]?.content).toContain('**Unternehmen in Hessen.**')
    expect(createObjectURL).toHaveBeenCalledTimes(2)
    await button('Druckansicht / PDF')?.trigger('click')
    expect(document.querySelector('iframe[aria-hidden="true"]')).not.toBeNull()
  })

  it('spricht Englisch, wenn locale gesetzt ist', () => {
    const wrapper = mount(FaSynopsis, { props: { result: standard.result, locale: 'en' } })
    expect(wrapper.text()).toContain('Previous version')
    expect(wrapper.text()).toContain('Next change')
    expect(wrapper.find('h2').text()).toBe('Förderrichtlinie_2025.docx → Förderrichtlinie_2026.docx')
  })

  it('zeigt ohne Daten einen leeren Zustand', () => {
    expect(mount(FaSynopsis).text()).toBe('Kein Vergleich ausgewählt.')
  })
})

describe('<flowaudit-synopsis>', () => {
  it('rendert im Light DOM, nimmt comparison als Eigenschaft und sendet Ereignisse', async () => {
    defineFlowauditElements({ only: ['flowaudit-synopsis'] })
    const element = document.createElement('flowaudit-synopsis') as HTMLElement & Record<string, unknown>
    element.comparison = standard
    document.body.append(element)
    await nextTick()
    expect(element.shadowRoot).toBeNull()
    expect(element.querySelector('h2')?.textContent).toBe(standard.title)
    const received: unknown[] = []
    element.addEventListener('navigate', (event) => received.push((event as CustomEvent<unknown[]>).detail[0]))
    element.querySelector('section')?.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', bubbles: true }))
    expect(received).toEqual([standard.result.rows[0]?.row_id])
  })
})
