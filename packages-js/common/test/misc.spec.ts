import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ariaSort,
  compareValues,
  createToastQueue,
  formatIban,
  isValidIban,
  isValidLeitwegId,
  iso7064CheckDigits,
  leitwegCheckDigits,
  mod97,
  newId,
  nextSort,
  shortId,
  sortRows,
} from '../src'

describe('Sortierung', () => {
  it('sortiert stabil mit leeren Werten zuletzt', () => {
    const rows = [{ v: 2 }, { v: null }, { v: 10 }, { v: 2 }]
    expect(sortRows(rows, { key: 'v', direction: 'desc' }).map((row) => row.v)).toEqual([10, 2, 2, null])
    expect(sortRows(rows, null)).toEqual(rows)
    expect(compareValues('Prüfung 10', 'Prüfung 9')).toBeGreaterThan(0)
    expect(compareValues(new Date(1), new Date(2))).toBeLessThan(0)
    expect(compareValues(true, false)).toBe(1)
  })

  it('schaltet drei- oder zweistufig', () => {
    expect(nextSort(null, 'a')).toEqual({ key: 'a', direction: 'asc' })
    expect(nextSort({ key: 'a', direction: 'asc' }, 'a')).toEqual({ key: 'a', direction: 'desc' })
    expect(nextSort({ key: 'a', direction: 'desc' }, 'a')).toBeNull()
    expect(nextSort({ key: 'a', direction: 'desc' }, 'a', { cycle: 'bi' })).toEqual({ key: 'a', direction: 'asc' })
    expect(ariaSort({ key: 'a', direction: 'desc' }, 'a')).toBe('descending')
    expect(ariaSort(null, 'a')).toBe('none')
  })
})

describe('Prüfziffern', () => {
  it('rechnet MOD 97-10', () => {
    expect(mod97('3704004405320130001314' + '00')).toBe(mod97('370400440532013000131400'))
    expect(() => mod97('12a')).toThrow(RangeError)
    expect(iso7064CheckDigits('370400440532013000DE')).toBe('89')
    expect(formatIban('de89370400440532013000')).toBe('DE89 3704 0044 0532 0130 00')
    expect(isValidIban('DE89-3704')).toBe(false)
  })

  it('prüft Leitweg-IDs', () => {
    expect(leitwegCheckDigits('04011000-1234512345')).toBe('06')
    expect(isValidLeitwegId('04011000-1234512345-06')).toBe(true)
    expect(isValidLeitwegId('04011000-1234512345-07')).toBe(false)
    expect(isValidLeitwegId(`991-33333TEST-${leitwegCheckDigits('991-33333TEST')}`)).toBe(true)
    expect(isValidLeitwegId('kein-leitweg')).toBe(false)
  })
})

describe('Kennungen', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('erzeugt UUID v4 auch ohne randomUUID', () => {
    const pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
    expect(newId()).toMatch(pattern)
    vi.stubGlobal('crypto', { getRandomValues: (bytes: Uint8Array) => bytes.fill(255) })
    expect(newId()).toBe('ffffffff-ffff-4fff-bfff-ffffffffffff')
    vi.stubGlobal('crypto', undefined)
    expect(newId()).toMatch(pattern)
    expect(shortId('x')).toMatch(/^x-[0-9a-z]{6}$/)
  })
})

describe('Toast-Warteschlange', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('blendet nach der Dauer aus und begrenzt die Anzahl', () => {
    vi.useFakeTimers()
    const queue = createToastQueue({ defaultMs: 1000, errorMs: 3000, max: 2 })
    const seen = vi.fn()
    const stop = queue.subscribe(seen)
    queue.success('gespeichert')
    const errorId = queue.error('fehlgeschlagen', 'Upload')
    expect(queue.list().map((toast) => toast.kind)).toEqual(['success', 'error'])
    vi.advanceTimersByTime(1000)
    expect(queue.list().map((toast) => toast.id)).toEqual([errorId])
    queue.info('a')
    queue.warning('b')
    expect(queue.list().map((toast) => toast.message)).toEqual(['a', 'b'])
    queue.push({ message: 'bleibt', durationMs: 0 })
    vi.advanceTimersByTime(10_000)
    expect(queue.list().map((toast) => toast.message)).toEqual(['bleibt'])
    queue.dismiss(999)
    queue.clear()
    expect(queue.list()).toEqual([])
    stop()
    queue.info('still')
    expect(seen.mock.calls.at(-1)?.[0]).toEqual([])
  })
})
