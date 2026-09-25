import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { debounce, keyedDebounce, poll, throttle } from '../src'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('debounce', () => {
  it('ruft nur mit den letzten Argumenten auf', () => {
    const fn = vi.fn()
    const debounced = debounce(fn, 100)
    debounced(1)
    debounced(2)
    expect(debounced.pending()).toBe(true)
    vi.advanceTimersByTime(99)
    expect(fn).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(fn).toHaveBeenCalledWith(2)
    expect(debounced.pending()).toBe(false)
  })

  it('kann abbrechen und sofort ausführen', () => {
    const fn = vi.fn()
    const debounced = debounce(fn, 100)
    debounced('a')
    debounced.cancel()
    vi.advanceTimersByTime(200)
    expect(fn).not.toHaveBeenCalled()
    debounced('b')
    debounced.flush()
    debounced.flush()
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn).toHaveBeenCalledWith('b')
  })
})

describe('throttle', () => {
  it('führt sofort und am Fensterende aus', () => {
    const fn = vi.fn()
    const throttled = throttle(fn, 100)
    throttled(1)
    throttled(2)
    throttled(3)
    expect(fn.mock.calls).toEqual([[1]])
    vi.advanceTimersByTime(100)
    expect(fn.mock.calls).toEqual([[1], [3]])
    throttled(4)
    expect(throttled.pending()).toBe(true)
    throttled.cancel()
    vi.advanceTimersByTime(200)
    expect(fn).toHaveBeenCalledTimes(2)
    throttled(5)
    throttled(6)
    throttled.flush()
    expect(fn.mock.calls.at(-1)).toEqual([6])
  })
})

describe('keyedDebounce', () => {
  it('entprellt je Schlüssel', () => {
    const fn = vi.fn()
    const save = keyedDebounce(fn, 50)
    save('a', 1)
    save('b', 2)
    save('a', 3)
    vi.advanceTimersByTime(50)
    expect(fn.mock.calls).toEqual([['b', 2], ['a', 3]])
    save('c', 4)
    save.cancel('c')
    save('d', 5)
    save.cancel()
    vi.advanceTimersByTime(100)
    expect(fn).toHaveBeenCalledTimes(2)
  })
})

describe('poll', () => {
  it('fragt bis zur Bedingung ab', async () => {
    let count = 0
    const done = poll(async () => ++count, { intervalMs: 1000, until: (value) => value === 3 })
    await vi.advanceTimersByTimeAsync(2000)
    await expect(done).resolves.toBe(3)
  })

  it('verlängert den Abstand nach Fehlern und gibt nach maxAttempts auf', async () => {
    const fn = vi.fn(async () => {
      throw new Error('offline')
    })
    const done = poll(fn, { intervalMs: 100, backoff: { factor: 2, maxMs: 300 }, maxAttempts: 3 })
    const check = expect(done).rejects.toThrow('offline')
    await vi.advanceTimersByTimeAsync(200)
    expect(fn).toHaveBeenCalledTimes(2)
    await vi.advanceTimersByTimeAsync(600)
    await check
    expect(fn).toHaveBeenCalledTimes(3)
  })

  it('wirft ohne backoff sofort, endet ohne Ergebnis und bricht ab', async () => {
    await expect(poll(async () => { throw new Error('x') }, { intervalMs: 10 })).rejects.toThrow('x')
    const limited = poll(async () => 1, { intervalMs: 10, maxAttempts: 1 })
    const limitedCheck = expect(limited).rejects.toThrow('Abfrage ohne Ergebnis beendet')
    await vi.advanceTimersByTimeAsync(10)
    await limitedCheck
    const controller = new AbortController()
    const running = poll(async () => 1, { intervalMs: 1000, signal: controller.signal })
    const abortCheck = expect(running).rejects.toThrow()
    await vi.advanceTimersByTimeAsync(10)
    controller.abort()
    await abortCheck
    await expect(poll(async () => 1, { intervalMs: 10, signal: AbortSignal.abort() })).rejects.toThrow()
  })
})
