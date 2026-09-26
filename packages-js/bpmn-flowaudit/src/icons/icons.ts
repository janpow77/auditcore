/**
 * FlowAudit icon set – drawn from scratch for this project.
 *
 * Uniform style: 24 px grid, 2 px safe margin, stroke width 1.75, round
 * caps and joins, `currentColor`. Filled shapes are used only for small
 * dots. The table is declarative; renderers exist for DOM (`iconElement`),
 * strings (`iconSvg`) and Vue (`FaIcon` in @auditcore/bpmn-vue).
 */

export type IconShape =
  | { d: string; fill?: boolean; dash?: boolean; width?: number }
  | { circle: [number, number, number]; fill?: boolean; width?: number }
  | { rect: [number, number, number, number, number?]; fill?: boolean; dash?: boolean }

const p = (d: string): IconShape => ({ d })
const c = (cx: number, cy: number, r: number, fill = false): IconShape => ({ circle: [cx, cy, r], fill })
const r = (x: number, y: number, w: number, h: number, rx = 0, dash = false): IconShape => ({ rect: [x, y, w, h, rx], dash })
const dot = (cx: number, cy: number, radius = 1): IconShape => c(cx, cy, radius, true)

const DOCUMENT = 'M6 3h8l4 4v14H6z M14 3v4h4'
const FOLDER = 'M3 7a1.5 1.5 0 0 1 1.5-1.5h4l2 2h9A1.5 1.5 0 0 1 21 9v9.5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18.5z'
const SHIELD = 'M12 3l7 3v5c0 4.6-3 8.3-7 10-4-1.7-7-5.4-7-10V6z'
const FLAG = 'M5 21V4 M5 4h11l-2 3.5 2 3.5H5'
const MAGNIFIER = [c(10.5, 10.5, 6.5), p('M15.5 15.5l5 5')]
const TRAY_DOWN = 'M4 15v4.5A1.5 1.5 0 0 0 5.5 21h13a1.5 1.5 0 0 0 1.5-1.5V15'

