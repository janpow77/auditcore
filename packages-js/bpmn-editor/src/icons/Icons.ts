/**
 * Eigenes, neu gezeichnetes SVG-Symbolset (24 × 24, `currentColor`) für
 * Palette, Kontextpad, Ersetzen-Menü und Werkzeugleisten.
 *
 * Ereignis-, Gateway- und Aufgabensymbole werden aus denselben eigenen
 * Glyphen erzeugt wie die Diagrammformen (siehe draw/Glyphs.ts).
 */

import * as G from '../draw/Glyphs'

const SVG_OPEN =
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" ' +
  'fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'

function svg(body: string): string {
  return `${SVG_OPEN}${body}</svg>`
}

const filled = 'fill="currentColor" stroke="currentColor" stroke-width="0.6"'
const hollow = 'fill="none" stroke="currentColor" stroke-width="0.9"'

// ---------------------------------------------------------------------------
// Ereignisse
// ---------------------------------------------------------------------------

export type EventKind = 'start' | 'intermediate-catch' | 'intermediate-throw' | 'boundary' | 'end'
export type EventDefinitionKind =
  | 'none'
  | 'message'
  | 'timer'
  | 'escalation'
  | 'conditional'
  | 'link'
  | 'error'
  | 'cancel'
  | 'compensation'
  | 'signal'
  | 'multiple'
  | 'parallel-multiple'
  | 'terminate'

const C = 12
const S = 0.5

/** Symbol je Ereignisdefinition (Parameter: Füllstil für werfende bzw. fangende Ereignisse). */
const EVENT_GLYPHS: Record<EventDefinitionKind, (style: string, isThrow: boolean) => string> = {
  none: () => '',
  message: (style, isThrow) => {
    const e = G.envelopePaths(C, C, S)
    return `<path d="${e.body}" ${style}/><path d="${e.flap}" fill="none" stroke="${isThrow ? '#fff' : 'currentColor'}" stroke-width="0.8"/>`
  },
  timer: () => `<circle cx="12" cy="12" r="5" ${hollow}/><path d="${G.timerHands(C, C, S)}" stroke-width="0.9"/>`,
  escalation: (style) => `<path d="${G.escalationPath(C, C, S)}" ${style}/>`,
  conditional: () => {
    const p = G.conditionalPaths(C, C, S)
    return `<path d="${p.sheet}" ${hollow}/><path d="${p.lines}" stroke-width="0.7"/>`
  },
  link: (style) => `<path d="${G.linkPath(C, C, S)}" ${style}/>`,
  error: (style) => `<path d="${G.errorPath(C, C, S)}" ${style}/>`,
  cancel: (style) => `<path d="${G.cancelPath(C, C, S)}" ${style}/>`,
  compensation: (style) => `<path d="${G.compensationPath(C, C, S)}" ${style}/>`,
  signal: (style) => `<path d="${G.signalPath(C, C, S)}" ${style}/>`,
  multiple: (style) => `<path d="${G.multiplePath(C, C, S)}" ${style}/>`,
  'parallel-multiple': () => `<path d="${G.parallelMultiplePath(C, C, S)}" ${hollow}/>`,
  terminate: () => `<circle cx="12" cy="12" r="5.5" ${filled}/>`,
}

function eventGlyph(definition: EventDefinitionKind, isThrow: boolean): string {
  return EVENT_GLYPHS[definition](isThrow ? filled : hollow, isThrow)
}

export function eventIcon(kind: EventKind, definition: EventDefinitionKind = 'none', nonInterrupting = false): string {
  const dash = nonInterrupting ? ' stroke-dasharray="2.6 1.8"' : ''
  let ring: string
  if (kind === 'start') ring = `<circle cx="12" cy="12" r="9"${dash}/>`
  else if (kind === 'end') ring = '<circle cx="12" cy="12" r="9" stroke-width="2.6"/>'
  else ring = `<circle cx="12" cy="12" r="9.5"${dash}/><circle cx="12" cy="12" r="7.8"${dash}/>`
  const isThrow = kind === 'end' || kind === 'intermediate-throw'
  return svg(ring + eventGlyph(definition, isThrow))
}

// ---------------------------------------------------------------------------
// Gateways
// ---------------------------------------------------------------------------

export type GatewayKind = 'exclusive' | 'parallel' | 'inclusive' | 'complex' | 'event-based' | 'event-based-parallel' | 'event-based-instantiate'

