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

export const DEFAULT_PAGE_FORMAT: PageFormat = { id: 'a4', label: 'DIN A4', widthMm: 210, heightMm: 297 }

export const PAGE_FORMATS: readonly PageFormat[] = [DEFAULT_PAGE_FORMAT, { id: 'a3', label: 'DIN A3', widthMm: 297, heightMm: 420 }]

export interface PageSize {
  widthPx: number
  heightPx: number
}

/** Page size in diagram pixels, including orientation. */
export function pageSize(formatId: string, orientation: Orientation, marginMm = 0): PageSize {
  const format = PAGE_FORMATS.find((entry) => entry.id === formatId) ?? DEFAULT_PAGE_FORMAT
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

interface GridRange {
  left: number
  right: number
  top: number
  bottom: number
}

function positive(...values: number[]): boolean {
  return values.every((value) => value > 0)
}

function pageLabels(range: GridRange, size: PageSize, toX: (x: number) => number, toY: (y: number) => number, screen: { width: number; height: number }, pageLabel: string): PageGrid['pages'] {
  const pages: PageGrid['pages'] = []
  for (let column = range.left; column < range.right; column += 1) {
    for (let row = range.top; row < range.bottom; row += 1) {
      const x = toX(column * size.widthPx) + 6
      const y = toY(row * size.heightPx) + 16
      const visible = x >= -60 && x <= screen.width && y >= 0 && y <= screen.height
      if (visible) pages.push({ x, y, label: `${pageLabel} ${row + 1}/${column + 1}` })
    }
  }
  return pages
}

/**
 * Computes the page break grid for the current view. The origin is the
 * diagram origin (0/0), so the grid moves with the diagram like a printout.
 */
export function computePageGrid(viewbox: ViewboxLike, size: PageSize, screenWidth: number, screenHeight: number, pageLabel = 'Seite'): PageGrid {
  const { widthPx, heightPx } = size
  if (!positive(widthPx, heightPx, viewbox.scale)) return EMPTY_GRID
  const range: GridRange = {
    left: Math.floor(viewbox.x / widthPx),
    right: Math.ceil((viewbox.x + viewbox.width) / widthPx),
    top: Math.floor(viewbox.y / heightPx),
    bottom: Math.ceil((viewbox.y + viewbox.height) / heightPx),
  }
  // More than 200 lines per axis is only load, nobody reads that.
  if (range.right - range.left > 200 || range.bottom - range.top > 200) return EMPTY_GRID
  const toX = (x: number) => (x - viewbox.x) * viewbox.scale
  const toY = (y: number) => (y - viewbox.y) * viewbox.scale
  return {
    vertical: lines(range.left, range.right, widthPx, toX, screenWidth),
    horizontal: lines(range.top, range.bottom, heightPx, toY, screenHeight),
    pages: pageLabels(range, size, toX, toY, { width: screenWidth, height: screenHeight }, pageLabel),
  }
}
