import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { recordEntries, recordRules, type RiskPort } from '@auditcore/ui-core'
import { riskEvaluation as evaluation, riskFlowstat as flowstat, riskPort, riskProfile as profile } from '../../ui-core/test/parity/cases-risk'
import { FlowauditRiskFlags, LocaleProvider, RiskFlagCard, RiskProfileInfo, type FlowauditRiskFlagsProps } from '../src'

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

afterEach(() => {
  cleanup()
  document.body.innerHTML = ''
})

function renderFlags(props: Partial<FlowauditRiskFlagsProps> = {}) {
  return render(<FlowauditRiskFlags evaluation={evaluation} {...props} />)
}

const tableRows = (container: HTMLElement) => Array.from(container.querySelectorAll('.fa-risk-table tbody tr'))
const rowFor = (container: HTMLElement, key: string) => tableRows(container).find((tr) => tr.textContent?.startsWith(key)) as HTMLElement

describe('FlowauditRiskFlags (nativ)', () => {
  it('zeigt Profil, Verteilung mit unbestimmten Belegen und betroffene Datensätze', () => {
    const { container } = renderFlags({ profile })
    expect(screen.getByTestId('risk-profile').textContent).toContain('riskanalysis.year_bound')
    expect(screen.getByTestId('risk-profile').textContent).toContain('2026.09.5')
    expect(container.textContent).toContain('Nettobetrag fehlt in der Quelle (3)')
    expect(container.textContent).toContain('3 mit unbestimmtem Merkmal')
    expect(tableRows(container)).toHaveLength(10)
    expect(screen.getAllByRole('img', { name: 'RF02: unbestimmt' }).length).toBeGreaterThan(0)
    expect(screen.getByTestId('risk-detail').textContent).toContain('Datensatz wählen')
  })

  it('öffnet die Karten eines Datensatzes und meldet die Auswahl; erneuter Klick hebt sie auf', () => {
    const onRecordSelect = vi.fn()
    const { container } = renderFlags({ profile, onRecordSelect })
    fireEvent.click(rowFor(container, 'B-012'))
    const cards = Array.from(screen.getByTestId('risk-detail').querySelectorAll('.fa-risk-card'))
    expect(cards.map((card) => card.getAttribute('data-code'))).toEqual(['RF02', 'RF08', 'RF11'])
    const rf08 = cards[1] as HTMLElement
    expect(rf08.classList).toContain('fa-risk-card--undetermined')
    expect(rf08.textContent).toContain('Nettobetrag fehlt in der Quelle')
    expect(rf08.querySelector('.fa-risk-card__empty')?.textContent).toBe('leer')
    expect(rf08.textContent).toContain('Betrag größer als')
    expect(rf08.textContent).toContain('25.000')
    expect(within(rf08).getByRole('heading', { level: 4 }).id).toBe(rf08.getAttribute('aria-labelledby'))
    expect(rowFor(container, 'B-012').querySelector('[aria-current="true"]')).not.toBeNull()
    fireEvent.click(rowFor(container, 'B-012'))
    expect(onRecordSelect.mock.calls).toEqual([[11], [null]])
    expect(screen.getByTestId('risk-detail').textContent).toContain('Datensatz wählen')
  })

  it('wählt Datensätze auch per Tastatur (Enter)', () => {
    const onRecordSelect = vi.fn()
    const { container } = renderFlags({ onRecordSelect })
    const row = rowFor(container, 'B-001')
    expect(row.tabIndex).toBe(0)
    fireEvent.keyDown(row, { key: 'Enter' })
    expect(onRecordSelect).toHaveBeenCalledWith(0)
  })

  it('filtert per Klick auf einen Code und über die Filterfelder und meldet den Filter', () => {
    const onFilterChange = vi.fn()
    const { container } = renderFlags({ onFilterChange })
    fireEvent.click(screen.getByRole('button', { name: 'RF13' }))
    expect(tableRows(container)).toHaveLength(1)
    expect(onFilterChange).toHaveBeenLastCalledWith({ code: 'RF13', state: 'affected', query: '' })
    fireEvent.change(screen.getByTestId('risk-filter-state'), { target: { value: 'all' } })
    fireEvent.change(screen.getByTestId('risk-filter-code'), { target: { value: '' } })
    expect(tableRows(container)).toHaveLength(12)
    fireEvent.change(screen.getByTestId('risk-filter-query'), { target: { value: 'B-00' } })
    expect(container.textContent).toContain('9 von 12 Datensätzen')
    expect(onFilterChange).toHaveBeenLastCalledWith({ code: null, state: 'all', query: 'B-00' })
    expect(screen.getByRole('search', { name: 'Filter' })).toBeTruthy()
  })

  it('zeigt übersprungene Regeln, Befunde über alle Datensätze und den Hinweis für Altprofile', () => {
    const { container } = render(<FlowauditRiskFlags evaluation={flowstat} />)
    expect(container.textContent).toContain('5 Regeln übersprungen')
    expect(container.textContent).toContain('Spalten fehlen: zahlungsdatum')
    expect(container.textContent).not.toContain('Fehlende Spalten: zahlungsdatum')
    expect(container.textContent).toContain('BL_RF10_VENDOR_CONCENTRATION')
    expect(container.textContent).toContain('charakterisiertes Altverhalten')
    expect(container.querySelector('.fa-risk__hint[role="note"]')).not.toBeNull()
  })

  it('setzt die Auswahl bei einer neuen Auswertung zurück', () => {
    const { container, rerender } = renderFlags()
    fireEvent.click(rowFor(container, 'B-001'))
    expect(screen.getByTestId('risk-detail').querySelector('h3')).not.toBeNull()
    rerender(<FlowauditRiskFlags evaluation={{ ...evaluation }} />)
    expect(screen.getByTestId('risk-detail').textContent).toContain('Datensatz wählen')
  })

  it('kommt ohne Auswertung aus', () => {
    const { container } = render(<FlowauditRiskFlags />)
    expect(container.textContent).toContain('0 von 0 Datensätzen')
  })

  it('lädt die Profilbeschreibung über den Port nach und zeigt Ladefehler', async () => {
    const port = riskPort()
    const spy = vi.spyOn(port, 'profile')
    const { container, unmount } = renderFlags({ port })
    await flush()
    expect(spy).toHaveBeenCalledWith('riskanalysis.year_bound', '2026.09.5')
    expect(container.textContent).toContain('Profil und Eingabefelder')
    unmount()
    render(<FlowauditRiskFlags evaluation={evaluation} port={riskPort('Netzwerkfehler')} />)
    await flush()
    expect(screen.getByRole('alert').textContent).toBe('Netzwerkfehler')
  })

  it('verwirft ein nachgeladenes Profil, wenn die Auswertung inzwischen gewechselt hat', async () => {
    let resolve: (value: typeof profile) => void = () => undefined
    const port = { ...riskPort(), profile: vi.fn(() => new Promise<typeof profile>((done) => { resolve = done })) } as RiskPort
    const other = { ...evaluation, profile: { ...evaluation.profile, fingerprint: 'anders' } }
    const { container, rerender } = renderFlags({ port })
    rerender(<FlowauditRiskFlags evaluation={other} />)
    await act(async () => resolve(profile))
    expect(container.querySelector('.fa-risk-profile')).toBeNull()
  })

  it('spricht Englisch über Prop oder Provider', () => {
    render(<LocaleProvider locale="en"><FlowauditRiskFlags evaluation={evaluation} /></LocaleProvider>)
    expect(screen.getByRole('heading', { level: 2 }).textContent).toBe('Risk flags')
    expect(screen.getByRole('region', { name: 'Distribution per flag' })).toBeTruthy()
  })
})

