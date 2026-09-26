/**
 * Port mit den Antworten des echten auditcore_identifiers.web (Fixtures,
 * synthetische Kennungen). `calls` hält die Anfragen fest; `failing` lässt
 * eine Methode scheitern.
 */
import type { IdentifierBatchAnswer, IdentifierCatalogue, IdentifierCheckAnswer, IdentifiersPort } from '../../src'
import batch from '../fixtures/identifiers-batch.json'
import catalogue from '../fixtures/identifiers-catalogue.json'
import invalid from '../fixtures/identifiers-check-invalid.json'
import valid from '../fixtures/identifiers-check-valid.json'

export const identifierCatalogue = catalogue as unknown as IdentifierCatalogue
export const invalidAnswer = invalid as unknown as IdentifierCheckAnswer
export const validAnswer = valid as unknown as IdentifierCheckAnswer
export const batchAnswer = batch as unknown as IdentifierBatchAnswer

/** Synthetische Tabelle für die Stapelprüfung (Semikolon, Kopfzeile). */
export const BATCH_CSV = 'Beleg;Art;Kennung\nB-1;IBAN;DE89 3704 0044 0532 0130 00\nB-2;iban;DE89370400440532013001\nB-3;USt-IdNr.;DE136695976\nB-4;LEI;\nB-5;ISIN;DE0005557508\n'

export type IdentifierFake = IdentifiersPort & { calls: Record<'check' | 'batch', unknown[]> }

export function fakeIdentifiersPort(failing?: keyof IdentifiersPort, message = 'Dienst nicht erreichbar'): IdentifierFake {
  const calls: IdentifierFake['calls'] = { check: [], batch: [] }
  const fail = (name: keyof IdentifiersPort): void => {
    if (failing === name) throw new Error(message)
  }
  return {
    calls,
    catalogue: async () => (fail('catalogue'), identifierCatalogue),
    check: async (request) => {
      fail('check')
      calls.check.push(request)
      return request.kind === 'vat_id' ? validAnswer : invalidAnswer
    },
    checkBatch: async (request) => (fail('checkBatch'), calls.batch.push(request), batchAnswer),
  }
}
