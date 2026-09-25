import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import { createModdle, createTranslate, translations } from '../src'
import { layoutText, wrapText, approximateMeasure, DEFAULT_TEXT_STYLE } from '../src/draw/TextLayout'
import Ids from '../src/util/Ids'
import { cloneModdleElement } from '../src/util/ModdleCopy'
import { getPathMid } from '../src/util/LabelUtil'
import * as Icons from '../src/icons/Icons'
import { boundaryEventOptions, endEventOptions, intermediateEventOptions, startEventOptions } from '../src/replace/options/eventOptions'
import { DATA_OPTIONS, EXPANDED_SUBPROCESS_OPTIONS, GATEWAY_OPTIONS, PARTICIPANT_OPTIONS, TASK_OPTIONS } from '../src/replace/options/elementOptions'
import { TYPE_LABELS } from '../src/i18n/typeLabels'
import { importXml } from './helpers/editor'
import { readFixture } from './helpers/fixtures'

function sourceFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory() ? sourceFiles(join(dir, entry.name)) : entry.name.endsWith('.ts') ? [join(dir, entry.name)] : [],
  )
}

describe('Übersetzung', () => {
  it('übersetzt jeden im Code verwendeten Text ins Deutsche', () => {
    const keys = new Set<string>()
    for (const file of sourceFiles(join(__dirname, '..', 'src'))) {
      const source = readFileSync(file, 'utf8')
      for (const match of source.matchAll(/(?:translate|\bt)\(\s*'([^']+)'/g)) if (match[1]) keys.add(match[1])
      for (const match of source.matchAll(/(?:title|label): '([^']+)'/g)) if (match[1]) keys.add(match[1])
    }
    const options = [
      ...startEventOptions(false),
      ...startEventOptions(true),
      ...boundaryEventOptions(true),
      ...intermediateEventOptions(),
      ...endEventOptions(true),
      ...GATEWAY_OPTIONS,
      ...TASK_OPTIONS,
      ...EXPANDED_SUBPROCESS_OPTIONS,
      ...DATA_OPTIONS,
      ...PARTICIPANT_OPTIONS,
    ]
    for (const option of options) keys.add(option.label)
    for (const label of Object.values(TYPE_LABELS)) keys.add(label)
    const missing = [...keys].filter((key) => !(key in translations))
    expect(missing).toEqual([])
  })

  it('verwendet echte Umlaute und füllt Platzhalter', () => {
    const translate = createTranslate('de')
    expect(translate('Delete')).toBe('Löschen')
    expect(translate('Element {id} exists more than once', { id: 'A' })).toBe('Element A ist mehrfach vorhanden')
    const ascii = Object.values(translations).filter((text) => /(ae|oe|ue)(?![a-z]*(?:eu|el))/.test(text) && /\b\w*(?:Pruef|Aender|Loesch|Groess|fuer)\w*/i.test(text))
    expect(ascii).toEqual([])
    expect(createTranslate('en')('Delete')).toBe('Delete')
  })
})

describe('Textsatz', () => {
  it('bricht nach Wörtern und Bindestrichen um und misst deterministisch', () => {
    const lines = wrapText('Antragsprüfung der Bewilligungsbehörde abschließen', 80)
    expect(lines.length).toBeGreaterThan(1)
    expect(lines.every((line) => line.width <= 80 || !line.text.includes(' '))).toBe(true)
    const hyphenated = wrapText('Vor-Ort-Kontrolle', 50).map((line) => line.text)
    expect(hyphenated[0]).toMatch(/-$/)
    expect(hyphenated.join('')).toBe('Vor-Ort-Kontrolle')
    expect(wrapText('Zeile 1\nZeile 2', 200).map((line) => line.text)).toEqual(['Zeile 1', 'Zeile 2'])
    expect(approximateMeasure('iii', DEFAULT_TEXT_STYLE)).toBeLessThan(approximateMeasure('MMM', DEFAULT_TEXT_STYLE))
    expect(layoutText('', { box: { width: 100, height: 20 } }).lines).toEqual([{ text: '', width: 0 }])
  })

  it('bricht überlange Wörter hart um', () => {
    const lines = wrapText('Donaudampfschifffahrtsgesellschaftskapitän', 50)
    expect(lines.length).toBeGreaterThan(2)
  })
})

describe('Hilfsfunktionen', () => {
  it('vergibt eindeutige Kennungen mit Präfix', () => {
    const ids = new Ids()
    ids.claim('Task_a')
    const created = new Set(Array.from({ length: 200 }, () => ids.nextPrefixed('Task_')))
    expect(created.size).toBe(200)
    expect([...created].every((id) => /^Task_[a-z][a-z0-9]{6}$/.test(id))).toBe(true)
    ids.unclaim('Task_a')
    expect(ids.assigned('Task_a')).toBeUndefined()
  })

  it('kopiert moddle-Elemente tief, auch generische Erweiterungen und in fremde Modelle', async () => {
    const source = createModdle()
    const { rootElement } = await source.fromXML(readFixture('synthetisch/alle-elemente.bpmn'))
    const task = (rootElement.rootElements || [])
      .flatMap((element) => element.flowElements || [])
      .find((element) => element.id === 'Task_Plain')
    if (!task) throw new Error('Aufgabe fehlt')
    const target = createModdle()
    const copy = cloneModdleElement(target, task)
    expect(copy.name).toBe('Aufgabe')
    expect(copy.$attrs['flowaudit:foo']).toBe('bar')
    const values = copy.extensionElements?.values || []
    expect(values.map((value) => value.$type)).toEqual(['flowaudit:rechtsgrundlage', 'flowaudit:interneNotiz', 'vendor:unbekannt'])
    expect(values[0]).not.toBe(task.extensionElements?.values?.[0])
  })

  it('bestimmt die Mitte eines Kantenzugs', () => {
    expect(getPathMid([{ x: 0, y: 0 }, { x: 100, y: 0 }, { x: 100, y: 100 }])).toEqual({ x: 100, y: 0 })
    expect(getPathMid([])).toEqual({ x: 0, y: 0 })
  })

  it('liefert eigene Symbole als SVG', () => {
    const icons = [
      Icons.eventIcon('start', 'message'),
      Icons.eventIcon('end', 'terminate'),
      Icons.eventIcon('boundary', 'timer', true),
      Icons.gatewayIcon('complex'),
      Icons.taskIcon('business-rule'),
      Icons.subProcessIcon('transaction'),
      Icons.dataObjectIcon('output'),
      Icons.laneIcon('divide-three'),
      ...Object.values(Icons.toolIcons),
    ]
    for (const icon of icons) {
      const doc = new DOMParser().parseFromString(icon, 'image/svg+xml')
      expect(doc.documentElement.localName).toBe('svg')
      expect(icon).toContain('aria-hidden="true"')
    }
  })
})

describe('SVG-Export', () => {
  it('erzeugt ein eigenständiges SVG ohne Interaktionshilfen', async () => {
    const { editor } = await importXml(readFixture('synthetisch/alle-elemente.bpmn'))
    const { svg } = await editor.saveSVG()
    expect(svg.startsWith('<?xml')).toBe(true)
    expect(svg).toContain('viewBox="')
    expect(svg).toContain('<marker')
    expect(svg).not.toContain('djs-hit')
    expect(svg).toContain('Rolle: Antrag prüfen'.split(':')[0])
    const doc = new DOMParser().parseFromString(svg, 'image/svg+xml')
    expect(doc.documentElement.getAttribute('width')).toMatch(/^\d+$/)
  })
})