describe('Einzelkomponenten (nativ)', () => {
  it('RiskFlagCard zeigt Profilbindung und Fundstelle', () => {
    const [entry] = recordEntries(evaluation.records[0]!, recordRules(evaluation))
    const { container } = render(<RiskFlagCard entry={entry!} profile={evaluation.profile} />)
    expect(container.textContent?.replace(/\s+/g, ' ')).toContain('Profil riskanalysis.year_bound · Version 2026.09.5 · freigegeben')
    expect(container.textContent).toContain('Fundstelle in der Quelle')
    expect(container.textContent).toContain('bruttobetrag')
  })

  it('RiskProfileInfo listet Eingabefelder mit Pflicht und Folge bei Fehlen', () => {
    const { container } = render(<RiskProfileInfo profile={profile} />)
    const rows = Array.from(container.querySelectorAll('tr'))
    const row = rows.find((tr) => tr.textContent?.startsWith('nettobetrag'))
    expect(row?.textContent).toContain('optional')
    expect(row?.textContent).toContain('Nettobetrag fehlt in der Quelle')
    expect(container.textContent).toContain('Wertgrenzen')
    expect(container.textContent).not.toContain('[object Object]')
    fireEvent.click(screen.getByRole('button', { name: 'Nach Feld sortieren' }))
    expect(screen.getAllByRole('columnheader').some((th) => th.getAttribute('aria-sort') === 'ascending')).toBe(true)
  })
})
