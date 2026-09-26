/** @vitest-environment happy-dom */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { copyText, downloadBlob, matchesMediaQuery, onClickOutside, safeStorage, saveFile, subscribeMediaQuery } from '../src/browser'

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
  vi.useRealTimers()
  localStorage.clear()
})

describe('Download', () => {
  it('klickt einen Anker und gibt die URL verzögert frei', () => {
    vi.useFakeTimers()
    const create = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:x')
    const revoke = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined)
    saveFile({ blob: new Blob(['a']), filename: 'a.csv', mediaType: 'text/csv' })
    expect(create).toHaveBeenCalled()
    expect(click).toHaveBeenCalledTimes(1)
    expect(document.querySelector('a')).toBeNull()
    expect(revoke).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1000)
    expect(revoke).toHaveBeenCalledWith('blob:x')
  })

  it('setzt ein Datumspräfix in Berliner Zeit', () => {
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:y')
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)
    let name = ''
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      name = this.download
    })
    downloadBlob(new Blob(['a'], { type: 'text/csv' }), 'liste.csv', { datePrefix: true, now: new Date('2026-01-31T23:30:00Z') })
    expect(name).toBe('2026-02-01_liste.csv')
    downloadBlob(new Blob(['a']), 'ohne.csv')
    expect(name).toBe('ohne.csv')
  })
})

describe('Zwischenablage', () => {
  it('nutzt die Clipboard-API und sonst das Textfeld', async () => {
    const writeText = vi.fn(async () => undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })
    await expect(copyText('a')).resolves.toBe(true)
    expect(writeText).toHaveBeenCalledWith('a')
    vi.stubGlobal('navigator', { clipboard: { writeText: vi.fn(async () => Promise.reject(new Error('verweigert'))) } })
    const exec = vi.fn(() => true)
    Object.defineProperty(document, 'execCommand', { value: exec, configurable: true })
    await expect(copyText('b')).resolves.toBe(true)
    expect(exec).toHaveBeenCalledWith('copy')
    Object.defineProperty(document, 'execCommand', { value: () => { throw new Error('nein') }, configurable: true })
    await expect(copyText('c')).resolves.toBe(false)
    expect(document.querySelector('textarea')).toBeNull()
  })
})

describe('safeStorage', () => {
  it('speichert JSON mit Präfix und Version', () => {
    const store = safeStorage({ prefix: 'app', version: 2 })
    expect(store.set('filter', { q: 'x' })).toBe(true)
    expect(localStorage.getItem('app:filter')).toBe('{"v":2,"data":{"q":"x"}}')
    expect(store.get('filter', null)).toEqual({ q: 'x' })
    expect(safeStorage({ prefix: 'app', version: 3 }).get('filter', 'alt')).toBe('alt')
    localStorage.setItem('app:kaputt', '{')
    expect(store.get('kaputt', 1)).toBe(1)
    expect(store.get('fehlt', 0)).toBe(0)
    store.remove('filter')
    expect(localStorage.getItem('app:filter')).toBeNull()
    expect(safeStorage({ storage: 'session' }).set('a', 1)).toBe(true)
  })

  it('übersteht fehlenden oder vollen Speicher', () => {
    vi.stubGlobal('localStorage', undefined)
    const store = safeStorage()
    expect(store.set('a', 1)).toBe(false)
    expect(store.get('a', 5)).toBe(5)
    store.remove('a')
    vi.stubGlobal('localStorage', { setItem: () => { throw new Error('voll') }, getItem: () => null, removeItem: () => { throw new Error('x') } })
    expect(safeStorage().set('a', 1)).toBe(false)
    safeStorage().remove('a')
  })
})

describe('Media-Query und Klick außerhalb', () => {
  it('abonniert Media-Queries', () => {
    const listeners: ((event: { matches: boolean }) => void)[] = []
    const list = {
      matches: true,
      addEventListener: (_: string, fn: (event: { matches: boolean }) => void) => listeners.push(fn),
      removeEventListener: vi.fn(),
    }
    vi.stubGlobal('matchMedia', () => list)
    expect(matchesMediaQuery('(max-width: 1px)')).toBe(true)
    const seen = vi.fn()
    const stop = subscribeMediaQuery('(max-width: 1px)', seen)
    listeners[0]?.({ matches: false })
    expect(seen).toHaveBeenCalledWith(false)
    stop()
    expect(list.removeEventListener).toHaveBeenCalled()
    vi.stubGlobal('matchMedia', undefined)
    expect(matchesMediaQuery('x')).toBe(false)
    subscribeMediaQuery('x', seen)()
  })

  it('meldet Klicks außerhalb und Escape', () => {
    const inside = document.createElement('div')
    const child = document.createElement('span')
    inside.append(child)
    const outside = document.createElement('div')
    document.body.append(inside, outside)
    const handler = vi.fn()
    const stop = onClickOutside([inside, () => null], handler)
    child.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    expect(handler).not.toHaveBeenCalled()
    outside.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'a' }))
    expect(handler).toHaveBeenCalledTimes(2)
    stop()
    outside.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    expect(handler).toHaveBeenCalledTimes(2)
  })
})
