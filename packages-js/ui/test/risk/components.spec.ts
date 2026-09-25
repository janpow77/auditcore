import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'
import { RiskFlagCard, RiskFlags, RiskProfileInfo, recordEntries, recordRules, type Evaluation, type ProfileDetail } from '../../src'
import { defineFlowauditElements } from '../../src/elements'
import flowstatJson from './fixtures/evaluation-flowstat.json'
import profileJson from './fixtures/profile-year-bound.json'
import yearBoundJson from './fixtures/evaluation-year-bound.json'

const evaluation = yearBoundJson as unknown as Evaluation
const flowstat = flowstatJson as unknown as Evaluation
const profile = profileJson as unknown as ProfileDetail

afterEach(() => {
  document.body.innerHTML = ''
})

function rowFor(wrapper: ReturnType<typeof mount>, key: string) {
  const row = wrapper.findAll('.fa-risk-table tbody tr').find((tr) => tr.text().startsWith(key))
  if (!row) throw new Error(`Zeile ${key} fehlt`)
  return row
}

describe('RiskFlags', () => {
  it('zeigt Profil, Verteilung mit unbestimmten Belegen und betroffene Datensätze', () => {
    const wrapper = mount(RiskFlags, { props: { evaluation, profile } })
    expect(wrapper.get('[data-testid="risk-profile"]').text()).toContain('riskanalysis.year_bound')
    expect(wrapper.get('[data-testid="risk-profile"]').text()).toContain('2026.09.5')
    expect(wrapper.text()).toContain('Nettobetrag fehlt in der Quelle (3)')
    expect(wrapper.text()).toContain('3 mit unbestimmtem Merkmal')
    expect(wrapper.findAll('.fa-risk-table tbody tr')).toHaveLength(10)
    expect(wrapper.find('[aria-label="RF02: unbestimmt"]').exists()).toBe(true)
    expect(wrapper.get('[data-testid="risk-detail"]').text()).toContain('Datensatz wählen')
  })

  it('öffnet die Karten eines Datensatzes mit Begründung, Eingabewerten und Schwellen', async () => {
    const wrapper = mount(RiskFlags, { props: { evaluation, profile } })
    await rowFor(wrapper, 'B-012').trigger('click')
    const detail = wrapper.get('[data-testid="risk-detail"]')
    const cards = detail.findAll('.fa-risk-card')
    expect(cards.map((card) => card.attributes('data-code'))).toEqual(['RF02', 'RF08', 'RF11'])
    const rf08 = cards[1]
    expect(rf08?.classes()).toContain('fa-risk-card--undetermined')
    expect(rf08?.text()).toContain('unbestimmt')
    expect(rf08?.text()).toContain('Nettobetrag fehlt in der Quelle')
    expect(rf08?.get('.fa-risk-card__empty').text()).toBe('leer')
    expect(rf08?.text()).toContain('Betrag größer als')
    expect(rf08?.text()).toContain('25.000')
    expect(wrapper.emitted('record-select')?.[0]).toEqual([11])
  })

  it('filtert per Klick auf einen Code und meldet den Filter', async () => {
    const wrapper = mount(RiskFlags, { props: { evaluation } })
    const button = wrapper.findAll('.fa-risk-summary__code').find((item) => item.text() === 'RF13')
    await button?.trigger('click')
    expect(wrapper.findAll('.fa-risk-table tbody tr')).toHaveLength(1)
    expect(wrapper.emitted('filter-change')?.at(-1)).toEqual([{ code: 'RF13', state: 'affected', query: '' }])
    await wrapper.get('[data-testid="risk-filter-state"]').setValue('all')
    await wrapper.get('[data-testid="risk-filter-code"]').setValue('')
    expect(wrapper.findAll('.fa-risk-table tbody tr')).toHaveLength(12)
    await wrapper.get('[data-testid="risk-filter-query"]').setValue('B-00')
    expect(wrapper.text()).toContain('9 von 12 Datensätzen')
  })

  it('zeigt übersprungene Regeln und Befunde über alle Datensätze', () => {
    const wrapper = mount(RiskFlags, { props: { evaluation: flowstat } })
    expect(wrapper.text()).toContain('5 Regeln übersprungen')
    expect(wrapper.text()).toContain('Spalten fehlen: zahlungsdatum')
    expect(wrapper.text()).not.toContain('Fehlende Spalten: zahlungsdatum')
    expect(wrapper.text()).toContain('Befunde über alle Datensätze')
    expect(wrapper.text()).toContain('BL_RF10_VENDOR_CONCENTRATION')
    expect(wrapper.text()).toContain('charakterisiertes Altverhalten')
    expect(wrapper.find('.fa-risk__hint').exists()).toBe(true)
  })

  it('nennt fehlende Spalten auch bei Regeln, die unbestimmt oder ohne Merkmal weiterlaufen', () => {
    const withMissing = { ...evaluation, missing_columns: { RF02: ['nettobetrag'] } }
    const wrapper = mount(RiskFlags, { props: { evaluation: withMissing } })
    expect(wrapper.text()).toContain('Fehlende Spalten: nettobetrag')
  })

  it('kommt ohne Auswertung aus', () => {
    const wrapper = mount(RiskFlags)
    expect(wrapper.text()).toContain('0 von 0 Datensätzen')
  })
})

describe('Einzelkomponenten', () => {
  it('RiskFlagCard zeigt Profilbindung und Fundstelle', () => {
    const [entry] = recordEntries(evaluation.records[0]!, recordRules(evaluation))
    const wrapper = mount(RiskFlagCard, { props: { entry: entry!, profile: evaluation.profile } })
    expect(wrapper.text()).toContain('Profil riskanalysis.year_bound · Version 2026.09.5 · freigegeben')
    expect(wrapper.text()).toContain('Fundstelle in der Quelle')
    expect(wrapper.text()).toContain('bruttobetrag')
  })

  it('RiskProfileInfo listet Eingabefelder mit Pflicht und Folge bei Fehlen', () => {
    const wrapper = mount(RiskProfileInfo, { props: { profile } })
    const row = wrapper.findAll('tr').find((tr) => tr.text().startsWith('nettobetrag'))
    expect(row?.text()).toContain('optional')
    expect(row?.text()).toContain('Nettobetrag fehlt in der Quelle')
    expect(wrapper.findAll('tr').find((tr) => tr.text().startsWith('Name'))?.text()).toContain('Pflicht')
    expect(wrapper.text()).toContain('Wertgrenzen')
    expect(wrapper.text()).not.toContain('[object Object]')
    expect(wrapper.text()).toContain('unbestimmt')
  })
})

describe('Web Component flowaudit-risk-flags', () => {
  it('rendert im Light DOM mit Objekt-Eigenschaften und sendet Ereignisse', async () => {
    defineFlowauditElements({ only: ['flowaudit-risk-flags'] })
    const element = document.createElement('flowaudit-risk-flags') as HTMLElement & Record<string, unknown>
    document.body.append(element)
    element.evaluation = evaluation
    await nextTick()
    expect(element.shadowRoot).toBeNull()
    expect(element.querySelectorAll('.fa-risk-table tbody tr')).toHaveLength(10)
    const received: unknown[] = []
    element.addEventListener('record-select', (event) => received.push((event as CustomEvent).detail))
    element.querySelector('.fa-risk-table tbody tr')?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    expect(received).toEqual([[0]])
  })
})
