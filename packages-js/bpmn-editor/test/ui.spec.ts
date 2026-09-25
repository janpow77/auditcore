/**
 * Oberfläche: Palette, Kontextpad, Menüs, Suche, Tastenkürzel,
 * Beschriftung bearbeiten, Übersichtskarte, Raster, Ebenen.
 */

import { describe, expect, it } from 'vitest'

import { getBusinessObject } from '../src'
import type { BpmnElement, EventBus } from '../src/types'
import type { PopupMenuActionEntry } from 'diagram-js/lib/features/popup-menu/PopupMenuProvider'
import { readFixture } from './helpers/fixtures'
import { createKit, type Kit } from './helpers/modeling'

type EntryMap = Record<string, { title?: string; action: unknown; html?: string }>
type Provider<T = EntryMap> = { getPopupMenuEntries(target: unknown): T }

function paletteEntries(kit: Kit): EntryMap {
  return kit.editor.get<{ getPaletteEntries(): EntryMap }>('paletteProvider').getPaletteEntries()
}

function padEntries(kit: Kit, element: BpmnElement): EntryMap {
  return kit.editor.get<{ getContextPadEntries(element: BpmnElement): EntryMap }>('contextPadProvider').getContextPadEntries(element)
}

function popupEntries(kit: Kit, provider: string, target: unknown): Record<string, PopupMenuActionEntry> {
  return kit.editor.get<Provider<Record<string, PopupMenuActionEntry>>>(provider).getPopupMenuEntries(target)
}

describe('Palette', () => {
  it('bietet Werkzeuge und alle Grundelemente mit eigenen Symbolen und deutschen Titeln', async () => {
    const entries = paletteEntries(await createKit())
    expect(Object.keys(entries)).toEqual(
      expect.arrayContaining([
        'hand-tool',
        'lasso-tool',
        'space-tool',
        'global-connect-tool',
        'create.start-event',
        'create.intermediate-event',
        'create.end-event',
        'create.exclusive-gateway',
        'create.task',
        'create.subprocess-expanded',
        'create.data-object',
        'create.data-store',
        'create.participant-expanded',
        'create.group',
        'create.text-annotation',
      ]),
    )
    expect(entries['create.task']?.title).toBe('Aufgabe anlegen')
    expect(entries['create.task']?.html).toContain('<svg')
  })
})

describe('Kontextpad', () => {
  it('bietet an Aufgaben Anhängen, Ersetzen, Verbinden, Anmerkung, Farbe und Löschen', async () => {
    const kit = await createKit()
    const keys = Object.keys(padEntries(kit, kit.create('bpmn:Task', 400, 120)))
    expect(keys).toEqual(
      expect.arrayContaining(['append.end-event', 'append.gateway', 'append.append-task', 'replace', 'connect', 'append.text-annotation', 'set-color', 'delete']),
    )
  })

  it('bietet an Pools Bahnen an und am ereignisbasierten Gateway passende Folgeelemente', async () => {
    const kit = await createKit(readFixture('synthetisch/alle-elemente.bpmn'))
    expect(Object.keys(padEntries(kit, kit.get('Participant_A')))).toEqual(expect.arrayContaining(['lane-insert-above', 'lane-insert-below']))
    expect(Object.keys(padEntries(kit, kit.get('Lane_Pruefung')))).toEqual(expect.arrayContaining(['lane-divide-two', 'lane-divide-three']))
    expect(Object.keys(padEntries(kit, kit.get('Gateway_E')))).toEqual(
      expect.arrayContaining(['append.receive-task', 'append.timer-intermediate-event', 'append.message-intermediate-event']),
    )
    expect(Object.keys(padEntries(kit, kit.get('End_None')))).not.toContain('append.append-task')
  })

  it('hängt per Klick an und legt die Aufgabe rechts neben die Quelle', async () => {
    const kit = await createKit()
    const start = kit.get('StartEvent_1')
    const action = padEntries(kit, start)['append.append-task']?.action as { click: (event: Event) => void }
    action.click(new MouseEvent('click'))
    const [flow] = start.outgoing
    const task = flow?.target as BpmnElement
    expect(task.type).toBe('bpmn:Task')
    expect(task.x).toBeGreaterThan(start.x + start.width)
  })
})

describe('Menüs', () => {
  it('Ersetzen-Menü ersetzt und zeigt Marker in der Kopfleiste', async () => {
    const kit = await createKit()
    const task = kit.create('bpmn:Task', 400, 120)
    const entries = popupEntries(kit, 'replaceMenuProvider', task)
    expect(entries['replace-user-task']?.label).toBe('Benutzeraufgabe')
    entries['replace-service-task']?.action(new Event('click'), entries['replace-service-task'] as PopupMenuActionEntry)
    const replaced = kit.get(task.id)
    expect(replaced.type).toBe('bpmn:ServiceTask')
    const headers = kit.editor
      .get<{ getPopupMenuHeaderEntries(target: unknown): { id: string; action: (event: Event, entry: unknown) => void }[] }>('replaceMenuProvider')
      .getPopupMenuHeaderEntries(replaced)
    expect(headers.map((header) => header.id)).toEqual(['toggle-loop', 'toggle-parallel-mi', 'toggle-sequential-mi', 'toggle-compensation'])
    headers[1]?.action(new Event('click'), headers[1])
    expect(getBusinessObject(replaced).loopCharacteristics?.$type).toBe('bpmn:MultiInstanceLoopCharacteristics')
  })

  it('Ersetzen-Menü an Sequenzflüssen und Farbmenü', async () => {
    const kit = await createKit()
    const gateway = kit.create('bpmn:ExclusiveGateway', 300, 120)
    const flow = kit.modeling.connect(gateway, kit.create('bpmn:Task', 500, 120))
    const flowEntries = popupEntries(kit, 'replaceMenuProvider', flow)
    expect(Object.keys(flowEntries)).toEqual(['replace-default-flow', 'replace-conditional-flow'])
    const colors = popupEntries(kit, 'colorMenuProvider', [gateway])
    expect(colors['color-0']?.label).toBe('Standard')
    colors['color-5']?.action(new Event('click'), colors['color-5'] as PopupMenuActionEntry)
    expect(gateway.di?.get('bioc:fill')).toBe('#fee2e2')
  })

  it('Ausrichten-Menü', async () => {
    const kit = await createKit()
    const a = kit.create('bpmn:Task', 300, 100)
    const b = kit.create('bpmn:Task', 500, 200)
    const entries = popupEntries(kit, 'alignMenuProvider', [a, b])
    entries['align-left']?.action(new Event('click'), entries['align-left'] as PopupMenuActionEntry)
    expect(a.x).toBe(b.x)
  })
})

