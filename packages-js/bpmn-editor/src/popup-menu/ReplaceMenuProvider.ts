/**
 * Ersetzen-Menü: Zieltypen als Einträge, Marker (Schleife, Mehrfachinstanz,
 * Kompensation, Sammlung, Mehrfachbeteiligung, unterbrechend) als Kopfleiste.
 */

import type PopupMenu from 'diagram-js/lib/features/popup-menu/PopupMenu'
import type {
  PopupMenuEntries,
  PopupMenuHeaderEntries,
  PopupMenuHeaderEntry,
} from 'diagram-js/lib/features/popup-menu/PopupMenuProvider'
import type { Element } from 'diagram-js/lib/model/Types'

import * as Icons from '../icons/Icons'
import { getFlowOptions, getReplaceOptions } from '../replace/ReplaceOptions'
import type BpmnReplace from '../replace/BpmnReplace'
import type BpmnFactory from '../modeling/BpmnFactory'
import type Modeling from '../modeling/Modeling'
import { getBusinessObject, getLoopType, is, isEventSubProcess, isInterrupting } from '../util/ModelUtil'
import type { Translate } from '../types'

export default class ReplaceMenuProvider {
  static $inject = ['popupMenu', 'bpmnReplace', 'bpmnFactory', 'modeling', 'translate']

  constructor(
    popupMenu: PopupMenu,
    private readonly bpmnReplace: BpmnReplace,
    private readonly bpmnFactory: BpmnFactory,
    private readonly modeling: Modeling,
    private readonly translate: Translate,
  ) {
    popupMenu.registerProvider('bpmn-replace', this)
  }

  getPopupMenuEntries(target: Element): PopupMenuEntries {
    const t = this.translate
    const entries: PopupMenuEntries = {}
    if (target.waypoints) {
      for (const option of getFlowOptions(target)) {
        entries[option.id] = {
          label: t(option.label),
          imageHtml: option.icon,
          action: () => this.bpmnReplace.replaceFlow(target, option.kind),
        }
      }
      return entries
    }
    for (const option of getReplaceOptions(target)) {
      entries[option.id] = {
        label: t(option.label),
        imageHtml: option.icon,
        ...(option.group ? { group: { id: option.group, name: t(groupName(option.group)) } } : {}),
        action: () => this.bpmnReplace.replaceElement(target, option.target),
      }
    }
    return entries
  }

  getPopupMenuHeaderEntries(target: Element): PopupMenuHeaderEntries {
    if (target.waypoints) return []
    const headers: PopupMenuHeaderEntries = []
    if (is(target, 'bpmn:Activity') && !isEventSubProcess(target)) headers.push(...this.loopEntries(target))
    if (is(target, 'bpmn:DataObjectReference')) headers.push(this.collectionEntry(target))
    if (is(target, 'bpmn:Participant')) headers.push(this.multiplicityEntry(target))
    if (this.canToggleInterrupting(target)) headers.push(this.interruptingEntry(target))
    return headers
  }

  private loopEntries(target: Element): PopupMenuHeaderEntry[] {
    const t = this.translate
    const bo = getBusinessObject(target)
    const current = getLoopType(target)
    const toggle = (kind: 'loop' | 'parallel' | 'sequential') => () => {
      if (current === kind) {
        this.modeling.updateProperties(target, { loopCharacteristics: undefined })
        return
      }
      const loop =
        kind === 'loop'
          ? this.bpmnFactory.create('bpmn:StandardLoopCharacteristics')
          : this.bpmnFactory.create('bpmn:MultiInstanceLoopCharacteristics', kind === 'sequential' ? { isSequential: true } : {})
      this.modeling.updateProperties(target, { loopCharacteristics: loop })
    }
    const entries: PopupMenuHeaderEntry[] = [
      { id: 'toggle-loop', title: t('Loop'), className: 'fa-toggle-loop', imageHtml: Icons.toolIcons.loop, active: current === 'loop', action: toggle('loop') },
      {
        id: 'toggle-parallel-mi',
        title: t('Parallel multi-instance'),
        className: 'fa-toggle-parallel-mi',
        imageHtml: Icons.toolIcons.parallelMi,
        active: current === 'parallel',
        action: toggle('parallel'),
      },
      {
        id: 'toggle-sequential-mi',
        title: t('Sequential multi-instance'),
        className: 'fa-toggle-sequential-mi',
        imageHtml: Icons.toolIcons.sequentialMi,
        active: current === 'sequential',
        action: toggle('sequential'),
      },
    ]
    if (!is(target, 'bpmn:SubProcess') || !bo.triggeredByEvent) {
      entries.push({
        id: 'toggle-compensation',
        title: t('Compensation'),
        className: 'fa-toggle-compensation',
        imageHtml: Icons.toolIcons.compensation,
        active: !!bo.isForCompensation,
        action: () => this.modeling.updateProperties(target, { isForCompensation: bo.isForCompensation ? undefined : true }),
      })
    }
    return entries
  }

  private collectionEntry(target: Element): PopupMenuHeaderEntry {
    const dataObject = getBusinessObject(target).dataObjectRef
    return {
      id: 'toggle-is-collection',
      title: this.translate('Collection'),
      className: 'fa-toggle-collection',
      imageHtml: Icons.toolIcons.collection,
      active: !!dataObject?.isCollection,
      action: () => {
        if (dataObject) this.modeling.updateModdleProperties(target, dataObject, { isCollection: !dataObject.isCollection || undefined })
      },
    }
  }

  private multiplicityEntry(target: Element): PopupMenuHeaderEntry {
    const bo = getBusinessObject(target)
    return {
      id: 'toggle-participant-multiplicity',
      title: this.translate('Participant multiplicity'),
      className: 'fa-toggle-multiplicity',
      imageHtml: Icons.toolIcons.collection,
      active: !!bo.participantMultiplicity,
      action: () => {
        const value = bo.participantMultiplicity ? undefined : this.bpmnFactory.create('bpmn:ParticipantMultiplicity')
        this.modeling.updateProperties(target, { participantMultiplicity: value })
      },
    }
  }

  private canToggleInterrupting(target: Element): boolean {
    if (is(target, 'bpmn:BoundaryEvent')) {
      return !['bpmn:ErrorEventDefinition', 'bpmn:CancelEventDefinition', 'bpmn:CompensateEventDefinition'].some((type) =>
        (getBusinessObject(target).eventDefinitions || []).some((definition: { $instanceOf(type: string): boolean }) => definition.$instanceOf(type)),
      )
    }
    return is(target, 'bpmn:StartEvent') && isEventSubProcess(target.parent)
  }

  private interruptingEntry(target: Element): PopupMenuHeaderEntry {
    const interrupting = isInterrupting(target)
    const property = is(target, 'bpmn:BoundaryEvent') ? 'cancelActivity' : 'isInterrupting'
    return {
      id: 'toggle-non-interrupting',
      title: this.translate('Toggle non-interrupting'),
      className: 'fa-toggle-non-interrupting',
      imageHtml: Icons.toolIcons.nonInterrupting,
      active: !interrupting,
      action: () => this.modeling.updateProperties(target, { [property]: interrupting ? false : undefined }),
    }
  }
}

function groupName(group: string): string {
  switch (group) {
    case 'start':
      return 'Start events'
    case 'intermediate':
      return 'Intermediate events'
    case 'end':
      return 'End events'
    case 'boundary':
      return 'Boundary events'
    default:
      return group
  }
}
