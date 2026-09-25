/**
 * Small, namespace-aware DOM helpers. `getElementsByTagNameNS` is not
 * reliable in every DOM implementation (happy-dom returns nothing for a
 * concrete local name), so elements are filtered explicitly.
 */

export function elementsByNs(root: Document | Element, namespace: string, localName = '*'): Element[] {
  return Array.from(root.getElementsByTagName('*')).filter(
    (element) => element.namespaceURI === namespace && (localName === '*' || element.localName === localName),
  )
}

export function childrenByNs(parent: Element, namespace: string, localName = '*'): Element[] {
  return Array.from(parent.children).filter((element) => element.namespaceURI === namespace && (localName === '*' || element.localName === localName))
}

/** Namespace declared for `prefix` on the element or its ancestors. */
export function resolvePrefix(element: Element, prefix: string): string | null {
  for (let current: Element | null = element; current; current = current.parentElement) {
    const declared = current.getAttribute(`xmlns:${prefix}`)
    if (declared) return declared
  }
  return null
}

/**
 * Namespace and local name of an attribute. Some DOM implementations keep
 * prefixed attributes unqualified (`bioc:fill` without namespace); the
 * prefix is then resolved from the declarations.
 */
export function attributeName(attribute: Attr, owner: Element): { namespace: string | null; local: string } {
  if (attribute.namespaceURI) return { namespace: attribute.namespaceURI, local: attribute.localName }
  const [prefix, local] = attribute.name.includes(':') ? attribute.name.split(':', 2) : [null, attribute.name]
  return { namespace: prefix && prefix !== 'xmlns' ? resolvePrefix(owner, prefix) : null, local }
}

export const XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>'

/**
 * Parses XML; the XML declaration and a BOM are removed first because not
 * every DOM parser accepts single-quoted declarations.
 */
export function parseXml(xml: string): XMLDocument | null {
  const body = xml.replace(/^\uFEFF?\s*<\?xml[^?]*\?>\s*/, '')
  const document = new DOMParser().parseFromString(body, 'application/xml')
  return document.getElementsByTagName('parsererror').length ? null : document
}

/** Serialises a document with a standard XML declaration. */
export function serializeXml(document: Document): string {
  return `${XML_DECLARATION}\n${new XMLSerializer().serializeToString(document).replace(/^<\?xml[^?]*\?>\s*/, '')}`
}
