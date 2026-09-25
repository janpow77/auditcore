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

/*
 * happy-dom liefert für getCTM/getBBox keine Layoutwerte. Für diagram-js
 * genügen: CTM aus der eigenen Transformationsliste, BBox mit fester Größe.
 */
type Graphics = {
  prototype: {
    getCTM?: () => unknown
    getBBox?: () => unknown
    transform?: { baseVal: { consolidate(): { matrix: unknown } | null } }
  }
}
const graphics = (globalThis as unknown as { SVGGraphicsElement?: Graphics }).SVGGraphicsElement
if (graphics) {
  graphics.prototype.getCTM = function getCTM(this: { transform?: { baseVal: { consolidate(): { matrix: unknown } | null } } }) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg') as unknown as { createSVGMatrix(): unknown }
    const consolidated = this.transform?.baseVal.consolidate()
    return consolidated ? consolidated.matrix : svg.createSVGMatrix()
  }
  graphics.prototype.getBBox = () => ({ x: 0, y: 0, width: 100, height: 100 })
}

if (proto && typeof proto.createSVGTransformFromMatrix !== 'function') {
  proto.createSVGTransformFromMatrix = function createSVGTransformFromMatrix(matrix: unknown) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg') as unknown as {
      createSVGTransformFromMatrix(m: unknown): unknown
    }
    return svg.createSVGTransformFromMatrix(matrix)
  }
}
