import { describe, expect, it, vi } from 'vitest'
import { folderCards } from '../src/collection/cards'
import { DiagramCollection } from '../src/collection/collection'
import { InMemoryStorage } from '../src/ports/inMemory'
import { createCollectionCore } from '../src/ui/collectionCore'
import { createTranslator } from '../src/ui/i18n/translator'
import { diagramFacts, isWideCard, legalShare, OVERVIEW_VIEW_KEY, overviewViews, readOverviewView, writeOverviewView } from '../src/ui/overviewViews'
import { clampWidth, COLLECTION_PANEL, dragWidth, keyWidth, panelKey, PROPERTIES_PANEL, readPanel, writePanel } from '../src/ui/panelSize'
import { readChoice, readJson } from '../src/ui/preferences'
import { handleShortcut } from '../src/ui/shortcuts'
import { createThumbnails } from '../src/ui/thumbnails'
import { fixture, modelOf } from './helpers'

function memory(): Pick<Storage, 'getItem' | 'setItem'> {
  const data = new Map<string, string>()
  return { getItem: (key) => data.get(key) ?? null, setItem: (key, value) => void data.set(key, value) }
}

const broken: Pick<Storage, 'getItem' | 'setItem'> = {
  getItem: () => {
    throw new Error('blocked')
  },
  setItem: () => {
    throw new Error('blocked')
  },
}

describe('preferences', () => {
  it('falls back for unknown, missing or unreadable values', () => {
    const store = memory()
    store.setItem('k', 'fremd')
    expect(readChoice('k', ['a', 'b'] as const, 'a', store)).toBe('a')
    expect(readChoice('k', ['a', 'b'] as const, 'b', broken)).toBe('b')
    store.setItem('j', '[1]')
    expect(readJson('j', store)).toBeNull()
    expect(readJson('j', broken)).toBeNull()
  })
})

describe('panel size', () => {
  it('keeps widths within the bounds', () => {
    expect(clampWidth(10, PROPERTIES_PANEL)).toBe(PROPERTIES_PANEL.min)
    expect(clampWidth(5000, PROPERTIES_PANEL)).toBe(PROPERTIES_PANEL.max)
    expect(clampWidth(Number.NaN, PROPERTIES_PANEL)).toBe(PROPERTIES_PANEL.initial)
  })

  it('grows a right panel when dragged to the left and a left panel when dragged to the right', () => {
    expect(dragWidth(420, 1000, 900, 'right', PROPERTIES_PANEL)).toBe(520)
    expect(dragWidth(300, 300, 360, 'left', COLLECTION_PANEL)).toBe(360)
  })

  it('answers arrows, Home and End and ignores other keys', () => {
    expect(keyWidth(420, 'ArrowLeft', 'right', PROPERTIES_PANEL)).toBe(444)
    expect(keyWidth(420, 'ArrowRight', 'right', PROPERTIES_PANEL)).toBe(396)
    expect(keyWidth(300, 'ArrowRight', 'left', COLLECTION_PANEL)).toBe(324)
    expect(keyWidth(420, 'Home', 'right', PROPERTIES_PANEL)).toBe(PROPERTIES_PANEL.min)
    expect(keyWidth(420, 'End', 'right', PROPERTIES_PANEL)).toBe(PROPERTIES_PANEL.max)
    expect(keyWidth(420, 'a', 'right', PROPERTIES_PANEL)).toBeNull()
  })

  it('remembers width and open state, clamps what was stored', () => {
    const store = memory()
    expect(readPanel('properties', PROPERTIES_PANEL, store)).toEqual({ width: 420, open: true })
    writePanel('properties', { width: 512.4, open: false }, store)
    expect(readPanel('properties', PROPERTIES_PANEL, store)).toEqual({ width: 512, open: false })
    store.setItem(panelKey('properties'), JSON.stringify({ width: 9999 }))
    expect(readPanel('properties', PROPERTIES_PANEL, store)).toEqual({ width: PROPERTIES_PANEL.max, open: true })
    expect(readPanel('properties', PROPERTIES_PANEL, broken)).toEqual({ width: 420, open: true })
  })
})

