/**
 * Suche nach Elementen (Name, Kennung, Typ) für das Suchfeld (Strg+F).
 */

import type SearchPad from 'diagram-js/lib/features/search-pad/SearchPad'
import type { SearchResult as PadResult } from 'diagram-js/lib/features/search-pad/SearchPadProvider'
import type { Element } from 'diagram-js/lib/model/Types'

import { getLabel } from '../util/LabelUtil'
import { getBusinessObject } from '../util/ModelUtil'
import type { Canvas, ElementRegistry, Translate } from '../types'

interface Token {
  match: boolean
  value: string
}

/** Zerlegt einen Text in Treffer-/Nicht-Treffer-Abschnitte (Groß-/Kleinschreibung egal). */
export function tokenize(text: string, pattern: string): Token[] {
  if (!pattern) return [{ match: false, value: text }]
  const tokens: Token[] = []
  const lower = text.toLocaleLowerCase('de')
  const needle = pattern.toLocaleLowerCase('de')
  let index = 0
  while (index < text.length) {
    const found = lower.indexOf(needle, index)
    if (found === -1) {
      tokens.push({ match: false, value: text.slice(index) })
      break
    }
    if (found > index) tokens.push({ match: false, value: text.slice(index, found) })
    tokens.push({ match: true, value: text.slice(found, found + needle.length) })
    index = found + needle.length
  }
  return tokens
}

function hasMatch(tokens: Token[]): boolean {
  return tokens.some((token) => token.match)
}

export default class BpmnSearchProvider {
  static $inject = ['elementRegistry', 'searchPad', 'canvas', 'translate']

  constructor(
    private readonly elementRegistry: ElementRegistry,
    searchPad: SearchPad,
    private readonly canvas: Canvas,
    private readonly translate: Translate,
  ) {
    searchPad.registerProvider(this)
  }

  find(pattern: string): PadResult[] {
    const root = this.canvas.getRootElement()
    const trimmed = pattern.trim()
    if (!trimmed) return []
    const elements = this.elementRegistry.filter(
      (element: Element) => !element.labelTarget && element !== root && !!element.businessObject,
    )
    const results: PadResult[] = []
    for (const element of elements) {
      const label = getLabel(element) || ''
      const id = String(getBusinessObject(element).id || element.id)
      const labelTokens = tokenize(label, trimmed)
      const idTokens = tokenize(id, trimmed)
      if (!hasMatch(labelTokens) && !hasMatch(idTokens)) continue
      const typeName = this.translate(String(getBusinessObject(element).$type).replace('bpmn:', ''))
      results.push({
        primaryTokens: label ? labelTokens : idTokens,
        secondaryTokens: [...(label ? idTokens : []), { match: false, value: label ? ` · ${typeName}` : typeName }],
        element,
      })
    }
    return results.sort((a, b) => rank(b, trimmed) - rank(a, trimmed))
  }
}

function rank(result: PadResult, pattern: string): number {
  const text = result.primaryTokens.map((token) => ('value' in token ? token.value : '')).join('')
  const lower = text.toLocaleLowerCase('de')
  const needle = pattern.toLocaleLowerCase('de')
  if (lower === needle) return 3
  if (lower.startsWith(needle)) return 2
  return 1
}