describe('Suche, Tastenkürzel, Editor-Aktionen', () => {
  it('findet Elemente nach Name und Kennung', async () => {
    const kit = await createKit(readFixture('synthetisch/alle-elemente.bpmn'))
    const search = kit.editor.get<{ find(pattern: string): { element: BpmnElement; secondaryTokens: { value: string }[] }[] }>('bpmnSearch')
    const results = search.find('antrag')
    expect(results.map((result) => result.element.id)).toContain('Task_User')
    expect(search.find('Task_Plain')[0]?.element.id).toBe('Task_Plain')
    expect(search.find('')).toEqual([])
  })

  it('registriert Editor-Aktionen und Tastenkürzel', async () => {
    const kit = await createKit()
    const actions = kit.editor.get<{ isRegistered(name: string): boolean; trigger(name: string, options?: unknown): unknown }>('editorActions')
    for (const name of ['undo', 'redo', 'copy', 'paste', 'selectElements', 'spaceTool', 'lassoTool', 'handTool', 'globalConnectTool', 'directEditing', 'find', 'replaceElement', 'toggleMinimap', 'zoomFit', 'alignElements', 'distributeElements', 'setColor']) {
      expect(actions.isRegistered(name), name).toBe(true)
    }
    const selected = actions.trigger('selectElements') as BpmnElement[]
    expect(selected.map((element) => element.id)).toEqual(['StartEvent_1'])
  })

  it('bearbeitet Beschriftungen direkt (übernehmen und abbrechen)', async () => {
    const kit = await createKit()
    const editing = kit.editor.get<{ activate(element: BpmnElement): boolean; complete(): void; cancel(): void; isActive(): boolean }>('labelEditing')
    const task = kit.create('bpmn:Task', 400, 120)
    expect(editing.activate(task)).toBe(true)
    const box = kit.editor.container.querySelector('.fa-label-editor') as HTMLElement
    expect(box.getAttribute('role')).toBe('textbox')
    box.textContent = 'Antrag prüfen'
    editing.complete()
    expect(getBusinessObject(task).name).toBe('Antrag prüfen')
    editing.activate(task)
    ;(kit.editor.container.querySelector('.fa-label-editor') as HTMLElement).textContent = 'Verworfen'
    editing.cancel()
    expect(getBusinessObject(task).name).toBe('Antrag prüfen')
    expect(editing.isActive()).toBe(false)
  })

  it('öffnet und schließt die Übersichtskarte und zeigt ein Raster', async () => {
    const kit = await createKit()
    const minimap = kit.editor.get<{ isOpen(): boolean; toggle(): void; update(): void }>('minimap')
    expect(minimap.isOpen()).toBe(false)
    minimap.toggle()
    minimap.update()
    expect(minimap.isOpen()).toBe(true)
    expect(kit.editor.container.querySelector('.fa-minimap.open use')?.getAttribute('href')).toMatch(/^#fa-minimap-layer-/)
    expect(kit.editor.container.querySelector('.fa-grid')).toBeTruthy()
    const snapping = kit.editor.get<{ getGridSpacing(): number; snapValue(value: number): number }>('gridSnapping')
    expect(snapping.getGridSpacing()).toBe(10)
    expect(snapping.snapValue(14)).toBe(10)
  })

  it('übernimmt eine abweichende Rasterweite', async () => {
    const { createEditor } = await import('./helpers/editor')
    const editor = createEditor({ gridSize: 20 })
    await editor.createDiagram()
    expect(editor.get<{ snapValue(value: number): number }>('gridSnapping').snapValue(14)).toBe(20)
  })
})

describe('Teilprozess-Ebenen', () => {
  it('öffnet zugeklappte Teilprozesse und zeigt Brotkrumen', async () => {
    const kit = await createKit(readFixture('synthetisch/alle-elemente.bpmn'))
    const planes = kit.editor.get<{ drillDown(element: BpmnElement): void; drillUp(): void }>('subProcessPlanes')
    const eventBus = kit.editor.get<EventBus>('eventBus')
    let rootChanges = 0
    eventBus.on('root.set', () => rootChanges++)
    expect(kit.editor.container.querySelector('.fa-drilldown-button')).toBeTruthy()
    planes.drillDown(kit.get('Sub_Collapsed'))
    expect(getBusinessObject(kit.root()).id).toBe('Sub_Collapsed')
    expect(kit.root().children.length).toBeGreaterThan(0)
    const crumbs = [...kit.editor.container.querySelectorAll('.fa-breadcrumb')].map((node) => node.textContent)
    expect(crumbs).toEqual(['Prozess', 'Eingeklappt'])
    planes.drillUp()
    expect(getBusinessObject(kit.root()).id).toBe('Collaboration_1')
    expect(rootChanges).toBe(2)
  })
})