describe('overview views', () => {
  it('offers thumbnails only with a source and remembers the choice', () => {
    const store = memory()
    expect(overviewViews(false)).toEqual(['tiles', 'list'])
    writeOverviewView('thumbnails', store)
    expect(store.getItem(OVERVIEW_VIEW_KEY)).toBe('thumbnails')
    expect(readOverviewView(true, store)).toBe('thumbnails')
    expect(readOverviewView(false, store)).toBe('tiles')
  })

  it('reports activities, legal basis share and date of a diagram', async () => {
    const collection = new DiagramCollection('s', 'Sammlung')
    collection.addDiagram('muster', { model: await modelOf(fixture('schema-1.1.bpmn')) })
    const [card] = folderCards(collection, null)
    const diagram = card!.diagrams[0]!
    expect(diagram.activities).toBeGreaterThan(0)
    expect(legalShare(diagram)).toBe(Math.round((diagram.withLegalBasis / diagram.activities) * 100))
    const facts = diagramFacts(diagram, createTranslator('de'), 'de')
    expect(facts[0]).toBe(`${diagram.activities} Aktivitäten`)
    expect(facts[1]).toMatch(/% mit Rechtsgrundlage$/)
    expect(legalShare({ ...diagram, activities: 0 })).toBeNull()
  })

  it('lets a single card or a card with many diagrams take the whole row', () => {
    expect(isWideCard(2, 1)).toBe(true)
    expect(isWideCard(8, 3)).toBe(true)
    expect(isWideCard(2, 3)).toBe(false)
  })
})

describe('thumbnails', () => {
  it('prefers the host thumbnail, renders otherwise and caches until invalidated', async () => {
    const storage = new InMemoryStorage({ diagrams: { a: '<a/>', b: '<b/>' } })
    const render = vi.fn(async (xml: string) => `data:${xml}`)
    const delivered = vi.fn(async (id: string) => (id === 'a' ? 'https://bild/a.png' : null))
    Object.assign(storage, { thumbnail: delivered })
    const thumbs = createThumbnails({ storage, render })
    expect(await thumbs.get('a')).toBe('https://bild/a.png')
    expect(await thumbs.get('b')).toBe('data:<b/>')
    await thumbs.get('b')
    expect(render).toHaveBeenCalledTimes(1)
    thumbs.invalidate('b')
    await thumbs.get('b')
    expect(render).toHaveBeenCalledTimes(2)
  })

  it('runs at most two renders at a time and turns failures into null', async () => {
    const storage = new InMemoryStorage({ diagrams: { a: 'a', b: 'b', c: 'c' } })
    let running = 0
    let peak = 0
    const render = async (xml: string) => {
      running += 1
      peak = Math.max(peak, running)
      await new Promise((resolve) => setTimeout(resolve, 5))
      running -= 1
      if (xml === 'c') throw new Error('kaputt')
      return xml
    }
    const thumbs = createThumbnails({ storage, render })
    expect(await Promise.all(['a', 'b', 'c'].map((id) => thumbs.get(id)))).toEqual(['a', 'b', null])
    expect(peak).toBe(2)
  })

  it('is told by the collection core when a diagram was saved', async () => {
    const storage = new InMemoryStorage()
    const saved: string[] = []
    const core = createCollectionCore(storage, { onDiagramSaved: (id) => saved.push(id) })
    await core.load()
    const id = await core.createDiagram('Neu')
    await core.saveDiagram(id!, fixture('enrichment.bpmn'))
    await core.describeDiagram(id!, 'Text')
    await core.removeDiagram(id!)
    expect(saved).toEqual([id, id, id, id])
  })
})

describe('properties panel shortcut', () => {
  it('toggles with Ctrl+Alt+P and leaves other keys alone', () => {
    const panel = vi.fn()
    const handlers = { save: vi.fn(), search: vi.fn(), help: vi.fn(), panel }
    const event = (init: KeyboardEventInit) => new KeyboardEvent('keydown', init)
    expect(handleShortcut(event({ key: 'p', code: 'KeyP', ctrlKey: true, altKey: true }), handlers)).toBe(true)
    expect(panel).toHaveBeenCalledTimes(1)
    expect(handleShortcut(event({ key: 'p', code: 'KeyP', ctrlKey: true }), handlers)).toBe(false)
    expect(handleShortcut(event({ key: 's', code: 'KeyS', metaKey: true }), handlers)).toBe(true)
    expect(handlers.save).toHaveBeenCalledTimes(1)
  })
})
