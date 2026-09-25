/**
 * Domain decorations drawn into the shapes' visuals: role colour band and
 * role icon in the pool/lane header, marker badges and the audit reference
 * plaque („KA 2 · BK 2.3“). Because they live inside `.djs-visual`, they
 * appear in the SVG export as well.
 *
 * Drawing happens after the core renderer (`shape.added`/`shape.changed`
 * at low priority), so this module does not depend on renderer internals.
 */

import { iconElement } from '../icons/icons'
import { readExtensions } from '../model/extensions'
import { roleOf, type ProfileData } from '../profile/profile'
import type { Role } from '../schema/roles'
import type { AuditReference, Marker } from '../schema/types'
import { MARKER_COLORS, MARKER_TYPES, label } from '../schema/vocabulary'
import type { Canvas, DiagramElement, ElementRegistry, EventBus, EventCallback } from './services'

const SVG = 'http://www.w3.org/2000/svg'
const HEADER_BAND = 30
const BADGE_RADIUS = 9
const MAX_BADGES = 4
const SMALL_SHAPES = /Event$|Gateway$/

export interface DecorationVisibility {
  actors: boolean
  markers: boolean
  auditReferences: boolean
}

export interface DecorationConfig {
  profile?: ProfileData | null
  visibility?: Partial<DecorationVisibility>
  locale?: 'de' | 'en'
}

function isContainer(element: DiagramElement): boolean {
  const type = element.businessObject?.$type
  return type === 'bpmn:Participant' || type === 'bpmn:Lane'
}

function create<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number>): SVGElementTagNameMap[K] {
  const node = document.createElementNS(SVG, tag)
  for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, String(value))
  return node
}

export function auditReferenceText(references: AuditReference[]): string {
  return references
    .map((ref) => [ref.keyRequirement ? `KA ${ref.keyRequirement}` : '', ref.assessmentCriterion ? `BK ${ref.assessmentCriterion}` : ''].filter(Boolean).join(' · '))
    .filter(Boolean)
    .join(', ')
}

export class FlowauditDecorations {
  static $inject = ['eventBus', 'elementRegistry', 'canvas', 'config.flowaudit']

  private visibility: DecorationVisibility
  private profile: ProfileData | null
  private locale: 'de' | 'en'

  constructor(
    eventBus: EventBus,
    private readonly elementRegistry: ElementRegistry,
    private readonly canvas: Canvas,
    config: DecorationConfig | undefined,
  ) {
    this.visibility = { actors: true, markers: true, auditReferences: true, ...(config?.visibility ?? {}) }
    this.profile = config?.profile ?? null
    this.locale = config?.locale ?? 'de'
    const redraw: EventCallback = (event) => {
      const element = event.element as DiagramElement | undefined
      const gfx = event.gfx as SVGElement | undefined
      if (element && gfx) this.decorate(element, gfx)
    }
    eventBus.on(['shape.added', 'shape.changed'], 250, redraw)
  }

  setVisibility(visibility: Partial<DecorationVisibility>): void {
    this.visibility = { ...this.visibility, ...visibility }
    this.refresh()
  }

  getVisibility(): DecorationVisibility {
    return { ...this.visibility }
  }

  setProfile(profile: ProfileData | null): void {
    this.profile = profile
    this.refresh()
  }

  refresh(): void {
    for (const element of this.elementRegistry.getAll()) {
      const gfx = this.elementRegistry.getGraphics(element)
      if (gfx && !element.waypoints) this.decorate(element, gfx)
    }
  }

  private decorate(element: DiagramElement, gfx: SVGElement): void {
    const visual = gfx.querySelector('.djs-visual')
    if (!visual || element.labelTarget || element.waypoints || element === this.canvas.getRootElement()) return
    visual.querySelectorAll(':scope > .fa-decoration').forEach((node) => node.remove())
    const extensions = readExtensions(element.businessObject)
    if (isContainer(element)) {
      const role = roleOf(this.profile, extensions.actor?.role)
      if (role && this.visibility.actors) this.drawHeader(visual, element, role)
      return
    }
    const group = create('g', { class: 'fa-decoration', 'pointer-events': 'none' })
    if (this.visibility.markers && extensions.markers.length) this.drawBadges(group, element, extensions.markers)
    if (this.visibility.auditReferences && extensions.auditReferences.length) this.drawPlaque(group, element, extensions.auditReferences)
    if (group.childNodes.length) visual.appendChild(group)
  }

