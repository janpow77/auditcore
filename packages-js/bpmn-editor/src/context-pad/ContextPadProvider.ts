/**
 * Kontextpad am Element: Anhängen, Ersetzen, Verbinden, Bahnen, Anmerkung,
 * Farbe und Löschen. Bei Mehrfachauswahl: Ausrichten, Farbe, Löschen.
 */

import type ContextPad from 'diagram-js/lib/features/context-pad/ContextPad'
import type { ContextPadEntries, ContextPadEntry } from 'diagram-js/lib/features/context-pad/ContextPadProvider'
import type Connect from 'diagram-js/lib/features/connect/Connect'
import type Create from 'diagram-js/lib/features/create/Create'
import type PopupMenu from 'diagram-js/lib/features/popup-menu/PopupMenu'
import type AutoPlace from 'diagram-js/lib/features/auto-place/AutoPlace'
import type { Element } from 'diagram-js/lib/model/Types'

import * as Icons from '../icons/Icons'
import { getReplaceOptions, getFlowOptions } from '../replace/ReplaceOptions'
import { getChildLanes } from '../modeling/LaneUtil'
import { getBusinessObject, hasEventDefinition, is, isAny, isEventSubProcess, isHorizontal } from '../util/ModelUtil'
import type ElementFactory from '../modeling/ElementFactory'
import type Modeling from '../modeling/Modeling'
import type { BpmnShape, Translate } from '../types'

interface AppendSpec {
  id: string
  title: string
  icon: string
  attrs: Record<string, unknown>
}

const APPEND_DEFAULT: AppendSpec[] = [
  { id: 'append.end-event', title: 'Append end event', icon: Icons.eventIcon('end'), attrs: { type: 'bpmn:EndEvent' } },
  { id: 'append.gateway', title: 'Append gateway', icon: Icons.gatewayIcon('exclusive'), attrs: { type: 'bpmn:ExclusiveGateway' } },
  { id: 'append.append-task', title: 'Append task', icon: Icons.taskIcon('task'), attrs: { type: 'bpmn:Task' } },
  {
    id: 'append.intermediate-event',
    title: 'Append intermediate/boundary event',
    icon: Icons.eventIcon('intermediate-throw'),
    attrs: { type: 'bpmn:IntermediateThrowEvent' },
  },
]

const APPEND_EVENT_BASED: AppendSpec[] = [
  { id: 'append.receive-task', title: 'Append receive task', icon: Icons.taskIcon('receive'), attrs: { type: 'bpmn:ReceiveTask' } },
  {
    id: 'append.message-intermediate-event',
    title: 'Append message intermediate catch event',
    icon: Icons.eventIcon('intermediate-catch', 'message'),
    attrs: { type: 'bpmn:IntermediateCatchEvent', eventDefinitionType: 'bpmn:MessageEventDefinition' },
  },
  {
    id: 'append.timer-intermediate-event',
    title: 'Append timer intermediate catch event',
    icon: Icons.eventIcon('intermediate-catch', 'timer'),
    attrs: { type: 'bpmn:IntermediateCatchEvent', eventDefinitionType: 'bpmn:TimerEventDefinition' },
  },
  {
    id: 'append.condition-intermediate-event',
    title: 'Append conditional intermediate catch event',
    icon: Icons.eventIcon('intermediate-catch', 'conditional'),
    attrs: { type: 'bpmn:IntermediateCatchEvent', eventDefinitionType: 'bpmn:ConditionalEventDefinition' },
  },
  {
    id: 'append.signal-intermediate-event',
    title: 'Append signal intermediate catch event',
    icon: Icons.eventIcon('intermediate-catch', 'signal'),
    attrs: { type: 'bpmn:IntermediateCatchEvent', eventDefinitionType: 'bpmn:SignalEventDefinition' },
  },
]

const APPEND_COMPENSATION: AppendSpec = {
  id: 'append.compensation-activity',
  title: 'Append compensation activity',
  icon: Icons.taskIcon('task'),
  attrs: { type: 'bpmn:Task', isForCompensation: true },
}

function html(icon: string): string {
  return `<div class="entry" draggable="true">${icon}</div>`
}

