/**
 * Port mit den Antworten des echten Python-Dienstes (Fixture von
 * auditcore_documents.web, Bestandsprüfung des synthetischen
 * Beispielbestands). `calls` hält die Anfragen fest.
 */
import type { BatchchecksAnswer, BatchchecksCatalogue, BatchchecksExportFormat, BatchchecksPort, BatchchecksRequest } from '../../src'
import contract from '../fixtures/batch-checks-contract.json'

export const batchCatalogue = contract.catalogue as unknown as BatchchecksCatalogue
export const batchAnswer = contract.answer as unknown as BatchchecksAnswer
export const batchAnswerPlain = contract.answer_plain as unknown as BatchchecksAnswer
/** Beispielbestand als CSV (Semikolon, deutsche Zahlen). */
export const batchCsv: string = contract.csv

export type BatchchecksFake = BatchchecksPort & { calls: Array<[string, BatchchecksRequest | null, BatchchecksExportFormat | null]> }

export function fakeBatchchecksPort(options: { failing?: keyof BatchchecksPort; answer?: BatchchecksAnswer } = {}): BatchchecksFake {
  const calls: BatchchecksFake['calls'] = []
  const fail = (name: keyof BatchchecksPort): void => {
    if (options.failing === name) throw new Error('Dienst nicht erreichbar')
  }
  return {
    calls,
    catalogue: async () => (fail('catalogue'), calls.push(['catalogue', null, null]), batchCatalogue),
    run: async (request) => (fail('run'), calls.push(['run', request, null]), options.answer ?? batchAnswer),
    exportRun: async (request, format) => {
      fail('exportRun')
      calls.push(['export', request, format])
      return { blob: new Blob(['x']), filename: `befunde-bestand.${format}`, mediaType: 'text/csv' }
    },
  }
}

/** Datei aus Text (CSV oder JSON). */
export function textFile(text: string, name: string): File {
  return new File([text], name, { type: name.endsWith('.json') ? 'application/json' : 'text/csv' })
}
