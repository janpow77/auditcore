import { describe, expect, it } from 'vitest'
import { WORD_LIMIT, diffSegments, lcsOperations, ndiffOperations, segmentsText, wholeSegments } from '../../src/synopsis/wordDiff'

const NDIFF = ['  Die', '  Verwaltungsbehörde', '  führt', '+ risikobasierte', '  Verwaltungskontrollen', '- nach', '+ gemäß', '?  ^^', '  Art.', '  74', '  durch.']

describe('Wortdifferenz', () => {
  it('liest ndiff und ignoriert Hinweiszeilen', () => {
    const operations = ndiffOperations(NDIFF)
    expect(operations).toHaveLength(10)
    expect(operations[3]).toEqual(['added', 'risikobasierte'])
    expect(operations.some(([, word]) => word.includes('^'))).toBe(false)
  })

  it('zeigt je Seite nur die passenden Wörter und hält Leerzeichen außerhalb der Markierung', () => {
    const old = diffSegments('', '', 'old', NDIFF)
    expect(segmentsText(old)).toBe('Die Verwaltungsbehörde führt Verwaltungskontrollen nach Art. 74 durch.')
    expect(old).toContainEqual({ text: 'nach', kind: 'removed' })
    const neu = diffSegments('', '', 'new', NDIFF)
    expect(segmentsText(neu)).toBe('Die Verwaltungsbehörde führt risikobasierte Verwaltungskontrollen gemäß Art. 74 durch.')
    expect(neu.filter((segment) => segment.kind === 'added').map((segment) => segment.text)).toEqual(['risikobasierte', 'gemäß'])
    for (const segment of neu) if (segment.kind !== 'same') expect(segment.text).toBe(segment.text.trim())
  })

  it('inline enthält Streichung und Einfügung nebeneinander', () => {
    const inline = diffSegments('', '', 'inline', NDIFF)
    const kinds = inline.map((segment) => segment.kind)
    expect(kinds).toContain('removed')
    expect(kinds).toContain('added')
    expect(segmentsText(inline)).toContain('nach gemäß')
  })

  it('rechnet ohne ndiff eine längste gemeinsame Teilfolge nach', () => {
    const operations = lcsOperations('Die Frist beträgt drei Monate.', 'Die Frist beträgt sechs Monate.')
    expect(operations).toEqual([
      ['same', 'Die'],
      ['same', 'Frist'],
      ['same', 'beträgt'],
      ['removed', 'drei'],
      ['added', 'sechs'],
      ['same', 'Monate.'],
    ])
    expect(diffSegments('a b', 'a c', 'new')).toEqual([
      { text: 'a ', kind: 'same' },
      { text: 'c', kind: 'added' },
    ])
  })

  it('fällt oberhalb der Wortgrenze auf unmarkierte Texte zurück', () => {
    const long = Array.from({ length: WORD_LIMIT + 1 }, (_, index) => `w${index}`).join(' ')
    expect(lcsOperations(long, 'kurz')).toBeNull()
    expect(diffSegments(long, 'kurz', 'old')).toEqual([{ text: long, kind: 'same' }])
    expect(diffSegments(long, 'kurz', 'new')).toEqual([{ text: 'kurz', kind: 'same' }])
    expect(diffSegments(long, 'kurz', 'inline').map((segment) => segment.kind)).toEqual(['removed', 'same', 'added'])
  })

  it('stellt neue und entfallene Texte ganz dar', () => {
    expect(wholeSegments('', 'neu')).toEqual([{ text: 'neu', kind: 'added' }])
    expect(wholeSegments('alt', '')).toEqual([{ text: 'alt', kind: 'removed' }])
  })
})
