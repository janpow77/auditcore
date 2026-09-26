import { describe, expect, it } from 'vitest'
import { compareRanks, isValidRank, rankBetween, RankError, spreadRanks } from '../src'

describe('Rang', () => {
  it('bleibt bei 500 Einfügungen an derselben Stelle streng geordnet', () => {
    let low = 'V'
    const high = 'W'
    for (let index = 0; index < 500; index += 1) {
      const key = rankBetween(low, high)
      expect(key > low && key < high).toBe(true)
      expect(isValidRank(key)).toBe(true)
      low = key
    }
  })

  it('fügt am Anfang und Ende ein', () => {
    expect(rankBetween(null, null)).toBe('V')
    expect(rankBetween(null, 'V') < 'V').toBe(true)
    expect(rankBetween('V', null) > 'V').toBe(true)
  })

  it('lehnt ungültige Schlüssel und falsche Reihenfolge ab', () => {
    expect(() => rankBetween('a0', null)).toThrow(RankError)
    expect(() => rankBetween('k', 'V')).toThrowError(/liegt nicht vor/)
    expect(isValidRank('')).toBe(false)
    expect(isValidRank('ä')).toBe(false)
  })

  it('verteilt gleichmäßig und sortierbar', () => {
    const keys = spreadRanks(100)
    expect(keys).toHaveLength(100)
    expect([...keys].sort(compareRanks)).toEqual(keys)
    expect(new Set(keys).size).toBe(100)
    expect(spreadRanks(0)).toEqual([])
    expect(() => spreadRanks(-1)).toThrow(RankError)
  })
})
