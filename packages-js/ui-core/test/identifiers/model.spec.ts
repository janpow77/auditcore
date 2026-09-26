import { parseTable } from '@auditcore/common'
import { describe, expect, it } from 'vitest'
import {
  buildIdentifierBatch,
  buildIdentifierCheck,
  identifierBatchCsv,
  identifierBatchSummary,
  identifierFacts,
  identifierMessages,
  identifierProfileKinds,
  identifierProfileLabel,
  identifierReasonText,
  identifierRowKind,
  identifierRowStatus,
  identifierStatusTone,
  resolveIdentifierKind,
  translator,
  visibleIdentifierRows,
  type IdentifierBatchMapping,
} from '../../src'
import { BATCH_CSV, batchAnswer, identifierCatalogue as catalogue, invalidAnswer, validAnswer } from './fake-port'

const t = translator(identifierMessages, 'de')
const mapping = (patch: Partial<IdentifierBatchMapping> = {}): IdentifierBatchMapping => ({
  table: parseTable(BATCH_CSV, true), hasHeader: true, valueColumn: 2, refColumn: 0, kind: null, kindColumn: 1, countryColumn: null, ...patch,
})

describe('Kennung prüfen – Kernlogik', () => {
  it('bietet je Profil nur dessen Kennungsarten an und kennzeichnet Empfehlung und Altverhalten', () => {
    expect(identifierProfileKinds(catalogue, 'strict')).toHaveLength(7)
    expect(identifierProfileKinds(catalogue, 'flowworkshop.legacy').map((kind) => kind.id)).toEqual(['lei'])
    expect(identifierProfileKinds(catalogue, null)).toEqual([])
    const [strict, legacy] = catalogue.profiles
    expect(identifierProfileLabel(catalogue, strict!, t)).toBe('Streng (Standard) (empfohlen)')
    expect(identifierProfileLabel(catalogue, legacy!, t)).toBe('flowinvoice validators.py (Altverhalten)')
  })

  it('baut die Einzelprüfung nur mit Profil und angebotener Art; Land nur für die USt-IdNr.', () => {
    const base = { catalogue, profile: 'strict', kind: 'iban', value: ' DE89 ', country: 'de' }
    expect(buildIdentifierCheck(base)).toEqual({ ok: true, request: { kind: 'iban', value: ' DE89 ', profile: 'strict' } })
    expect(buildIdentifierCheck({ ...base, kind: 'vat_id' })).toEqual({ ok: true, request: { kind: 'vat_id', value: ' DE89 ', profile: 'strict', country: 'DE' } })
    expect(buildIdentifierCheck({ ...base, value: '  ' })).toMatchObject({ ok: true, request: { value: null } })
    expect(buildIdentifierCheck({ ...base, profile: null })).toEqual({ ok: false, error: 'profile' })
    expect(buildIdentifierCheck({ ...base, profile: 'flowworkshop.legacy' })).toEqual({ ok: false, error: 'kind' })
  })

  it('ordnet Kennungsarten aus Tabellenzellen über Kennung oder Bezeichnung zu', () => {
    expect(resolveIdentifierKind(catalogue, ' USt-IdNr. ')).toBe('vat_id')
    expect(resolveIdentifierKind(catalogue, 'IBAN')).toBe('iban')
    expect(resolveIdentifierKind(catalogue, 'ISIN')).toBe('ISIN')
  })

  it('baut die Stapelprüfung aus Tabelle und Spaltenzuordnung', () => {
    const built = buildIdentifierBatch(catalogue, 'strict', mapping())
    expect(built.ok && built.request.items.map((item) => [item.ref, item.kind, item.value])).toEqual([
      ['B-1', 'iban', 'DE89 3704 0044 0532 0130 00'], ['B-2', 'iban', 'DE89370400440532013001'],
      ['B-3', 'vat_id', 'DE136695976'], ['B-4', 'lei', null], ['B-5', 'ISIN', 'DE0005557508'],
    ])
    const fixed = buildIdentifierBatch(catalogue, 'strict', mapping({ kind: 'iban', refColumn: null, countryColumn: 1 }))
    expect(fixed.ok && fixed.request.items[0]).toEqual({ ref: '2', kind: 'iban', value: 'DE89 3704 0044 0532 0130 00', country: 'IBAN' })
    expect(buildIdentifierBatch(catalogue, 'strict', mapping({ table: null }))).toEqual({ ok: false, error: 'noTable' })
    expect(buildIdentifierBatch(catalogue, 'strict', mapping({ table: parseTable('Kennung\n', true) }))).toEqual({ ok: false, error: 'noRows' })
    expect(buildIdentifierBatch(catalogue, 'strict', mapping({ kindColumn: null }))).toEqual({ ok: false, error: 'kindColumn' })
    expect(buildIdentifierBatch({ ...catalogue, limits: { ...catalogue.limits, max_items: 2 } }, 'strict', mapping())).toEqual({ ok: false, error: 'tooMany' })
  })

  it('begründet Ergebnisse und bezeichnet Einzelheiten deutsch', () => {
    expect(identifierReasonText(invalidAnswer.result, 'Streng', t)).toBe('IBAN-Prüfziffer ist falsch')
    expect(identifierReasonText(validAnswer.result, 'Streng', t)).toBe('Die Kennung erfüllt alle Prüfungen des Profils „Streng“.')
    expect(identifierFacts(catalogue, validAnswer.result, t)).toEqual([
      { key: 'eu', label: 'EU-Mitgliedstaat', value: 'ja' },
      { key: 'checksum', label: 'Prüfziffer', value: 'geprüft' },
    ])
    expect(identifierStatusTone('INVALID')).toBe('danger')
    expect(identifierStatusTone(null)).toBe('neutral')
  })

  it('fasst die Stapelprüfung zusammen, filtert Auffälligkeiten und exportiert CSV', () => {
    expect(identifierBatchSummary(batchAnswer, t)).toBe('5 Zeilen geprüft: 2 gültig, 1 ungültig, 1 ohne Wert, 1 nicht prüfbar')
    expect(visibleIdentifierRows(batchAnswer, true).map((row) => row.ref)).toEqual(['B-2', 'B-4', 'B-5'])
    const last = batchAnswer.results[4]!
    expect(identifierRowStatus(last)).toBeNull()
    expect(identifierRowKind(catalogue, last, { profile: 'strict', items: [{ kind: 'x', value: null }, { kind: 'x', value: null }, { kind: 'x', value: null }, { kind: 'x', value: null }, { kind: 'ISIN', value: 'DE0005557508' }] })).toBe('ISIN')
    const csv = identifierBatchCsv(catalogue, batchAnswer, null, t)
    expect(csv.split('\r\n')[0]).toBe('﻿Bezug;Art;Wert;Ergebnis;Begründung;Normalform')
    expect(csv).toContain('B-2;IBAN;DE89370400440532013001;ungültig;IBAN-Prüfziffer ist falsch;')
  })
})
