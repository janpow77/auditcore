import { readdirSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import type { DiagramElement, ModdleElement, Modeling } from '../src/diagram/services'
import { loadDefinitions, saveDefinitions, type LoadedDefinitions } from '../src/model/load'
import { namedPropertyValue, readNamedProperties, setNamedPropertiesDirect, writeNamedProperties } from '../src/model/camundaProperties'
import { propertyActive, propertyDefinitionsFor, splitPropertyValue, type PropertyCatalogue } from '../src/profile/properties'
import { isYes, propertyFields, textPatch, togglePatch, yesNoPatch, type PropertyField } from '../src/ui/propertyFields'
import { tabsFor } from '../src/ui/tabs'
import { fixture, TEST_PROFILE } from './helpers'

const MODELS = readdirSync(join(process.cwd(), 'test', 'fixtures', 'camunda')).filter((name) => name.endsWith('.bpmn')).sort()

/** Synthetic catalogue in the format of the systems audits (values shortened). */
const CATALOGUE: PropertyCatalogue = {
  title: { de: 'Prüfungsmerkmale' },
  entries: [
    { name: 'pb_art', label: { de: 'Art' }, kind: 'choice', values: ['Planung', 'Dokumentenanalyse', 'Durchlauftest', 'Kontrolltest'] },
    { name: 'pb_ka', label: { de: 'Kernanforderung' }, kind: 'multi_choice', values: ['1', '2', '3', '4'] },
    {
      name: 'pb_coso',
      label: { de: 'COSO-Komponente' },
      kind: 'multi_choice',
      values: ['Kontrollumfeld', 'Risikobeurteilung', 'Kontrollaktivitäten'],
      depends_on: { property: 'pb_art', values: ['Durchlauftest', 'Kontrolltest'] },
    },
    { name: 'pb_offen', label: { de: 'Offener Punkt' }, kind: 'yes_no', values: ['ja'] },
    { name: 'pb_gj', label: { de: 'Geschäftsjahr' }, kind: 'text', applies_to: ['event'] },
  ],
}
const PROFILE = { ...TEST_PROFILE, properties: CATALOGUE }

function flowElement(loaded: LoadedDefinitions, id: string): ModdleElement {
  const roots = loaded.definitions.get('rootElements') as ModdleElement[]
  for (const root of roots) {
    const found = ((root.get('flowElements') as ModdleElement[] | undefined) ?? []).find((element) => element.id === id)
    if (found) return found
  }
  throw new Error(`Element ${id} fehlt`)
}

/** All (element, name, value) triples of a model, in document order. */
function triples(xml: string): string[] {
  const document = new DOMParser().parseFromString(xml, 'application/xml')
  const properties = Array.from(document.getElementsByTagName('*')).filter(
    (element) => element.namespaceURI === 'http://camunda.org/schema/1.0/bpmn' && element.localName === 'property',
  )
  return properties.map((property) => {
    let owner = property.parentElement
    while (owner && !owner.getAttribute('id')) owner = owner.parentElement
    return `${owner?.getAttribute('id')}|${property.getAttribute('name')}|${property.getAttribute('value')}`
  })
}

async function loaded(name: string): Promise<LoadedDefinitions> {
  const result = await loadDefinitions(fixture(`camunda/${name}`))
  expect(result.warnings).toEqual([])
  return result
}

describe('camunda:property lesen', () => {
  it('liest alle Merkmale einer Prüfungshandlung in Dokumentreihenfolge', async () => {
    const model = await loaded('synthetische-systempruefung.bpmn')
    const task = flowElement(model, 'T_DT_KA4_Doppelfoerderung')
    expect(readNamedProperties(task).map((entry) => entry.name)).toEqual(['pb_art', 'pb_ka', 'pb_bk', 'pb_coso', 'pb_ziel', 'pb_stelle', 'pb_rechtsgrundlage', 'pb_offen'])
    expect(namedPropertyValue(task, 'pb_offen')).toBe('ja')
    expect(namedPropertyValue(flowElement(model, 'Start_PB'), 'pb_gj')).toBe('2030/2031')
    expect(namedPropertyValue(flowElement(model, 'G_Split'), 'pb_art')).toBe('')
  })
})

describe('camunda:property schreiben', () => {
  it('ändert nur das genannte Merkmal und erhält Reihenfolge und fremde Merkmale', async () => {
    const model = await loaded('synthetische-systempruefung.bpmn')
    const task = flowElement(model, 'T_DT_KA4_Doppelfoerderung')
    const before = readNamedProperties(task)
    setNamedPropertiesDirect(task, { pb_ka: '1;4' }, model.moddle)
    expect(readNamedProperties(task)).toEqual(before.map((entry) => (entry.name === 'pb_ka' ? { ...entry, value: '1;4' } : entry)))
  })

  it('entfernt ein leeres Merkmal statt es leer zu speichern und hängt neue hinten an', async () => {
    const model = await loaded('synthetische-systempruefung.bpmn')
    const task = flowElement(model, 'T_DT_KA4_Doppelfoerderung')
    setNamedPropertiesDirect(task, { pb_offen: '', pb_neu: ' x ', pb_bk: null }, model.moddle)
    const names = readNamedProperties(task).map((entry) => entry.name)
    expect(names).toEqual(['pb_art', 'pb_ka', 'pb_coso', 'pb_ziel', 'pb_stelle', 'pb_rechtsgrundlage', 'pb_neu'])
    expect(namedPropertyValue(task, 'pb_neu')).toBe('x')
  })

  it('legt Container und Erweiterung an und räumt sie wieder ab', async () => {
    const model = await loaded('synthetische-systempruefung.bpmn')
    const gateway = flowElement(model, 'G_Split')
    setNamedPropertiesDirect(gateway, { pb_art: 'Planung' }, model.moddle)
    expect(namedPropertyValue(gateway, 'pb_art')).toBe('Planung')
    const xml = await saveDefinitions(model, false)
    expect(xml).toMatch(/<bpmn:parallelGateway id="G_Split" name=""><bpmn:extensionElements><camunda:properties><camunda:property name="pb_art" value="Planung" \/><\/camunda:properties><\/bpmn:extensionElements>/)
    setNamedPropertiesDirect(gateway, { pb_art: '' }, model.moddle)
    expect(gateway.get('extensionElements')).toBeUndefined()
  })

  it('schreibt im Editor über modeling in einem Schritt je Container', async () => {
    const model = await loaded('synthetische-systempruefung.bpmn')
    const task = flowElement(model, 'T_KT')
    const calls: string[] = []
    const modeling = {
      updateModdleProperties: (_element: DiagramElement, target: ModdleElement, props: Record<string, unknown>) => {
        calls.push(Object.keys(props).join(','))
        for (const [key, value] of Object.entries(props)) target.set(key, value)
      },
    } as unknown as Modeling
    writeNamedProperties({ id: 'T_KT', type: 'bpmn:Task', businessObject: task }, { pb_coso: 'Kontrollaktivitäten;Risikobeurteilung' }, { modeling, moddle: model.moddle })
    expect(calls).toEqual(['$children'])
    expect(namedPropertyValue(task, 'pb_coso')).toBe('Kontrollaktivitäten;Risikobeurteilung')
  })
})

describe('Round-Trip eines Camunda-Modells', () => {
  it.each(MODELS)('%s bleibt beim Laden und Speichern ohne Bearbeitung erhalten', async (name) => {
    const original = fixture(`camunda/${name}`)
    const model = await loaded(name)
    const xml = await saveDefinitions(model, false)
    expect(triples(original).length).toBeGreaterThan(15)
    expect(triples(xml)).toEqual(triples(original))
    expect(xml).toContain('modeler:executionPlatform="Camunda Platform"')
    expect(xml).toContain('xmlns:camunda="http://camunda.org/schema/1.0/bpmn"')
    const again = await saveDefinitions(await loadDefinitions(xml), false)
    expect(again).toBe(xml)
  })

  it.each(MODELS)('%s: eine Änderung betrifft nur das geänderte Merkmal', async (name) => {
    const original = fixture(`camunda/${name}`)
    const model = await loaded(name)
    setNamedPropertiesDirect(flowElement(model, 'T_KT'), { pb_ziel: 'Berichterstattung' }, model.moddle)
    setNamedPropertiesDirect(flowElement(model, 'T_DT_KA4_Interessenkonflikte'), { pb_coso: 'Risikobeurteilung' }, model.moddle)
    const expected = triples(original).map((entry) =>
      entry.startsWith('T_KT|pb_ziel|') ? 'T_KT|pb_ziel|Berichterstattung' : entry.startsWith('T_DT_KA4_Interessenkonflikte|pb_coso|') ? 'T_DT_KA4_Interessenkonflikte|pb_coso|Risikobeurteilung' : entry,
    )
    const xml = await saveDefinitions(model, false)
    expect(triples(xml)).toEqual(expected)
    expect(xml).toContain('<camunda:property name="x_fremd" value="bleibt" />')
    expect(xml).toMatch(/<flowaudit:interneNotiz>Synthetische Notiz<\/flowaudit:interneNotiz>/)
  })
})

describe('Merkmalsdefinition im Profil', () => {
  it('bietet Merkmale nach Elementart an (Standard: Aktivitäten)', () => {
    expect(propertyDefinitionsFor(PROFILE, 'bpmn:Task').map((entry) => entry.name)).toEqual(['pb_art', 'pb_ka', 'pb_coso', 'pb_offen'])
    expect(propertyDefinitionsFor(PROFILE, 'bpmn:StartEvent').map((entry) => entry.name)).toEqual(['pb_gj'])
    expect(propertyDefinitionsFor(PROFILE, 'bpmn:ParallelGateway')).toEqual([])
    expect(propertyDefinitionsFor(TEST_PROFILE, 'bpmn:Task')).toEqual([])
  })

  it('zeigt den Reiter nur, wenn das Profil Merkmale für den Typ kennt', () => {
    expect(tabsFor('bpmn:Task', PROFILE).map((tab) => tab.id)).toContain('properties')
    expect(tabsFor('bpmn:Task', TEST_PROFILE).map((tab) => tab.id)).not.toContain('properties')
    expect(tabsFor('bpmn:ParallelGateway', PROFILE).map((tab) => tab.id)).not.toContain('properties')
    expect(tabsFor('bpmn:Task').map((tab) => tab.id)).not.toContain('properties')
  })

  it('wertet Bedingungen und Mehrfachwerte aus', () => {
    const coso = CATALOGUE.entries[2]!
    expect(propertyActive(coso, { pb_art: 'Durchlauftest' }, CATALOGUE.entries)).toBe(true)
    expect(propertyActive(coso, { pb_art: 'Interview' }, CATALOGUE.entries)).toBe(false)
    expect(splitPropertyValue(' 1; 4;; ')).toEqual(['1', '4'])
  })
})

describe('Formularmodell des Reiters', () => {
  const entries = [
    { name: 'pb_art', value: 'Durchlauftest' },
    { name: 'pb_ka', value: '4;9' },
    { name: 'pb_offen', value: 'ja' },
    { name: 'pb_fremd', value: 'bleibt' },
  ]

  it('liefert Felder mit aktuellen Werten und markiert unbekannte Werte', () => {
    const fields = propertyFields(PROFILE, 'bpmn:Task', entries)
    expect(fields.map((field) => field.name)).toEqual(['pb_art', 'pb_ka', 'pb_coso', 'pb_offen'])
    const ka = fields[1]!
    expect(ka.selected).toEqual(['4', '9'])
    expect(ka.options.find((option) => option.value === '9')).toEqual({ value: '9', label: '9', known: false })
    expect(fields[2]!.active).toBe(true)
    expect(isYes(fields[3]!)).toBe(true)
  })

  it('erzeugt Patches für Auswahl, Mehrfachauswahl und Ja/Nein', () => {
    const [art, ka, , offen] = propertyFields(PROFILE, 'bpmn:Task', entries) as [PropertyField, PropertyField, PropertyField, PropertyField]
    expect(textPatch(art, ' Kontrolltest ')).toEqual({ pb_art: 'Kontrolltest' })
    expect(togglePatch(ka, '1')).toEqual({ pb_ka: '1;4;9' })
    expect(togglePatch(ka, '4')).toEqual({ pb_ka: '9' })
    expect(yesNoPatch(offen, false)).toEqual({ pb_offen: '' })
    expect(yesNoPatch(offen, true)).toEqual({ pb_offen: 'ja' })
  })
})
