/**
 * Kopieren und Einfügen von BPMN-Elementen – auch zwischen zwei Editoren
 * (gemeinsame Zwischenablage). Semantische Objekte werden beim Einfügen
 * tief kopiert; Verweise zwischen kopierten Elementen werden umgesetzt,
 * Verweise ins Leere entfallen.
 */

import type { Element } from 'diagram-js/lib/model/Types'

import { cloneModdleElement, type CopyOptions } from '../util/ModdleCopy'
import { getBusinessObject, getDefinitions, getDi, is, isAny } from '../util/ModelUtil'
import type BpmnFactory from '../modeling/BpmnFactory'
import type { EventBus, Moddle, ModdleElement } from '../types'

/** Gemeinsame Zwischenablage aller Editor-Instanzen einer Seite. */
export class SharedClipboard {
  private data: unknown = undefined

  get(): unknown {
    return this.data
  }

  set(data: unknown): void {
    this.data = data
  }

  clear(): unknown {
    const data = this.data
    this.data = undefined
    return data
  }

  isEmpty(): boolean {
    return this.data === undefined
  }
}

export const sharedClipboard = new SharedClipboard()

/** Beim Einfügen nicht zu kopierende Eigenschaften (Kinder kommen als eigene Elemente). */
const CHILD_PROPERTIES = ['flowElements', 'artifacts', 'laneSets', 'flowNodeRef', 'ioSpecification', 'childLaneSet', 'categoryValueRef', 'dataObjectRef', 'processRef']

const COLOR_KEYS: [string, 'fill' | 'stroke'][] = [
  ['bioc:fill', 'fill'],
  ['bioc:stroke', 'stroke'],
  ['color:background-color', 'fill'],
  ['color:border-color', 'stroke'],
]

/**
 * Fremde Attribute (z. B. `flowaudit:marke`) brauchen im Zieldiagramm die
 * Namensraum-Erklärung (`xmlns:flowaudit`), sonst gehen sie beim Export verloren.
 */
function copyNamespaceDeclarations(element: ModdleElement, source: ModdleElement | undefined, target: ModdleElement | undefined): void {
  if (!source || !target) return
  for (const key of Object.keys(element.$attrs || {})) {
    const prefix = key.includes(':') ? key.split(':')[0] : undefined
    const declaration = prefix && prefix !== 'xmlns' ? `xmlns:${prefix}` : undefined
    const uri = declaration ? source.$attrs[declaration] : undefined
    if (declaration && uri && !target.$attrs[declaration]) target.$attrs[declaration] = uri
  }
}

interface Descriptor {
  id: string
  labelTarget?: string
  businessObject?: ModdleElement
  di?: Record<string, unknown> | ModdleElement
  colors?: { fill?: string; stroke?: string }
  type?: string
  oldBusinessObject?: ModdleElement
  diAttrs?: Record<string, unknown>
  [key: string]: unknown
}

export default class BpmnCopyPaste {
  static $inject = ['eventBus', 'moddle', 'bpmnFactory', 'canvas']

  private boMap = new Map<ModdleElement, ModdleElement>()

  constructor(
    eventBus: EventBus,
    private readonly moddle: Moddle,
    private readonly bpmnFactory: BpmnFactory,
    private readonly canvas: { getRootElement(): Element },
  ) {
    eventBus.on('copyPaste.copyElement', 500, (context: { descriptor: Descriptor; element: Element }) =>
      this.copyElement(context.descriptor, context.element),
    )
    eventBus.on('copyPaste.pasteElements', 2000, () => {
      this.boMap = new Map()
    })
    eventBus.on('copyPaste.pasteElement', 500, (context: { cache: Record<string, Element>; descriptor: Descriptor }) =>
      this.pasteElement(context.cache, context.descriptor),
    )
    eventBus.on('commandStack.elements.create.preExecute', 2000, () => this.resolvePending())
    eventBus.on('copyPaste.canCopyElements', (context: { elements: Element[] }) =>
      context.elements.filter((element) => !!element.parent && !(is(element, 'bpmn:Lane') && !context.elements.includes(element.parent))),
    )
  }

