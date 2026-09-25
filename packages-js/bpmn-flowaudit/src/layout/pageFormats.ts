/**
 * Page formats and page break guides, ported from `seitenformate.ts` of the
 * audit_designer (`seitenMasse` → `pageSize`, `berechneRaster` →
 * `computePageGrid`).
 *
 * BPMN coordinates are CSS pixels; at 96 dpi 1 mm ≈ 3.7795 px. The guides
 * show where a printout breaks – a process diagram running over the fold
 * is useless in the file.
 */

export const PX_PER_MM = 96 / 25.4

export type Orientation = 'hoch' | 'quer'

export interface PageFormat {
  id: string
  label: string
  /** Edge lengths in portrait orientation, in millimetres. */
  widthMm: number
  heightMm: number
}

export const PAGE_FORMATS: readonly PageFormat[] = [
  { id: 'a4', label: 'DIN A4', widthMm: 210, heightMm: 297 },
  { id: 'a3', label: 'DIN A3', widthMm: 297, heightMm: 420 },
] as const

export interface PageSize {
  widthPx: number
  heightPx: number
}

/** Page size in diagram pixels, including orientation. */
export function pageSize(formatId: string, orientation: Orientation, marginMm = 0): PageSize {
  const format = PAGE_FORMATS.find((entry) => entry.id === formatId) ?? PAGE_FORMATS[0]
  const width = Math.max(format.widthMm - 2 * marginMm, 10)
  const height = Math.max(format.heightMm - 2 * marginMm, 10)
  const [w, h] = orientation === 'quer' ? [height, width] : [width, height]
  return { widthPx: w * PX_PER_MM, heightPx: h * PX_PER_MM }
}

export interface ViewboxLike {
  x: number
  y: number
  width: number
  height: number
  scale: number
}

export interface PageGrid {
  /** Vertical lines in screen pixels relative to the canvas. */
  vertical: number[]
  horizontal: number[]
  pages: { x: number; y: number; label: string }[]
}

const EMPTY_GRID: PageGrid = { vertical: [], horizontal: [], pages: [] }

function lines(start: number, end: number, step: number, toScreen: (v: number) => number, limit: number): number[] {
  const result: number[] = []
  for (let index = start; index <= end; index += 1) {
    const px = toScreen(index * step)
    if (px >= -1 && px <= limit + 1) result.push(px)
  }
  return result
}

/**
 * Computes the page break grid for the current view. The origin is the
 * diagram origin (0/0), so the grid moves with the diagram like a printout.
 */
export function computePageGrid(viewbox: ViewboxLike, size: PageSize, screenWidth: number, screenHeight: number, pageLabel = 'Seite'): PageGrid {
  const { widthPx, heightPx } = size
  if (!(widthPx > 0) || !(heightPx > 0) || !(viewbox.scale > 0)) return EMPTY_GRID
  const left = Math.floor(viewbox.x / widthPx)
  const right = Math.ceil((viewbox.x + viewbox.width) / widthPx)
  const top = Math.floor(viewbox.y / heightPx)
  const bottom = Math.ceil((viewbox.y + viewbox.height) / heightPx)
  // More than 200 lines per axis is only load, nobody reads that.
  if (right - left > 200 || bottom - top > 200) return EMPTY_GRID
  const toX = (x: number) => (x - viewbox.x) * viewbox.scale
  const toY = (y: number) => (y - viewbox.y) * viewbox.scale
  const pages: PageGrid['pages'] = []
  for (let column = left; column < right; column += 1) {
    for (let row = top; row < bottom; row += 1) {
      const x = toX(column * widthPx) + 6
      const y = toY(row * heightPx) + 16
      if (x >= -60 && x <= screenWidth && y >= 0 && y <= screenHeight) pages.push({ x, y, label: `${pageLabel} ${row + 1}/${column + 1}` })
    }
  }
  return {
    vertical: lines(left, right, widthPx, toX, screenWidth),
    horizontal: lines(top, bottom, heightPx, toY, screenHeight),
    pages,
  }
}