export const ICONS: Record<string, IconShape[]> = {
  // ----- roles ---------------------------------------------------------------
  'role-vb': [p('M3 9.5 12 4l9 5.5 M6 10.5v7 M10 10.5v7 M14 10.5v7 M18 10.5v7 M3.5 20h17')],
  'role-zgs': [r(2, 9, 5, 6, 1), r(17, 9, 5, 6, 1), c(12, 12, 3), p('M7 12h2 M15 12h2')],
  'role-rfs': [r(5, 3, 14, 18, 2), p('M8 7h8'), dot(9, 12), dot(12, 12), dot(15, 12), dot(9, 16), dot(12, 16), dot(15, 16)],
  'role-bb': [r(4, 4, 16, 12, 1.5), p('M8 8h8 M8 11h5 M14.5 19l-1 2.5 M17.5 19l1 2.5'), c(16, 17, 2.5)],
  'role-pb': [...MAGNIFIER, p('M7.5 10.5l2 2 3.5-4')],
  'role-pbs': [c(6, 7, 2.5), c(18, 7, 2.5), c(12, 17, 2.5), p('M8.5 7h7 M7.3 9.2l3.4 5.6 M16.7 9.2l-3.4 5.6')],
  'role-kom': [c(12, 12, 8.5), p('M3.5 12h17 M12 3.5c2.5 2.3 3.5 5.2 3.5 8.5s-1 6.2-3.5 8.5c-2.5-2.3-3.5-5.2-3.5-8.5s1-6.2 3.5-8.5z')],
  'role-beg': [c(12, 8, 3.5), p('M5 20c.8-3.8 3.6-6 7-6s6.2 2.2 7 6')],
  'role-bga': [c(12, 7.5, 2.6), c(5.5, 10, 2.1), c(18.5, 10, 2.1), p('M7.5 19c.4-3.2 2.2-5 4.5-5s4.1 1.8 4.5 5 M2.5 18c.2-2.2 1.4-3.6 3-3.9 M21.5 18c-.2-2.2-1.4-3.6-3-3.9')],
  'role-gs': [p('M3 13l2.5-7h13L21 13v5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18z M3 13h5l1.5 2.5h5L16 13h5')],
  'role-gdp': [c(8, 10, 4.5), c(16, 10, 4.5), p('M5 13.5 2.5 17 M19 13.5l2.5 3.5 M11 8.5c.6-.4 1.3-.5 2-.5')],
  'role-fb': [c(12, 5, 2), p('M10.5 7h3l.5 4h-4z M5 11h14v4H5z M5 19h14')],
  'role-ftd': [p('M14.7 6.3a4 4 0 0 0-5.4 5.4L3.5 17.5l3 3 5.8-5.8a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.8-.4-.4-2.8z')],
  'role-gut': [p(`${DOCUMENT} M9 17.5l5-5 1.5 1.5-5 5H9z`)],
  'role-gre': [c(12, 12, 4), c(12, 4.5, 1.5), c(12, 19.5, 1.5), c(4.5, 12, 1.5), c(19.5, 12, 1.5)],
  'role-fr': [p(`${FOLDER} M8 13.5h8`)],
  'role-ds': [p(SHIELD), r(9.5, 11, 5, 4, 1), p('M10.5 11V9.8a1.5 1.5 0 0 1 3 0V11')],
  'role-it': [r(3, 4, 18, 12, 1.5), p('M8 20h8 M12 16v4')],
  'role-sonstige': [c(12, 12, 8.5), dot(8, 12), dot(12, 12), dot(16, 12)],

  // ----- markers -------------------------------------------------------------
  'marker-rechtsgrundlage': [p('M14.5 6.5c-.5-1.4-1.6-2-3-2-1.7 0-3 1-3 2.4 0 3.2 7 2.4 7 6 0 1.1-.8 2-2 2.4 M9.5 17.5c.5 1.4 1.6 2 3 2 1.7 0 3-1 3-2.4 0-3.2-7-2.4-7-6 0-1.1.8-2 2-2.4')],
  'marker-pruefpunkt': [c(12, 12, 8.5), p('M8 12.3l2.7 2.7L16 9.5')],
  'marker-frist': [p('M7 3.5h10 M7 20.5h10 M8 3.5c0 4 8 5 8 8.5s-8 4.5-8 8.5 M16 3.5c0 4-8 5-8 8.5s8 4.5 8 8.5')],
  'marker-vier_augen': [
    p('M2 12c1.3-2.3 3-3.5 5-3.5s3.7 1.2 5 3.5c-1.3 2.3-3 3.5-5 3.5S3.3 14.3 2 12z M12 12c1.3-2.3 3-3.5 5-3.5s3.7 1.2 5 3.5c-1.3 2.3-3 3.5-5 3.5s-3.7-1.2-5-3.5z'),
    dot(7, 12, 1.4),
    dot(17, 12, 1.4),
  ],
  'marker-dokument': [p(`${DOCUMENT} M9 12h6 M9 16h6`)],
  'marker-risiko': [p('M12 3.5 21.5 20h-19z M12 10v4.5'), dot(12, 17.3, 0.9)],
  'marker-system': [r(7, 7, 10, 10, 1.5), p('M10 3.5V7 M14 3.5V7 M10 17v3.5 M14 17v3.5 M3.5 10H7 M3.5 14H7 M17 10h3.5 M17 14h3.5')],
  'marker-zahlung': [c(12, 12, 8.5), p('M15 8.8a4 4 0 1 0 0 6.4 M7.5 11h5.5 M7.5 13.2h5.5')],
  'marker-bewilligung': [p(`${DOCUMENT} M9 14l2 2 4-4.5`)],
  'marker-schluesselkontrolle': [c(8, 15, 4), p('M10.8 12.2 19 4 M16 7l2.5 2.5 M13.5 9.5l2 2')],
  'marker-checkliste': [p('M4 6.5 5.5 8 8 5.5 M4 12.5 5.5 14 8 11.5 M4 18.5 5.5 20 8 17.5 M11 7h9 M11 13h9 M11 19h9')],
  'marker-bescheid': [r(3, 5.5, 18, 13, 1.5), p('M3.5 6.5 12 13l8.5-6.5')],
  'marker-stellungnahme': [p('M4 5h16v10.5H10L6 19v-3.5H4z M8 9h8 M8 12h5')],
  'marker-gremium': [c(7, 8, 2), c(12, 6.5, 2), c(17, 8, 2), p('M3 14h18 M5 14v5 M19 14v5')],
  'marker-interessenkonflikt': [p('M3 12h6 M6 9l3 3-3 3 M21 12h-6 M18 9l-3 3 3 3 M12 7v10')],
  'marker-veroeffentlichung': [p('M3.5 10v4h3l7 4.5v-13l-7 4.5z M17 9a4 4 0 0 1 0 6 M6.5 14l1 5H10l-1-5')],
  'marker-feststellung': [p(FLAG)],
  'marker-feststellung_formell': [p(`${FLAG} M7.5 7.5h4`)],
  'marker-feststellung_finanziell': [p(FLAG), c(17.5, 17.5, 3), p('M17.5 16v3')],
  'marker-offener_nachweis': [p(`${DOCUMENT} M10 11.5a2 2 0 1 1 2.8 1.8c-.5.3-.8.7-.8 1.2v.5`), dot(12, 17.5, 0.9)],
  'marker-ohne_befund': [p(`${SHIELD} M8.8 12l2.2 2.2 4.2-4.4`)],
  'marker-soll_ohne_regelung': [p('M9.5 14.5 8 16a3 3 0 0 1-4.2-4.2L5.5 10 M14.5 9.5 16 8a3 3 0 0 1 4.2 4.2L18.5 14 M8 4.5l1 2.5 M4.5 8 7 9 M16 19.5l-1-2.5 M19.5 16 17 15')],

  // ----- tools and UI ---------------------------------------------------------
  save: [p('M5 3.5h11l3.5 3.5v12a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 19V5A1.5 1.5 0 0 1 5 3.5z M8 3.5v5h7v-5 M7.5 20.5v-6h9v6')],
  new: [p(`${DOCUMENT} M12 11v6 M9 14h6`)],
  import: [p(`M12 15V4 M8 8l4-4 4 4 ${TRAY_DOWN}`)],
  export: [p(`M12 4v11 M8 11l4 4 4-4 ${TRAY_DOWN}`)],
  undo: [p('M9 14 4 9l5-5 M4 9h10.5a5.5 5.5 0 0 1 0 11H11')],
  redo: [p('M15 14l5-5-5-5 M20 9H9.5a5.5 5.5 0 0 0 0 11H13')],
  'zoom-in': [...MAGNIFIER, p('M10.5 7.5v6 M7.5 10.5h6')],
  'zoom-out': [...MAGNIFIER, p('M7.5 10.5h6')],
  fit: [p('M4 9V4h5 M15 4h5v5 M20 15v5h-5 M9 20H4v-5')],
  search: [...MAGNIFIER],
  keyboard: [r(2.5, 6, 19, 12, 1.5), p('M6 10h1 M9.5 10h1 M13 10h1 M16.5 10h1 M7 14h10')],
  info: [c(12, 12, 8.5), p('M12 11v5.5'), dot(12, 7.8, 0.9)],
  filter: [p('M3.5 5h17l-6.5 7.5v6l-4 2v-8z')],
  folder: [p(FOLDER)],
  'folder-open': [p('M3 18.5V7a1.5 1.5 0 0 1 1.5-1.5h4l2 2h7A1.5 1.5 0 0 1 19 9v1.5 M3 18.5l2.6-7a1.5 1.5 0 0 1 1.4-1h13.5a1 1 0 0 1 .9 1.3l-2.3 6.6a1.5 1.5 0 0 1-1.4 1.1H4.5A1.5 1.5 0 0 1 3 18.5z')],
  'folder-new': [p(`${FOLDER} M12 10.5v6 M9 13.5h6`)],
  diagram: [r(3, 4, 6, 5, 1), r(15, 4, 6, 5, 1), r(9, 15, 6, 5, 1), p('M9 6.5h6 M12 9v6')],
  tag: [p('M3.5 4.5v7.3l8.7 8.7 8.3-8.3-8.7-8.7H4.5a1 1 0 0 0-1 1z'), c(8, 8, 1.5)],
  grip: [dot(9, 6, 1.3), dot(15, 6, 1.3), dot(9, 12, 1.3), dot(15, 12, 1.3), dot(9, 18, 1.3), dot(15, 18, 1.3)],
  delete: [p('M4 7h16 M10 11v6 M14 11v6 M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12 M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2')],
  plus: [p('M12 5v14 M5 12h14')],
  close: [p('M6 6l12 12 M18 6 6 18')],
  'chevron-right': [p('M9 5l7 7-7 7')],
  'chevron-left': [p('M15 5l-7 7 7 7')],
  'chevron-down': [p('M5 9l7 7 7-7')],
  'chevron-up': [p('M5 15l7-7 7 7')],
  check: [p('M5 12.5l4.5 4.5L19 7.5')],
  warning: [p('M12 3.5 21.5 20h-19z M12 10v4.5'), dot(12, 17.3, 0.9)],
  error: [c(12, 12, 8.5), p('M9 9l6 6 M15 9l-6 6')],
  hint: [p('M9 18h6 M10 21h4 M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z')],
  play: [p('M7 4.5v15l12-7.5z')],
  'step-forward': [p('M6 5v14l10-7z M18 5v14')],
  'step-back': [p('M18 5v14L8 12z M6 5v14')],
  compare: [p('M8 4v16 M16 4v16 M3 8h5 M16 16h5 M5 6 3 8l2 2 M19 14l2 2-2 2')],
  neutral: [c(7, 15, 3), c(17, 15, 3), p('M10 15h4 M3 11h18 M5.5 11l2-6h9l2 6')],
  minimap: [r(3, 4, 18, 16, 1.5), r(12, 11, 6, 6, 1)],
  color: [
    p('M12 3.5a8.5 8.5 0 1 0 0 17c1 0 1.6-.7 1.6-1.6 0-.5-.2-.8-.5-1.1-.3-.3-.5-.7-.5-1.1 0-.9.7-1.6 1.6-1.6h1.9A4.4 4.4 0 0 0 20.5 11c0-4.2-3.8-7.5-8.5-7.5z'),
    dot(7.5, 11.5, 1.1),
    dot(9.5, 7.5, 1.1),
    dot(14.5, 7.5, 1.1),
  ],
  horizontal: [p('M3 12h18 M17 8l4 4-4 4')],
  vertical: [p('M12 3v18 M8 17l4 4 4-4')],
  page: [r(5, 3, 14, 18, 1.5), { d: 'M5 12h14', dash: true }],
  lock: [r(5, 10.5, 14, 10, 1.5), p('M8 10.5v-3a4 4 0 0 1 8 0v3')],
  hash: [p('M5 9h14 M5 15h14 M10 4 8 20 M16 4l-2 16')],
  sun: [c(12, 12, 4), p('M12 2.5v2 M12 19.5v2 M2.5 12h2 M19.5 12h2 M5.3 5.3l1.4 1.4 M17.3 17.3l1.4 1.4 M5.3 18.7l1.4-1.4 M17.3 6.7l1.4-1.4')],
  moon: [p('M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z')],
  language: [p('M3 5h9 M7.5 3v2 M5 5c.8 3.2 3.2 6 6 7.5 M10 5c-.8 3.7-3.2 6.7-6.5 8 M13 21l4-9 4 9 M14.3 18h5.4')],
  validate: [p('M9 4.5h6v2H9z M8 5.5H6.5A1.5 1.5 0 0 0 5 7v12.5A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V7a1.5 1.5 0 0 0-1.5-1.5H16 M9 13.5l2 2 4-4.5')],
  enrich: [p('M4 20 15 9 M13.5 7.5l3 3 M18 3v3 M16.5 4.5h3 M20 9v2 M19 10h2 M9 3.5v2 M8 4.5h2')],
  xml: [p('M8 7l-5 5 5 5 M16 7l5 5-5 5 M13.5 5l-3 14')],
  'panel-left': [r(3, 4, 18, 16, 1.5), p('M9 4v16')],
  'panel-right': [r(3, 4, 18, 16, 1.5), p('M15 4v16')],
  more: [dot(6, 12, 1.4), dot(12, 12, 1.4), dot(18, 12, 1.4)],
  share: [c(6, 12, 2.5), c(18, 6, 2.5), c(18, 18, 2.5), p('M8.3 10.9l7.4-3.8 M8.3 13.1l7.4 3.8')],
  analysis: [p('M4 20V4 M4 20h16 M8 16v-5 M12 16V8 M16 16v-3')],
  overview: [r(3.5, 3.5, 7, 7, 1), r(13.5, 3.5, 7, 7, 1), r(3.5, 13.5, 7, 7, 1), r(13.5, 13.5, 7, 7, 1)],
  comment: [p('M4 5h16v10.5H10L6 19v-3.5H4z M8 9h8 M8 12h5')],
  hand: [p('M8 12V5.5a1.5 1.5 0 0 1 3 0V11 M11 10V4.5a1.5 1.5 0 0 1 3 0V11 M14 10.5V6a1.5 1.5 0 0 1 3 0v7c0 4-2.7 7.5-6.5 7.5-2.5 0-4-1.2-5.2-3L3.8 13.5a1.4 1.4 0 0 1 2.2-1.8L8 14')],
  lasso: [p('M5.5 12c0-3.6 2.9-6.5 6.5-6.5s6.5 2.9 6.5 6.5-2.9 5-6.5 5c-1 0-2-.2-2.8-.5 M9.2 16.5c-1.4.6-2.2 1.6-2.2 2.7 0 .8.5 1.3 1.2 1.3')],
  space: [p('M12 3v18 M4 12h5 M6.5 9.5 9 12l-2.5 2.5 M20 12h-5 M17.5 9.5 15 12l2.5 2.5')],
  connect: [c(5.5, 18.5, 2), p('M7 17 19 5 M13 5h6v6')],
  'bpmn-task': [r(3, 6, 18, 12, 3)],
  'bpmn-start': [c(12, 12, 8)],
  'bpmn-end': [{ circle: [12, 12, 7.5], width: 3 }],
  'bpmn-intermediate': [c(12, 12, 8.5), c(12, 12, 6)],
  'bpmn-gateway': [p('M12 3l9 9-9 9-9-9z M9.5 9.5l5 5 M14.5 9.5l-5 5')],
  'bpmn-subprocess': [r(3, 6, 18, 12, 3), r(10, 13, 4, 4, 0.5), p('M12 13.8v2.4 M10.8 15h2.4')],
  'bpmn-pool': [r(2.5, 5, 19, 14, 1), p('M7 5v14')],
  'bpmn-lane': [r(2.5, 5, 19, 14, 1), p('M7 5v14 M7 12h14.5')],
  'bpmn-data-object': [p(DOCUMENT)],
  'bpmn-data-store': [p('M5 6.5c0-1.7 3.1-3 7-3s7 1.3 7 3v11c0 1.7-3.1 3-7 3s-7-1.3-7-3z M5 6.5c0 1.7 3.1 3 7 3s7-1.3 7-3 M5 10c0 1.7 3.1 3 7 3s7-1.3 7-3')],
  'bpmn-annotation': [p('M9 4H5v16h4 M9 9h10 M9 13h8')],
  'bpmn-group': [r(3, 4, 18, 16, 3, true)],
}

