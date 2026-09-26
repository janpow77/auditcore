/**
 * Port mit den Antworten des echten Python-Dienstes (Fixture von
 * auditcore_documents.web, Belegerkennung mit Attrappen-Ports und
 * synthetischen Rechnungsbildern). `calls` hält die Läufe fest.
 */
import type { ExtractionCatalogue, ExtractionPort, ExtractionRun } from '../../src'
import contract from '../fixtures/extraction-contract.json'

export const extractionCatalogue = contract.catalogue as unknown as ExtractionCatalogue
export const extractionDisabled = contract.catalogue_disabled as unknown as ExtractionCatalogue
export const runOk = contract.run_ok as unknown as ExtractionRun
export const runReview = contract.run_review as unknown as ExtractionRun
export const runDonut = contract.run_donut as unknown as ExtractionRun
export const runFailed = contract.run_failed as unknown as ExtractionRun

export type ExtractionFake = ExtractionPort & { calls: Array<[string, string, number]> }

export function fakeExtractionPort(options: { failing?: keyof ExtractionPort; catalogue?: ExtractionCatalogue; result?: ExtractionRun } = {}): ExtractionFake {
  const calls: ExtractionFake['calls'] = []
  const fail = (name: keyof ExtractionPort): void => {
    if (options.failing === name) throw new Error('Dienst nicht erreichbar')
  }
  return {
    calls,
    catalogue: async () => (fail('catalogue'), options.catalogue ?? extractionCatalogue),
    run: async (file, filename, profile) => (fail('run'), calls.push([filename, profile, file.size]), options.result ?? runDonut),
  }
}

/** Synthetische Bilddatei (nur PNG-Signatur). */
export function syntheticFile(name = 'beleg.png', size = 64): File {
  const bytes = new Uint8Array(size)
  bytes.set([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
  return new File([bytes], name, { type: 'image/png' })
}
