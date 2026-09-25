/**
 * Rundlauf Import → Export: Ohne Bearbeitung muss der Export dem kanonisch
 * serialisierten Original exakt entsprechen (Semantik, DI-Koordinaten,
 * Farben, Erweiterungen).
 */

import { describe, expect, it } from 'vitest'

import { importXml, svc } from './helpers/editor'
import { canonicalXml, listFixtures, readFixture } from './helpers/fixtures'

const FIXTURES = [...listFixtures('synthetisch'), ...listFixtures('audit-designer')]

describe('Rundlauf Import → Export', () => {
  it.each(FIXTURES)('%s bleibt unverändert', async (path) => {
    const xml = readFixture(path)
    const { editor } = await importXml(xml)
    const { xml: exported } = await editor.saveXML({ format: true })
    expect(exported).toBe(await canonicalXml(xml))
    editor.destroy()
  })

  it('bleibt nach zweifachem Rundlauf stabil', async () => {
    const xml = readFixture('synthetisch/alle-elemente.bpmn')
    const first = await importXml(xml)
    const { xml: once } = await first.editor.saveXML({ format: true })
    const second = await importXml(once)
    const { xml: twice } = await second.editor.saveXML({ format: true })
    expect(twice).toBe(once)
  })

  it('erhält unbekannte Erweiterungen und Farben', async () => {
    const { editor } = await importXml(readFixture('synthetisch/alle-elemente.bpmn'))
    const { xml } = await editor.saveXML()
    expect(xml).toContain('flowaudit:foo="bar"')
    expect(xml).toContain('duration="15"')
    expect(xml).toContain('<vendor:unbekannt')
    expect(xml).toContain('<flowaudit:rechtsgrundlage>Art. 74 VO (EU) 2021/1060</flowaudit:rechtsgrundlage>')
    expect(xml).toContain('bioc:fill="#bbdefb"')
    expect(xml).toContain('color:border-color="#b71c1c"')
    expect(xml).toContain('BPMNPlane_Collapsed')
  })

  it('meldet nur den erwarteten Hinweis auf fremde Attribute', async () => {
    const { warnings } = await importXml(readFixture('synthetisch/alle-elemente.bpmn'))
    expect(warnings).toEqual(['unknown attribute <duration>'])
  })

  it('stellt jedes Element mit DI dar', async () => {
    const xml = readFixture('synthetisch/alle-elemente.bpmn')
    const { editor } = await importXml(xml)
    const registry = svc(editor, 'elementRegistry')
    const ids = [...xml.matchAll(/bpmnElement="([^"]+)"/g)].map((match) => match[1])
    for (const id of ids) {
      const planeRoot = registry.get(`${id}_plane`)
      expect(registry.get(id) || planeRoot, id).toBeTruthy()
    }
  })

  it('reicht Diagramme ohne DI verlustfrei durch und warnt', async () => {
    const xml = readFixture('audit-designer/flowaudit-metadaten.bpmn')
    const { editor, warnings } = await importXml(xml)
    expect(warnings.join(' ')).toMatch(/DI/)
    const { xml: exported } = await editor.saveXML()
    expect(exported).toContain('<flowaudit:rechtsgrundlage>§ 55 BHO; Art. 74 VO (EU) 2021/1060</flowaudit:rechtsgrundlage>')
    expect(exported).toContain('<flowaudit:interneNotiz>')
  })

  it('lehnt nicht wohlgeformtes XML ab', async () => {
    const broken = '<bpmn:startEvent xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"><bpmn:endEvent>'
    await expect(importXml(broken)).rejects.toThrow()
  })
})
