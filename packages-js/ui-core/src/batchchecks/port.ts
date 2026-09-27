import type { BatchchecksAnswer, BatchchecksCatalogue, BatchchecksPort } from './types'

/**
 * Port mit festen Antworten (Demo ohne Server, Tests): Katalog und Antwort
 * wie vom Dienst; der Export liefert die Antwort als JSON-Datei.
 */
export function createBatchchecksMemoryPort(catalogue: BatchchecksCatalogue, answer: BatchchecksAnswer): BatchchecksPort {
  return {
    catalogue: async () => catalogue,
    run: async () => answer,
    exportRun: async (_request, format) => ({
      blob: new Blob([JSON.stringify(answer, null, 2)], { type: 'application/json' }),
      filename: `befunde-bestand.${format}`,
      mediaType: 'application/json',
    }),
  }
}
