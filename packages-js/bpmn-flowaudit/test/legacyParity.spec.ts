/**
 * Parity with the audit_designer BPMN editor: every test of
 * `bpmnErweiterungen.spec.ts` and `useBpmnEditor.spec.ts`, ported to the
 * new module names (see docs/bpmn/paritaet-audit-designer.md).
 */

import { describe, expect, it, vi } from 'vitest'
import { prepareSvg } from '../src/export/svgPostProcessing'
import { collectColors } from '../src/export/exportData'
import { computePageGrid, pageSize } from '../src/layout/pageFormats'
import { buildGroups, type LegacyListItem } from '../src/collection/legacyTree'
import { base64Utf8, buildMystSnippet, diagramLabel } from '../src/export/myst'
import { readMetadata, writeMetadata } from '../src/model/legacyMetadata'
import { germanTranslate } from '../src/i18n/translate'
import { findPaletteColor, normalizeColor } from '../src/export/colorPalette'
import { readTasksFromXml, writeTaskToXml } from '../src/model/flowstatAttributes'
import type { ModelElement } from '../src/model/processModel'
import { emptyExtensions } from '../src/schema/types'
import type { DiagramElement, ModdleElement } from '../src/diagram/services'

const RAW_SVG =
  '<?xml version="1.0" encoding="utf-8"?>' +
  '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200" ' +
  'viewBox="100 50 400 200" version="1.1"><defs><marker id="pfeil"/></defs>' +
  '<g class="viewport"><rect x="120" y="60" width="100" height="80"/></g></svg>'

const BASE = {
  title: '',
  showLegend: false,
  showMetadata: false,
  showLegalBases: false,
  colors: [],
  legalBases: [],
  metadata: { createdOn: '18.08.2026', editor: 'Prüferin', version: '3' },
}

const parse = (svg: string) => new DOMParser().parseFromString(svg, 'image/svg+xml')
const texts = (doc: Document) => [...doc.querySelectorAll('text')].map((t) => t.textContent)

describe('prepareSvg (bereiteSvgAuf)', () => {
  it('puts the title above the diagram and enlarges the area', () => {
    const doc = parse(prepareSvg(RAW_SVG, { ...BASE, title: 'Verfahren der Vorhabenprüfung' }))
    expect(texts(doc)).toContain('Verfahren der Vorhabenprüfung')
    const [, minY, , height] = (doc.documentElement.getAttribute('viewBox') ?? '').split(' ').map(Number)
    expect(minY).toBeLessThan(50)
    expect(height).toBeGreaterThan(200)
  })

  it('lists only used colours in the legend', () => {
    const out = prepareSvg(RAW_SVG, {
      ...BASE,
      showLegend: true,
      colors: [{ fill: '#ffcdd2', stroke: '#b71c1c', label: 'Kritisch / neu', meaning: 'Feststellung', count: 2 }],
    })
    expect(out).toContain('Farblegende')
    expect(out).toContain('Kritisch / neu')
    expect(out).not.toContain('Validiert')
  })

  it('numbers legal bases and sets marks at the element', () => {
    const doc = parse(
      prepareSvg(RAW_SVG, {
        ...BASE,
        showLegalBases: true,
        legalBases: [{ elementId: 'Task_1', name: 'Vergabe prüfen', text: '§ 55 BHO', x: 120, y: 60, width: 100 }],
      }),
    )
    expect(texts(doc)).toContain('Rechtsgrundlagen')
    expect(texts(doc)).toContain('[1]')
    const circle = doc.querySelector('circle')
    expect(circle?.getAttribute('cx')).toBe('214')
    expect(circle?.getAttribute('cy')).toBe('66')
  })

  it('keeps <defs> on top level so arrow heads survive', () => {
    const doc = parse(prepareSvg(RAW_SVG, { ...BASE, title: 'X' }))
    expect(doc.documentElement.querySelector(':scope > defs')).not.toBeNull()
  })

  it('returns unusable input unchanged instead of guessing', () => {
    expect(prepareSvg('kein svg', BASE)).toBe('kein svg')
  })

  it('draws the coloured header with subtitle (new)', () => {
    const doc = parse(prepareSvg(RAW_SVG, { ...BASE, title: 'T', subtitle: 'U', headerColor: '#1976d2', headerTextColor: '#ffffff' }))
    expect(texts(doc)).toEqual(expect.arrayContaining(['T', 'U']))
    expect([...doc.querySelectorAll('rect')].some((rect) => rect.getAttribute('fill') === '#1976d2')).toBe(true)
  })
})

