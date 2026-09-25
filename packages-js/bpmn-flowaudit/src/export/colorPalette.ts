/**
 * Audit-compliant colour palette for BPMN elements, ported from
 * `farbpalette.ts` of the audit_designer. In an audit report every colour
 * must carry a statement; otherwise colouring is decoration and misleading.
 * The same palette feeds the context menu, the export legend and the
 * recognition of colours read from files.
 */

export interface PaletteColor {
  id: string
  label: string
  meaning: string
  fill: string
  stroke: string
}

export const PALETTE_COLORS: readonly PaletteColor[] = [
  { id: 'validiert', label: 'Validiert', meaning: 'Schritt geprüft und bestätigt', fill: '#c8e6c9', stroke: '#1b5e20' },
  { id: 'kritisch', label: 'Kritisch / neu', meaning: 'Feststellung, Änderung oder offener Punkt', fill: '#ffcdd2', stroke: '#b71c1c' },
  { id: 'system', label: 'Systemisch', meaning: 'Automatisierter oder IT-gestützter Schritt', fill: '#bbdefb', stroke: '#0d47a1' },
  { id: 'inaktiv', label: 'Inaktiv', meaning: 'Nicht mehr angewandt oder ausgesetzt', fill: '#e0e0e0', stroke: '#424242' },
] as const

/** Compares colour values tolerant of case and short form (`#abc`). */
export function normalizeColor(value: string | null | undefined): string {
  if (!value) return ''
  const color = value.trim().toLowerCase()
  if (/^#[0-9a-f]{3}$/.test(color)) return `#${color[1]}${color[1]}${color[2]}${color[2]}${color[3]}${color[3]}`
  return color
}

export function findPaletteColor(fill: string | null | undefined, palette: readonly PaletteColor[] = PALETTE_COLORS): PaletteColor | null {
  const wanted = normalizeColor(fill)
  return wanted ? palette.find((color) => normalizeColor(color.fill) === wanted) ?? null : null
}