  private copyElement(descriptor: Descriptor, element: Element): void {
    const bo = getBusinessObject(element)
    descriptor.type = element.type || bo.$type
    if (element.labelTarget) return
    descriptor.oldBusinessObject = bo
    const di = getDi(element)
    if (!di) return
    const colors: { fill?: string; stroke?: string } = {}
    for (const [key, target] of COLOR_KEYS) {
      const value = di.get(key) as string | undefined
      if (value && !colors[target]) colors[target] = value
    }
    descriptor.colors = colors
    const diAttrs: Record<string, unknown> = {}
    for (const key of ['isExpanded', 'isHorizontal', 'isMarkerVisible']) {
      const value: unknown = di.get(key)
      if (value !== undefined) diAttrs[key] = value
    }
    descriptor.diAttrs = diAttrs
  }

  private pasteElement(cache: Record<string, Element>, descriptor: Descriptor): void {
    if (descriptor.labelTarget) {
      const target = cache[descriptor.labelTarget]
      if (target) {
        descriptor.businessObject = target.businessObject
        descriptor.di = target.di
      }
      delete descriptor.oldBusinessObject
      return
    }
    const oldBo = descriptor.oldBusinessObject
    if (!oldBo) return
    const newBo = this.cloneBusinessObject(oldBo)
    descriptor.businessObject = newBo
    descriptor.type = newBo.$type
    descriptor.di = { ...(descriptor.diAttrs || {}) }
    if (descriptor.colors && (descriptor.colors.fill || descriptor.colors.stroke)) {
      descriptor.colors = { ...descriptor.colors }
    } else {
      delete descriptor.colors
    }
    delete descriptor.oldBusinessObject
    delete descriptor.diAttrs
  }

  private cloneBusinessObject(oldBo: ModdleElement): ModdleElement {
    const targetDefinitions = getDefinitions(getBusinessObject(this.canvas.getRootElement()))
    const sameDiagram = getDefinitions(oldBo) === targetDefinitions
    const options: CopyOptions = {
      exclude: CHILD_PROPERTIES,
      mapReference: (value, property) => this.mapReference(value, property, sameDiagram),
      onCreate: (copy, original) => {
        if (copy.$descriptor?.propertiesByName?.id && original.id) this.bpmnFactory._ensureId(copy)
        if (!sameDiagram) copyNamespaceDeclarations(original, getDefinitions(oldBo), targetDefinitions)
      },
    }
    const newBo = cloneModdleElement(this.moddle, oldBo, options)
    this.boMap.set(oldBo, newBo)
    this.cloneOwnedReferences(oldBo, newBo)
    return newBo
  }

  /** Mitkopierte Objekte, die per Verweis gehalten werden (Datenobjekt, Kategoriewert, Prozess). */
  private cloneOwnedReferences(oldBo: ModdleElement, newBo: ModdleElement): void {
    if (is(oldBo, 'bpmn:DataObjectReference') && oldBo.dataObjectRef) {
      newBo.dataObjectRef = cloneModdleElement(this.moddle, oldBo.dataObjectRef, { onCreate: (copy) => this.bpmnFactory._ensureId(copy) })
    } else if (is(oldBo, 'bpmn:DataObjectReference')) {
      newBo.dataObjectRef = this.bpmnFactory.create('bpmn:DataObject')
    }
    if (is(oldBo, 'bpmn:Group')) {
      const value = this.bpmnFactory.create('bpmn:CategoryValue', { value: oldBo.categoryValueRef?.value })
      const category = this.bpmnFactory.create('bpmn:Category', { categoryValue: [value] })
      value.$parent = category
      newBo.categoryValueRef = value
    }
    if (is(oldBo, 'bpmn:Participant') && oldBo.processRef) {
      const process = cloneModdleElement(this.moddle, oldBo.processRef, {
        exclude: CHILD_PROPERTIES,
        onCreate: (copy) => this.bpmnFactory._ensureId(copy),
      })
      newBo.processRef = process
      this.boMap.set(oldBo.processRef, process)
    }
  }

  private mapReference(value: ModdleElement, property: string, sameDiagram: boolean): ModdleElement | undefined {
    const mapped = this.boMap.get(value)
    if (mapped) return mapped
    if (property === 'default' || property === 'attachedToRef' || property === 'sourceRef' || property === 'targetRef') {
      // Wird nach dem Anlegen der Kopien aufgelöst.
      return undefined
    }
    if (isAny(value, ['bpmn:RootElement']) && sameDiagram) return value
    return undefined
  }

  private resolvePending(): void {
    for (const [oldBo, newBo] of this.boMap) {
      if (oldBo.default) {
        const mapped = this.boMap.get(oldBo.default)
        if (mapped) newBo.default = mapped
      }
    }
  }
}
