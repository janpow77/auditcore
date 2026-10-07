import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import type { NamedProperty, ProfileData, PropertyCatalogue } from '@auditcore/bpmn-flowaudit'
import PropertiesTab from '../src/panels/tabs/PropertiesTab.vue'
import { mountInContext } from './context'

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

function mountTab(entries: NamedProperty[], readonly = false) {
  const writeProperties = vi.fn()
  const selection = { type: ref('bpmn:Task'), namedProperties: () => entries, writeProperties }
  const wrapper = mountInContext(PropertiesTab, {}, { profile: PROFILE, selection, readonly })
  return { wrapper, writeProperties }
}

describe('PropertiesTab', () => {
  it('zeigt die Merkmale des Profils mit den aktuellen Werten', () => {
    const { wrapper } = mountTab([
      { name: 'pb_art', value: 'Planung' },
      { name: 'pb_ka', value: '4;9' },
    ])
    expect(wrapper.findAll('.fa-property .fa-label').map((label) => label.text())).toEqual(['Art', 'Kernanforderung', 'COSO-Komponente', 'Offener Punkt', 'Rechtsgrundlage'])
    expect((wrapper.find('select').element as HTMLSelectElement).value).toBe('Planung')
    expect(wrapper.text()).toContain('nicht im Profil')
    expect(wrapper.find('.fa-property--inactive').text()).toContain('Nur bei Art: Durchlauftest')
    expect(wrapper.text()).toContain('Freitext')
  })

  it('schreibt Auswahl, Mehrfachauswahl, Ja/Nein und Freitext als Patch', async () => {
    const { wrapper, writeProperties } = mountTab([{ name: 'pb_ka', value: '4' }])
    await wrapper.find('select').setValue('Durchlauftest')
    expect(writeProperties).toHaveBeenLastCalledWith({ pb_art: 'Durchlauftest' })
    await wrapper.findAll('.fa-property__choices')[0]!.findAll('input')[0]!.setValue(true)
    expect(writeProperties).toHaveBeenLastCalledWith({ pb_ka: '1;4' })
    const checks = wrapper.findAll('input[type="checkbox"]')
    await checks[checks.length - 1]!.setValue(true)
    expect(writeProperties).toHaveBeenLastCalledWith({ pb_offen: 'ja' })
    await wrapper.find('input.fa-input').setValue('  Art. 77 VO (EU) 2021/1060 ')
    expect(writeProperties).toHaveBeenLastCalledWith({ pb_rechtsgrundlage: 'Art. 77 VO (EU) 2021/1060' })
  })

  it('sperrt alle Felder im Lesemodus', () => {
    const { wrapper } = mountTab([], true)
    expect(wrapper.findAll('input, select').every((field) => field.attributes('disabled') !== undefined)).toBe(true)
  })
})
