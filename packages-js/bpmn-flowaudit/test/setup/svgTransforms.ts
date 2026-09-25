/**
 * happy-dom lacks `SVGTransformList.consolidate`, which diagram-js uses via
 * tiny-svg when moving graphics. This adds a minimal version: all items are
 * multiplied into one matrix transform.
 */

interface TransformList {
  numberOfItems: number
  getItem(index: number): { matrix: DOMMatrix }
  clear(): void
  appendItem(item: unknown): unknown
}

const listPrototype = (globalThis as unknown as { SVGTransformList?: { prototype: Record<string, unknown> } }).SVGTransformList?.prototype

if (listPrototype && typeof listPrototype.consolidate !== 'function') {
  listPrototype.consolidate = function consolidate(this: TransformList) {
    if (!this.numberOfItems) return null
    let matrix = this.getItem(0).matrix
    for (let index = 1; index < this.numberOfItems; index += 1) matrix = matrix.multiply(this.getItem(index).matrix)
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg') as unknown as { createSVGTransformFromMatrix(m: DOMMatrix): unknown }
    this.clear()
    return this.appendItem(svg.createSVGTransformFromMatrix(matrix))
  }
}

/**
 * `getCTM()` returns a DOMMatrix in happy-dom, but `SVGMatrix.multiply`
 * accepts only SVGMatrix (diagram-js `Canvas.scroll`). Other matrices are
 * converted first.
 */
type MatrixValues = { a: number; b: number; c: number; d: number; e: number; f: number }
const SvgMatrix = (globalThis as unknown as { SVGMatrix?: { prototype: { multiply(m: unknown): unknown } } }).SVGMatrix

if (SvgMatrix) {
  const multiply = SvgMatrix.prototype.multiply
  SvgMatrix.prototype.multiply = function patchedMultiply(this: unknown, other: unknown) {
    if (other instanceof (SvgMatrix as unknown as new () => unknown)) return multiply.call(this, other)
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg') as unknown as { createSVGMatrix(): MatrixValues }
    const converted = Object.assign(svg.createSVGMatrix(), pick(other as MatrixValues))
    return multiply.call(this, converted)
  }
}

function pick(m: MatrixValues): MatrixValues {
  return { a: m.a, b: m.b, c: m.c, d: m.d, e: m.e, f: m.f }
}
