/**
 * Synthetic demo data: the process templates of `auditcore_bpmn` (built
 * from the text of Regulation (EU) 2021/1060, no user diagrams) and the
 * synthetic test fixtures. Everything stays in memory.
 */

import { DiagramCollection, InMemoryStorage, loadDefinitions, modelFromDefinitions } from '@flowaudit/bpmn-flowaudit'
import legacy from '../../bpmn-flowaudit/test/fixtures/legacy-1.0.bpmn?raw'
import schema11 from '../../bpmn-flowaudit/test/fixtures/schema-1.1.bpmn?raw'
import enrichment from '../../bpmn-flowaudit/test/fixtures/enrichment.bpmn?raw'

const templates = import.meta.glob('../../../packages/auditcore_bpmn/src/auditcore_bpmn/templates/*.bpmn', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>

interface DemoDiagram {
  id: string
  name: string
  folderId: string
  xml: string
  tags?: string[]
}

const EXAMPLES: DemoDiagram[] = [
  { id: 'bewilligung-muster', name: 'Bewilligung und Auszahlung (Muster, Schema 1.1)', folderId: 'beispiele', xml: schema11, tags: ['muster'] },
  { id: 'altbestand', name: 'Altbestand (Schema 1.0)', folderId: 'beispiele', xml: legacy },
  { id: 'anreicherung', name: 'Anreicherung aus Dokumentation', folderId: 'beispiele', xml: enrichment },
]

function templateDiagrams(): DemoDiagram[] {
  return Object.entries(templates).map(([path, xml]) => {
    const id = path.split('/').pop()!.replace(/\.bpmn$/, '')
    const title = /titel="([^"]+)"/.exec(xml)?.[1] ?? id
    return { id, name: title, folderId: 'vks', xml, tags: ['vorlage'] }
  })
}

export async function demoStorage(): Promise<InMemoryStorage> {
  const collection = new DiagramCollection('demo', 'Demo-Sammlung')
  collection.createFolder('vks', 'Verwaltungs- und Kontrollsystem', null, 'Vorlagen aus der Dachverordnung')
  collection.createFolder('beispiele', 'Beispiele')
  collection.createTag('vorlage', 'Vorlage', '#1976d2')
  collection.createTag('muster', 'Muster', '#2e7d32')
  const diagrams = [...templateDiagrams(), ...EXAMPLES]
  for (const diagram of diagrams) {
    const model = modelFromDefinitions((await loadDefinitions(diagram.xml)).definitions)
    collection.addDiagram(diagram.id, { name: diagram.name, folderId: diagram.folderId, tags: diagram.tags, model })
  }
  return new InMemoryStorage({ collection: collection.toData(), diagrams: Object.fromEntries(diagrams.map((d) => [d.id, d.xml])) })
}
