/**
 * Keeping unknown elements of the flowaudit namespace across a round trip.
 *
 * Schema 1.1 requires readers to preserve unknown elements of the
 * namespace. moddle drops them as “unknown type”. Before import they are
 * therefore moved into a protection namespace (which moddle keeps as
 * generic elements, including attributes and children) and moved back
 * after export. Without unknown elements the text stays untouched.
 */

import { FLOWAUDIT_NAMESPACE } from '../schema/descriptor'
import { TEXT_TYPES, TYPES } from '../schema/spec'
import { elementsByNs, parseXml, serializeXml } from './xmlDom'

export const PROTECTION_NAMESPACE = `${FLOWAUDIT_NAMESPACE}#unbekannt`
const PROTECTION_PREFIX = 'flowauditUnbekannt'
const KNOWN = new Set<string>([...Object.keys(TYPES), ...Object.keys(TEXT_TYPES)])
const XMLNS = 'http://www.w3.org/2000/xmlns/'

function copyAttributes(from: Element, to: Element): void {
  for (const attribute of Array.from(from.attributes)) {
    if (attribute.namespaceURI) to.setAttributeNS(attribute.namespaceURI, attribute.name, attribute.value)
    else to.setAttribute(attribute.name, attribute.value)
  }
}

export function protectUnknownElements(xml: string): string {
  if (!xml.includes(FLOWAUDIT_NAMESPACE) || typeof DOMParser === 'undefined') return xml
  const document = parseXml(xml)
  if (!document) return xml
  const unknown = elementsByNs(document, FLOWAUDIT_NAMESPACE).filter((el) => !KNOWN.has(el.localName))
  if (!unknown.length) return xml
  for (const original of unknown) {
    const replacement = document.createElementNS(PROTECTION_NAMESPACE, `${PROTECTION_PREFIX}:${original.localName}`)
    copyAttributes(original, replacement)
    while (original.firstChild) replacement.appendChild(original.firstChild)
    original.parentNode?.replaceChild(replacement, original)
  }
  document.documentElement.setAttributeNS(XMLNS, `xmlns:${PROTECTION_PREFIX}`, PROTECTION_NAMESPACE)
  return serializeXml(document)
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\/#]/g, '\\$&')
}

export function restoreUnknownElements(xml: string): string {
  if (!xml.includes(PROTECTION_NAMESPACE)) return xml
  const declared = new RegExp(`xmlns:([\\w.-]+)="${escapeRegExp(PROTECTION_NAMESPACE)}"`).exec(xml)
  if (!declared) return xml
  const prefix = declared[1]
  const flowauditDeclaration = new RegExp(`xmlns:([\\w.-]+)="${escapeRegExp(FLOWAUDIT_NAMESPACE)}"`)
  const flowauditPrefix = flowauditDeclaration.exec(xml)?.[1] ?? 'flowaudit'
  let result = xml.replace(new RegExp(`\\s+xmlns:${prefix}="[^"]*"`), '')
  result = result.replace(new RegExp(`<(/?)${prefix}:`, 'g'), `<$1${flowauditPrefix}:`)
  if (!flowauditDeclaration.test(result)) {
    result = result.replace(/<([\w.-]+:)?definitions\b/, (start) => `${start} xmlns:${flowauditPrefix}="${FLOWAUDIT_NAMESPACE}"`)
  }
  return result
}
