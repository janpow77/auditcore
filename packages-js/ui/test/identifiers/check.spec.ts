import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineFlowauditElements } from '../../src/elements'
import IdentifierCheck from '../../src/identifiers/IdentifierCheck.vue'
import { BATCH_CSV, batchAnswer, fakeIdentifiersPort, invalidAnswer } from '../../../ui-core/test/identifiers/fake-port'

afterEach(() => {
  document.body.innerHTML = ''
  vi.restoreAllMocks()
})

describe('IdentifierCheck', () => {
  it('prüft eine Kennung und zeigt Status, Begründung, Grund und Einzelheiten', async () => {
    const port = fakeIdentifiersPort()
    const wrapper = mount(IdentifierCheck, { props: { port } })
    await flushPromises()
    await wrapper.get('[data-testid="ident-value"]').setValue('DE89370400440532013001')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(port.calls.check).toEqual([{ kind: 'iban', value: 'DE89370400440532013001', profile: 'strict' }])
    const result = wrapper.get('[data-testid="ident-result"]')
    expect(result.get('.fa-ident__badge--danger').text()).toBe('ungültig')
    expect(result.text()).toContain('IBAN-Prüfziffer ist falsch')
    expect(result.text()).toContain('Prüfziffer falsch')
    expect(result.attributes('aria-live')).toBe('polite')
    expect(wrapper.emitted('identifier-checked')?.[0]).toEqual([invalidAnswer.result])
  })

  it('bietet das Land nur für die USt-IdNr. an und beschreibt es', async () => {
    const wrapper = mount(IdentifierCheck, { props: { port: fakeIdentifiersPort() }, attachTo: document.body })
    await flushPromises()
    expect(wrapper.find('[data-testid="ident-country"]').exists()).toBe(false)
    await wrapper.get('[data-testid="ident-kind"]').setValue('vat_id')
    const country = wrapper.get('[data-testid="ident-country"]')
    expect(document.getElementById(country.attributes('aria-describedby') ?? '')?.textContent).toContain('ohne Länderpräfix')
    await country.setValue('de')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.get('[data-testid="ident-result"]').text()).toContain('DE136695976')
    wrapper.unmount()
  })

  it('prüft eine Tabelle als Stapel und exportiert das Ergebnis als CSV', async () => {
    const port = fakeIdentifiersPort()
    const wrapper = mount(IdentifierCheck, { props: { port } })
    await flushPromises()
    const input = wrapper.get('[data-testid="ident-file"]')
    Object.defineProperty(input.element, 'files', { value: [new File([BATCH_CSV], 'kennungen.csv')] })
    await input.trigger('change')
    await flushPromises()
    expect(wrapper.text()).toContain('kennungen.csv: 5 Zeilen')
    await wrapper.get('[data-testid="ident-col-value"]').setValue('2')
    await wrapper.get('[data-testid="ident-batch-run"]').trigger('submit')
    await flushPromises()
    expect(port.calls.batch).toHaveLength(1)
    expect(wrapper.get('.fa-ident__summary').text()).toBe('5 Zeilen geprüft: 2 gültig, 1 ungültig, 1 ohne Wert, 1 nicht prüfbar')
    expect(wrapper.emitted('batch-checked')?.[0]).toEqual([batchAnswer])
    const created = vi.fn(() => 'blob:csv')
    Object.assign(URL, { createObjectURL: created, revokeObjectURL: vi.fn() })
    await wrapper.get('[data-testid="ident-export"]').trigger('click')
    expect(created).toHaveBeenCalledOnce()
  })

  it('meldet Fehler als Ereignis und zeigt englische Texte mit Rückfall', async () => {
    const wrapper = mount(IdentifierCheck, { props: { port: fakeIdentifiersPort('catalogue'), locale: 'en' } })
    await flushPromises()
    expect(wrapper.emitted('error')?.[0]).toEqual(['Dienst nicht erreichbar'])
    expect(wrapper.get('[role="alert"]').text()).toContain('Anfrage abgelehnt')
  })

  it('läuft als Web Component <flowaudit-identifier-check>', async () => {
    defineFlowauditElements({ only: ['flowaudit-identifier-check'] })
    const element = document.createElement('flowaudit-identifier-check') as HTMLElement & Record<string, unknown>
    element.port = fakeIdentifiersPort()
    document.body.append(element)
    await flushPromises()
    const received: unknown[] = []
    element.addEventListener('identifier-checked', (event) => received.push((event as CustomEvent<unknown[]>).detail[0]))
    element.querySelector('form')?.dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(received).toEqual([invalidAnswer.result])
  })
})
