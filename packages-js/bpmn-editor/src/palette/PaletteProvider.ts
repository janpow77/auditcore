/**
 * Palette: Werkzeuge und Grundelemente zum Anlegen per Ziehen oder Klick.
 */

import type Palette from 'diagram-js/lib/features/palette/Palette'
import type { PaletteEntries, PaletteEntry } from 'diagram-js/lib/features/palette/PaletteProvider'
import type Create from 'diagram-js/lib/features/create/Create'
import type SpaceTool from 'diagram-js/lib/features/space-tool/SpaceTool'
import type LassoTool from 'diagram-js/lib/features/lasso-tool/LassoTool'
import type HandTool from 'diagram-js/lib/features/hand-tool/HandTool'
import type GlobalConnect from 'diagram-js/lib/features/global-connect/GlobalConnect'

import * as Icons from '../icons/Icons'
import type ElementFactory from '../modeling/ElementFactory'
import type { Translate } from '../types'

interface CreateSpec {
  id: string
  group: string
  title: string
  icon: string
  attrs: Record<string, unknown>
}

/** Deklarative Tabelle der anlegbaren Elemente. */
const CREATE_ENTRIES: CreateSpec[] = [
  { id: 'create.start-event', group: 'event', title: 'Create start event', icon: Icons.eventIcon('start'), attrs: { type: 'bpmn:StartEvent' } },
  {
    id: 'create.intermediate-event',
    group: 'event',
    title: 'Create intermediate/boundary event',
    icon: Icons.eventIcon('intermediate-throw'),
    attrs: { type: 'bpmn:IntermediateThrowEvent' },
  },
  { id: 'create.end-event', group: 'event', title: 'Create end event', icon: Icons.eventIcon('end'), attrs: { type: 'bpmn:EndEvent' } },
  { id: 'create.exclusive-gateway', group: 'gateway', title: 'Create gateway', icon: Icons.gatewayIcon('exclusive'), attrs: { type: 'bpmn:ExclusiveGateway' } },
  { id: 'create.task', group: 'activity', title: 'Create task', icon: Icons.taskIcon('task'), attrs: { type: 'bpmn:Task' } },
  {
    id: 'create.subprocess-expanded',
    group: 'activity',
    title: 'Create expanded sub-process',
    icon: Icons.subProcessIcon('expanded'),
    attrs: { type: 'bpmn:SubProcess', isExpanded: true },
  },
  {
    id: 'create.data-object',
    group: 'data-object',
    title: 'Create data object reference',
    icon: Icons.dataObjectIcon(),
    attrs: { type: 'bpmn:DataObjectReference' },
  },
  {
    id: 'create.data-store',
    group: 'data-store',
    title: 'Create data store reference',
    icon: Icons.dataStoreIcon(),
    attrs: { type: 'bpmn:DataStoreReference' },
  },
  {
    id: 'create.participant-expanded',
    group: 'collaboration',
    title: 'Create pool/participant',
    icon: Icons.participantIcon('expanded'),
    attrs: { type: 'bpmn:Participant', isExpanded: true },
  },
  { id: 'create.group', group: 'artifact', title: 'Create group', icon: Icons.groupIcon(), attrs: { type: 'bpmn:Group' } },
  {
    id: 'create.text-annotation',
    group: 'artifact',
    title: 'Create text annotation',
    icon: Icons.textAnnotationIcon(),
    attrs: { type: 'bpmn:TextAnnotation' },
  },
]

export function entryHtml(icon: string): string {
  return `<div class="entry" draggable="true">${icon}</div>`
}

export default class PaletteProvider {
  static $inject = ['palette', 'create', 'elementFactory', 'spaceTool', 'lassoTool', 'handTool', 'globalConnect', 'translate']

  constructor(
    palette: Palette,
    private readonly create: Create,
    private readonly elementFactory: ElementFactory,
    private readonly spaceTool: SpaceTool,
    private readonly lassoTool: LassoTool,
    private readonly handTool: HandTool,
    private readonly globalConnect: GlobalConnect,
    private readonly translate: Translate,
  ) {
    palette.registerProvider(this)
  }

  getPaletteEntries(): PaletteEntries {
    const t = this.translate
    const entries: PaletteEntries = {
      'hand-tool': this.tool('tools', t('Activate hand tool'), Icons.toolIcons.hand, (event) => this.handTool.activateHand(event)),
      'lasso-tool': this.tool('tools', t('Activate lasso tool'), Icons.toolIcons.lasso, (event) =>
        this.lassoTool.activateSelection(event as MouseEvent),
      ),
      'space-tool': this.tool('tools', t('Activate create/remove space tool'), Icons.toolIcons.space, (event) =>
        this.spaceTool.activateSelection(event as MouseEvent, false, false),
      ),
      'global-connect-tool': this.tool('tools', t('Activate global connect tool'), Icons.toolIcons.connect, (event) =>
        this.globalConnect.start(event, false),
      ),
      'tool-separator': { group: 'tools', separator: true, action: {} },
    }
    for (const spec of CREATE_ENTRIES) {
      entries[spec.id] = this.createEntry(spec)
    }
    return entries
  }

  private tool(group: string, title: string, icon: string, run: (event: Event) => void): PaletteEntry {
    return {
      group,
      title,
      html: entryHtml(icon),
      className: 'fa-palette-tool',
      action: { click: (event: Event) => run(event) },
    }
  }

  private createEntry(spec: CreateSpec): PaletteEntry {
    const start = (event: Event) => {
      const shape = this.elementFactory.createShape({ ...spec.attrs })
      this.create.start(event, shape)
    }
    return {
      group: spec.group,
      title: this.translate(spec.title),
      html: entryHtml(spec.icon),
      className: `fa-palette-${spec.id.replace('create.', '')}`,
      action: { dragstart: start, click: start },
    }
  }
}
