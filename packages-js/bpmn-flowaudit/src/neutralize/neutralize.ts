/**
 * Neutralising: export without references to bodies, persons and findings.
 *
 * Same behaviour as `auditcore_bpmn` neutralisation, on the XML DOM:
 * - display names of pools and lanes → role label (actor or profile
 *   alias; otherwise „Stelle n“); the same names are replaced in task
 *   prefixes, labels and documentation;
 * - replacements named by the application (e.g. names of authorities);
 * - e-mail addresses, IBAN, amounts, company names, salutations with names
 *   and identifiers (SAP, MaStR, file numbers, funding codes);
 * - internal notes, audit steps, findings, finding references, finding
 *   markers and finding colours, internal sources and everything marked
 *   `vertraulich="true"`;
 * - person fields (`autor`, `freigegebenDurch`, `pruefer`).
 *
 * Automatic recognition does not replace a review: the report lists every
 * change so a person can check the result.
 */

import { FLOWAUDIT_NAMESPACE } from '../schema/descriptor'
import { attributeName, elementsByNs, parseXml, serializeXml } from '../model/xmlDom'
import { roleFromText, roleOf, type ProfileData } from '../profile/profile'
import { label } from '../schema/vocabulary'
import {
  CODE_ATTRIBUTES,
  FINDING_COLORS,
  FINDING_MARKERS,
  INTERNAL_SOURCES,
  PERSON_ATTRIBUTES,
  REMOVED_ELEMENTS,
  TEXT_PATTERNS,
  type ReplacementKind,
} from './patterns'

const BPMN = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
const BPMNDI = 'http://www.omg.org/spec/BPMN/20100524/DI'
const COLOR_ATTRIBUTES = [
  ['http://bpmn.io/schema/bpmn/biocolor/1.0', 'fill'],
  ['http://bpmn.io/schema/bpmn/biocolor/1.0', 'stroke'],
  ['http://www.omg.org/spec/BPMN/non-normative/color/1.0', 'background-color'],
  ['http://www.omg.org/spec/BPMN/non-normative/color/1.0', 'border-color'],
] as const

export interface Replacement {
  elementId: string | null
  location: string
  kind: ReplacementKind
  replacement: string
  original?: string
}

export interface NeutralizationResult {
  xml: string
  replacements: Replacement[]
  /** Count per kind. */
  summary: Record<string, number>
}

export interface NeutralizeOptions {
  profile?: ProfileData | null
  /** Names known to the application → replacement. */
  replacements?: Record<string, string>
  /** Include the original texts in the report (internal review only). */
  withOriginals?: boolean
}

function isConfidential(element: Element): boolean {
  return (element.getAttribute('vertraulich') ?? '').toLowerCase() === 'true'
}

function shouldRemove(element: Element): boolean {
  const name = element.localName
  const type = element.getAttribute('typ') ?? ''
  const kind = element.getAttribute('art') ?? ''
  return (
    REMOVED_ELEMENTS.has(name) ||
    isConfidential(element) ||
    (name === 'kennzeichen' && FINDING_MARKERS.has(type)) ||
    (name === 'quelle' && INTERNAL_SOURCES.has(kind)) ||
    (name === 'verweis' && kind === 'feststellung_ref')
  )
}

function ownerId(node: Element): string | null {
  let current: Element | null = node
  while (current && !current.getAttribute('id')) current = current.parentElement
  return current?.getAttribute('id') ?? null
}

class Neutralizer {
  readonly report: Replacement[] = []
  private readonly names = new Map<string, string>()
  private counter = 0

  constructor(
    private readonly document: XMLDocument,
    private readonly options: NeutralizeOptions,
  ) {
    for (const [old, replacement] of Object.entries(options.replacements ?? {})) if (old.trim()) this.names.set(old.trim(), replacement)
  }

  log(elementId: string | null, location: string, kind: ReplacementKind, replacement: string, original?: string): void {
    this.report.push({ elementId, location, kind, replacement, ...(this.options.withOriginals && original ? { original } : {}) })
  }

  private actorOf(element: Element): Element | undefined {
    const container = Array.from(element.children).find((child) => child.namespaceURI === BPMN && child.localName === 'extensionElements')
    return Array.from(container?.children ?? []).find((child) => child.namespaceURI === FLOWAUDIT_NAMESPACE && child.localName === 'akteur')
  }

  roles(): void {
    const containers = [...elementsByNs(this.document, BPMN, 'participant'), ...elementsByNs(this.document, BPMN, 'lane')]
    for (const element of containers) {
      const old = (element.getAttribute('name') ?? '').trim()
      const actor = this.actorOf(element)
      const code = actor?.getAttribute('rolle') || roleFromText(this.options.profile, old)
      const role = roleOf(this.options.profile, code)
      const replacement = role ? label(role.label) : `Stelle ${(this.counter += 1)}`
      const displayName = actor?.getAttribute('anzeigename')
      if (displayName && !this.names.has(displayName)) this.names.set(displayName, replacement)
      if (old && old !== replacement) {
        if (!this.names.has(old)) this.names.set(old, replacement)
        element.setAttribute('name', replacement)
        this.log(element.getAttribute('id'), 'name', 'anzeigename', replacement, old)
      }
    }
  }

