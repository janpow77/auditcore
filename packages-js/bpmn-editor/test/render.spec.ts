/**
 * Renderer: jede Form und Kante der Fixture wird gezeichnet; die SVG-
 * Ausgabe je Elementtyp ist als Snapshot festgehalten.
 */

import { describe, expect, it } from 'vitest'

import type { BpmnElement, ElementRegistry } from '../src/types'
import { readFixture } from './helpers/fixtures'
import { importXml } from './helpers/editor'

function visualOf(registry: ElementRegistry, element: BpmnElement): string {
  const gfx = registry.getGraphics(element)
  const visual = gfx.querySelector('.djs-visual')
  return (visual ? visual.innerHTML : '').replace(/fa-bpmn-\d+-/g, 'fa-bpmn-N-')
}

async function renderedFixture() {
  const { editor } = await importXml(readFixture('synthetisch/alle-elemente.bpmn'))
  const registry = editor.get<ElementRegistry>('elementRegistry')
  return { editor, registry }
}

describe('Renderer', () => {
  it('zeichnet jedes Element mit sichtbarem Inhalt', async () => {
    const { registry } = await renderedFixture()
    const elements = registry.filter((element) => !!element.parent)
    expect(elements.length).toBeGreaterThan(100)
    for (const element of elements) {
      expect(visualOf(registry, element).length, element.id).toBeGreaterThan(20)
    }
  })

  it('hält die SVG-Ausgabe je Elementtyp fest', async () => {
    const { registry } = await renderedFixture()
    const byType: Record<string, string> = {}
    const samples = registry.filter((element) => !!element.parent && !element.labelTarget)
    for (const element of samples) {
      const key = `${element.type}:${element.id}`
      byType[key] = visualOf(registry, element)
    }
    expect(byType).toMatchSnapshot()
  })

  it('übernimmt Farben aus bioc:/color:', async () => {
    const { registry } = await renderedFixture()
    const task = registry.get('Task_User') as BpmnElement
    const visual = visualOf(registry, task)
    expect(visual).toContain('fill: #bbdefb')
    expect(visual).toContain('stroke: #0d4372')
    const flow = registry.get('Flow_Default') as BpmnElement
    expect(visualOf(registry, flow)).toContain('stroke: #b71c1c')
  })

  it('zeigt Marker (Schleife, Mehrfachinstanz, Kompensation, Ad-hoc, zugeklappt)', async () => {
    const { registry } = await renderedFixture()
    const marker = (id: string) => visualOf(registry, registry.get(id) as BpmnElement)
    expect(marker('Task_User')).toContain('fa-marker-loop')
    expect(marker('Task_Manual')).toContain('fa-marker-parallel')
    expect(marker('Task_Service')).toContain('fa-marker-sequential')
    expect(marker('Task_Script')).toContain('fa-marker-compensation')
    expect(marker('Sub_AdHoc')).toContain('fa-marker-adhoc')
    expect(marker('Sub_Collapsed')).toContain('fa-marker-collapsed')
  })

  it('setzt Standard- und Bedingungsmarken an Sequenzflüssen', async () => {
    const { registry } = await renderedFixture()
    expect(visualOf(registry, registry.get('Flow_Default') as BpmnElement)).toContain('default-start')
    expect(visualOf(registry, registry.get('Flow_ActCond') as BpmnElement)).toContain('conditional-start')
    expect(visualOf(registry, registry.get('MessageFlow_1') as BpmnElement)).toContain('message-start')
  })

  it('beschriftet senkrechte Pools waagerecht im Kopfband', async () => {
    const { registry } = await renderedFixture()
    const vertical = visualOf(registry, registry.get('Participant_C') as BpmnElement)
    expect(vertical).toContain('Europäische Kommission')
    expect(vertical).not.toContain('rotate(-90)')
    expect(visualOf(registry, registry.get('Participant_A') as BpmnElement)).toContain('rotate(-90)')
  })
})
