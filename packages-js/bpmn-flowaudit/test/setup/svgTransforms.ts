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