function element(fill?: string): ModelElement {
  return {
    id: 'x',
    type: 'bpmn:Task',
    name: '',
    documentation: '',
    extensions: emptyExtensions(),
    incoming: [],
    outgoing: [],
    eventDefinitions: [],
    attributes: {},
    ...(fill ? { color: { fill } } : {}),
  }
}

describe('collectColors (sammleFarben)', () => {
  it('counts palette colours and reports foreign ones', () => {
    const colors = collectColors([element('#ffcdd2'), element('#FFCDD2'), element('#123456'), element()])
    expect(colors).toHaveLength(2)
    expect(colors[0]).toMatchObject({ label: 'Kritisch / neu', count: 2 })
    expect(colors[1]!.label).toBe('Nicht zugeordnet')
  })

  it('recognises palette colours case-insensitively', () => {
    expect(collectColors([element('#C8E6C9')])[0]!.label).toBe('Validiert')
  })
})

describe('page grid (Seitenraster)', () => {
  it('converts DIN A4 landscape into diagram pixels', () => {
    const size = pageSize('a4', 'quer')
    expect(Math.round(size.widthPx)).toBe(1123)
    expect(Math.round(size.heightPx)).toBe(794)
  })

  it('anchors lines at the diagram origin, not the screen edge', () => {
    const grid = computePageGrid({ x: 0, y: 0, width: 1600, height: 1200, scale: 1 }, { widthPx: 800, heightPx: 600 }, 1600, 1200)
    expect(grid.vertical).toEqual([0, 800, 1600])
    expect(grid.horizontal).toEqual([0, 600, 1200])
    expect(grid.pages[0]!.label).toBe('Seite 1/1')
  })

  it('draws nothing at absurd zoom levels instead of thousands of lines', () => {
    const grid = computePageGrid({ x: 0, y: 0, width: 5_000_000, height: 10, scale: 0.0001 }, { widthPx: 800, heightPx: 600 }, 1000, 800)
    expect(grid.vertical).toHaveLength(0)
  })
})

describe('buildGroups (baueGruppen)', () => {
  const items: LegacyListItem[] = [
    { id: 1, name: 'VP-Ablauf', description: '', process_type: 'Vorhabenprüfung', process_owner: 'Referat 23', owner: 'a' },
    { id: 2, name: 'SP-Ablauf', description: '', process_type: 'Systemprüfung', process_owner: 'Referat 23', owner: 'a' },
    { id: 3, name: 'Sonstiges', description: '', process_type: '', process_owner: '', owner: 'b' },
  ]

  it('groups by process type and puts „Ohne Zuordnung“ last', () => {
    const groups = buildGroups(items, { search: '', filter: 'alle', grouping: 'prozesstyp', isOwn: () => true })
    expect(groups.map((g) => g.label)).toEqual(['Systemprüfung', 'Vorhabenprüfung', 'Ohne Zuordnung'])
  })

  it('searches name and description', () => {
    const groups = buildGroups(items, { search: 'vp-', filter: 'alle', grouping: 'keine', isOwn: () => true })
    expect(groups[0]!.entries).toHaveLength(1)
    expect(groups[0]!.entries[0]!.name).toBe('VP-Ablauf')
  })

  it('filters own diagrams', () => {
    const groups = buildGroups(items, { search: '', filter: 'eigene', grouping: 'keine', isOwn: (d) => d.id === 3 })
    expect(groups[0]!.entries.map((d) => d.id)).toEqual([3])
  })

  it('groups by responsibility with owner fallback', () => {
    const groups = buildGroups(items, { search: '', filter: 'alle', grouping: 'verantwortlich', isOwn: () => true })
    expect(groups.map((g) => g.label)).toEqual(['b', 'Referat 23'])
  })
})

describe('MyST export', () => {
  it('encodes umlauts without loss', () => {
    const encoded = base64Utf8('Prüfung gemäß § 44 LHO')
    expect(new TextDecoder().decode(Uint8Array.from(atob(encoded), (c) => c.charCodeAt(0)))).toBe('Prüfung gemäß § 44 LHO')
  })

  it('builds a book label without umlauts', () => {
    expect(diagramLabel('Prüfung Ablauf', 7)).toBe('pruefung-ablauf-7')
    expect(diagramLabel('', null)).toBe('diagramm')
  })

  it('creates a complete directive block', () => {
    const snippet = buildMystSnippet({ title: 'Ablauf der Prüfung', name: 'VP', id: 4, xml: '<x/>' })
    expect(snippet.startsWith('```{bpmn}')).toBe(true)
    expect(snippet).toContain('caption: Ablauf der Prüfung')
    expect(snippet).toContain('name: vp-4')
    expect(snippet.trimEnd().endsWith('```')).toBe(true)
  })
})