function canAppendFlowNode(element: Element): boolean {
  if (!is(element, 'bpmn:FlowNode') || is(element, 'bpmn:EndEvent') || isEventSubProcess(element)) return false
  if (getBusinessObject(element).isForCompensation) return false
  if (is(element, 'bpmn:IntermediateThrowEvent') && hasEventDefinition(element, 'bpmn:LinkEventDefinition')) return false
  return !(is(element, 'bpmn:BoundaryEvent') && hasEventDefinition(element, 'bpmn:CompensateEventDefinition'))
}

export default class ContextPadProvider {
  static $inject = [
    'contextPad',
    'modeling',
    'elementFactory',
    'connect',
    'create',
    'popupMenu',
    'autoPlace',
    'translate',
  ]

  constructor(
    private readonly contextPad: ContextPad,
    private readonly modeling: Modeling,
    private readonly elementFactory: ElementFactory,
    private readonly connect: Connect,
    private readonly create: Create,
    private readonly popupMenu: PopupMenu,
    private readonly autoPlace: AutoPlace,
    private readonly translate: Translate,
  ) {
    contextPad.registerProvider(this)
  }

  getContextPadEntries(element: Element): ContextPadEntries {
    if (element.labelTarget) return {}
    const entries: ContextPadEntries = {}
    this.addAppendEntries(element, entries)
    this.addLaneEntries(element, entries)
    this.addReplaceEntry(element, entries)
    this.addConnectEntries(element, entries)
    this.addAnnotationEntry(element, entries)
    this.addColorEntry(element, entries)
    this.addDeleteEntry(element, entries)
    return entries
  }

  getMultiElementContextPadEntries(elements: Element[]): ContextPadEntries {
    const t = this.translate
    const shapes = elements.filter((element) => !element.labelTarget)
    return {
      'align-elements': {
        group: 'align-elements',
        title: t('Align elements'),
        html: html(Icons.toolIcons.alignLeft),
        className: 'fa-context-align',
        action: { click: (event: Event) => this.openPopup(shapes, 'bpmn-align', event) },
      },
      'set-color': this.colorEntry(shapes),
      delete: {
        group: 'edit',
        title: t('Delete'),
        html: html(Icons.toolIcons.delete),
        className: 'fa-context-delete',
        action: { click: () => this.modeling.removeElements(shapes.slice()) },
      },
    }
  }

  // -------------------------------------------------------------------------

  private appendEntry(element: Element, spec: AppendSpec): ContextPadEntry {
    const start = (event: Event) => {
      const shape = this.elementFactory.createShape({ ...spec.attrs })
      this.create.start(event, shape, { source: element })
    }
    const append = () => {
      const shape = this.elementFactory.createShape({ ...spec.attrs })
      this.autoPlace.append(element as BpmnShape, shape)
    }
    return {
      group: 'model',
      title: this.translate(spec.title),
      html: html(spec.icon),
      className: `fa-context-${spec.id.replace('append.', 'append-')}`,
      action: { dragstart: start, click: append },
    }
  }

  private addAppendEntries(element: Element, entries: ContextPadEntries): void {
    if (!canAppendFlowNode(element)) {
      if (is(element, 'bpmn:BoundaryEvent') && hasEventDefinition(element, 'bpmn:CompensateEventDefinition')) {
        entries[APPEND_COMPENSATION.id] = this.appendEntry(element, APPEND_COMPENSATION)
      }
      return
    }
    const specs = is(element, 'bpmn:EventBasedGateway') ? APPEND_EVENT_BASED : APPEND_DEFAULT
    for (const spec of specs) entries[spec.id] = this.appendEntry(element, spec)
  }

  private addLaneEntries(element: Element, entries: ContextPadEntries): void {
    if (!isAny(element, ['bpmn:Participant', 'bpmn:Lane'])) return
    if (is(element, 'bpmn:Participant') && !getBusinessObject(element).processRef) return
    const t = this.translate
    const horizontal = isHorizontal(element)
    const shape = element as BpmnShape
    entries['lane-insert-above'] = {
      group: 'lane-insert-above',
      title: t(horizontal ? 'Add lane above' : 'Add lane to the left'),
      html: html(Icons.laneIcon('above')),
      className: 'fa-context-lane-above',
      action: { click: () => this.modeling.addLane(shape, horizontal ? 'top' : 'left') },
    }
    if (getChildLanes(shape).length === 0) {
      entries['lane-divide-two'] = {
        group: 'lane-divide',
        title: t('Divide into two lanes'),
        html: html(Icons.laneIcon('divide-two')),
        className: 'fa-context-lane-divide-two',
        action: { click: () => this.modeling.splitLane(shape, 2) },
      }
      entries['lane-divide-three'] = {
        group: 'lane-divide',
        title: t('Divide into three lanes'),
        html: html(Icons.laneIcon('divide-three')),
        className: 'fa-context-lane-divide-three',
        action: { click: () => this.modeling.splitLane(shape, 3) },
      }
    }
    entries['lane-insert-below'] = {
      group: 'lane-insert-below',
      title: t(horizontal ? 'Add lane below' : 'Add lane to the right'),
      html: html(Icons.laneIcon('below')),
      className: 'fa-context-lane-below',
      action: { click: () => this.modeling.addLane(shape, horizontal ? 'bottom' : 'right') },
    }
  }

