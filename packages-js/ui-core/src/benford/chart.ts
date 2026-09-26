/**
 * Geometrie des Benford-Diagramms als reine Funktion (kein DOM, keine
 * Diagrammbibliothek): beobachtete Anteile als Balken, erwartete Anteile als
 * Linie mit Punkten, Überschreitungen des kritischen z-Werts markiert.
 */
import type { ConformityRow } from './types'

export interface ChartBox {
  width: number
  height: number
  top: number
  right: number
  bottom: number
  left: number
}

export interface ChartBar {
  digit: number
  x: number
  y: number
  width: number
  height: number
  exceeds: boolean
}

export interface ChartGeometry {
  box: ChartBox
  plot: { x: number; y: number; width: number; height: number }
  bars: ChartBar[]
  expected: { x: number; y: number }[]
  expectedPath: string
  yTicks: { y: number; value: number }[]
  /** Nachkommastellen der Prozentbeschriftung (0 für ganze Prozent, sonst 1). */
  tickDigits: number
  xLabels: { x: number; digit: number }[]
}

export const DEFAULT_BOX: ChartBox = { width: 720, height: 300, top: 16, right: 16, bottom: 36, left: 52 }

/** Obergrenze der y-Achse: nächstes Vielfaches des Tickabstands über dem Maximum. */
export function axisMaximum(maximum: number): { top: number; step: number } {
  const steps = [0.005, 0.01, 0.02, 0.025, 0.05, 0.1, 0.2, 0.25, 0.5]
  const step = steps.find((candidate) => maximum / candidate <= 5) ?? 1
  const top = Math.max(step, Math.ceil((maximum * 1.05) / step) * step)
  return { top, step }
}

function labelEvery(count: number): number {
  return count > 20 ? 10 : 1
}

export function chartGeometry(rows: readonly ConformityRow[], box: ChartBox = DEFAULT_BOX): ChartGeometry {
  const plot = {
    x: box.left,
    y: box.top,
    width: box.width - box.left - box.right,
    height: box.height - box.top - box.bottom,
  }
  const maximum = Math.max(0, ...rows.flatMap((row) => [row.observed_share, row.expected_share]))
  const axis = axisMaximum(maximum)
  const slot = rows.length > 0 ? plot.width / rows.length : 0
  const gap = Math.min(slot * 0.25, 8)
  const scaleY = (share: number): number => plot.y + plot.height - (share / axis.top) * plot.height
  const centre = (index: number): number => plot.x + slot * index + slot / 2
  const bars = rows.map((row, index) => {
    const y = scaleY(row.observed_share)
    return { digit: row.digit, x: plot.x + slot * index + gap / 2, y, width: slot - gap, height: plot.y + plot.height - y, exceeds: row.exceeds }
  })
  const expected = rows.map((row, index) => ({ x: centre(index), y: scaleY(row.expected_share) }))
  const expectedPath = expected.map((point, index) => `${index === 0 ? 'M' : 'L'}${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(' ')
  const tickCount = Math.round(axis.top / axis.step)
  const yTicks = Array.from({ length: tickCount + 1 }, (_, index) => ({ value: index * axis.step, y: scaleY(index * axis.step) }))
  const every = labelEvery(rows.length)
  const xLabels = rows.flatMap((row, index) => (row.digit % every === 0 || every === 1 ? [{ x: centre(index), digit: row.digit }] : []))
  const tickDigits = Number.isInteger(Math.round(axis.step * 1000) / 10) ? 0 : 1
  return { box, plot, bars, expected, expectedPath, yTicks, xLabels, tickDigits }
}