  clean(value: string, elementId: string | null, location: string): string {
    let result = value
    for (const old of [...this.names.keys()].sort((a, b) => b.length - a.length)) {
      if (old && result.includes(old)) {
        result = result.split(old).join(this.names.get(old) as string)
        this.log(elementId, location, 'anzeigename', this.names.get(old) as string, old)
      }
    }
    for (const { kind, pattern, replacement } of TEXT_PATTERNS) {
      result = result.replace(pattern, (match) => {
        this.log(elementId, location, kind, replacement, match)
        return replacement
      })
    }
    return result === value ? result : result.replace(/[ \t]{2,}/g, ' ').replace(/ ,/g, ',').replace(/ \./g, '.')
  }

  flowaudit(): void {
    for (const container of elementsByNs(this.document, BPMN, 'extensionElements')) {
      const elementId = ownerId(container)
      for (const child of Array.from(container.children)) {
        if (child.namespaceURI !== FLOWAUDIT_NAMESPACE) continue
        this.flowauditChild(container, child, elementId)
      }
      if (container.children.length === 0) container.parentNode?.removeChild(container)
    }
  }

  private flowauditChild(container: Element, child: Element, elementId: string | null): void {
    const name = child.localName
    if (shouldRemove(child)) {
      container.removeChild(child)
      this.log(elementId, `flowaudit:${name}`, 'entfernt', '')
      return
    }
    if (name === 'akteur' && child.getAttribute('anzeigename')) {
      child.removeAttribute('anzeigename')
      this.log(elementId, 'flowaudit:akteur/@anzeigename', 'anzeigename', '')
    }
    if (name === 'diagrammInfo') this.diagramInfo(child, elementId)
  }

  private diagramInfo(info: Element, elementId: string | null): void {
    for (const attribute of PERSON_ATTRIBUTES) {
      if (info.hasAttribute(attribute)) {
        info.removeAttribute(attribute)
        this.log(elementId, `diagrammInfo/@${attribute}`, 'person', '')
      }
    }
    for (const child of Array.from(info.children)) {
      if (child.localName === 'feststellung' || shouldRemove(child)) {
        info.removeChild(child)
        this.log(elementId, `diagrammInfo/flowaudit:${child.localName}`, 'entfernt', '')
      }
    }
  }

  private cleanNode(node: Element): void {
    const id = ownerId(node)
    const inFlowaudit = node.namespaceURI === FLOWAUDIT_NAMESPACE
    for (const attribute of Array.from(node.attributes)) {
      if (attribute.namespaceURI || attribute.name.includes(':')) continue
      const relevant = attribute.name === 'name' || (inFlowaudit && !CODE_ATTRIBUTES.has(attribute.name))
      if (!relevant) continue
      if (inFlowaudit && attribute.name === 'pruefer') continue
      const cleaned = this.clean(attribute.value, id, `@${attribute.name}`)
      if (cleaned !== attribute.value) node.setAttribute(attribute.name, cleaned)
    }
    const text = node.textContent ?? ''
    if (node.children.length === 0 && text.trim()) {
      const cleaned = this.clean(text, id, node.localName)
      if (cleaned !== text) node.textContent = cleaned
    }
  }

  private colors(shape: Element): void {
    for (const attribute of Array.from(shape.attributes)) {
      const { namespace: ns, local } = attributeName(attribute, shape)
      const isColor = COLOR_ATTRIBUTES.some(([namespace, name]) => ns === namespace && local === name)
      if (isColor && FINDING_COLORS.has(attribute.value.toLowerCase())) {
        shape.removeAttributeNode(attribute)
        this.log(shape.getAttribute('bpmnElement'), 'DI-Farbe', 'befundfarbe', '')
      }
    }
  }

  texts(): void {
    for (const node of Array.from(this.document.getElementsByTagName('*'))) {
      if (node.namespaceURI === BPMN || node.namespaceURI === FLOWAUDIT_NAMESPACE) this.cleanNode(node)
      if (node.namespaceURI === BPMNDI && node.localName === 'BPMNShape') this.colors(node)
    }
  }
}

/** Neutralises a diagram; `replacements` adds names known to the application. */
export function neutralize(xml: string, options: NeutralizeOptions = {}): NeutralizationResult {
  const document = parseXml(xml)
  if (!document) throw new Error('Das BPMN-XML ist nicht wohlgeformt.')
  const worker = new Neutralizer(document, options)
  worker.roles()
  worker.flowaudit()
  worker.texts()
  const summary: Record<string, number> = {}
  for (const item of worker.report) summary[item.kind] = (summary[item.kind] ?? 0) + 1
  return { xml: serializeXml(document), replacements: worker.report, summary }
}
