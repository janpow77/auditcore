/**
 * BpmnEditor – öffentlicher Einstiegspunkt des Editors.
 *
 * Baut eine diagram-js-Instanz mit den BPMN-Modulen dieses Pakets auf und
 * stellt Import/Export (BPMN 2.0 XML mit DI, SVG) bereit.
 */

import Diagram from 'diagram-js'

import { createModdle } from './moddle/createModdle'
import { getIds } from './util/Ids'
import { createTranslate } from './i18n/translate'
import { translations } from './i18n/translations'
import { exportSvg } from './export/SvgExport'
import { DEFAULT_MODULES } from './modules'
import { INITIAL_DIAGRAM } from './initialDiagram'
import type { BpmnImporter } from './import/Importer'
import type { Canvas, ElementRegistry, EventBus, Moddle, ModdleElement, Translate } from './types'

export interface EditorOptions {
  container: HTMLElement
  /** diagram-js-Module (z. B. aus bpmn-flowaudit) */
  additionalModules?: unknown[]
  /** moddle-Erweiterungen, z. B. `{ flowaudit: flowauditModdleDescriptor }` */
  moddleExtensions?: Record<string, unknown>
  keyboard?: { bindTo?: EventTarget }
  /** Rasterweite in Pixeln (Standard 10) */
  gridSize?: number
  /** Sprache der Oberfläche (Standard 'de') */
  locale?: 'de' | 'en'
  /** Zusätzliche Konfiguration einzelner Module (z. B. `bpmnRenderer`, `colorPicker`, `minimap`, `grid`). */
  config?: Record<string, unknown>
}

export interface ImportXMLResult {
  warnings: string[]
}

type Listener = (event: unknown) => unknown

interface DiagramInstance {
  get<T>(name: string, strict?: boolean): T
  invoke<T>(fn: (...args: unknown[]) => T): T
  clear(): void
  destroy(): void
}

type DiagramConstructor = new (options: Record<string, unknown>) => DiagramInstance

type ParseError = Error & { warnings?: Array<{ message: string } | string> }

function toMessage(warning: { message?: string } | string): string {
  return typeof warning === 'string' ? warning : warning?.message || String(warning)
}

function createContainer(host: HTMLElement, label: string): HTMLElement {
  const container = document.createElement('div')
  container.className = 'fa-bpmn-editor'
  container.setAttribute('role', 'application')
  container.setAttribute('aria-label', label)
  Object.assign(container.style, { width: '100%', height: '100%', position: 'relative' })
  host.appendChild(container)
  return container
}

export class BpmnEditor {
  private readonly diagram: DiagramInstance
  private readonly moddle: Moddle
  private readonly element: HTMLElement
  private definitions: ModdleElement | null = null
  private destroyed = false

  constructor(options: EditorOptions) {
    if (!options || !options.container) throw new Error('BpmnEditor: Option „container“ fehlt')
    const locale = options.locale || 'de'
    const translate = createTranslate(locale)
    this.element = createContainer(options.container, translate('BPMN diagram editor'))
    this.moddle = createModdle(options.moddleExtensions || {})
    const editorModule = {
      bpmnEditor: ['value', this],
      moddle: ['value', this.moddle],
      translate: ['value', translate],
    }
    const DiagramClass = Diagram as unknown as DiagramConstructor
    this.diagram = new DiagramClass({
      ...(options.config || {}),
      canvas: { container: this.element, deferUpdate: false },
      // diagram-js bindet Tastenkürzel seit Version 15 an die fokussierte Zeichenfläche;
      // `keyboard.bindTo` wird aus Kompatibilitätsgründen angenommen, aber nicht weitergereicht.
      keyboard: {},
      gridSize: options.gridSize ?? 10,
      locale,
      modules: [...DEFAULT_MODULES, editorModule, ...(options.additionalModules || [])],
    })
  }

  /** Liest BPMN-2.0-XML ein und stellt das Diagramm dar. */
  async importXML(xml: string): Promise<ImportXMLResult> {
    this.assertAlive()
    const eventBus = this.get<EventBus>('eventBus')
    const source = (eventBus.fire('import.parse.start', { xml }) as string | undefined) || xml
    let parsed: Awaited<ReturnType<Moddle['fromXML']>>
    try {
      parsed = await this.moddle.fromXML(source, 'bpmn:Definitions')
    } catch (error) {
      throw this.parseFailure(error as ParseError)
    }
    const parseWarnings = (parsed.warnings || []).map(toMessage)
    eventBus.fire('import.parse.complete', { error: null, definitions: parsed.rootElement, warnings: parseWarnings })
    try {
      const result = this.importDefinitions(parsed.rootElement, parsed.elementsById)
      const warnings = [...parseWarnings, ...result.warnings]
      eventBus.fire('import.done', { error: null, warnings })
      return { warnings }
    } catch (error) {
      eventBus.fire('import.done', { error, warnings: parseWarnings })
      Object.assign(error as object, { warnings: parseWarnings })
      throw error
    }
  }

