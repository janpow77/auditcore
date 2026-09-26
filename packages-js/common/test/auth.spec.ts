import { describe, expect, it, vi } from 'vitest'
import { bearerHeaders, createTokenStore, isTokenExpired, jwtExpiry, jwtPayload } from '../src'

function jwt(payload: object): string {
  const encode = (value: object): string => Buffer.from(JSON.stringify(value)).toString('base64url')
  return `${encode({ alg: 'none' })}.${encode(payload)}.sig`
}

class MemoryStorage {
  data = new Map<string, string>()
  getItem(key: string): string | null {
    return this.data.get(key) ?? null
  }
  setItem(key: string, value: string): void {
    this.data.set(key, value)
  }
  removeItem(key: string): void {
    this.data.delete(key)
  }
}

describe('TokenStore', () => {
  it('hält Tokens im Arbeitsspeicher und benachrichtigt', () => {
    const store = createTokenStore({ storage: 'memory' })
    const listener = vi.fn()
    const stop = store.subscribe(listener)
    expect(bearerHeaders(store)).toEqual({})
    store.set('abc')
    expect(bearerHeaders(store)).toEqual({ Authorization: 'Bearer abc' })
    store.clear()
    stop()
    store.set('x')
    expect(listener.mock.calls).toEqual([['abc'], [null]])
  })

  it('nutzt Web Storage und fällt ohne ihn zurück', () => {
    const storage = new MemoryStorage()
    vi.stubGlobal('localStorage', storage)
    storage.setItem('app_token', 'vorhanden')
    const store = createTokenStore({ key: 'app_token' })
    expect(store.get()).toBe('vorhanden')
    store.set('neu')
    expect(storage.getItem('app_token')).toBe('neu')
    store.clear()
    expect(storage.getItem('app_token')).toBeNull()
    vi.unstubAllGlobals()
    const fallback = createTokenStore({ storage: 'session' })
    fallback.set('t')
    expect(fallback.get()).toBe('t')
  })

  it('übersteht gesperrten Speicher', () => {
    const broken = { getItem: () => { throw new Error('gesperrt') }, setItem: () => { throw new Error('voll') }, removeItem: () => { throw new Error('x') } }
    vi.stubGlobal('localStorage', broken)
    const store = createTokenStore()
    store.set('t')
    expect(store.get()).toBe('t')
    store.clear()
    expect(store.get()).toBeNull()
    vi.unstubAllGlobals()
  })
})

describe('JWT', () => {
  it('liest Ablauf und Nutzdaten ohne Signaturprüfung', () => {
    const token = jwt({ sub: 'jan', exp: 1_800_000_000 })
    expect(jwtPayload(token)).toEqual({ sub: 'jan', exp: 1_800_000_000 })
    expect(jwtExpiry(token)?.toISOString()).toBe('2027-01-15T08:00:00.000Z')
    expect(isTokenExpired(token, { now: new Date('2027-01-15T07:59:45Z') })).toBe(true)
    expect(isTokenExpired(token, { now: new Date('2027-01-15T07:59:45Z'), leewaySeconds: 0 })).toBe(false)
    expect(isTokenExpired(jwt({ sub: 'x' }))).toBe(false)
    expect(jwtPayload('kein.jwt')).toBeNull()
    expect(jwtPayload(`a.${Buffer.from('[1]').toString('base64url')}.c`)).toBeNull()
    expect(jwtPayload('nur-ein-teil')).toBeNull()
  })
})
