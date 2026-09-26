/**
 * Shared parity cases of the collection views (Vue `@auditcore/bpmn-vue`
 * and React `@auditcore/bpmn-react`): the same synthetic collection, the
 * same filter or folder choice, the same expectations. Fixtures are the
 * synthetic diagrams of this package (no user data).
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import type { CollectionFilter } from '../../src/ui'
import type { Expectation } from './expectation'

export type { Expectation } from './expectation'

const fixture = (name: string) => readFileSync(join(__dirname, '..', 'fixtures', name), 'utf-8')

/** The part of a collection store both versions offer. */
export interface FillableCollection {
  load(): Promise<void>
  createFolder(name: string, parentId?: string | null): Promise<{ id: string } | undefined>
  createDiagram(name: string, folderId?: string | null, xml?: string): Promise<string | undefined>
  createTag(name: string, color?: string): Promise<unknown>
  setTags(id: string, tags: string[]): Promise<unknown>
}

/** Folder „Antragsverfahren“ with „Bewilligung“, top-level „Anreicherung“, tag „Kern“. */
export async function fillCollection(store: FillableCollection): Promise<string> {
  await store.load()
  const folder = await store.createFolder('Antragsverfahren')
  await store.createDiagram('Bewilligung', folder?.id ?? null, fixture('schema-1.1.bpmn'))
  await store.createDiagram('Anreicherung', null, fixture('enrichment.bpmn'))
  await store.createTag('Kern', '#2451c4')
  await store.setTags('anreicherung', ['kern'])
  return folder?.id ?? ''
}

export interface TreeCase {
  name: string
  filter: Partial<CollectionFilter>
  /** Select the folder of `fillCollection` before comparing. */
  selectFolder?: boolean
  expect: Expectation
}

export const TREE_CASES: TreeCase[] = [
  {
    name: 'ungefiltert',
    filter: {},
    expect: { texts: ['Antragsverfahren', 'Bewilligung', 'Anreicherung', 'Oberste Ebene'], roles: [['tree', 'Diagrammsammlung'], ['button', 'Neuer Ordner']], counts: { '[role="treeitem"]': 4, '.fa-tree__row--selected': 2 } },
  },
  { name: 'Suche', filter: { search: 'anreich' }, expect: { texts: ['Anreicherung'], counts: { '.fa-tree__name': 1 } } },
  { name: 'Status', filter: { status: 'freigegeben' }, expect: { texts: ['Bewilligung'], counts: { '.fa-tree__name': 1 } } },
  { name: 'Tag', filter: { tag: 'kern' }, expect: { texts: ['Anreicherung'], counts: { '.fa-tree__name': 1 } } },
  { name: 'Ordner gewählt', filter: {}, selectFolder: true, expect: { counts: { '.fa-tree__row--folder.fa-tree__row--selected': 1 } } },
]

export const OVERVIEW_EXPECT: Expectation = { texts: ['Diagramme', 'KA 1'], counts: { '.fa-overview__ka-cell': 18, '[role="meter"]': 1 } }
export const INFO_EXPECT: Expectation = { texts: ['Bewilligung', 'Öffnen'], roles: [['button', 'Öffnen'], ['combobox', 'Verschieben nach …']] }