export function gatewayIcon(kind: GatewayKind = 'exclusive'): string {
  const diamond = '<path d="M12 2.5 L21.5 12 L12 21.5 L2.5 12 Z"/>'
  let inner = ''
  switch (kind) {
    case 'exclusive':
      inner = `<path d="${G.crossPath(12, 12, 1.1, 4.6, Math.PI / 4)}" ${filled}/>`
      break
    case 'parallel':
      inner = `<path d="${G.crossPath(12, 12, 1.1, 5.2)}" ${filled}/>`
      break
    case 'inclusive':
      inner = '<circle cx="12" cy="12" r="4.4" stroke-width="1.4"/>'
      break
    case 'complex':
      inner = `<path d="${G.crossPath(12, 12, 0.8, 5)}" ${filled}/><path d="${G.crossPath(12, 12, 0.8, 4.4, Math.PI / 4)}" ${filled}/>`
      break
    case 'event-based':
      inner = `<circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="4"/><path d="${G.regularPolygonPath(12, 12.2, 2.6, 5)}" stroke-width="0.8"/>`
      break
    case 'event-based-parallel':
      inner = `<circle cx="12" cy="12" r="5"/><path d="${G.crossPath(12, 12, 0.9, 3)}" stroke-width="0.8"/>`
      break
    case 'event-based-instantiate':
      inner = `<circle cx="12" cy="12" r="5"/><path d="${G.regularPolygonPath(12, 12.2, 2.6, 5)}" stroke-width="0.8"/>`
      break
  }
  return svg(diamond + inner)
}

// ---------------------------------------------------------------------------
// Aktivitäten
// ---------------------------------------------------------------------------

export type TaskKind = 'task' | 'user' | 'manual' | 'service' | 'script' | 'business-rule' | 'send' | 'receive'

export function taskIcon(kind: TaskKind = 'task'): string {
  const frame = '<rect x="2.5" y="5" width="19" height="14" rx="3"/>'
  const scale = (body: string) => `<g transform="translate(4.2 6.4) scale(0.5)" stroke-width="1.6">${body}</g>`
  let inner = ''
  switch (kind) {
    case 'user': {
      const icon = G.userIcon(0, 0)
      inner = scale(`<path d="${icon.body}"/><circle cx="${icon.head.cx}" cy="${icon.head.cy}" r="${icon.head.r}"/>`)
      break
    }
    case 'manual':
      inner = scale(`<path d="${G.manualIcon(0, 0)}"/>`)
      break
    case 'service': {
      const icon = G.serviceIcon(0, 0)
      inner = scale(icon.gears.map((gear) => `<path d="${gear}"/>`).join(''))
      break
    }
    case 'script': {
      const icon = G.scriptIcon(0, 0)
      inner = scale(`<path d="${icon.sheet}"/><path d="${icon.lines}"/>`)
      break
    }
    case 'business-rule': {
      const icon = G.businessRuleIcon(0, 0)
      inner = scale(`<path d="${icon.table}"/><path d="${icon.header}" fill="currentColor" fill-opacity="0.4"/><path d="${icon.lines}"/>`)
      break
    }
    case 'send': {
      const icon = G.messageTaskIcon(0, 0)
      inner = scale(`<path d="${icon.body}" fill="currentColor"/><path d="${icon.flap}" stroke="#fff"/>`)
      break
    }
    case 'receive': {
      const icon = G.messageTaskIcon(0, 0)
      inner = scale(`<path d="${icon.body}"/><path d="${icon.flap}"/>`)
      break
    }
  }
  return svg(frame + inner)
}

export function callActivityIcon(): string {
  return svg('<rect x="2.5" y="5" width="19" height="14" rx="3" stroke-width="2.8"/>')
}

export function subProcessIcon(variant: 'collapsed' | 'expanded' | 'event' | 'transaction' | 'adhoc' = 'collapsed'): string {
  switch (variant) {
    case 'expanded':
      return svg('<rect x="2" y="3.5" width="20" height="17" rx="3"/><path d="M9.5 16 h5" stroke-width="1"/><rect x="9.5" y="14.5" width="5" height="4" stroke-width="0.9"/>')
    case 'event':
      return svg('<rect x="2.5" y="5" width="19" height="14" rx="3" stroke-dasharray="1 2.2"/><path d="M10 15 h4 M12 13 v4" stroke-width="1"/>')
    case 'transaction':
      return svg('<rect x="2" y="4.5" width="20" height="15" rx="3"/><rect x="4" y="6.5" width="16" height="11" rx="2"/>')
    case 'adhoc':
      return svg('<rect x="2.5" y="5" width="19" height="14" rx="3"/><path d="M8.5 15.5 c1.2 -2 2.4 -2 3.5 0 s2.3 2 3.5 0" stroke-width="1.1"/>')
    default:
      return svg('<rect x="2.5" y="5" width="19" height="14" rx="3"/><rect x="9.5" y="12.5" width="5" height="5" stroke-width="0.9"/><path d="M12 13.5 v3 M10.5 15 h3" stroke-width="0.9"/>')
  }
}

