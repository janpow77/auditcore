/** Kleinste XML-Helfer für die Arbeitsmappe: Maskieren, Entmaskieren, Attribute, Spaltenbuchstaben. */

/** Zeichen, die in XML 1.0 nicht vorkommen dürfen (Steuerzeichen außer Tab, Zeilenvorschub, Wagenrücklauf). */
function allowed(code: number): boolean {
  return code === 0x9 || code === 0xa || code === 0xd || (code >= 0x20 && code !== 0xfffe && code !== 0xffff)
}

function withoutControls(text: string): string {
  let clean = ''
  for (const character of text) {
    if (allowed(character.codePointAt(0) ?? 0)) clean += character
  }
  return clean
}

/**
 * Text für XML maskieren. Zeichenfolgen der Form `_x0041_` liest Excel als
 * maskiertes Zeichen; ihr Unterstrich wird deshalb selbst maskiert (`_x005F_`).
 */
export function escapeXml(text: string): string {
  return withoutControls(text)
    .replace(/_x(?=[0-9A-Fa-f]{4}_)/g, '_x005F_x')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const ENTITIES: ReadonlyMap<string, string> = new Map([
  ['lt', '<'],
  ['gt', '>'],
  ['amp', '&'],
  ['quot', '"'],
  ['apos', "'"],
])
const REPLACEMENT = '\uFFFD'

/** Zeichen zu einer Zeichenreferenz; ungültige Werte (über U+10FFFF, Ersatzzeichenhälften) ergeben U+FFFD. */
function character(code: number): string {
  const valid = Number.isInteger(code) && code > 0 && code <= 0x10ffff && !(code >= 0xd800 && code <= 0xdfff)
  return valid ? String.fromCodePoint(code) : REPLACEMENT
}

export function unescapeXml(text: string): string {
  return text.replace(/&(#x[0-9a-fA-F]+|#[0-9]+|[A-Za-z]+);/g, (match, name: string) => {
    if (name.startsWith('#x')) return character(Number.parseInt(name.slice(2), 16))
    if (name.startsWith('#')) return character(Number.parseInt(name.slice(1), 10))
    return ENTITIES.get(name) ?? match
  })
}

/** Zellen- und Zeichenkettentext: XML entmaskieren, danach die Excel-Maskierung `_xHHHH_`. */
export function decodeText(text: string): string {
  return unescapeXml(text).replace(/_x([0-9A-Fa-f]{4})_/g, (_, hex: string) => character(Number.parseInt(hex, 16)))
}

/** Attribute eines Start-Tags (`name="wert"` oder `name='wert'`), ohne Namensraumpräfix. */
export function attributesOf(tag: string): Record<string, string> {
  const attributes: Record<string, string> = Object.create(null) as Record<string, string>
  for (const match of tag.matchAll(/([\w:.-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g)) {
    const name = match[1]!.replace(/^\w+:/, '')
    attributes[name] = unescapeXml(match[2] ?? match[3] ?? '')
  }
  return attributes
}

/** Ein Stück XML: Start-, End- oder leeres Element oder Text dazwischen. */
export interface XmlToken {
  kind: 'open' | 'close' | 'empty' | 'text'
  /** Elementname ohne Namensraumpräfix; bei Text leer. */
  name: string
  /** Rohtext der Attribute bzw. der Text zwischen den Elementen. */
  text: string
}

/**
 * Zerlegt XML in einem Durchlauf in Elemente und Text (linear in der Länge,
 * auch bei nicht geschlossenen Elementen). Kommentare, Verarbeitungsanweisungen
 * und DOCTYPE werden übergangen; es wird nichts aufgelöst oder nachgeladen.
 */
export function* tokenize(xml: string): Generator<XmlToken> {
  let position = 0
  while (position < xml.length) {
    const start = xml.indexOf('<', position)
    const end = start < 0 ? -1 : xml.indexOf('>', start)
    if (end < 0) break
    if (start > position) yield { kind: 'text', name: '', text: xml.slice(position, start) }
    position = end + 1
    const tag = parseTag(xml.slice(start + 1, end))
    if (tag) yield tag
  }
}

/** Inhalt zwischen `<` und `>` als Element; Kommentare, Anweisungen und DOCTYPE ergeben `null`. */
function parseTag(body: string): XmlToken | null {
  if (body.startsWith('?') || body.startsWith('!')) return null
  const closing = body.startsWith('/')
  const empty = body.endsWith('/')
  const inner = body.slice(closing ? 1 : 0, empty ? -1 : undefined)
  const space = inner.search(/\s/)
  const name = (space < 0 ? inner : inner.slice(0, space)).replace(/^[\w.-]+:/, '')
  return { kind: closing ? 'close' : empty ? 'empty' : 'open', name, text: space < 0 ? '' : inner.slice(space) }
}

/** Spaltenbuchstabe zur Spaltennummer ab 1 (`1` → `A`, `27` → `AA`). */
export function columnName(index: number): string {
  let name = ''
  for (let rest = index; rest > 0; rest = Math.floor((rest - 1) / 26)) name = String.fromCharCode(65 + ((rest - 1) % 26)) + name
  return name
}
