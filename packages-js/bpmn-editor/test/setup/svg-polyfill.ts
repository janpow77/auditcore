/**
 * Ergänzt die SVG-Schnittstellen, die happy-dom nicht vollständig abbildet
 * und die diagram-js bzw. tiny-svg benötigen (Transformationslisten).
 */
const proto = (globalThis as unknown as { SVGTransformList?: { prototype: Record<string, unknown> } })
  .SVGTransformList?.prototype

if (proto && typeof proto.consolidate !== 'function') {
  proto.consolidate = function consolidate(this: {
    numberOfItems: number
    getItem(i: number): { matrix: DOMMatrix }
    clear(): void
    appendItem(t: unknown): unknown
  }) {
    if (this.numberOfItems === 0) return null
    let matrix = this.getItem(0).matrix
    for (let i = 1; i < this.numberOfItems; i++) {
      matrix = matrix.multiply(this.getItem(i).matrix)
    }
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg') as unknown as {
      createSVGTransformFromMatrix(m: DOMMatrix): unknown
    }
    const transform = svg.createSVGTransformFromMatrix(matrix)
    this.clear()
    return this.appendItem(transform)
  }
}