// ---------------------------------------------------------------------------
// Daten, Artefakte, Pools
// ---------------------------------------------------------------------------

export function dataObjectIcon(variant: 'object' | 'collection' | 'input' | 'output' = 'object'): string {
  let extra = ''
  if (variant === 'collection') extra = '<path d="M10 16 v3 M12 16 v3 M14 16 v3" stroke-width="1.1"/>'
  if (variant === 'input') extra = `<path d="${G.dataArrowPath(7.5, 6)}" stroke-width="0.8" transform="translate(-1 0) scale(1)"/>`
  if (variant === 'output') extra = `<path d="${G.dataArrowPath(7.5, 6)}" stroke-width="0.8" fill="currentColor"/>`
  return svg('<path d="M6 2.5 H14.5 L18.5 6.5 V21.5 H6 Z"/><path d="M14.5 2.5 V6.5 H18.5"/>' + extra)
}

export function dataStoreIcon(): string {
  return svg(
    '<path d="M4 6 A8 3 0 0 1 20 6 V18 A8 3 0 0 1 4 18 Z"/><path d="M4 6 A8 3 0 0 0 20 6"/><path d="M4 9 A8 3 0 0 0 20 9"/><path d="M4 12 A8 3 0 0 0 20 12"/>',
  )
}

export function textAnnotationIcon(): string {
  return svg('<path d="M9 4 H5 V20 H9"/><path d="M11 8 H19 M11 12 H19 M11 16 H16" stroke-width="1.1"/>')
}

export function groupIcon(): string {
  return svg('<rect x="2.5" y="3.5" width="19" height="17" rx="3" stroke-dasharray="4 2 1 2"/>')
}

export function participantIcon(variant: 'expanded' | 'collapsed' = 'expanded'): string {
  if (variant === 'collapsed') return svg('<rect x="2" y="7" width="20" height="10"/>')
  return svg('<rect x="2" y="4" width="20" height="16"/><path d="M6.5 4 V20"/>')
}

export function laneIcon(where: 'above' | 'below' | 'divide-two' | 'divide-three'): string {
  const pool = '<rect x="2" y="4" width="20" height="16"/><path d="M6.5 4 V20"/>'
  switch (where) {
    case 'above':
      return svg(pool + '<path d="M6.5 10 H22" stroke-width="1.1"/><rect x="8" y="5.5" width="12" height="3" fill="currentColor" fill-opacity="0.35" stroke="none"/>')
    case 'below':
      return svg(pool + '<path d="M6.5 14 H22" stroke-width="1.1"/><rect x="8" y="15.5" width="12" height="3" fill="currentColor" fill-opacity="0.35" stroke="none"/>')
    case 'divide-two':
      return svg(pool + '<path d="M6.5 12 H22" stroke-width="1.1"/>')
    case 'divide-three':
      return svg(pool + '<path d="M6.5 9.3 H22 M6.5 14.7 H22" stroke-width="1.1"/>')
  }
}

// ---------------------------------------------------------------------------
// Werkzeuge und Aktionen
// ---------------------------------------------------------------------------

