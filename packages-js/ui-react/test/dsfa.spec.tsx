import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { draftAssessment, fakePort } from '../../ui-core/test/dataprotection/fake-port'
import { FlowauditDsfa, type FlowauditDsfaProps } from '../src/dataprotection/FlowauditDsfa'

afterEach(() => {
  cleanup()
  vi.useRealTimers()
})

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

async function renderDsfa(props: Partial<FlowauditDsfaProps> = {}) {
  const port = fakePort()
  const onAssessmentChange = vi.fn()
  const view = render(<FlowauditDsfa port={port} actor="daten-b" onAssessmentChange={onAssessmentChange} {...props} />)
  await flush()
  await flush()
  return { port, onAssessmentChange, root: view.container.firstElementChild as HTMLElement }
}

const byTestId = (root: HTMLElement, id: string): HTMLElement => root.querySelector(`[data-testid="${id}"]`) as HTMLElement

describe('FlowauditDsfa (React)', () => {
  it('zeigt die Tätigkeiten mit Stand und Ergebnis der Abschätzung', async () => {
    const { root } = await renderDsfa()
    const rows = Array.from(byTestId(root, 'dsfa-overview').querySelectorAll('tbody tr'))
    expect(rows.map((row) => row.querySelector('th')?.textContent)).toEqual(['Bewilligung von Zuwendungen', 'Vorhabenprüfung mit Stichprobe'])
    expect(rows[1]!.textContent).toContain('freigegeben')
    expect(rows[1]!.textContent).toContain('Freigabe mit Auflagen')
  })

  it('öffnet eine freigegebene Abschätzung schreibgeschützt mit Muss-Kriterium und Ergebnis', async () => {
    const { port, root } = await renderDsfa({ activityId: 'pruefung' })
    expect(port.assessment).toHaveBeenCalledWith('demo-assessment-1')
    expect(byTestId(root, 'dsfa-head').textContent).toContain('Fassung 1 – freigegeben')
    const screening = byTestId(root, 'dsfa-screening')
    expect(screening.textContent).toContain('DSFA erforderlich')
    expect(screening.textContent).toContain('1 Muss-Kriterien bejaht')
    const trigger = screening.querySelector('[data-question="dsk_nr08_beschaeftigte"]') as HTMLFieldSetElement
    expect(trigger.classList).toContain('fa-dsfa__question--yes')
    expect(trigger.disabled).toBe(true)
    expect(trigger.textContent).toContain('Muss-Kriterium')
  })

  it('wechselt die Abschnitte per Pfeiltaste (WAI-ARIA Tabs)', async () => {
    const { root } = await renderDsfa({ activityId: 'pruefung' })
    const tabs = () => screen.getAllByRole('tab')
    expect(tabs().map((tab) => tab.getAttribute('aria-selected'))).toEqual(['true', 'false', 'false'])
    fireEvent.keyDown(screen.getByRole('tablist'), { key: 'ArrowRight' })
    expect(tabs()[1]!.getAttribute('aria-selected')).toBe('true')
    expect(document.activeElement).toBe(tabs()[1])
    expect(byTestId(root, 'dsfa-risk').textContent).toContain('brutto 9 (hoch) → netto 3 (mittel)')
    fireEvent.keyDown(screen.getByRole('tablist'), { key: 'End' })
    expect(byTestId(root, 'dsfa-proposal')).not.toBeNull()
    expect(byTestId(root, 'dsfa-decision').textContent).toContain('Mit der Freigabe dokumentierte offene Punkte')
  })

  it('beantwortet Fragen, rechnet die Vorschau über die Bibliothek und speichert', async () => {
    const { port, onAssessmentChange, root } = await renderDsfa({ activityId: 'foerderung' })
    expect(byTestId(root, 'dsfa-screening').textContent).toContain('unvollständig')
    vi.useFakeTimers()
    fireEvent.click(root.querySelector('[data-question="art35_3_a"] input[value="ja"]')!)
    expect(byTestId(root, 'dsfa-head').textContent).toContain('Ungespeicherte Änderungen')
    await act(() => vi.advanceTimersByTimeAsync(500))
    expect(port.calculate).toHaveBeenCalledWith({ art35_3_a: { value: 'ja', justification: '' } }, [])
    expect(byTestId(root, 'dsfa-screening').textContent).toContain('Vorschau der Bibliothek')
    vi.useRealTimers()
    fireEvent.click(screen.getByRole('button', { name: 'Entwurf speichern' }))
    await flush()
    await flush()
    expect(port.updateAssessment).toHaveBeenCalledWith(draftAssessment.id, draftAssessment.revision, expect.objectContaining({ answers: { art35_3_a: { value: 'ja', justification: '' } } }))
    expect(onAssessmentChange.mock.calls[0]?.[0]).toMatchObject({ step: 'saved', id: draftAssessment.id })
  })

  it('verlangt bei Abweichung eine Begründung und sperrt die Freigabe für Bearbeitende', async () => {
    const { port, root } = await renderDsfa({ activityId: 'foerderung', actor: 'daten-a' })
    fireEvent.click(screen.getAllByRole('tab')[2]!)
    const decision = byTestId(root, 'dsfa-decision')
    expect(byTestId(decision, 'dsfa-four-eyes').textContent).toContain('Vier-Augen-Prinzip')
    expect(within(decision).getByRole('button', { name: /^Freigeben/ })).toHaveProperty('disabled', true)
    fireEvent.change(decision.querySelector('select')!, { target: { value: 'freigabe' } })
    fireEvent.change(decision.querySelector('textarea')!, { target: { value: 'Begründung der Abweichung' } })
    fireEvent.click(within(decision).getByRole('button', { name: 'Entscheidung speichern' }))
    await flush()
    expect(port.decide).toHaveBeenCalledWith(draftAssessment.id, draftAssessment.revision, { decision: 'freigabe', justification: 'Begründung der Abweichung', conditions: [] })
  })

  it('startet eine Abschätzung aus der Übersicht und meldet Fehler des Ports', async () => {
    const onError = vi.fn()
    const port = fakePort({ overview: vi.fn(async () => ({ items: [] })), profile: vi.fn(async () => Promise.reject(new Error('offline'))) })
    render(<FlowauditDsfa port={port} onError={onError} />)
    await flush()
    await flush()
    expect(onError).toHaveBeenCalledWith(expect.objectContaining({ code: 'network_error', message: 'Verbindung fehlgeschlagen: offline' }))
    expect(screen.getAllByRole('alert').map((node) => node.textContent)).toContain('Verbindung fehlgeschlagen: offline')
  })
})
