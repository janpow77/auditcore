import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineFlowauditElements } from '../../src/elements'
import { RestError } from '../../src/rest'
import ScreeningReview from '../../src/screening/ScreeningReview.vue'
import type { HitView, LogView, RunView, ScreeningPort, SettingsView, SourcesView } from '../../src'
import fixture from '../../../ui-core/test/fixtures/screening-contract.json'

const run = fixture.run as unknown as RunView
const firstSubject = run.subjects[0]!
const secondHit = firstSubject.hits[1]!

function fakePort(overrides: Partial<ScreeningPort> = {}) {
  const decided: HitView = { ...secondHit, review: { ...secondHit.review, status: 'dismissed', status_label: 'verworfen' } }
  const port = {
    settings: vi.fn(async () => fixture.settings as unknown as SettingsView),
    sources: vi.fn(async () => fixture.sources as unknown as SourcesView),
    runs: vi.fn(async () => ({ contract: run.contract, runs: [run] })),
    createRun: vi.fn(async () => run),
    run: vi.fn(async () => run),
    log: vi.fn(async () => fixture.log as unknown as LogView),
    decide: vi.fn(async () => decided),
    secondReview: vi.fn(async () => decided),
    ...overrides,
  } satisfies ScreeningPort
  return port
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('ScreeningReview', () => {
  it('zeigt Prüfläufe, Treffer je Name, Vergleich und Aufschlüsselung', async () => {
    const wrapper = mount(ScreeningReview, { props: { port: fakePort(), runId: run.run_id } })
    await flushPromises()
    expect(wrapper.text()).toContain('Screening-Trefferprüfung')
    expect(wrapper.findAll('.fa-screening__subject')).toHaveLength(2)
    expect(wrapper.text()).toContain('nicht abgefragt')
    expect(wrapper.find('.fa-screening__cmp').text()).toContain('Musterstraße 1, 12345 Musterstadt')
    expect(wrapper.find('.fa-screening__steps').text()).toContain('Ergebniswert')
    expect(wrapper.text()).toContain('wartet auf Zweitprüfung')
    expect(wrapper.text()).toContain('Quellenstand zum Zeitpunkt des Prüflaufs')
  })

  it('verlangt eine Begründung und sendet die Entscheidung mit der gelesenen Sequenz', async () => {
    const port = fakePort()
    const wrapper = mount(ScreeningReview, { props: { port, runId: run.run_id } })
    await flushPromises()
    await wrapper.findAll('.fa-screening__hit')[1]!.trigger('click')
    const dismiss = wrapper.findAll('button').find((b) => b.text() === 'Treffer verwerfen')!
    await dismiss.trigger('click')
    expect(dismiss.attributes('aria-pressed')).toBe('true')
    const form = wrapper.find('[aria-labelledby="fa-screening-decision-title"] form')
    await form.trigger('submit')
    expect(wrapper.find('[role="alert"]').text()).toContain('Eine Begründung ist Pflicht.')
    expect(port.decide).not.toHaveBeenCalled()
    await form.find('textarea').setValue('Geburtsjahr widerspricht.')
    await form.trigger('submit')
    await flushPromises()
    expect(port.decide).toHaveBeenCalledWith(run.run_id, secondHit.hit_id, {
      outcome: 'dismissed',
      reason: 'Geburtsjahr widerspricht.',
      four_eyes: false,
      expected_sequence: 0,
    })
    expect(wrapper.emitted('decided')?.[0]).toEqual([{ runId: run.run_id, hitId: secondHit.hit_id, status: 'dismissed' }])
  })

  it('meldet Portfehler als Ereignis und Warnung', async () => {
    const port = fakePort({ settings: vi.fn(async () => Promise.reject(new RestError('Nicht angemeldet.', 401, 'unauthenticated'))) })
    const wrapper = mount(ScreeningReview, { props: { port } })
    await flushPromises()
    expect(wrapper.emitted('error')?.[0]).toEqual([{ code: 'unauthenticated', message: 'Nicht angemeldet.', status: 401 }])
    expect(wrapper.find('[role="alert"]').text()).toBe('Nicht angemeldet.')
  })

  it('zeigt ohne Port einen Hinweis und spricht Englisch mit locale="en"', async () => {
    const wrapper = mount(ScreeningReview, { props: { locale: 'en' } })
    await flushPromises()
    expect(wrapper.find('h2').text()).toBe('Screening hit review')
    expect(wrapper.find('[role="alert"]').text()).toContain('port')
  })

  it('lädt, sobald der Port nachträglich gesetzt wird', async () => {
    const port = fakePort()
    const wrapper = mount(ScreeningReview)
    await wrapper.setProps({ port })
    await flushPromises()
    expect(port.settings).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Neuer Prüflauf')
  })
})

describe('<flowaudit-screening-review>', () => {
  it('läuft im Light DOM, nimmt den Port als Eigenschaft und sendet run-created', async () => {
    defineFlowauditElements({ only: ['flowaudit-screening-review'] })
    const element = document.createElement('flowaudit-screening-review') as HTMLElement & Record<string, unknown>
    const port = fakePort()
    element.port = port
    document.body.append(element)
    await flushPromises()
    expect(element.shadowRoot).toBeNull()
    expect(element.querySelector('.fa-screening__header h2')?.textContent).toBe('Screening-Trefferprüfung')
    const received: unknown[] = []
    element.addEventListener('run-created', (event) => received.push((event as CustomEvent<unknown[]>).detail[0]))
    const textarea = element.querySelector<HTMLTextAreaElement>('[data-testid="screening-subjects"]')!
    textarea.value = 'Maximilian Beispielmann; 1970-03-14; de'
    textarea.dispatchEvent(new Event('input'))
    element.querySelector('[aria-labelledby="fa-screening-run-form-title"] form')?.dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(port.createRun).toHaveBeenCalledOnce()
    expect(received).toEqual([{ runId: run.run_id }])
  })
})
