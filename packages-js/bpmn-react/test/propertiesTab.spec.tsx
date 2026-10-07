import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent } from '@testing-library/react'
import type { NamedProperty, ProfileData, PropertyCatalogue } from '@auditcore/bpmn-flowaudit'
import { PropertiesTab } from '../src/panels/tabs/PropertiesTab'
import { renderInContext } from './context'

afterEach(cleanup)

const CATALOGUE: PropertyCatalogue = {
  entries: [
    { name: 'pb_art', label: { de: 'Art' }, kind: 'choice', values: ['Planung', 'Durchlauftest'] },
    { name: 'pb_ka', label: { de: 'Kernanforderung' }, kind: 'multi_choice', values: ['1', '2', '4'] },
    { name: 'pb_coso', label: { de: 'COSO-Komponente' }, kind: 'multi_choice', values: ['Kontrollaktivitäten'], depends_on: { property: 'pb_art', values: ['Durchlauftest'] } },
    { name: 'pb_offen', label: { de: 'Offener Punkt' }, kind: 'yes_no' },
    { name: 'pb_rechtsgrundlage', label: { de: 'Rechtsgrundlage' }, kind: 'text', help: { de: 'Freitext' } },
  ],
}
const PROFILE = { schema: 'auditcore_bpmn.profile/1', id: 'test', version: '2026.10.1', title: 'Test', roles: [], properties: CATALOGUE } as ProfileData

const store = <S extends object>(state: S) => ({ get: () => state, set: () => undefined, subscribe: () => () => undefined })

function renderTab(entries: NamedProperty[], readonly = false) {
  const writeProperties = vi.fn()
  const selection = { store: store({ element: { id: 'T' }, type: 'bpmn:Task', version: 1 }), namedProperties: () => entries, writeProperties }
  const result = renderInContext(<PropertiesTab />, { profile: PROFILE, selection, readonly })
  return { ...result, writeProperties }
}

describe('PropertiesTab', () => {
  it('zeigt die Merkmale des Profils mit den aktuellen Werten', () => {
    const { container } = renderTab([
      { name: 'pb_art', value: 'Planung' },
      { name: 'pb_ka', value: '4;9' },
    ])
    expect(Array.from(container.querySelectorAll('.fa-property .fa-label')).map((label) => label.textContent)).toEqual(['Art', 'Kernanforderung', 'COSO-Komponente', 'Offener Punkt', 'Rechtsgrundlage'])
    expect(container.querySelector<HTMLSelectElement>('select')!.value).toBe('Planung')
    expect(container.textContent).toContain('nicht im Profil')
    expect(container.querySelector('.fa-property--inactive')!.textContent).toContain('Nur bei Art: Durchlauftest')
    expect(container.textContent).toContain('Freitext')
  })

  it('schreibt Auswahl, Mehrfachauswahl, Ja/Nein und Freitext als Patch', () => {
    const { container, writeProperties } = renderTab([{ name: 'pb_ka', value: '4' }])
    fireEvent.change(container.querySelector('select')!, { target: { value: 'Durchlauftest' } })
    expect(writeProperties).toHaveBeenLastCalledWith({ pb_art: 'Durchlauftest' })
    fireEvent.click(container.querySelector('.fa-property__choices input')!)
    expect(writeProperties).toHaveBeenLastCalledWith({ pb_ka: '1;4' })
    const checks = container.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    fireEvent.click(checks[checks.length - 1]!)
    expect(writeProperties).toHaveBeenLastCalledWith({ pb_offen: 'ja' })
    const text = container.querySelector<HTMLInputElement>('input.fa-input')!
    fireEvent.change(text, { target: { value: '  Art. 77 VO (EU) 2021/1060 ' } })
    fireEvent.blur(text)
    expect(writeProperties).toHaveBeenLastCalledWith({ pb_rechtsgrundlage: 'Art. 77 VO (EU) 2021/1060' })
  })

  it('sperrt alle Felder im Lesemodus', () => {
    const { container } = renderTab([], true)
    expect(Array.from(container.querySelectorAll('input, select')).every((field) => (field as HTMLInputElement).disabled)).toBe(true)
  })
})
