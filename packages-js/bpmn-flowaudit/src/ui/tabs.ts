/**
 * Tabs of the properties panel (declarative): which tab is offered for
 * which element type and which lists it edits.
 */

import { isActivity, isEvent, isFlowNode, isGateway, type ListExtensionKey } from '../index'

export type TabId = 'general' | 'role' | 'legal' | 'references' | 'control' | 'evidence' | 'findings' | 'source' | 'notes' | 'color'

export interface TabDefinition {
  id: TabId
  label: string
  icon: string
  visible: (type: string) => boolean
  /** Lists edited by the generic list tab. */
  lists?: ListExtensionKey[]
}

const CONTAINERS = ['bpmn:Participant', 'bpmn:Lane']
const DATA = ['bpmn:DataObjectReference', 'bpmn:DataStoreReference', 'bpmn:DataObject', 'bpmn:DataStore']
const CONNECTIONS = ['bpmn:SequenceFlow', 'bpmn:MessageFlow', 'bpmn:Association']
const ROOTS = ['bpmn:Process', 'bpmn:Collaboration']

const isContainer = (type: string) => CONTAINERS.includes(type)
const isData = (type: string) => DATA.includes(type)
const isElement = (type: string) => !CONNECTIONS.includes(type) && !ROOTS.includes(type)

export const TABS: TabDefinition[] = [
  { id: 'general', label: 'props.tab.general', icon: 'info', visible: () => true },
  { id: 'role', label: 'props.tab.role', icon: 'role-sonstige', visible: (type) => isContainer(type) || isFlowNode(type) },
  { id: 'legal', label: 'props.tab.legal', icon: 'marker-rechtsgrundlage', visible: (type) => isFlowNode(type) || isContainer(type) || isData(type) },
  { id: 'references', label: 'props.tab.references', icon: 'marker-pruefpunkt', visible: isElement, lists: ['auditReferences', 'crossReferences'] },
  { id: 'control', label: 'props.tab.control', icon: 'marker-schluesselkontrolle', visible: (type) => isActivity(type) || isGateway(type), lists: ['controls', 'risks'] },
  { id: 'evidence', label: 'props.tab.evidence', icon: 'marker-dokument', visible: (type) => isData(type) || isActivity(type) || isEvent(type), lists: ['evidence', 'deadlines'] },
  { id: 'findings', label: 'props.tab.findings', icon: 'marker-feststellung', visible: isElement, lists: ['findings', 'auditSteps'] },
  { id: 'source', label: 'props.tab.source', icon: 'bpmn-annotation', visible: isElement, lists: ['sources'] },
  { id: 'notes', label: 'props.tab.notes', icon: 'comment', visible: (type) => isElement(type) || CONNECTIONS.includes(type) },
  { id: 'color', label: 'props.tab.color', icon: 'color', visible: (type) => !ROOTS.includes(type) },
]

/** Which lists make sense for a type (e.g. evidence only at data objects). */
export function listsFor(tab: TabDefinition, type: string): ListExtensionKey[] {
  const lists = tab.lists ?? []
  if (tab.id === 'evidence') return lists.filter((key) => (key === 'evidence' ? isData(type) : !isData(type)))
  return lists
}

export function tabsFor(type: string | null): TabDefinition[] {
  return type ? TABS.filter((tab) => tab.visible(type)) : []
}
