import { RestError } from '@auditcore/common'
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fakePort, run, secondHit } from '../../ui-core/test/screening/fake-port'
import { FlowauditScreeningReview, LocaleProvider } from '../src'

afterEach(() => {
  cleanup()
  document.body.innerHTML = ''
})

const settle = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

describe('FlowauditScreeningReview (nativ)', () => {
  it('zeigt Prüfläufe, Treffer je Name, Vergleich und Aufschlüsselung', async () => {
    const { container } = render(<FlowauditScreeningReview port={fakePort()} runId={run.run_id} />)
    await settle()
    expect(screen.getByRole('heading', { level: 2 }).textContent).toBe('Screening-Trefferprüfung')
    expect(container.querySelectorAll('.fa-screening__subject')).toHaveLength(2)
    expect(container.textContent).toContain('nicht abgefragt')
    expect(container.querySelector('.fa-screening__cmp')?.textContent).toContain('Musterstraße 1, 12345 Musterstadt')
    expect(container.querySelector('.fa-screening__steps')?.textContent).toContain('Ergebniswert')
    expect(container.textContent).toContain('wartet auf Zweitprüfung')
    expect(container.querySelector('[data-testid="screening-review"]')?.getAttribute('aria-busy')).toBe('false')
  })

  it('verlangt eine Begründung und sendet die Entscheidung mit der gelesenen Sequenz', async () => {
    const port = fakePort()
    const onDecided = vi.fn()
    const { container } = render(<FlowauditScreeningReview port={port} runId={run.run_id} onDecided={onDecided} />)
    await settle()
    fireEvent.click(container.querySelectorAll('.fa-screening__hit')[1]!)
    const dismiss = screen.getByRole('button', { name: 'Treffer verwerfen' })
    fireEvent.click(dismiss)
    expect(dismiss.getAttribute('aria-pressed')).toBe('true')
    const panel = container.querySelector<HTMLElement>('[aria-labelledby="fa-screening-decision-title"]')!
    const form = panel.querySelector('form')!
    fireEvent.submit(form)
    expect(within(panel).getByRole('alert').textContent).toContain('Eine Begründung ist Pflicht.')
    expect(port.decide).not.toHaveBeenCalled()
    fireEvent.change(form.querySelector('textarea')!, { target: { value: 'Geburtsjahr widerspricht.' } })
    fireEvent.submit(form)
    await settle()
    expect(port.decide).toHaveBeenCalledWith(run.run_id, secondHit.hit_id, {
      outcome: 'dismissed',
      reason: 'Geburtsjahr widerspricht.',
      four_eyes: false,
      expected_sequence: 0,
    })
    expect(onDecided).toHaveBeenCalledWith({ runId: run.run_id, hitId: secondHit.hit_id, status: 'dismissed' })
  })

  it('Zweitprüfung: Zustimmen per Tastatur sendet approve und Sequenz', async () => {
    const port = fakePort()
    render(<FlowauditScreeningReview port={port} runId={run.run_id} />)
    await settle()
    fireEvent.change(screen.getByLabelText('Begründung (Pflicht)'), { target: { value: 'Identität belegt.' } })
    const approve = screen.getByRole('button', { name: 'Zustimmen' })
    approve.focus()
    expect(document.activeElement).toBe(approve)
    fireEvent.click(approve)
    await settle()
    const first = run.subjects[0]!.hits[0]!
    expect(port.secondReview).toHaveBeenCalledWith(run.run_id, first.hit_id, { approve: true, reason: 'Identität belegt.', expected_sequence: first.review.sequence })
  })

  it('meldet Portfehler als Ereignis und Warnung', async () => {
    const onError = vi.fn()
    const port = fakePort({ settings: vi.fn(async () => Promise.reject(new RestError('Nicht angemeldet.', 401, 'unauthenticated'))) })
    render(<FlowauditScreeningReview port={port} onError={onError} />)
    await settle()
    expect(onError).toHaveBeenCalledWith({ code: 'unauthenticated', message: 'Nicht angemeldet.', status: 401 })
    expect(screen.getByRole('alert').textContent).toBe('Nicht angemeldet.')
  })

  it('zeigt ohne Port einen Hinweis und spricht Englisch mit locale="en" oder LocaleProvider', async () => {
    render(<FlowauditScreeningReview locale="en" />)
    await settle()
    expect(screen.getByRole('heading', { level: 2 }).textContent).toBe('Screening hit review')
    expect(screen.getByRole('alert').textContent).toContain('port')
    cleanup()
    render(<LocaleProvider locale="en"><FlowauditScreeningReview /></LocaleProvider>)
    expect(screen.getByRole('heading', { level: 2 }).textContent).toBe('Screening hit review')
  })

  it('lädt, sobald der Port nachträglich gesetzt wird, und meldet einen neuen Prüflauf', async () => {
    const port = fakePort()
    const onRunCreated = vi.fn()
    const { rerender } = render(<FlowauditScreeningReview onRunCreated={onRunCreated} />)
    rerender(<FlowauditScreeningReview port={port} onRunCreated={onRunCreated} />)
    await settle()
    expect(port.settings).toHaveBeenCalledOnce()
    expect(screen.getByRole('heading', { name: 'Neuer Prüflauf' })).toBeTruthy()
    fireEvent.change(screen.getByTestId('screening-subjects'), { target: { value: 'Maximilian Beispielmann; 1970-03-14; de' } })
    fireEvent.change(screen.getByTestId('screening-case'), { target: { value: '  Los 1  ' } })
    fireEvent.click(screen.getByTestId('screening-start'))
    await settle()
    expect(port.createRun).toHaveBeenCalledOnce()
    expect(vi.mocked(port.createRun).mock.calls[0]![0]).toMatchObject({
      kind: 'sanctions',
      subjects: [{ name: 'Maximilian Beispielmann', birth_date: '1970-03-14', country: 'de' }],
      case_reference: 'Los 1',
    })
    expect(onRunCreated).toHaveBeenCalledWith({ runId: run.run_id })
  })
})
