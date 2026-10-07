import { describe, expect, it } from 'vitest'
import { folderCards } from '../src/collection/cards'
import { DiagramCollection } from '../src/collection/collection'
import { InMemoryStorage } from '../src/ports/inMemory'
import { rolesFor } from '../src/profile/profile'
import { collectionCards, createCollectionCore, describedXml, hintCount } from '../src/ui/collectionCore'
import { createTranslator } from '../src/ui/i18n/translator'
import { hostActionsFor } from '../src/ui/toolbarActions'
import { PALETTE_VIEW_KEY, paletteCaption, paletteName, readPaletteEntries, readPaletteView, writePaletteView } from '../src/ui/paletteEntries'
import { fixture, modelOf } from './helpers'

async function sample(): Promise<DiagramCollection> {
  const collection = new DiagramCollection('s', 'Sammlung')
  collection.createFolder('antrag', 'Antragsverfahren', null, 'Bewilligungsverfahren der Programme')
  collection.createFolder('antrag-sub', 'Unterordner', 'antrag')
  collection.createFolder('leer', 'Leerer Ordner')
  collection.addDiagram('muster', { folderId: 'antrag', model: await modelOf(fixture('schema-1.1.bpmn')) })
  collection.addDiagram('alt', { folderId: 'antrag-sub', model: await modelOf(fixture('legacy-1.0.bpmn')) })
  collection.addDiagram('lose', { name: 'Lose', model: await modelOf(fixture('enrichment.bpmn')) })
  return collection
}

describe('folder cards', () => {
  it('lists subfolders with recursive diagrams, then the diagrams of the folder itself', async () => {
    const cards = folderCards(await sample(), null)
    expect(cards.map((card) => [card.folderId, card.name, card.count])).toEqual([
      ['antrag', 'Antragsverfahren', 2],
      ['leer', 'Leerer Ordner', 0],
      [null, '', 1],
    ])
    expect(cards[0]!.description).toBe('Bewilligungsverfahren der Programme')
    expect(cards[0]!.diagrams.map((diagram) => diagram.id)).toEqual(['muster', 'alt'])
    expect(cards[1]!.description).toBe('')
  })

  it('shows the cards of a selected folder', async () => {
    const cards = collectionCards(await sample(), 'antrag')
    expect(cards.map((card) => [card.folderId, card.count])).toEqual([
      ['antrag-sub', 1],
      [null, 1],
    ])
  })

  it('sets and removes folder descriptions', async () => {
    const collection = await sample()
    collection.describeFolder('leer', '  Noch zu befüllen  ')
    expect(collection.folders.get('leer')!.description).toBe('Noch zu befüllen')
    collection.describeFolder('leer', ' ')
    expect('description' in collection.folders.get('leer')!).toBe(false)
    expect(() => collection.describeFolder('fehlt', 'x')).toThrow()
  })

  it('renames folders with trimmed names and keeps the old name for an empty one', async () => {
    const collection = await sample()
    collection.renameFolder('leer', '  Prüfstrategie  ')
    expect(collection.folders.get('leer')!.name).toBe('Prüfstrategie')
    collection.renameFolder('leer', '   ')
    expect(collection.folders.get('leer')!.name).toBe('Prüfstrategie')
    expect(() => collection.renameFolder('fehlt', 'x')).toThrow()
  })

  it('counts collection issues plus expired diagrams as audit hints', () => {
    expect(hintCount({ expired: ['a'] }, [{}, {}])).toBe(3)
    expect(hintCount({ expired: [] }, [])).toBe(0)
  })
})

describe('diagram descriptions', () => {
  it('writes the description into the diagram info and keeps the other fields', async () => {
    const xml = await describedXml(fixture('schema-1.1.bpmn'), 'Kurzbeschreibung des Ablaufs')
    const model = await modelOf(xml)
    expect(model.info?.description).toBe('Kurzbeschreibung des Ablaufs')
    expect(model.info?.title).toBe((await modelOf(fixture('schema-1.1.bpmn'))).info?.title)
    expect((await modelOf(await describedXml(xml, ''))).info?.description).toBeUndefined()
  })

  it('persists folder and diagram descriptions through the storage port', async () => {
    const storage = new InMemoryStorage()
    const core = createCollectionCore(storage)
    await core.load()
    const folder = await core.createFolder('Antragsverfahren')
    const id = (await core.createDiagram('Bewilligung', folder!.id, fixture('schema-1.1.bpmn')))!
    await core.describeFolder(folder!.id, 'Ordnerbeschreibung')
    await core.describeDiagram(id, 'Diagrammbeschreibung')
    const saved = await storage.loadCollection()
    expect(saved!.folders[0]!.description).toBe('Ordnerbeschreibung')
    expect(saved!.diagrams[0]!.info?.description).toBe('Diagrammbeschreibung')
    expect((await modelOf(await storage.loadDiagram(id))).info?.description).toBe('Diagrammbeschreibung')
    expect(core.store.get().error).toBeNull()
  })
})

describe('palette views', () => {
  const t = createTranslator('de')
  const roles = rolesFor(null, '2021-2027')
  const items = readPaletteEntries(
    { 'create.start-event': { group: 'event', title: 'Startereignis anlegen' }, 'flowaudit-pool-rfs': { group: 'flowaudit-roles', title: 'Pool anlegen: RFS' } },
    roles,
  )

  it('names elements and roles from the same role catalogue', () => {
    const rfs = roles.find((role) => role.code === 'rfs')!
    expect(paletteName(items[0]!, t)).toBe('Startereignis')
    expect(paletteCaption(items[0]!, t)).toBe('Startereignis')
    expect(items[1]!.short).toBe(rfs.short)
    expect(paletteCaption(items[1]!, t)).toBe('RFS')
    expect(paletteName(items[1]!, t)).toBe('Stelle mit Rechnungsführungsfunktion (Art. 76 CPR)')
  })

  it('falls back to the editor title for unknown entries', () => {
    expect(paletteName({ id: 'x', title: 'Eigenes Werkzeug', icon: '', group: 'other' }, t)).toBe('Eigenes Werkzeug')
  })

  it('remembers the view and tolerates missing or blocked storage', () => {
    const values = new Map<string, string>()
    const storage = { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => void values.set(key, value) }
    expect(readPaletteView(storage)).toBe('icons')
    writePaletteView('list', storage)
    expect(values.get(PALETTE_VIEW_KEY)).toBe('list')
    expect(readPaletteView(storage)).toBe('list')
    values.set(PALETTE_VIEW_KEY, 'unbekannt')
    expect(readPaletteView(storage)).toBe('icons')
    const blocked = {
      getItem: () => {
        throw new Error('blockiert')
      },
      setItem: () => {
        throw new Error('blockiert')
      },
    }
    expect(readPaletteView(blocked)).toBe('icons')
    expect(() => writePaletteView('tiles', blocked)).not.toThrow()
    expect(readPaletteView(null)).toBe('icons')
  })
})

describe('host actions', () => {
  it('splits host actions into export dialog and toolbar menu', () => {
    const actions = [{ id: 'a', label: 'A', group: 'export' as const }, { id: 'b', label: 'B' }]
    expect(hostActionsFor(actions, 'export').map((action) => action.id)).toEqual(['a'])
    expect(hostActionsFor(actions, 'menu').map((action) => action.id)).toEqual(['b'])
    expect(hostActionsFor(undefined, 'menu')).toEqual([])
  })
})