export type IconName = keyof typeof ICONS

const SVG = 'http://www.w3.org/2000/svg'

function attributesOf(shape: IconShape): [string, Record<string, string>] {
  const style: Record<string, string> = shape.fill ? { fill: 'currentColor', stroke: 'none' } : { fill: 'none' }
  if ('width' in shape && shape.width) style['stroke-width'] = String(shape.width)
  if ('dash' in shape && shape.dash) style['stroke-dasharray'] = '3 2.5'
  if ('d' in shape) return ['path', { d: shape.d, ...style }]
  if ('circle' in shape) {
    const [cx, cy, radius] = shape.circle
    return ['circle', { cx: String(cx), cy: String(cy), r: String(radius), ...style }]
  }
  const [x, y, w, h, rx] = shape.rect
  return ['rect', { x: String(x), y: String(y), width: String(w), height: String(h), rx: String(rx ?? 0), ...style }]
}

/** Primitive shapes of an icon as `[tag, attributes]` (for Vue render functions). */
export function iconPrimitives(name: string): [string, Record<string, string>][] {
  return (ICONS[name] ?? ICONS.info ?? []).map(attributesOf)
}

const ROOT_ATTRIBUTES = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': '1.75',
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round',
}

/** SVG markup of an icon (e.g. for CSS data URIs or `innerHTML`). */
export function iconSvg(name: string, size = 24): string {
  const root = Object.entries({ xmlns: SVG, width: String(size), height: String(size), ...ROOT_ATTRIBUTES })
    .map(([key, value]) => `${key}="${value}"`)
    .join(' ')
  const children = iconPrimitives(name)
    .map(([tag, attrs]) => `<${tag} ${Object.entries(attrs).map(([key, value]) => `${key}="${value}"`).join(' ')}/>`)
    .join('')
  return `<svg ${root}>${children}</svg>`
}

/** Icon as SVG element inside an existing SVG (diagram decorations). */
export function iconElement(document: Document, name: string, x: number, y: number, size: number): SVGGElement {
  const group = document.createElementNS(SVG, 'g')
  group.setAttribute('transform', `translate(${x} ${y}) scale(${size / 24})`)
  for (const [key, value] of Object.entries(ROOT_ATTRIBUTES)) if (key !== 'viewBox') group.setAttribute(key, value)
  for (const [tag, attrs] of iconPrimitives(name)) {
    const child = document.createElementNS(SVG, tag)
    for (const [key, value] of Object.entries(attrs)) child.setAttribute(key, value)
    group.appendChild(child)
  }
  return group
}

export function hasIcon(name: string): boolean {
  return name in ICONS
}