  private addReplaceEntry(element: Element, entries: ContextPadEntries): void {
    const hasOptions = element.waypoints ? getFlowOptions(element).length > 0 : getReplaceOptions(element).length > 0
    if (!hasOptions) return
    entries.replace = {
      group: 'edit',
      title: this.translate('Change element'),
      html: html(Icons.toolIcons.replace),
      className: 'fa-context-replace',
      action: { click: (event: Event) => this.openPopup(element, 'bpmn-replace', event) },
    }
  }

  private addConnectEntries(element: Element, entries: ContextPadEntries): void {
    if (element.waypoints) return
    if (!isAny(element, ['bpmn:FlowNode', 'bpmn:InteractionNode', 'bpmn:DataObjectReference', 'bpmn:DataStoreReference', 'bpmn:TextAnnotation'])) return
    const start = (event: Event) => this.connect.start(event as MouseEvent, element as BpmnShape, undefined as never)
    entries.connect = {
      group: 'connect',
      title: this.translate(is(element, 'bpmn:TextAnnotation') ? 'Connect using association' : 'Connect to other element'),
      html: html(Icons.toolIcons.connect),
      className: 'fa-context-connect',
      action: { click: start, dragstart: start },
    }
  }

  private addAnnotationEntry(element: Element, entries: ContextPadEntries): void {
    if (element.waypoints || is(element, 'bpmn:TextAnnotation') || is(element, 'bpmn:Group') || !element.parent) return
    entries['append.text-annotation'] = this.appendEntry(element, {
      id: 'append.text-annotation',
      title: 'Add text annotation',
      icon: Icons.textAnnotationIcon(),
      attrs: { type: 'bpmn:TextAnnotation' },
    })
    const entry = entries['append.text-annotation']
    if (entry) entry.group = 'artifact'
  }

  private colorEntry(elements: Element[]): ContextPadEntry {
    return {
      group: 'edit',
      title: this.translate('Set color'),
      html: html(Icons.toolIcons.color),
      className: 'fa-context-color',
      action: { click: (event: Event) => this.openPopup(elements, 'bpmn-color', event) },
    }
  }

  private addColorEntry(element: Element, entries: ContextPadEntries): void {
    if (!element.parent) return
    entries['set-color'] = this.colorEntry([element])
  }

  private addDeleteEntry(element: Element, entries: ContextPadEntries): void {
    entries.delete = {
      group: 'edit',
      title: this.translate('Delete'),
      html: html(Icons.toolIcons.delete),
      className: 'fa-context-delete',
      action: {
        click: () => {
          if (element.waypoints) this.modeling.removeConnection(element as never)
          else this.modeling.removeElements([element])
        },
      },
    }
  }

  private openPopup(target: Element | Element[], providerId: string, event: Event): void {
    const position = this.popupPosition(target, event)
    this.popupMenu.open(target as never, providerId, position, {
      title: this.translate(providerId === 'bpmn-replace' ? 'Change element' : providerId === 'bpmn-color' ? 'Set color' : 'Align elements'),
      width: 320,
    })
  }

  private popupPosition(target: Element | Element[], event: Event): { x: number; y: number; cursor?: { x: number; y: number } } {
    const pad = this.contextPad.getPad(target as never).html as HTMLElement
    const rect = pad.getBoundingClientRect()
    const mouse = event as MouseEvent
    return {
      x: rect.left,
      y: rect.bottom + 5,
      cursor: { x: mouse.clientX ?? rect.left, y: mouse.clientY ?? rect.bottom },
    }
  }
}
