/**
 * Thumbnails of diagrams for the folder overview. A host may deliver them
 * (`StoragePort.thumbnail`, e.g. rendered on the server); otherwise they are
 * rendered in the browser from the XML with the editor core and kept per
 * diagram until the diagram is saved again. At most `concurrency` renders
 * run at the same time; a failure yields `null` (the view shows a
 * placeholder).
 */

import type { StoragePort } from '../ports'
import type { EditorFactory } from './editorFactory'

/** XML → image URL (`data:` or `https:`); `null` when nothing can be shown. */
export type ThumbnailRenderer = (xml: string) => Promise<string | null>

export interface Thumbnails {
  get(diagramId: string): Promise<string | null>
  /** Forget the picture of a diagram (after saving it). */
  invalidate(diagramId: string): void
  clear(): void
}

export interface ThumbnailOptions {
  storage: StoragePort
  render?: ThumbnailRenderer
  concurrency?: number
}

function limiter(concurrency: number) {
  let running = 0
  const waiting: (() => void)[] = []
  return async function run<T>(task: () => Promise<T>): Promise<T> {
    if (running >= concurrency) await new Promise<void>((resolve) => waiting.push(resolve))
    running += 1
    try {
      return await task()
    } finally {
      running -= 1
      waiting.shift()?.()
    }
  }
}

export function createThumbnails(options: ThumbnailOptions): Thumbnails {
  const cache = new Map<string, Promise<string | null>>()
  const run = limiter(Math.max(1, options.concurrency ?? 2))

  async function produce(id: string): Promise<string | null> {
    const delivered = await options.storage.thumbnail?.(id)
    if (delivered) return delivered
    if (!options.render) return null
    return options.render(await options.storage.loadDiagram(id))
  }

  return {
    get(id) {
      let entry = cache.get(id)
      if (!entry) {
        entry = run(() => produce(id)).catch(() => null)
        cache.set(id, entry)
      }
      return entry
    },
    invalidate: (id) => void cache.delete(id),
    clear: () => cache.clear(),
  }
}

const OFFSCREEN = 'position:fixed;left:-20000px;top:0;width:1200px;height:800px;visibility:hidden;pointer-events:none'

/** Renders a thumbnail in the browser with the editor core (read-only use, destroyed afterwards). */
export function createSvgThumbnailRenderer(factory: EditorFactory, locale: 'de' | 'en' = 'de'): ThumbnailRenderer {
  return async (xml) => {
    if (typeof document === 'undefined') return null
    const container = document.createElement('div')
    container.setAttribute('aria-hidden', 'true')
    container.style.cssText = OFFSCREEN
    document.body.appendChild(container)
    const editor = factory({ container, locale, flowaudit: { rolePalette: false } })
    try {
      await editor.importXML(xml)
      const { svg } = await editor.saveSVG()
      return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
    } finally {
      editor.destroy()
      container.remove()
    }
  }
}
