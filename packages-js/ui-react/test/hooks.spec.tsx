import { createToastQueue, createTokenStore, type SortState } from '@auditcore/common'
import { act, createRef, useRef } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ToastProvider,
  formatDate,
  localeTag,
  nextSort,
  parseNumber,
  sharedToastQueue,
  useAuthToken,
  useClickOutside,
  useDebouncedCallback,
  useMediaQuery,
  useSort,
  useToast,
  type UseAuthToken,
  type UseSort,
  type UseToast,
} from '../src'

;(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

let root: Root | null = null

afterEach(() => {
  act(() => root?.unmount())
  root = null
  document.body.innerHTML = ''
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

function render(node: React.ReactNode): HTMLElement {
  const host = document.createElement('div')
  document.body.append(host)
  root = createRoot(host)
  act(() => root?.render(node))
  return host
}

function Capture<T>({ use, into }: { use: () => T; into: { current: T | null } }) {
  into.current = use()
  return null
}

describe('Re-Exporte aus @auditcore/common', () => {
  it('stehen mit den Namen aus @auditcore/ui bereit', () => {
    expect(localeTag('en')).toBe('en-GB')
    expect(formatDate(null, 'de')).toBe('')
    expect(nextSort(null, 'x')).toEqual({ key: 'x', direction: 'asc' })
    expect(parseNumber('1,5', ',')).toBe(1.5)
  })
})

describe('Hooks', () => {
  it('useToast rendert neu und nutzt den Provider', () => {
    vi.useFakeTimers()
    const queue = createToastQueue({ defaultMs: 100 })
    const toast = { current: null as UseToast | null }
    render(
      <ToastProvider queue={queue}>
        <Capture use={() => useToast()} into={toast} />
      </ToastProvider>,
    )
    act(() => void toast.current?.success('gespeichert'))
    expect(toast.current?.toasts.map((entry) => entry.message)).toEqual(['gespeichert'])
    act(() => vi.advanceTimersByTime(100))
    expect(toast.current?.toasts).toEqual([])
    expect(sharedToastQueue()).toBe(sharedToastQueue())
  })

  it('useSort und useDebouncedCallback', () => {
    vi.useFakeTimers()
    const sort = { current: null as UseSort<{ n: number }> | null }
    const rows = [{ n: 2 }, { n: 1 }]
    const fn = vi.fn()
    const debounced = { current: null as ((value: number) => void) | null }
    render(
      <>
        <Capture use={() => useSort(rows, { initial: { key: 'n', direction: 'desc' } satisfies SortState })} into={sort} />
        <Capture use={() => useDebouncedCallback(fn, 50)} into={debounced} />
      </>,
    )
    expect(sort.current?.sorted.map((row) => row.n)).toEqual([2, 1])
    act(() => sort.current?.toggle('n'))
    expect(sort.current?.sort).toBeNull()
    act(() => sort.current?.toggle('n'))
    expect(sort.current?.ariaSortFor('n')).toBe('ascending')
    debounced.current?.(1)
    debounced.current?.(2)
    vi.advanceTimersByTime(50)
    expect(fn.mock.calls).toEqual([[2]])
    debounced.current?.(3)
    act(() => root?.unmount())
    root = null
    vi.advanceTimersByTime(100)
    expect(fn).toHaveBeenCalledTimes(1)
  })

})

describe('Hooks für Speicher und DOM', () => {
  it('useAuthToken folgt dem Speicher', () => {
    const store = createTokenStore({ storage: 'memory' })
    const auth = { current: null as UseAuthToken | null }
    render(<Capture use={() => useAuthToken(store)} into={auth} />)
    expect(auth.current?.expired).toBe(true)
    act(() => auth.current?.set('abc'))
    expect(auth.current?.headers).toEqual({ Authorization: 'Bearer abc' })
    act(() => auth.current?.clear())
    expect(auth.current?.token).toBeNull()
  })

  it('useMediaQuery und useClickOutside', () => {
    let notify: ((event: { matches: boolean }) => void) | undefined
    let matches = true
    vi.stubGlobal('matchMedia', () => ({
      get matches() {
        return matches
      },
      addEventListener: (_: string, fn: (event: { matches: boolean }) => void) => {
        notify = fn
      },
      removeEventListener: () => undefined,
    }))
    const media = { current: null as boolean | null }
    const handler = vi.fn()
    const box = createRef<HTMLDivElement>()
    function Box() {
      const ref = useRef<HTMLDivElement | null>(null)
      useClickOutside(ref, handler)
      return <div ref={(element) => { ref.current = element; (box as { current: HTMLDivElement | null }).current = element }} />
    }
    render(
      <>
        <Capture use={() => useMediaQuery('(max-width: 1px)')} into={media} />
        <Box />
      </>,
    )
    expect(media.current).toBe(true)
    matches = false
    act(() => notify?.({ matches: false }))
    expect(media.current).toBe(false)
    box.current?.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    document.body.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    expect(handler).toHaveBeenCalledTimes(1)
  })
})
