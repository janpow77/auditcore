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

/* eslint-disable @typescript-eslint/no-explicit-any */

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
  /** Zusätzliche Konfiguration einzelner Module (z. B. `bpmnRenderer`). */
  config?: Record<string, unknown>
}

export interface ImportXMLResult {
  warnings: string[]
}

export class BpmnEditor {
  private _diagram: any
  private _moddle: any
  private _definitions: any = null
  private _container: HTMLElement
  private _hostContainer: HTMLElement
  private _destroyed = false

  constructor(options: EditorOptions) {
    if (!options || !options.container) {
      throw new Error('BpmnEditor: Option „container“ fehlt')
    }
    this._hostContainer = options.container
    this._container = document.createElement('div')
    this._container.className = 'fa-bpmn-editor'
    this._container.setAttribute('role', 'application')
    this._container.style.width = '100%'
    this._container.style.height = '100%'
    this._container.style.position = 'relative'
    this._hostContainer.appendChild(this._container)

    const locale = options.locale || 'de'
    this._moddle = createModdle(options.moddleExtensions || {})

    const editorModule = {
      bpmnEditor: ['value', this],
      moddle: ['value', this._moddle],
      translate: ['value', createTranslate(locale)],
    }

    const config: Record<string, unknown> = {
      ...(options.config || {}),
      canvas: { container: this._container, deferUpdate: false },
      keyboard: options.keyboard,
      gridSize: options.gridSize ?? 10,
      locale,
    }

    this._container.setAttribute('aria-label', createTranslate(locale)('BPMN diagram editor'))

    this._diagram = new (Diagram as any)({
      ...config,
      modules: [...DEFAULT_MODULES, editorModule, ...(options.additionalModules || [])],
    })
  }

  /** Liest BPMN-2.0-XML ein und stellt das Diagramm dar. */
  async importXML(xml: string): Promise<ImportXMLResult> {
    this._assertAlive()
    const eventBus = this.get<any>('eventBus')
    let parseResult: any
    xml = eventBus.fire('import.parse.start', { xml }) || xml
    try {
      parseResult = await this._moddle.fromXML(xml, 'bpmn:Definitions')
    } catch (error: any) {
      const warnings = (error.warnings || []).map(toMessage)
      eventBus.fire('import.parse.complete', { error, warnings })
      eventBus.fire('import.done', { error, warnings })
      const wrapped = new Error(`${this.get<any>('translate')('Invalid BPMN XML')}: ${error.message}`) as Error & {
        warnings?: string[]
      }
      wrapped.warnings = warnings
      throw wrapped
    }

    const definitions = parseResult.rootElement
    const parseWarnings: string[] = (parseResult.warnings || []).map(toMessage)
    eventBus.fire('import.parse.complete', { error: null, definitions, warnings: parseWarnings })

    try {
      const result = this.importDefinitions(definitions, parseResult.elementsById)
      const warnings = [...parseWarnings, ...result.warnings]
      eventBus.fire('import.done', { error: null, warnings })
      return { warnings }
    } catch (error: any) {
      eventBus.fire('import.done', { error, warnings: parseWarnings })
      error.warnings = parseWarnings
      throw error
    }
  }

  /** Stellt bereits geparste Definitionen dar. */
  importDefinitions(definitions: any, elementsById?: Record<string, any>): ImportXMLResult {
    this.clear()
    this._definitions = definitions
    const ids = getIds(this._moddle)
    ids.clear()
    if (elementsById) {
      for (const [id, element] of Object.entries(elementsById)) ids.claim(id, element)
    } else {
      claimAll(definitions, ids)
    }
    const eventBus = this.get<any>('eventBus')
    eventBus.fire('import.render.start', { definitions })
    const result = this.get<any>('bpmnImporter').importDefinitions(definitions)
    eventBus.fire('import.render.complete', { error: null, warnings: result.warnings })
    return result
  }

  /** Serialisiert das Diagramm als BPMN-2.0-XML (mit DI). */
  async saveXML(opts: { format?: boolean } = {}): Promise<{ xml: string }> {
    this._assertAlive()
    if (!this._definitions) throw new Error(this.get<any>('translate')('No diagram loaded'))
    const eventBus = this.get<any>('eventBus')
    const definitions = eventBus.fire('saveXML.start', { definitions: this._definitions }) || this._definitions
    const result = await this._moddle.toXML(definitions, { format: !!opts.format, preamble: true })
    const xml = eventBus.fire('saveXML.serialized', { xml: result.xml }) || result.xml
    eventBus.fire('saveXML.done', { xml })
    return { xml }
  }

  /** Erzeugt ein eigenständiges SVG der aktuell angezeigten Ebene. */
  async saveSVG(): Promise<{ svg: string }> {
    this._assertAlive()
    const eventBus = this.get<any>('eventBus')
    eventBus.fire('saveSVG.start')
    const svg = exportSvg(this.get('canvas'), this.get('elementRegistry'))
    eventBus.fire('saveSVG.done', { svg })
    return { svg }
  }

  /** Legt ein leeres Diagramm mit Startereignis an. */
  async createDiagram(): Promise<void> {
    await this.importXML(INITIAL_DIAGRAM)
  }

  /** Aktuelle `bpmn:Definitions` (oder `null`). */
  getDefinitions(): any {
    return this._definitions
  }

  /** Zugriff auf Dienste des diagram-js-Injektors. */
  get<T = unknown>(service: string, strict = true): T {
    return this._diagram.get(service, strict)
  }

  invoke<T = unknown>(fn: (...args: any[]) => T): T {
    return this._diagram.invoke(fn)
  }

  on(event: string, cb: (e: unknown) => void, priority?: number): void
  on(event: string, priority: number, cb: (e: unknown) => void): void
  on(event: string, a: any, b?: any): void {
    const eventBus = this.get<any>('eventBus')
    if (typeof a === 'function') {
      if (typeof b === 'number') eventBus.on(event, b, a)
      else eventBus.on(event, a)
    } else {
      eventBus.on(event, a, b)
    }
  }

  off(event: string, cb: (e: unknown) => void): void {
    this.get<any>('eventBus').off(event, cb)
  }

  /** Entfernt alle Elemente (ohne Definitionen zu verwerfen). */
  clear(): void {
    this._diagram.clear()
  }

  /** Gibt alle Ressourcen frei und entfernt die Oberfläche. */
  destroy(): void {
    if (this._destroyed) return
    this._destroyed = true
    this._diagram.destroy()
    this._container.parentNode?.removeChild(this._container)
  }

  /** Das vom Editor verwaltete Container-Element. */
  get container(): HTMLElement {
    return this._container
  }

  private _assertAlive(): void {
    if (this._destroyed) throw new Error('BpmnEditor wurde bereits zerstört')
  }
}

function toMessage(warning: any): string {
  if (typeof warning === 'string') return warning
  return warning?.message || String(warning)
}

function claimAll(element: any, ids: any, seen = new Set<any>()): void {
  if (!element || typeof element !== 'object' || seen.has(element)) return
  seen.add(element)
  if (element.id && typeof element.$instanceOf === 'function') ids.claim(element.id, element)
  const descriptor = element.$descriptor
  if (!descriptor) return
  for (const property of descriptor.properties || []) {
    if (property.isReference) continue
    const value = element[property.name]
    if (Array.isArray(value)) value.forEach((child) => claimAll(child, ids, seen))
    else if (value && typeof value === 'object') claimAll(value, ids, seen)
  }
}

export { translations }
export default BpmnEditor
