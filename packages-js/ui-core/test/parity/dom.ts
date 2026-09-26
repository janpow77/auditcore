/**
 * Kanonische Form eines gerenderten DOM-Teilbaums für den Paritätsvergleich
 * Vue ↔ React: Attribute sortiert, Klassen sortiert, Kennungen (id und alle
 * Verweise darauf) in Reihenfolge ihres Auftretens durchnummeriert, Kommentare
 * und reine Leerraum-Textknoten entfernt, Leerraum in Texten zusammengefasst.
 * Formularzustand (value/checked) steht in DOM-Eigenschaften, nicht im Markup;
 * er wird getrennt über `formState` verglichen.
 */
const ID_REFERENCES = ['for', 'aria-labelledby', 'aria-describedby', 'aria-controls', 'list']
/** Textinhalt eines <textarea> setzt React als Kind, Vue nur als Eigenschaft; verglichen wird `value`. */
const SKIP_CHILDREN = new Set(['TEXTAREA'])
/** Wert und Häkchen an Formularfeldern: je nach Framework Attribut oder nur Eigenschaft; leeres `class` wie fehlendes. */
const FORM_ATTRIBUTES = new Set(['value', 'checked'])
const FORM_ELEMENTS = new Set(['INPUT', 'TEXTAREA', 'SELECT', 'OPTION'])

function collectIds(root: Element): Map<string, string> {
  const ids = new Map<string, string>()
  for (const element of [root, ...Array.from(root.querySelectorAll('[id]'))]) {
    const id = element.getAttribute('id')
    if (id && !ids.has(id)) ids.set(id, `id${ids.size + 1}`)
  }
  // Gruppennamen von Optionsfeldern entstehen wie Kennungen je Instanz.
  for (const element of Array.from(root.querySelectorAll('input[name]'))) {
    const name = `name:${element.getAttribute('name')}`
    if (!ids.has(name)) ids.set(name, `name${ids.size + 1}`)
  }
  return ids
}

function attributeValue(name: string, value: string, ids: Map<string, string>): string {
  if (name === 'class') return value.split(/\s+/).filter(Boolean).sort().join(' ')
  if (name === 'id') return ids.get(value) ?? value
  if (name === 'name') return ids.get(`name:${value}`) ?? value
  if (ID_REFERENCES.includes(name)) return value.split(/\s+/).filter(Boolean).map((part) => ids.get(part) ?? part).join(' ')
  return value
}

function attributes(element: Element, ids: Map<string, string>): string {
  return Array.from(element.attributes)
    .filter((attribute) => !attribute.name.startsWith('data-v-') && !(FORM_ATTRIBUTES.has(attribute.name) && FORM_ELEMENTS.has(element.tagName)) && !(attribute.name === 'class' && !attribute.value.trim()))
    .map((attribute) => `${attribute.name}="${attributeValue(attribute.name, attribute.value, ids)}"`)
    .sort()
    .join(' ')
}

function serialize(node: Node, ids: Map<string, string>, depth: number, out: string[]): void {
  const pad = '  '.repeat(depth)
  if (node.nodeType === 3) {
    // Leerraum am Rand eines Textknotens stammt aus der Vorlagenformatierung (Vue) bzw. JSX.
    const text = (node.textContent ?? '').replace(/\s+/g, ' ').trim()
    if (text) out.push(`${pad}${JSON.stringify(text)}`)
    return
  }
  if (node.nodeType !== 1) return
  const element = node as Element
  const attrs = attributes(element, ids)
  out.push(`${pad}<${element.tagName.toLowerCase()}${attrs ? ` ${attrs}` : ''}>`)
  if (SKIP_CHILDREN.has(element.tagName)) return
  // Benachbarte Textknoten (React erzeugt je Ausdruck einen) zusammenführen.
  for (const child of Array.from(element.childNodes).reduce<Node[]>(merge, [])) serialize(child, ids, depth + 1, out)
}

function merge(nodes: Node[], child: Node): Node[] {
  const last = nodes[nodes.length - 1]
  if (child.nodeType === 8) return nodes
  if (last && last.nodeType === 3 && child.nodeType === 3) {
    nodes[nodes.length - 1] = document.createTextNode((last.textContent ?? '') + (child.textContent ?? ''))
    return nodes
  }
  nodes.push(child)
  return nodes
}

export function normalizeDom(root: Element): string {
  const out: string[] = []
  serialize(root, collectIds(root), 0, out)
  return out.join('\n')
}

/** Formularzustand in Dokumentreihenfolge: Werte, Häkchen, Auswahl. */
export function formState(root: Element): string[] {
  return Array.from(root.querySelectorAll('input, textarea, select')).map((element) => {
    const field = element as HTMLInputElement
    if (field.type === 'checkbox' || field.type === 'radio') return `${field.tagName.toLowerCase()}[${field.type}]:${field.checked}`
    return `${field.tagName.toLowerCase()}:${field.value}`
  })
}
