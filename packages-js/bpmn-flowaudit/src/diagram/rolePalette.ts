/**
 * Palette entries „Pool: VB/ZGS/…“ per role of the profile and context pad
 * entries on pools and lanes („Bahn mit Rolle hinzufügen“, „Rolle
 * zuweisen“). Creating a pool sets `flowaudit:akteur` and the role label as
 * name; choosing the role is announced through the event bus
 * (`flowaudit.role.choose`) so the UI can show its own role picker.
 */

import { iconSvg } from '../icons/icons'
import { writeExtensions } from '../model/extensions'
import { rolesFor, type ProfileData } from '../profile/profile'
import type { Role } from '../schema/roles'
import { label } from '../schema/vocabulary'
import type {
  ContextPad,
  ContextPadEntry,
  Create,
  DiagramElement,
  ElementFactory,
  EventBus,
  ModdleFactory,
  Modeling,
  Palette,
  PaletteEntry,
  Translate,
} from './services'
import type { DecorationConfig } from './decorations'

function entryHtml(role: Role): string {
  return `<span class="fa-role-entry" style="color:${role.color.stroke};background:${role.color.fill}" data-role="${role.code}">${iconSvg(role.icon, 20)}</span>`
}

export class RolePaletteProvider {
  static $inject = ['palette', 'contextPad', 'create', 'elementFactory', 'modeling', 'moddle', 'eventBus', 'translate', 'config.flowaudit']

  private profile: ProfileData | null
  private readonly locale: 'de' | 'en'

  constructor(
    palette: Palette,
    contextPad: ContextPad,
    private readonly create: Create,
    private readonly elementFactory: ElementFactory,
    private readonly modeling: Modeling,
    private readonly moddle: ModdleFactory,
    private readonly eventBus: EventBus,
    private readonly translate: Translate,
    config: DecorationConfig & { rolePalette?: boolean } | undefined,
  ) {
    this.profile = config?.profile ?? null
    this.locale = config?.locale ?? 'de'
    if (config?.rolePalette !== false) palette.registerProvider(900, this)
    contextPad.registerProvider(600, this)
  }

  setProfile(profile: ProfileData | null): void {
    this.profile = profile
  }

  roles(): Role[] {
    return rolesFor(this.profile)
  }

  /** Creates a pool shape for a role (for palette and UI buttons). */
  createPool(role: Role): DiagramElement {
    const shape = this.elementFactory.createParticipantShape
      ? this.elementFactory.createParticipantShape({ type: 'bpmn:Participant' })
      : this.elementFactory.createShape({ type: 'bpmn:Participant' })
    shape.businessObject.set('name', label(role.label, this.locale))
    return shape
  }

  /** Starts creating a pool with role; the actor is written after creation. */
  startPool(event: Event, role: Role): void {
    const shape = this.createPool(role)
    const once = (payload: Record<string, unknown>) => {
      const created = (payload.context as { shape?: DiagramElement } | undefined)?.shape
      if (created !== shape) return
      this.eventBus.off('commandStack.shape.create.postExecuted', once)
      this.assignRole(created, role)
    }
    this.eventBus.on('commandStack.shape.create.postExecuted', 500, once)
    this.create.start(event, shape)
  }

  assignRole(element: DiagramElement, role: Role): void {
    writeExtensions(element, { actor: { role: role.code } }, { modeling: this.modeling, moddle: this.moddle })
  }

  getPaletteEntries(): (entries: Record<string, PaletteEntry>) => Record<string, PaletteEntry> {
    return (entries) => {
      const result = { ...entries }
      for (const role of this.roles()) {
        const start = (event: Event) => this.startPool(event, role)
        result[`flowaudit-pool-${role.code}`] = {
          group: 'flowaudit-roles',
          className: `fa-palette-role fa-palette-role-${role.code}`,
          title: this.translate('Create pool: {role}', { role: label(role.label, this.locale) }),
          html: entryHtml(role),
          action: { click: start, dragstart: start },
        }
      }
      return result
    }
  }

  getContextPadEntries(element: DiagramElement): (entries: Record<string, ContextPadEntry>) => Record<string, ContextPadEntry> {
    return (entries) => {
      const type = element.businessObject?.$type
      if (type !== 'bpmn:Participant' && type !== 'bpmn:Lane') return entries
      return {
        ...entries,
        'flowaudit-assign-role': {
          group: 'edit',
          className: 'fa-context-role',
          title: this.translate('Assign role'),
          html: `<span class="fa-context-icon">${iconSvg('role-sonstige', 18)}</span>`,
          action: {
            click: (event: Event) => {
              this.eventBus.fire('flowaudit.role.choose', { element, event, mode: 'assign' })
              return false
            },
          },
        },
        'flowaudit-add-lane-role': {
          group: 'edit',
          className: 'fa-context-lane-role',
          title: this.translate('Add lane with role'),
          html: `<span class="fa-context-icon">${iconSvg('bpmn-lane', 18)}</span>`,
          action: {
            click: (event: Event) => {
              this.eventBus.fire('flowaudit.role.choose', { element, event, mode: 'add-lane' })
              return false
            },
          },
        },
      }
    }
  }

  /** Adds a lane below `element` and assigns the role (used by the UI after choosing). */
  addLaneWithRole(element: DiagramElement, role: Role): DiagramElement | undefined {
    const lane = this.modeling.addLane?.(element, 'bottom')
    if (!lane) return undefined
    this.modeling.updateProperties(lane, { name: label(role.label, this.locale) })
    this.assignRole(lane, role)
    return lane
  }
}

export const rolePaletteModule = {
  __init__: ['flowauditRolePalette'],
  flowauditRolePalette: ['type', RolePaletteProvider],
}