describe('legacy metadata (extensionElements)', () => {
  function build(values: Record<string, unknown>[] = [], withExtension = true): DiagramElement {
    const extension = { $type: 'bpmn:ExtensionElements', get: (name: string) => (name === 'values' ? values : undefined) }
    return {
      id: 'Task_1',
      type: 'bpmn:Task',
      businessObject: { $type: 'bpmn:Task', get: (name: string) => (name === 'extensionElements' && withExtension ? extension : undefined) } as unknown as ModdleElement,
    }
  }
  const bpmnFactory = {
    create: (type: string, attrs: Record<string, unknown> = {}) =>
      ({ $type: type, ...attrs, get: (name: string) => attrs[name], set: () => undefined }) as unknown as ModdleElement,
  }

  it('reads an existing entry', () => {
    expect(readMetadata(build([{ $type: 'flowaudit:Rechtsgrundlage', get: () => '§ 55 BHO' }]), 'flowaudit:Rechtsgrundlage')).toBe('§ 55 BHO')
  })

  it('returns empty text if nothing is maintained', () => {
    expect(readMetadata(build([], false), 'flowaudit:Rechtsgrundlage')).toBe('')
  })

  it('creates extensionElements and entry in one step', () => {
    const modeling = { updateModdleProperties: vi.fn() }
    writeMetadata(build([], false), 'flowaudit:Rechtsgrundlage', '§ 44 LHO', { modeling, bpmnFactory })
    expect(modeling.updateModdleProperties).toHaveBeenCalledTimes(1)
    expect(modeling.updateModdleProperties.mock.calls[0]![2]!.extensionElements.$type).toBe('bpmn:ExtensionElements')
  })

  it('removes the entry on empty text instead of leaving an empty element', () => {
    const entry = { $type: 'flowaudit:Rechtsgrundlage', get: () => 'alt' }
    const other = { $type: 'flowaudit:InterneNotiz', get: () => 'bleibt' }
    const modeling = { updateModdleProperties: vi.fn() }
    writeMetadata(build([entry, other]), 'flowaudit:Rechtsgrundlage', '   ', { modeling, bpmnFactory })
    expect(modeling.updateModdleProperties.mock.calls[0]![2]!.values).toEqual([other])
  })

  it('does nothing if an empty field stays empty', () => {
    const modeling = { updateModdleProperties: vi.fn() }
    writeMetadata(build([], false), 'flowaudit:Rechtsgrundlage', '', { modeling, bpmnFactory })
    expect(modeling.updateModdleProperties).not.toHaveBeenCalled()
  })
})

describe('translation and palette', () => {
  it('translates known strings and keeps unknown ones', () => {
    expect(germanTranslate('Job execution')).toBe('Job-Ausführung')
    expect(germanTranslate('Etwas ganz Neues')).toBe('Etwas ganz Neues')
  })

  it('fills placeholders', () => {
    expect(germanTranslate('Append {typ}', { typ: 'Aufgabe' })).toBe('Append Aufgabe')
  })

  it('recognises colours regardless of case and short form', () => {
    expect(normalizeColor('#FFF')).toBe('#ffffff')
    expect(findPaletteColor('#C8E6C9')?.label).toBe('Validiert')
    expect(findPaletteColor('#010203')).toBeNull()
  })
})

const LEGACY_XML = `<?xml version="1.0"?>
<model:definitions xmlns:model="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <model:process id="Process_1">
    <model:userTask id="Task_1" name="Prüfen" duration="15" cost="4.5"
      resource="Sachbearbeitung" frequencyPerYear="12" personnel_count="2" />
  </model:process>
</model:definitions>`

describe('FlowStat task fields (useBpmnEditor)', () => {
  it('reads legacy aliases for all workshop fields', () => {
    expect(readTasksFromXml(LEGACY_XML)).toEqual([
      { id: 'Task_1', name: 'Prüfen', duration_minutes: 15, cost: 4.5, resource: 'Sachbearbeitung', frequency: 12, personnel_count: 2 },
    ])
  })

  it('migrates to canonical attributes on write', () => {
    const xml = writeTaskToXml(LEGACY_XML, { id: 'Task_1', name: 'Freigeben', duration_minutes: 20, cost: 7, resource: 'Referatsleitung', frequency: 24, personnel_count: 3 })
    for (const part of ['durationEstimated="20"', 'durationUnit="Minuten"', 'costEstimate="7"', 'resourcesPersonnel="Referatsleitung"', 'frequency="24"', 'personnelCount="3"']) {
      expect(xml).toContain(part)
    }
    expect(xml).not.toContain('frequencyPerYear=')
    expect(xml).not.toContain('personnel_count=')
  })
})