  private parseFailure(error: ParseError): Error {
    const eventBus = this.get<EventBus>('eventBus')
    const warnings = (error.warnings || []).map(toMessage)
    eventBus.fire('import.parse.complete', { error, warnings })
    eventBus.fire('import.done', { error, warnings })
    const wrapped = new Error(`${this.get<Translate>('translate')('Invalid BPMN XML')}: ${error.message}`) as Error & { warnings?: string[] }
    wrapped.warnings = warnings
    return wrapped
  }

  /** Stellt bereits geparste Definitionen dar. */
  importDefinitions(definitions: ModdleElement, elementsById?: Record<string, ModdleElement>): ImportXMLResult {
    this.clear()
    this.definitions = definitions
    const ids = getIds(this.moddle)
    ids.clear()
    for (const [id, element] of Object.entries(elementsById || collectIds(definitions))) ids.claim(id, element)
    const eventBus = this.get<EventBus>('eventBus')
    eventBus.fire('import.render.start', { definitions })
    const result = this.get<BpmnImporter>('bpmnImporter').importDefinitions(definitions)
    eventBus.fire('import.render.complete', { error: null, warnings: result.warnings })
    return result
  }

  /** Serialisiert das Diagramm als BPMN-2.0-XML (mit DI). */
  async saveXML(opts: { format?: boolean } = {}): Promise<{ xml: string }> {
    this.assertAlive()
    if (!this.definitions) throw new Error(this.get<Translate>('translate')('No diagram loaded'))
    const eventBus = this.get<EventBus>('eventBus')
    const definitions = (eventBus.fire('saveXML.start', { definitions: this.definitions }) as ModdleElement | undefined) || this.definitions
    const result = await this.moddle.toXML(definitions, { format: !!opts.format, preamble: true })
    const xml = (eventBus.fire('saveXML.serialized', { xml: result.xml }) as string | undefined) || result.xml
    eventBus.fire('saveXML.done', { xml })
    return { xml }
  }

  /** Erzeugt ein eigenständiges SVG der aktuell angezeigten Ebene. */
  async saveSVG(): Promise<{ svg: string }> {
    this.assertAlive()
    const eventBus = this.get<EventBus>('eventBus')
    eventBus.fire('saveSVG.start')
    const svg = exportSvg(this.get<Canvas>('canvas'), this.get<ElementRegistry>('elementRegistry'))
    eventBus.fire('saveSVG.done', { svg })
    return { svg }
  }

  /** Legt ein leeres Diagramm mit Startereignis an. */
  async createDiagram(): Promise<void> {
    await this.importXML(INITIAL_DIAGRAM)
  }

  /** Aktuelle `bpmn:Definitions` (oder `null`). */
  getDefinitions(): ModdleElement | null {
    return this.definitions
  }

  /** Zugriff auf Dienste des diagram-js-Injektors. */
  get<T = unknown>(service: string, strict = true): T {
    return this.diagram.get<T>(service, strict)
  }

  invoke<T = unknown>(fn: (...args: unknown[]) => T): T {
    return this.diagram.invoke(fn)
  }

  on(event: string, cb: Listener, priority?: number): void {
    const eventBus = this.get<EventBus>('eventBus')
    if (typeof priority === 'number') eventBus.on(event, priority, cb)
    else eventBus.on(event, cb)
  }

  off(event: string, cb: Listener): void {
    this.get<EventBus>('eventBus').off(event, cb)
  }

  /** Entfernt alle Elemente (ohne Definitionen zu verwerfen). */
  clear(): void {
    this.diagram.clear()
  }

  /** Gibt alle Ressourcen frei und entfernt die Oberfläche. */
  destroy(): void {
    if (this.destroyed) return
    this.destroyed = true
    this.diagram.destroy()
    this.element.remove()
  }

  /** Das vom Editor verwaltete Container-Element. */
  get container(): HTMLElement {
    return this.element
  }

  private assertAlive(): void {
    if (this.destroyed) throw new Error('BpmnEditor wurde bereits zerstört')
  }
}

/** Sammelt alle Kennungen eines moddle-Baums (ohne Verweise zu verfolgen). */
function collectIds(root: ModdleElement): Record<string, ModdleElement> {
  const result: Record<string, ModdleElement> = {}
  const seen = new Set<ModdleElement>()
  const visit = (element: ModdleElement) => {
    if (seen.has(element)) return
    seen.add(element)
    if (element.id) result[element.id] = element
    for (const property of element.$descriptor?.properties || []) {
      if (property.isReference) continue
      for (const child of childElements(element.get(property.name))) visit(child)
    }
  }
  visit(root)
  return result
}

function childElements(value: unknown): ModdleElement[] {
  const values = Array.isArray(value) ? value : [value]
  return values.filter((item): item is ModdleElement => !!item && typeof item === 'object' && typeof (item as ModdleElement).$type === 'string')
}

export { translations }
export default BpmnEditor
