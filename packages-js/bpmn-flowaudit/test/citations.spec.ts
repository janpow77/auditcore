/**
 * Legal citations in exactly the notations found in the analysed diagrams
 * (AUSWERTUNG.md, section 5) – texts are synthetic.
 */

import { describe, expect, it } from 'vitest'
import { completeEuAct, euAct, findCitations, parseCitation } from '../src/enrichment/citations'
import { actLong, actShort, citation, displayText, forWriting, isStructured, legalBasisKey, normalized, shortCitation, splitFreeText } from '../src/model/legalBasis'

describe('citation forms', () => {
  it('builds long and short citations', () => {
    const basis = { act: 'VO (EU) 2021/1060', article: '73', paragraph: '2', point: 'b' }
    expect(citation(basis)).toBe('Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060')
    expect(shortCitation(basis)).toBe('Art. 73 Abs. 2 Buchst. b VO (EU) 2021/1060')
  })

  it('handles sections, annexes and administrative rules', () => {
    expect(citation({ act: 'LHO', section: '44', paragraph: '1' })).toBe('§ 44 Absatz 1 LHO')
    expect(citation({ act: 'VO (EU) 2021/1060', annex: 'XIII' })).toBe('Anhang XIII der Verordnung (EU) 2021/1060')
    expect(citation({ act: 'VV zu § 44 LHO', number: '4.2' })).toBe('VV Nummer 4.2 zu § 44 LHO')
    expect(shortCitation({ act: 'VV zu § 44 LHO', number: '4.2' })).toBe('VV Nr. 4.2 zu § 44 LHO')
  })

  it('normalises acts and keeps free text', () => {
    expect(actLong('Delegierte VO (EU) Nr. 480/2014')).toBe('Delegierte Verordnung (EU) Nr. 480/2014')
    expect(actShort('Richtlinie 2014/24/EU')).toBe('RL 2014/24/EU')
    expect(normalized({ act: 'VO (EU) 2021/1060', article: '74' }).text).toBe('Artikel 74 der Verordnung (EU) 2021/1060')
    expect(forWriting({ text: 'Freitext bleibt', act: 'LHO', section: '44' }).text).toBe('Freitext bleibt')
    expect(displayText({ text: '  § 55 BHO ' })).toBe('§ 55 BHO')
    expect(isStructured({ text: 'nur Text' })).toBe(false)
    expect(splitFreeText('§ 55 BHO; Art. 74 VO (EU) 2021/1060')).toEqual(['§ 55 BHO', 'Art. 74 VO (EU) 2021/1060'])
    expect(legalBasisKey({ act: 'VO (EU) 2021/1060', article: '74' })).toBe(legalBasisKey({ act: 'Verordnung (EU) 2021/1060', article: '74' }))
  })
})

describe('findCitations', () => {
  it('recognises the long form (177 hits in the analysed diagrams)', () => {
    const [hit] = findCitations('Prüfung nach Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060.')
    expect(hit.form).toBe('long')
    expect(hit.legalBasis).toMatchObject({ act: 'Verordnung (EU) 2021/1060', article: '73', paragraph: '2', point: 'b' })
    expect(hit.legalBasis.text).toBe('Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060')
  })

  it('recognises the short form with subparagraph', () => {
    const [hit] = findCitations('Art. 74 Abs. 2 UAbs. 2 VO (EU) 2021/1060')
    expect(hit.form).toBe('short')
    expect(hit.legalBasis).toMatchObject({ article: '74', paragraph: '2', subparagraph: '2', act: 'Verordnung (EU) 2021/1060' })
  })

  it('splits „§§ 23 und 44 LHO“ into two sections', () => {
    const hits = findCitations('Zuwendungen nach §§ 23 und 44 LHO.')
    expect(hits.map((h) => h.legalBasis.section)).toEqual(['23', '44'])
    expect(hits.every((h) => h.legalBasis.act === 'LHO')).toBe(true)
  })

  it('recognises administrative rules and sections with sentence', () => {
    const hits = findCitations('VV Nummer 4.2 zu § 44 LHO; § 37 Absatz 2 Satz 2 HVwVfG')
    expect(hits[0].legalBasis).toMatchObject({ act: 'VV zu § 44 LHO', number: '4.2' })
    expect(hits[1].legalBasis).toMatchObject({ act: 'HVwVfG', section: '37', paragraph: '2', sentence: '2' })
  })

  it('recognises annexes and does not overlap', () => {
    const hits = findCitations('Anhang XIII der Verordnung (EU) 2021/1060')
    expect(hits).toHaveLength(1)
    expect(hits[0].legalBasis.annex).toBe('XIII')
  })

  it('parses a single citation or keeps free text', () => {
    expect(parseCitation('§ 44 LHO')).toMatchObject({ act: 'LHO', section: '44' })
    expect(parseCitation('Förderrichtlinie Nummer 3')).toEqual({ text: 'Förderrichtlinie Nummer 3' })
  })
})

describe('EU acts', () => {
  it('resolves CELEX, ELI and URL syntactically', () => {
    expect(euAct('Verordnung (EU) 2021/1060')).toEqual(['reg', 2021, 1060])
    expect(euAct('Verordnung (EU) Nr. 651/2014')).toEqual(['reg', 2014, 651])
    expect(euAct('Richtlinie 2014/24/EU')).toEqual(['dir', 2014, 24])
    const completed = completeEuAct({ act: 'VO (EU) 2021/1060', article: '74' })
    expect(completed.celex).toBe('32021R1060')
    expect(completed.eli).toBe('http://data.europa.eu/eli/reg/2021/1060/oj')
    expect(completeEuAct({ act: 'LHO' })).toEqual({ act: 'LHO' })
  })
})