export const toolIcons = {
  hand: svg(
    '<path d="M8 13 V6.5 a1.4 1.4 0 0 1 2.8 0 V11 M10.8 5.5 a1.4 1.4 0 0 1 2.8 0 V11 M13.6 6.5 a1.4 1.4 0 0 1 2.8 0 V12 M16.4 9 a1.4 1.4 0 0 1 2.8 0 V15 c0 3.5 -2.5 6 -6 6 h-1 c-2 0 -3.5 -1 -4.6 -2.6 L5 14.5 a1.4 1.4 0 0 1 2.2 -1.7 L8 14"/>',
  ),
  lasso: svg('<rect x="3" y="4" width="18" height="14" stroke-dasharray="3 2"/><path d="M14 13 L20 21 M14 13 L18 13.5 M14 13 L14.5 17"/>'),
  space: svg('<path d="M12 3 V21" stroke-dasharray="2 2"/><path d="M4 12 H10 M4 12 L6.5 9.5 M4 12 L6.5 14.5 M20 12 H14 M20 12 L17.5 9.5 M20 12 L17.5 14.5"/>'),
  connect: svg('<circle cx="5.5" cy="18.5" r="2.5"/><path d="M7.5 16.5 L18 6"/><path d="M13 5.5 H18.5 V11"/>'),
  delete: svg('<path d="M4.5 7 H19.5 M9.5 7 V4.5 H14.5 V7 M6.5 7 L7.5 20 H16.5 L17.5 7 M10.5 10.5 V16.5 M13.5 10.5 V16.5"/>'),
  replace: svg('<path d="M14.5 5.5 a4 4 0 0 0 -5.3 5.2 L4 16 V20 H8 L13.3 14.8 a4 4 0 0 0 5.2 -5.3 L16 12 L12 8 Z"/>'),
  color: svg('<path d="M12 3 C12 3 5.5 10 5.5 14.5 a6.5 6.5 0 0 0 13 0 C18.5 10 12 3 12 3 Z"/><path d="M9 15.5 a3 3 0 0 0 3 3" stroke-width="1.1"/>'),
  annotation: textAnnotationIcon(),
  undo: svg('<path d="M9 7 L4.5 11.5 L9 16"/><path d="M4.5 11.5 H14 a5 5 0 0 1 0 10 H11"/>'),
  redo: svg('<path d="M15 7 L19.5 11.5 L15 16"/><path d="M19.5 11.5 H10 a5 5 0 0 0 0 10 H13"/>'),
  zoomIn: svg('<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 L21 21 M7.5 10.5 H13.5 M10.5 7.5 V13.5"/>'),
  zoomOut: svg('<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 L21 21 M7.5 10.5 H13.5"/>'),
  zoomFit: svg('<path d="M3 8 V3 H8 M16 3 H21 V8 M21 16 V21 H16 M8 21 H3 V16"/><rect x="8" y="8" width="8" height="8" rx="1"/>'),
  search: svg('<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 L21 21"/>'),
  minimap: svg('<rect x="2.5" y="4" width="19" height="16" rx="2"/><rect x="12" y="11" width="7" height="6.5" rx="1" fill="currentColor" fill-opacity="0.25"/>'),
  alignLeft: svg('<path d="M4 3 V21"/><rect x="6" y="5.5" width="11" height="5" rx="1"/><rect x="6" y="13.5" width="7" height="5" rx="1"/>'),
  alignCenter: svg('<path d="M12 3 V21" stroke-dasharray="2 1.5"/><rect x="5.5" y="5.5" width="13" height="5" rx="1"/><rect x="8" y="13.5" width="8" height="5" rx="1"/>'),
  alignRight: svg('<path d="M20 3 V21"/><rect x="7" y="5.5" width="11" height="5" rx="1"/><rect x="11" y="13.5" width="7" height="5" rx="1"/>'),
  alignTop: svg('<path d="M3 4 H21"/><rect x="5.5" y="6" width="5" height="11" rx="1"/><rect x="13.5" y="6" width="5" height="7" rx="1"/>'),
  alignMiddle: svg('<path d="M3 12 H21" stroke-dasharray="2 1.5"/><rect x="5.5" y="5.5" width="5" height="13" rx="1"/><rect x="13.5" y="8" width="5" height="8" rx="1"/>'),
  alignBottom: svg('<path d="M3 20 H21"/><rect x="5.5" y="7" width="5" height="11" rx="1"/><rect x="13.5" y="11" width="5" height="7" rx="1"/>'),
  distributeHorizontal: svg('<path d="M3 3 V21 M21 3 V21"/><rect x="9.5" y="7" width="5" height="10" rx="1"/>'),
  distributeVertical: svg('<path d="M3 3 H21 M3 21 H21"/><rect x="7" y="9.5" width="10" height="5" rx="1"/>'),
  drilldown: svg('<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 12 H16 M12 8 V16"/>'),
  back: svg('<path d="M14.5 5.5 L8 12 L14.5 18.5"/>'),
  loop: svg(`<path d="${G.loopMarker(12, 11)}" stroke-width="1.3"/>`),
  parallelMi: svg(`<path d="${G.parallelMarker(12, 12)}" stroke-width="1.8"/>`),
  sequentialMi: svg(`<path d="${G.sequentialMarker(12, 12)}" stroke-width="1.8"/>`),
  compensation: svg(`<path d="${G.compensationPath(12, 12, 0.9)}" stroke-width="1.1"/>`),
  collection: svg('<path d="M8 6 V18 M12 6 V18 M16 6 V18" stroke-width="1.8"/>'),
  sequenceFlow: svg('<path d="M3 12 H19"/><path d="M15.5 8.5 L20.5 12 L15.5 15.5 Z" fill="currentColor"/>'),
  defaultFlow: svg('<path d="M3 12 H19 M6 9 L9 15"/><path d="M15.5 8.5 L20.5 12 L15.5 15.5 Z" fill="currentColor"/>'),
  conditionalFlow: svg('<path d="M9.5 12 H19"/><path d="M2.5 12 L6 9.5 L9.5 12 L6 14.5 Z"/><path d="M15.5 8.5 L20.5 12 L15.5 15.5 Z" fill="currentColor"/>'),
  nonInterrupting: svg('<circle cx="12" cy="12" r="9" stroke-dasharray="2.6 1.8"/>'),
}

export { svg as wrapIcon }
