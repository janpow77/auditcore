/**
 * Eigene Strichsymbole (24er-Raster, Strichstärke über CSS). Jede Zeile ist
 * eine Liste von SVG-Pfaden; neue Symbole nur hier ergänzen.
 */
export const ICONS = {
  close: ['M6 6l12 12', 'M18 6L6 18'],
  plus: ['M12 5v14', 'M5 12h14'],
  minus: ['M5 12h14'],
  check: ['M5 12.5l4.5 4.5L19 7.5'],
  search: ['M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13z', 'M15.5 15.5L20 20'],
  filter: ['M4 5h16', 'M7 12h10', 'M10 19h4'],
  settings: ['M4 6h9', 'M17 6h3', 'M15 4v4', 'M4 12h3', 'M11 12h9', 'M9 10v4', 'M4 18h11', 'M19 18h1', 'M17 16v4'],
  share: ['M6 14a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z', 'M18 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z', 'M18 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z', 'M8.2 10.4l7.6-4.3', 'M8.2 12.6l7.6 4.3'],
  trash: ['M4 7h16', 'M9 7V4.5h6V7', 'M6.5 7l1 13h9l1-13', 'M10 11v6', 'M14 11v6'],
  edit: ['M4 20h4L19 9l-4-4L4 16v4z', 'M13.5 6.5l4 4'],
  'chevron-down': ['M6 9l6 6 6-6'],
  'chevron-up': ['M6 15l6-6 6 6'],
  'chevron-left': ['M15 6l-6 6 6 6'],
  'chevron-right': ['M9 6l6 6-6 6'],
  sort: ['M8 4v16', 'M4.5 7.5L8 4l3.5 3.5', 'M16 20V4', 'M12.5 16.5L16 20l3.5-3.5'],
  'sort-asc': ['M12 19V5', 'M6.5 10.5L12 5l5.5 5.5'],
  'sort-desc': ['M12 5v14', 'M6.5 13.5L12 19l5.5-5.5'],
  grip: ['M9 6h.01', 'M15 6h.01', 'M9 12h.01', 'M15 12h.01', 'M9 18h.01', 'M15 18h.01'],
  calendar: ['M4.5 6.5h15v13h-15z', 'M4.5 10.5h15', 'M8.5 4v4', 'M15.5 4v4'],
  clock: ['M12 20.5a8.5 8.5 0 1 0 0-17 8.5 8.5 0 0 0 0 17z', 'M12 7.5V12l3 2'],
  paperclip: ['M19 11.5l-7.2 7.2a4.5 4.5 0 0 1-6.4-6.4l7.8-7.8a3 3 0 0 1 4.2 4.2l-7.6 7.6a1.5 1.5 0 0 1-2.1-2.1l6.9-6.9'],
  user: ['M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z', 'M4.5 20.5a7.5 7.5 0 0 1 15 0'],
  lock: ['M6 11h12v9H6z', 'M8.5 11V8a3.5 3.5 0 0 1 7 0v3'],
  pin: ['M9 4h6l-1 6 3 3H7l3-3-1-6z', 'M12 13v7'],
  sun: ['M12 16.5a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9z', 'M12 2.5v2', 'M12 19.5v2', 'M2.5 12h2', 'M19.5 12h2', 'M5.3 5.3l1.4 1.4', 'M17.3 17.3l1.4 1.4', 'M5.3 18.7l1.4-1.4', 'M17.3 6.7l1.4-1.4'],
  moon: ['M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z'],
  warning: ['M12 4l9 16H3z', 'M12 10v4.5', 'M12 17.5h.01'],
  info: ['M12 20.5a8.5 8.5 0 1 0 0-17 8.5 8.5 0 0 0 0 17z', 'M12 11v5.5', 'M12 7.5h.01'],
  expand: ['M4 9V4h5', 'M20 9V4h-5', 'M4 15v5h5', 'M20 15v5h-5'],
  'more-vertical': ['M12 5.5h.01', 'M12 12h.01', 'M12 18.5h.01'],
} as const satisfies Readonly<Record<string, readonly string[]>>

export type IconName = keyof typeof ICONS

export function isIconName(value: string): value is IconName {
  return Object.prototype.hasOwnProperty.call(ICONS, value)
}
