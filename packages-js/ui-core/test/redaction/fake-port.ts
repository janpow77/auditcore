/**
 * Port mit den Antworten des echten Python-Dienstes (Fixture aus
 * `ui/demo/redaction_demo.py`: synthetische PDF, Attrappe der
 * KI-Namenserkennung). `calls` hält die Anfragen fest.
 */
import type { RedactionCatalogue, RedactionPlan, RedactionPort, RedactionResult, RedactionSelection, RedactionUrls } from '../../src'
import contract from '../fixtures/redaction-contract.json'

export const redactionCatalogue = contract.catalogue as unknown as RedactionCatalogue
export const redactionCatalogueWithoutNer = contract.catalogue_without_ner as unknown as RedactionCatalogue
export const redactionPlan = contract.plan as unknown as RedactionPlan
export const redactionEmptyPlan = contract.empty_plan as unknown as RedactionPlan

export const redactionReport: RedactionResult['report'] = { redactions: 7, areas: 1, hidden: 2, deselected: 0, pages: 2, sanitized: true, verified: true }

export type RedactionCall = ['plan', string, string] | ['preview', string, number] | ['apply', string, RedactionSelection]
export type RedactionFake = RedactionPort & { calls: RedactionCall[] }

export function fakeRedactionPort(options: { failing?: keyof RedactionPort; catalogue?: RedactionCatalogue; plan?: RedactionPlan } = {}): RedactionFake {
  const calls: RedactionCall[] = []
  const fail = (name: keyof RedactionPort): void => {
    if (options.failing === name) throw new Error('Dienst nicht erreichbar')
  }
  return {
    calls,
    catalogue: async () => (fail('catalogue'), options.catalogue ?? redactionCatalogue),
    plan: async (_file, filename, criteria) => (fail('plan'), calls.push(['plan', filename, JSON.stringify(criteria)]), options.plan ?? redactionPlan),
    preview: async (_file, filename, page) => (fail('preview'), calls.push(['preview', filename, page]), new Blob([`seite-${page}`], { type: 'image/png' })),
    apply: async (_file, filename, selection) => {
      fail('apply')
      calls.push(['apply', filename, selection])
      return { blob: new Blob(['%PDF-1.7 geschwärzt'], { type: 'application/pdf' }), filename: 'vermerk_geschwärzt.pdf', report: { ...redactionReport, areas: selection.areas.length } }
    },
  }
}

/** Objekt-URLs ohne Browser: eindeutig je Inhalt, damit Vue und React dieselben Werte zeigen. */
export function fakeUrls(): RedactionUrls & { live: Set<string> } {
  const live = new Set<string>()
  return {
    live,
    create: (blob) => {
      const url = `blob:fa-test/${blob.type}/${blob.size}`
      live.add(url)
      return url
    },
    revoke: (url) => void live.delete(url),
  }
}

/** Synthetische PDF-Datei (nur Signatur; der Fake-Port liest sie nicht). */
export function syntheticPdf(name = 'vermerk.pdf', size = 64): File {
  const bytes = new Uint8Array(size)
  bytes.set([0x25, 0x50, 0x44, 0x46, 0x2d])
  return new File([bytes], name, { type: 'application/pdf' })
}
