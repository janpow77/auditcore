/**
 * Lokaler Paritätstest gegen nicht veröffentlichte Nutzerdiagramme.
 *
 * Aktiv nur, wenn `BPMN_LOCAL_FIXTURES` auf ein Verzeichnis zeigt; die
 * Dateien werden nie ins Repository übernommen.
 */

import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import { importXml, svc } from './helpers/editor'
import { canonicalXml } from './helpers/fixtures'

const directory = process.env.BPMN_LOCAL_FIXTURES
const files = directory ? readdirSync(directory).filter((name) => /\.(bpmn|xml)$/i.test(name)) : []

describe.skipIf(!directory)('Lokale Parität (BPMN_LOCAL_FIXTURES)', () => {
  it.each(files)('%s: Rundlauf und Darstellung', async (name) => {
    const xml = readFileSync(join(directory as string, name), 'utf8')
    const { editor, warnings } = await importXml(xml)
    const { xml: exported } = await editor.saveXML({ format: true })
    expect(exported).toBe(await canonicalXml(xml))
    const registry = svc(editor, 'elementRegistry')
    const shapes = (xml.match(/<bpmndi:BPMNShape\b/g) || []).length
    const edges = (xml.match(/<bpmndi:BPMNEdge\b/g) || []).length
    const rendered = registry.filter((element: { labelTarget?: unknown; parent?: unknown }) => !element.labelTarget && !!element.parent).length
    expect(rendered).toBe(shapes + edges)
    expect(warnings.filter((warning) => !/unknown attribute/.test(warning))).toEqual([])
    const { svg } = await editor.saveSVG()
    expect(svg).toContain('<svg')
    editor.destroy()
  })
})
