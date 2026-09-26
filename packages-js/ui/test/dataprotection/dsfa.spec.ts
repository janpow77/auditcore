import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import FaDsfa from '../../src/dataprotection/FaDsfa.vue'
import { defineFlowauditElements } from '../../src/elements'
import { draftAssessment, fakePort } from './fake-port'

afterEach(() => {
  vi.useRealTimers()
  document.body.innerHTML = ''
})

async function mountDsfa(props: Record<string, unknown> = {}) {
  const port = fakePort()
  const wrapper = mount(FaDsfa, { props: { port, actor: 'daten-b', ...props }, attachTo: document.body })
  await flushPromises()
  return { port, wrapper }
}

describe('FaDsfa', () => {
  it('zeigt die Tätigkeiten mit Stand und Ergebnis der Abschätzung', async () => {
    const { wrapper } = await mountDsfa()
    const rows = wrapper.findAll('[data-testid="dsfa-overview"] tbody tr')
    expect(rows.map((row) => row.get('th').text())).toEqual(['Bewilligung von Zuwendungen', 'Vorhabenprüfung mit Stichprobe'])
    expect(rows[1]!.text()).toContain('freigegeben')
    expect(rows[1]!.text()).toContain('Freigabe mit Auflagen')
  })

  it('öffnet eine freigegebene Abschätzung schreibgeschützt mit Muss-Kriterium und Ergebnis', async () => {
    const { port, wrapper } = await mountDsfa({ activityId: 'pruefung' })
    expect(port.assessment).toHaveBeenCalledWith('demo-assessment-1')
    expect(wrapper.get('[data-testid="dsfa-head"]').text()).toContain('Fassung 1 – freigegeben')
    const screening = wrapper.get('[data-testid="dsfa-screening"]')
    expect(screening.text()).toContain('DSFA erforderlich')
    expect(screening.text()).toContain('1 Muss-Kriterien bejaht')
    const trigger = screening.get('[data-question="dsk_nr08_beschaeftigte"]')
    expect(trigger.classes()).toContain('fa-dsfa__question--yes')
    expect(trigger.attributes('disabled')).toBeDefined()
    expect(trigger.text()).toContain('Muss-Kriterium')
  })

  it('wechselt die Abschnitte per Pfeiltaste (WAI-ARIA Tabs)', async () => {
    const { wrapper } = await mountDsfa({ activityId: 'pruefung' })
    const tabs = wrapper.findAll('[role="tab"]')
    expect(tabs.map((tab) => tab.attributes('aria-selected'))).toEqual(['true', 'false', 'false'])
    await wrapper.get('[role="tablist"]').trigger('keydown', { key: 'ArrowRight' })
    expect(wrapper.findAll('[role="tab"]')[1]!.attributes('aria-selected')).toBe('true')
    expect(wrapper.get('[data-testid="dsfa-risk"]').text()).toContain('brutto 9 (hoch) → netto 3 (mittel)')
    await wrapper.get('[role="tablist"]').trigger('keydown', { key: 'End' })
    expect(wrapper.find('[data-testid="dsfa-proposal"]').exists()).toBe(true)
    expect(wrapper.get('[data-testid="dsfa-decision"]').text()).toContain('Mit der Freigabe dokumentierte offene Punkte')
  })

  it('beantwortet Fragen, rechnet die Vorschau über die Bibliothek und speichert', async () => {
    vi.useFakeTimers()
    const { port, wrapper } = await mountDsfa({ activityId: 'foerderung' })
    expect(wrapper.get('[data-testid="dsfa-screening"]').text()).toContain('unvollständig')
    await wrapper.get('[data-question="art35_3_a"] input[value="ja"]').setValue(true)
    expect(wrapper.get('[data-testid="dsfa-head"]').text()).toContain('Ungespeicherte Änderungen')
    await vi.advanceTimersByTimeAsync(500)
    expect(port.calculate).toHaveBeenCalledWith({ art35_3_a: { value: 'ja', justification: '' } }, [])
    await flushPromises()
    expect(wrapper.get('[data-testid="dsfa-screening"]').text()).toContain('Vorschau der Bibliothek')
    await wrapper.findAll('button').find((button) => button.text() === 'Entwurf speichern')!.trigger('click')
    await flushPromises()
    expect(port.updateAssessment).toHaveBeenCalledWith(draftAssessment.id, draftAssessment.revision, expect.objectContaining({ answers: { art35_3_a: { value: 'ja', justification: '' } } }))
    expect(wrapper.emitted('assessment-change')?.[0]?.[0]).toMatchObject({ step: 'saved', id: draftAssessment.id })
  })

  it('verlangt bei Abweichung eine Begründung und sperrt die Freigabe für Bearbeitende', async () => {
    const { port, wrapper } = await mountDsfa({ activityId: 'foerderung', actor: 'daten-a' })
    await wrapper.findAll('[role="tab"]')[2]!.trigger('click')
    const decision = wrapper.get('[data-testid="dsfa-decision"]')
    expect(decision.get('[data-testid="dsfa-four-eyes"]').text()).toContain('Vier-Augen-Prinzip')
    const release = decision.findAll('button').find((button) => button.text().startsWith('Freigeben'))!
    expect(release.attributes('disabled')).toBeDefined()
    await decision.get('select').setValue('freigabe')
    await decision.get('textarea').setValue('Begründung der Abweichung')
    await decision.findAll('button').find((button) => button.text() === 'Entscheidung speichern')!.trigger('click')
    await flushPromises()
    expect(port.decide).toHaveBeenCalledWith(draftAssessment.id, draftAssessment.revision, { decision: 'freigabe', justification: 'Begründung der Abweichung', conditions: [] })
  })

  it('läuft als Web Component <flowaudit-dsfa> im Light DOM', async () => {
    defineFlowauditElements({ only: ['flowaudit-dsfa', 'flowaudit-vvt'] })
    const element = document.createElement('flowaudit-dsfa') as HTMLElement & Record<string, unknown>
    element.port = fakePort()
    document.body.append(element)
    await flushPromises()
    await nextTick()
    expect(element.shadowRoot).toBeNull()
    expect(element.querySelector('h2')?.textContent).toContain('Datenschutz-Folgenabschätzung')
    ;(element.querySelector('[data-testid="dsfa-overview"] tbody tr button') as HTMLButtonElement).click()
    await flushPromises()
    expect(element.querySelector('[data-testid="dsfa-head"]')?.textContent).toContain('Bewilligung von Zuwendungen')
    const vvt = document.createElement('flowaudit-vvt') as HTMLElement & Record<string, unknown>
    vvt.port = fakePort()
    document.body.append(vvt)
    await flushPromises()
    expect(vvt.querySelector('[data-testid="vvt-status"]')?.textContent).toContain('Fassung 2')
  })
})
