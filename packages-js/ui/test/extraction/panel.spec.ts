import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import FaExtraction from '../../src/extraction/FaExtraction.vue'
import { defineFlowauditElements } from '../../src/elements'
import { fakeExtractionPort, runDonut, runOk, syntheticFile } from '../../../ui-core/test/extraction/fake-port'

afterEach(() => {
  document.body.innerHTML = ''
})

function chooseFile(input: HTMLInputElement, file: File): void {
  Object.defineProperty(input, 'files', { value: [file], configurable: true })
  input.dispatchEvent(new Event('change'))
}

describe('FaExtraction', () => {
  it('lädt hoch, zeigt Feldkonfidenz, Entscheidung und Befunde und meldet das Ergebnis', async () => {
    const port = fakeExtractionPort()
    const wrapper = mount(FaExtraction, { props: { port }, attachTo: document.body })
    await flushPromises()
    await wrapper.get('form').trigger('submit')
    expect(wrapper.get('[role="alert"]').text()).toBe('Bitte eine Datei auswählen.')
    chooseFile(wrapper.get('[data-testid="extraction-file"]').element as HTMLInputElement, syntheticFile())
    await wrapper.get('[data-testid="extraction-profile"]').setValue('auditcore.pipeline.donut')
    expect(wrapper.find('[data-testid="extraction-experimental"]').exists()).toBe(true)
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(port.calls).toEqual([['beleg.png', 'auditcore.pipeline.donut', 64]])
    expect(wrapper.get('[data-testid="extraction-status"]').text()).toBe('Prüfung erforderlich')
    const total = wrapper.get('[data-field="total"]')
    expect(total.text()).toContain('verworfen (Plausibilität)')
    expect(total.text()).toContain('Vorschlag: 99.999,99')
    expect(wrapper.get('[data-field="date"] .fa-badge--warning').text()).toMatch(/81\s%/)
    expect(wrapper.findAll('[data-testid="extraction-findings"] tbody tr')[0]?.attributes('data-rule')).toBe('VAL_DONUT_PLAUSIBILITY')
    expect(wrapper.emitted('extraction-completed')?.[0]).toEqual([runDonut])
  })

  it('zeigt ein übergebenes Ergebnis ohne Port', async () => {
    const wrapper = mount(FaExtraction, { props: { result: runOk } })
    await flushPromises()
    expect(wrapper.text()).toContain('Kein Port übergeben')
    expect(wrapper.get('[data-testid="extraction-status"]').text()).toBe('Ohne Auffälligkeiten')
    expect(wrapper.text()).toContain('Keine Auffälligkeiten.')
    expect(wrapper.find('form').exists()).toBe(false)
  })

  it('meldet abgelehnte Läufe als Ereignis error', async () => {
    const wrapper = mount(FaExtraction, { props: { port: fakeExtractionPort({ failing: 'run' }) } })
    await flushPromises()
    chooseFile(wrapper.get('[data-testid="extraction-file"]').element as HTMLInputElement, syntheticFile())
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.emitted('error')?.[0]).toEqual(['Dienst nicht erreichbar'])
    expect(wrapper.get('.fa-extraction__failure').text()).toBe('Anfrage abgelehnt: Dienst nicht erreichbar')
  })

  it('läuft als Web Component <flowaudit-extraction>', async () => {
    defineFlowauditElements({ only: ['flowaudit-extraction'] })
    const element = document.createElement('flowaudit-extraction') as HTMLElement & { port: unknown }
    document.body.append(element)
    element.port = fakeExtractionPort()
    await flushPromises()
    await new Promise((resolve) => setTimeout(resolve, 0))
    await flushPromises()
    expect(element.querySelector('[data-testid="extraction-run"]')?.textContent).toContain('Erkennen')
  })
})
