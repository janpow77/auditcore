/**
 * Kanonische Form der Eingaben und Prüfsumme. Kanonisch heißt: Schlüssel
 * sortiert, leere Werte (`null`, `""`) entfernt, keine Leerzeichen – dieselben
 * Eingaben ergeben unabhängig von Reihenfolge und Leerwerten dieselbe Prüfsumme.
 */
import type { WorkspaceFile } from './types'

function canonicalValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalValue)
  if (value === null || typeof value !== 'object') return value
  const result: Record<string, unknown> = {}
  for (const key of Object.keys(value).sort()) {
    const entry = (value as Record<string, unknown>)[key]
    if (entry === null || entry === undefined || entry === '') continue
    result[key] = canonicalValue(entry)
  }
  return result
}

/** Kanonischer JSON-Text der Eingaben einer Arbeitsstandsdatei (Kopf, aktive Methode, Blätter). */
export function canonicalInputs(file: Pick<WorkspaceFile, 'kopf' | 'aktiveMethode' | 'blaetter'>): string {
  return JSON.stringify(canonicalValue({ aktiveMethode: file.aktiveMethode, blaetter: file.blaetter, kopf: file.kopf }))
}

const K = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74,
  0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d,
  0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e,
  0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
  0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]

const rotate = (value: number, bits: number): number => (value >>> bits) | (value << (32 - bits))

function padded(bytes: Uint8Array): Uint8Array {
  const length = (bytes.length + 9 + 63) & ~63
  const block = new Uint8Array(length)
  block.set(bytes)
  block[bytes.length] = 0x80
  new DataView(block.buffer).setUint32(length - 4, bytes.length * 8)
  new DataView(block.buffer).setUint32(length - 8, Math.floor((bytes.length * 8) / 2 ** 32))
  return block
}

function compress(state: Uint32Array, words: Uint32Array): void {
  for (let i = 16; i < 64; i += 1) {
    const w15 = words[i - 15]!
    const w2 = words[i - 2]!
    const s0 = rotate(w15, 7) ^ rotate(w15, 18) ^ (w15 >>> 3)
    const s1 = rotate(w2, 17) ^ rotate(w2, 19) ^ (w2 >>> 10)
    words[i] = (words[i - 16]! + s0 + words[i - 7]! + s1) | 0
  }
  let [a, b, c, d, e, f, g, h] = state as unknown as [number, number, number, number, number, number, number, number]
  for (let i = 0; i < 64; i += 1) {
    const t1 = (h + (rotate(e, 6) ^ rotate(e, 11) ^ rotate(e, 25)) + ((e & f) ^ (~e & g)) + K[i]! + words[i]!) | 0
    const t2 = ((rotate(a, 2) ^ rotate(a, 13) ^ rotate(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) | 0
    ;[h, g, f, e, d, c, b, a] = [g, f, e, (d + t1) | 0, c, b, a, (t1 + t2) | 0]
  }
  ;[a, b, c, d, e, f, g, h].forEach((value, index) => {
    state[index] = (state[index]! + value) | 0
  })
}

/** SHA-256 in reinem JavaScript; nur für Umgebungen ohne Web Crypto (Seiten ohne HTTPS). */
export function sha256Fallback(bytes: Uint8Array): Uint8Array {
  const state = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19])
  const block = padded(bytes)
  const view = new DataView(block.buffer)
  const words = new Uint32Array(64)
  for (let offset = 0; offset < block.length; offset += 64) {
    for (let i = 0; i < 16; i += 1) words[i] = view.getUint32(offset + i * 4)
    compress(state, words)
  }
  const digest = new Uint8Array(32)
  state.forEach((value, index) => new DataView(digest.buffer).setUint32(index * 4, value))
  return digest
}

async function sha256(bytes: Uint8Array<ArrayBuffer>): Promise<Uint8Array> {
  const subtle = globalThis.crypto?.subtle
  return subtle ? new Uint8Array(await subtle.digest('SHA-256', bytes)) : sha256Fallback(bytes)
}

/** Prüfsumme `sha256:<hex>` über einen Text (Web Crypto, UTF-8). */
export async function checksumOf(text: string): Promise<string> {
  const digest = await sha256(new TextEncoder().encode(text))
  return `sha256:${[...digest].map((byte) => byte.toString(16).padStart(2, '0')).join('')}`
}
