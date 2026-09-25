import { createTokenStore, createToastQueue } from '@flowaudit/common'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { effectScope, nextTick, ref } from 'vue'
import {
  formatDate,
  formatNumber,
  formatPercent,
  localeTag,
  nextSort,
  parseNumber,
  RestError,
  saveFile,
  sharedToastQueue,
  useAuthToken,
  useClickOutside,
  useDebouncedFn,
  useDebouncedRef,
  useMediaQuery,
  useSort,
  useThrottledFn,
  useToast,
} from '../src'

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('Re-Exporte aus @flowaudit/common (API unverändert)', () => {
  it('behält Namen und Signaturen', () => {
    expect(localeTag('de')).toBe('de-DE')
    expect(formatDate('kaputt', 'de')).toBe('')
    expect(formatNumber(1234.5, 'de')).toBe('1.234,5')
    expect(formatPercent(0.5, 'de')).toBe('50 %')
    expect(nextSort(null, 'a')).toEqual({ key: 'a', direction: 'asc' })
    expect(parseNumber('1.234,5', ',')).toBe(1234.5)
    expect(new RestError('x', 400, 'c')).toBeInstanceOf(Error)
    expect(typeof saveFile).toBe('function')
  })
})

describe('Composables', () => {
  it('useToast folgt der Warteschlange und meldet sich ab', () => {
    vi.useFakeTimers()
    const queue = createToastQueue({ defaultMs: 100 })
    const scope = effectScope()
    const toast = scope.run(() => useToast(queue))!
    toast.success('gespeichert')
    expect(toast.toasts.value.map((entry) => entry.message)).toEqual(['gespeichert'])
    vi.advanceTimersByTime(100)
    expect(toast.toasts.value).toEqual([])
    scope.stop()
    queue.info('danach')
    expect(toast.toasts.value).toEqual([])
    expect(sharedToastQueue()).toBe(sharedToastQueue())
    expect(useToast().toasts.value).toEqual([])
  })

  it('useSort sortiert reaktiv', () => {
    const rows = ref([{ n: 2 }, { n: 1 }])
    const { sorted, toggle, sort, ariaSortFor } = useSort(rows, { cycle: 'bi' })
    toggle('n')
    expect(sorted.value.map((row) => row.n)).toEqual([1, 2])
    toggle('n')
    toggle('n')
    expect(sort.value).toEqual({ key: 'n', direction: 'asc' })
    expect(ariaSortFor('n')).toBe('ascending')
    rows.value = [...rows.value, { n: 0 }]
    expect(sorted.value.map((row) => row.n)).toEqual([0, 1, 2])
  })

  it('useDebouncedFn und useDebouncedRef verwerfen beim Abbau', async () => {
    vi.useFakeTimers()
    const fn = vi.fn()
    const source = ref('a')
    const scope = effectScope()
    const { debounced, value, throttled } = scope.run(() => ({
      debounced: useDebouncedFn(fn, 50),
      value: useDebouncedRef(source, 50, source.value),
      throttled: useThrottledFn(fn, 50),
    }))!
    source.value = 'ab'
    await nextTick()
    vi.advanceTimersByTime(50)
    expect(value.value).toBe('ab')
    throttled(1)
    throttled(2)
    debounced(3)
    scope.stop()
    vi.advanceTimersByTime(100)
    expect(fn.mock.calls).toEqual([[1]])
  })

  it('useAuthToken spiegelt den Speicher', () => {
    const store = createTokenStore({ storage: 'memory' })
    const scope = effectScope()
    const auth = scope.run(() => useAuthToken(store))!
    expect(auth.expired.value).toBe(true)
    auth.set('abc')
    expect(auth.token.value).toBe('abc')
    expect(auth.headers.value).toEqual({ Authorization: 'Bearer abc' })
    expect(auth.expired.value).toBe(false)
    auth.clear()
    expect(auth.headers.value).toEqual({})
    scope.stop()
  })

  it('useMediaQuery und useClickOutside', async () => {
    const listeners = new Map<string, (event: { matches: boolean }) => void>()
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: query.includes('dark'),
      addEventListener: (_: string, fn: (event: { matches: boolean }) => void) => listeners.set(query, fn),
      removeEventListener: () => listeners.delete(query),
    }))
    const query = ref('(prefers-color-scheme: dark)')
    const scope = effectScope()
    const matches = scope.run(() => useMediaQuery(query))!
    expect(matches.value).toBe(true)
    listeners.get(query.value)?.({ matches: false })
    expect(matches.value).toBe(false)
    query.value = '(max-width: 1px)'
    await nextTick()
    expect(matches.value).toBe(false)
    expect(listeners.size).toBe(1)

    const element = document.createElement('div')
    document.body.append(element)
    const handler = vi.fn()
    scope.run(() => useClickOutside(ref(element), handler))
    document.body.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    element.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    expect(handler).toHaveBeenCalledTimes(1)
    scope.stop()
    document.body.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    expect(handler).toHaveBeenCalledTimes(1)
    expect(listeners.size).toBe(0)
  })
})
