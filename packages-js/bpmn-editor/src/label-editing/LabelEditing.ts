/**
 * Direktes Bearbeiten von Beschriftungen (eigene Umsetzung).
 *
 * Ein bearbeitbares Feld (`contenteditable`) wird über die Beschriftung
 * gelegt. Enter übernimmt, Umschalt+Enter fügt einen Zeilenumbruch ein,
 * Escape bricht ab; Verlassen des Feldes übernimmt ebenfalls.
 */

import type { Element } from 'diagram-js/lib/model/Types'

import { getExternalLabelMid, getLabel, isAnyLabelEditable, isLabelExternal } from '../util/LabelUtil'
import { is, isExpanded, isHorizontal } from '../util/ModelUtil'
import { LANE_BAND } from '../modeling/LaneUtil'
import type Modeling from '../modeling/Modeling'
import type { Bounds, Canvas, EventBus, Translate } from '../types'

type Editable = Element & { x?: number; y?: number; width?: number; height?: number }

const EXTERNAL_BOX = { width: 120, height: 40 }

/** Ermittelt den Bearbeitungsbereich (Diagrammkoordinaten) eines Elements. */
export function getEditingBounds(element: Editable): Bounds & { align: 'center' | 'left' } {
  const target = (element.labelTarget as Editable | undefined) || element
  if (element.labelTarget) {
    return { x: element.x ?? 0, y: element.y ?? 0, width: Math.max(element.width ?? 0, EXTERNAL_BOX.width), height: Math.max(element.height ?? 0, 20), align: 'center' }
  }
  if (isLabelExternal(target)) {
    if (target.label) return getEditingBounds(target.label as Editable)
    if (target.waypoints) {
      const mid = getExternalLabelMid(target)
      return { x: mid.x - EXTERNAL_BOX.width / 2, y: mid.y - 10, ...EXTERNAL_BOX, align: 'center' }
    }
    if (is(target, 'bpmn:Group')) {
      return { x: target.x ?? 0, y: target.y ?? 0, width: target.width ?? 0, height: 30, align: 'center' }
    }
    const mid = getExternalLabelMid(target)
    return { x: mid.x - EXTERNAL_BOX.width / 2, y: mid.y - 10, ...EXTERNAL_BOX, align: 'center' }
  }
  const x = target.x ?? 0
  const y = target.y ?? 0
  const width = target.width ?? 0
  const height = target.height ?? 0
  if (is(target, 'bpmn:Participant') || is(target, 'bpmn:Lane')) {
    if (!is(target, 'bpmn:Lane') && !isExpanded(target)) return { x, y, width, height, align: 'center' }
    return isHorizontal(target)
      ? { x, y, width: Math.min(Math.max(height, 150), 300), height: LANE_BAND * 2, align: 'left' }
      : { x, y, width, height: LANE_BAND, align: 'center' }
  }
  if (is(target, 'bpmn:SubProcess') && isExpanded(target)) return { x, y, width, height: 36, align: 'left' }
  if (is(target, 'bpmn:TextAnnotation')) return { x, y, width, height, align: 'left' }
  return { x, y, width, height, align: 'center' }
}

export default class LabelEditing {
  static $inject = ['eventBus', 'canvas', 'modeling', 'translate']

  private box: HTMLDivElement | null = null
  private element: Element | null = null
  private initialText = ''

  constructor(
    private readonly eventBus: EventBus,
    private readonly canvas: Canvas,
    private readonly modeling: Modeling,
    private readonly translate: Translate,
  ) {
    eventBus.on('element.dblclick', (event: { element: Element }) => this.activate(event.element))
    eventBus.on(['element.mousedown', 'drag.init', 'canvas.viewbox.changing', 'popupMenu.open', 'diagram.clear'], () => {
      if (this.isActive()) this.complete()
    })
    eventBus.on('create.end', 500, (event: { elements?: Element[]; context?: { canExecute?: boolean; shape?: Element } }) => {
      const shape = event.context?.shape || (event.elements || [])[0]
      if (shape && event.context?.canExecute !== false && this.shouldActivateOnCreate(shape)) this.activate(shape)
    })
    eventBus.on('autoPlace.end', 500, (event: { shape: Element }) => {
      if (this.shouldActivateOnCreate(event.shape)) this.activate(event.shape)
    })
    eventBus.on('diagram.destroy', () => this.removeBox())
  }

