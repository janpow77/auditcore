// Objekt-URLs und Seitenbilder des Zustandsautomaten von „PDF schwärzen“.

import type { RedactionSource, RedactionStore, RedactionUrls } from './controller'
import type { RedactionPort } from './types'

export const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

const browserUrls: RedactionUrls = {
  create: (blob) => URL.createObjectURL(blob),
  revoke: (url) => URL.revokeObjectURL(url),
}

/**
 * Objekt-URLs von Seitenbildern und Ergebnis; Seitenbilder werden je Seite
 * zwischengespeichert, eine laufende Anfrage je Seite wird geteilt. `generation`
 * steigt bei jedem Verwerfen (neuer Plan, Zurück, Entfernen der Komponente);
 * Antworten einer älteren Generation werden verworfen.
 */
export function createResources(store: RedactionStore, source: RedactionSource) {
  const urls = source.urls ?? browserUrls
  let previews = new Map<number, string>()
  let pending = new Map<number, Promise<void>>()
  let generation = 0

  function dropPreviews(): void {
    for (const url of previews.values()) urls.revoke(url)
    previews = new Map()
    pending = new Map()
    generation += 1
  }

  function dropResult(): void {
    const url = store.get().resultUrl
    if (url) urls.revoke(url)
  }

  function loadPreview(page: number): Promise<void> {
    const cached = previews.get(page)
    if (cached) {
      store.set({ preview: cached, previewError: null })
      return Promise.resolve()
    }
    store.set({ preview: null, previewError: null })
    return pending.get(page) ?? fetchPreview(page)
  }

  function fetchPreview(page: number): Promise<void> {
    const { file, filename, plan } = store.get()
    const port = source.port()
    if (!file || !plan || !port) return Promise.resolve()
    const running = requestPreview(port, file, filename, page)
    const list = pending
    list.set(page, running)
    void running.finally(() => {
      if (list.get(page) === running) list.delete(page)
    })
    return running
  }

  async function requestPreview(port: RedactionPort, file: Blob, filename: string, page: number): Promise<void> {
    const token = generation
    try {
      const image = await port.preview(file, filename, page)
      if (token !== generation) return
      const url = urls.create(image)
      previews.set(page, url)
      if (store.get().page === page) store.set({ preview: url })
    } catch (caught) {
      if (token === generation && store.get().page === page) store.set({ previewError: errorText(caught) })
    }
  }

  return {
    urls,
    loadPreview,
    dropResult,
    generation: (): number => generation,
    /** Seitenbilder und Ergebnis freigeben. */
    dropAll(): void {
      dropPreviews()
      dropResult()
    },
  }
}

export type Resources = ReturnType<typeof createResources>
