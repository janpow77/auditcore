import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import FaComparisons from '../../src/documents/FaComparisons.vue'
import { defineFlowauditElements } from '../../src/elements'
import { created, fakePort, file, imported, summaries } from '../../../ui-core/test/documents/fake-port'

afterEach(() => {
  document.body.innerHTML = ''
})

function choose(input: HTMLInputElement, chosen: File): void {
  Object.defineProperty(input, 'files', { value: [chosen], configurable: true })
  input.dispatchEvent(new Event('change'))
}

async function mounted(props: Record<string, unknown> = {}) {
  const port = fakePort()
  const wrapper = mount(FaComparisons, { props: { port, ...props }, attachTo: document.body })
  await flushPromises()
  return { port, wrapper }
}

describe('FaComparisons', () => {
  it('prüft vor dem Hochladen und zeigt die Befunde an den Feldern', async () => {
    const { port, wrapper } = await mounted({ maxUploadBytes: 1024 })
    await wrapper.find('form').trigger('submit')
    expect(port.create).not.toHaveBeenCalled()
    expect(wrapper.find('.fa-comparisons-form__problems').text()).toContain('Die bisherige Fassung fehlt.')
    choose(wrapper.find<HTMLInputElement>('[data-testid="comparisons-oldFile"]').element, file('alt.odt'))
    await flushPromises()
    const old = wrapper.find('[data-testid="comparisons-oldFile"]')
    expect(old.attributes('aria-invalid')).toBe('true')
    expect(wrapper.text()).toContain('alt.odt: Bitte eine DOCX-, DOCM- oder PDF-Datei auswählen.')
  })

  it('legt einen Vergleich an, meldet ihn und öffnet die Synopse', async () => {
    const { port, wrapper } = await mounted()
    choose(wrapper.find<HTMLInputElement>('[data-testid="comparisons-oldFile"]').element, file('alt.docx'))
    choose(wrapper.find<HTMLInputElement>('[data-testid="comparisons-newFile"]').element, file('neu.docx'))
    await wrapper.find('input[type="radio"][value="article_law"]').setValue(true)
    expect(wrapper.text()).toContain('Stammgesetz (geltende Fassung)')
    expect(wrapper.find('input[type="number"]').exists()).toBe(false)
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(port.create).toHaveBeenCalledWith(expect.any(File), 'alt.docx', expect.any(File), 'neu.docx', expect.objectContaining({ comparison_type: 'article_law' }))
    expect(wrapper.emitted('comparison-created')?.[0]).toEqual([created])
    expect(wrapper.find('[role="status"]').text()).toBe(`„${created.title}“ wurde angelegt.`)
    await wrapper.find(`[aria-label="„${created.title}“ öffnen"]`).trigger('click')
    await flushPromises()
    expect(wrapper.emitted('comparison-open')?.[0]).toEqual([created.id])
    expect(port.load).toHaveBeenCalledWith(created.id)
    expect(wrapper.find('.fa-synopsis').exists()).toBe(true)
    await wrapper.find('.fa-comparisons__open > button').trigger('click')
    expect(wrapper.find('.fa-synopsis').exists()).toBe(false)
  })

  it('öffnet ohne eingebettete Synopse nur per Ereignis', async () => {
    const { port, wrapper } = await mounted({ showSynopsis: false })
    await wrapper.find('.fa-comparisons-list__actions button').trigger('click')
    expect(wrapper.emitted('comparison-open')?.[0]).toEqual([summaries[0]?.id])
    expect(port.load).not.toHaveBeenCalled()
  })

  it('löscht erst nach Bestätigung im Dialog', async () => {
    const { port, wrapper } = await mounted()
    const target = summaries[1]!
    await wrapper.find(`[aria-label="„${target.title}“ löschen"]`).trigger('click')
    const dialog = document.querySelector('[role="dialog"]') as HTMLElement
    expect(dialog.textContent).toContain(`„${target.title}“ wird endgültig gelöscht.`)
    ;(dialog.querySelector('[data-testid="comparisons-confirm-remove"]') as HTMLButtonElement).click()
    await flushPromises()
    expect(port.remove).toHaveBeenCalledWith(target.id)
    expect(wrapper.emitted('comparison-removed')?.[0]).toEqual([target.id])
    expect(wrapper.findAll('.fa-comparisons-list__item')).toHaveLength(summaries.length - 1)
    expect(document.querySelector('[role="dialog"]')).toBeNull()
  })

  it('importiert eine JSON-Datei und zeigt Fehler des Imports', async () => {
    const { port, wrapper } = await mounted()
    const picker = wrapper.find<HTMLInputElement>('[data-testid="comparisons-import"]').element
    choose(picker, new File(['kein json'], 'x.json'))
    await flushPromises()
    await vi.waitFor(() => expect(wrapper.find('[role="alert"]').text()).toBe('Die Datei ist kein gültiges JSON.'))
    choose(picker, new File([JSON.stringify(created.result)], 'ergebnis.json'))
    await vi.waitFor(() => expect(port.importResult).toHaveBeenCalledWith({ result: created.result }))
    await flushPromises()
    expect(wrapper.emitted('comparison-imported')?.[0]).toEqual([imported])
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
  })

  it('filtert die Liste über die Suche', async () => {
    const { wrapper } = await mounted()
    await wrapper.find('input[type="search"]').setValue('al_stamm')
    expect(wrapper.findAll('.fa-comparisons-list__item')).toHaveLength(1)
    expect(wrapper.text()).toContain(`1 von ${summaries.length} Vergleichen`)
  })

  it('läuft als Web Component <flowaudit-comparisons> mit Port als Eigenschaft', async () => {
    defineFlowauditElements({ only: ['flowaudit-comparisons'] })
    const element = document.createElement('flowaudit-comparisons') as HTMLElement & { port?: unknown }
    document.body.append(element)
    element.port = fakePort()
    await flushPromises()
    await vi.waitFor(() => expect(element.querySelectorAll('.fa-comparisons-list__item')).toHaveLength(summaries.length))
    const opened = vi.fn()
    element.addEventListener('comparison-open', opened)
    ;(element.querySelector('.fa-comparisons-list__actions button') as HTMLButtonElement).click()
    expect(opened).toHaveBeenCalledOnce()
  })
})