  private shouldActivateOnCreate(element: Element): boolean {
    return (
      !!element &&
      !!element.parent &&
      (is(element, 'bpmn:Task') ||
        is(element, 'bpmn:CallActivity') ||
        is(element, 'bpmn:TextAnnotation') ||
        (is(element, 'bpmn:SubProcess') && !isExpanded(element)) ||
        (is(element, 'bpmn:Participant') && isExpanded(element)))
    )
  }

  isActive(): boolean {
    return !!this.box
  }

  getValue(): string {
    return this.box ? readText(this.box) : ''
  }

  /** Öffnet das Eingabefeld für das Element (bzw. sein Beschriftungsziel). */
  activate(element: Element): boolean {
    if (this.isActive()) this.complete()
    const target = (element?.labelTarget as Element | undefined) || element
    if (!target || !target.parent || !isAnyLabelEditable(target)) return false
    this.element = target
    this.initialText = getLabel(target) || ''
    this.box = this.createBox(element)
    this.eventBus.fire('directEditing.activate', { active: { element: target } })
    return true
  }

  complete(): void {
    const element = this.element
    const box = this.box
    if (!element || !box) return
    const text = readText(box)
    this.removeBox()
    if (text !== this.initialText) {
      this.modeling.updateLabel(element, text.trim().length ? text : null)
    }
    this.eventBus.fire('directEditing.complete', { active: { element } })
  }

  cancel(): void {
    if (!this.element) return
    const element = this.element
    this.removeBox()
    this.eventBus.fire('directEditing.cancel', { active: { element } })
  }

  private createBox(element: Element): HTMLDivElement {
    const bounds = getEditingBounds(element as Editable)
    const viewbox = this.canvas.viewbox()
    const scale = viewbox.scale || 1
    const box = document.createElement('div')
    box.className = 'fa-label-editor'
    box.contentEditable = 'true'
    box.setAttribute('role', 'textbox')
    box.setAttribute('aria-multiline', 'true')
    box.setAttribute('aria-label', this.translate('Edit label'))
    box.spellcheck = true
    Object.assign(box.style, {
      position: 'absolute',
      left: `${(bounds.x - viewbox.x) * scale}px`,
      top: `${(bounds.y - viewbox.y) * scale}px`,
      width: `${bounds.width * scale}px`,
      minHeight: `${bounds.height * scale}px`,
      fontSize: `${12 * scale}px`,
      textAlign: bounds.align,
      zIndex: '10',
    })
    box.innerText = this.initialText
    box.textContent = this.initialText
    box.addEventListener('keydown', (event) => this.onKeyDown(event))
    box.addEventListener('blur', () => this.isActive() && this.complete())
    this.canvas.getContainer().appendChild(box)
    try {
      box.focus()
      const selection = window.getSelection && window.getSelection()
      if (selection && document.createRange) {
        const range = document.createRange()
        range.selectNodeContents(box)
        selection.removeAllRanges()
        selection.addRange(range)
      }
    } catch {
      // Fokus ist in Testumgebungen nicht immer möglich.
    }
    return box
  }

  private onKeyDown(event: KeyboardEvent): void {
    event.stopPropagation()
    if (event.key === 'Escape') {
      event.preventDefault()
      this.cancel()
    } else if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      this.complete()
    }
  }

  private removeBox(): void {
    if (this.box && this.box.parentNode) this.box.parentNode.removeChild(this.box)
    this.box = null
    this.element = null
  }
}

function readText(box: HTMLElement): string {
  const raw = typeof box.innerText === 'string' && box.innerText.length ? box.innerText : box.textContent || ''
  return raw.replace(/ /g, ' ').replace(/\n$/, '')
}