  private drawHeader(visual: Element, element: DiagramElement, role: Role): void {
    const horizontal = element.di?.get('isHorizontal') !== false
    const width = element.width ?? 0
    const height = element.height ?? 0
    const band = horizontal ? { x: 0, y: 0, width: HEADER_BAND, height } : { x: 0, y: 0, width, height: HEADER_BAND }
    const group = create('g', { class: 'fa-decoration fa-role-band', 'data-role': role.code, 'pointer-events': 'none' })
    group.appendChild(create('rect', { ...band, fill: role.color.fill, stroke: 'none' }))
    const edge = horizontal ? { x1: HEADER_BAND, y1: 0, x2: HEADER_BAND, y2: height } : { x1: 0, y1: HEADER_BAND, x2: width, y2: HEADER_BAND }
    group.appendChild(create('line', { ...edge, stroke: role.color.stroke, 'stroke-width': 2 }))
    const icon = iconElement(document, role.icon, 7, 6, 16)
    icon.setAttribute('stroke', role.color.stroke)
    icon.appendChild(create('title', {})).textContent = label(role.label, this.locale)
    group.appendChild(icon)
    // Behind the label text, in front of the frame.
    visual.insertBefore(group, visual.childNodes[1] ?? null)
  }

  private drawBadges(group: SVGGElement, element: DiagramElement, markers: Marker[]): void {
    const width = element.width ?? 0
    const small = SMALL_SHAPES.test(element.businessObject.$type)
    const y = small ? -BADGE_RADIUS - 4 : 0
    const visible = markers.slice(0, MAX_BADGES)
    visible.forEach((marker, index) => {
      const cx = small ? width / 2 + (index - (visible.length - 1) / 2) * 20 : width - 12 - index * 20
      const accent = MARKER_COLORS[marker.type]?.stroke ?? '#37474f'
      const badge = create('g', { class: `fa-badge fa-badge-${marker.type}` })
      badge.appendChild(create('circle', { cx, cy: y, r: BADGE_RADIUS, fill: '#ffffff', stroke: accent, 'stroke-width': 1.25 }))
      const icon = iconElement(document, `marker-${marker.type}`, cx - 6.5, y - 6.5, 13)
      icon.setAttribute('stroke', accent)
      badge.appendChild(icon)
      badge.appendChild(create('title', {})).textContent = [label(MARKER_TYPES[marker.type], this.locale) || marker.type, marker.text].filter(Boolean).join(': ')
      group.appendChild(badge)
    })
    if (markers.length > MAX_BADGES) {
      const x = small ? width / 2 + (visible.length / 2) * 20 + 6 : width - 12 - MAX_BADGES * 20
      const more = create('text', { x, y: y + 3.5, 'font-size': 10, 'font-family': 'sans-serif', fill: '#37474f', 'text-anchor': 'middle' })
      more.textContent = `+${markers.length - MAX_BADGES}`
      group.appendChild(more)
    }
  }

  private drawPlaque(group: SVGGElement, element: DiagramElement, references: AuditReference[]): void {
    const text = auditReferenceText(references)
    if (!text) return
    const height = element.height ?? 0
    const width = Math.min(Math.max(text.length * 5.4 + 10, 40), Math.max(element.width ?? 0, 60) + 40)
    const y = SMALL_SHAPES.test(element.businessObject.$type) ? height + 16 : height - 7
    const plaque = create('g', { class: 'fa-plaque' })
    plaque.appendChild(create('rect', { x: 2, y, width, height: 14, rx: 7, fill: '#eef1fb', stroke: '#3949ab', 'stroke-width': 1 }))
    const caption = create('text', { x: 2 + width / 2, y: y + 10, 'font-size': 9, 'font-family': 'sans-serif', fill: '#1a237e', 'text-anchor': 'middle' })
    caption.textContent = text
    plaque.appendChild(caption)
    group.appendChild(plaque)
  }
}

export const decorationsModule = {
  __init__: ['flowauditDecorations'],
  flowauditDecorations: ['type', FlowauditDecorations],
}
