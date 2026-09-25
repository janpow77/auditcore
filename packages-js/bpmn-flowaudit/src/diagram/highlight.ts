/**
 * Highlighting through canvas markers (CSS classes on the graphics):
 * key filter („all elements for key X“), walk-through state and graphical
 * diff. Each layer is independent; styles live in `style.css`.
 */

import type { Canvas, DiagramElement, ElementRegistry } from './services'

export type HighlightLayer = 'filter' | 'walkthrough' | 'diff' | 'issues'

/** CSS classes per layer and state. */
export const HIGHLIGHT_CLASSES = {
  filter: { hit: 'fa-hit', dimmed: 'fa-dimmed' },
  walkthrough: { current: 'fa-walk-current', erfuellt: 'fa-walk-met', nicht_erfuellt: 'fa-walk-not-met', offen: 'fa-walk-open', nicht_anwendbar: 'fa-walk-na' },
  diff: { hinzugefuegt: 'fa-diff-added', entfallen: 'fa-diff-removed', geaendert: 'fa-diff-changed', unveraendert: 'fa-diff-same' },
  issues: { fehler: 'fa-issue-error', warnung: 'fa-issue-warning', hinweis: 'fa-issue-note' },
} as const

export class FlowauditHighlight {
  static $inject = ['canvas', 'elementRegistry']

  private readonly applied = new Map<HighlightLayer, [string, string][]>()

  constructor(
    private readonly canvas: Canvas,
    private readonly elementRegistry: ElementRegistry,
  ) {}

  private shapes(): DiagramElement[] {
    const root = this.canvas.getRootElement()
    return this.elementRegistry.filter((element) => element !== root && !element.labelTarget)
  }

  clear(layer: HighlightLayer): void {
    for (const [id, marker] of this.applied.get(layer) ?? []) {
      if (this.elementRegistry.get(id)) this.canvas.removeMarker(id, marker)
    }
    this.applied.delete(layer)
  }

  clearAll(): void {
    for (const layer of [...this.applied.keys()]) this.clear(layer)
  }

  /** Sets classes by element id; replaces the previous state of the layer. */
  apply(layer: HighlightLayer, classes: Map<string, string>): void {
    this.clear(layer)
    const applied: [string, string][] = []
    for (const [id, marker] of classes) {
      if (!this.elementRegistry.get(id)) continue
      this.canvas.addMarker(id, marker)
      applied.push([id, marker])
    }
    this.applied.set(layer, applied)
  }

  /** Key filter: hits emphasised, everything else dimmed. Returns the hit count. */
  filter(ids: string[]): number {
    const hits = new Set(ids)
    const classes = new Map<string, string>()
    for (const shape of this.shapes()) classes.set(shape.id, hits.has(shape.id) ? HIGHLIGHT_CLASSES.filter.hit : HIGHLIGHT_CLASSES.filter.dimmed)
    this.apply('filter', classes)
    return ids.filter((id) => this.elementRegistry.get(id)).length
  }
}

export const highlightModule = {
  __init__: ['flowauditHighlight'],
  flowauditHighlight: ['type', FlowauditHighlight],
}
