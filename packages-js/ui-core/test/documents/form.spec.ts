import { describe, expect, it } from 'vitest'
import {
  DEFAULT_FORM,
  defaultProfile,
  formatBytes,
  formProblems,
  hasAcceptedExtension,
  involvesPdf,
  toCompareFields,
  toggleSection,
} from '../../src/documents/form'
import { file, profiles } from './fake-port'

describe('Formular „Neuer Vergleich“', () => {
  it('meldet fehlende Dateien, falsche Endungen, Größe und Schwelle in Formularreihenfolge', () => {
    expect(formProblems(DEFAULT_FORM).map((p) => p.key)).toEqual(['problem_oldMissing', 'problem_newMissing'])
    const form = { ...DEFAULT_FORM, oldFile: file('alt.txt'), newFile: file('neu.docx', 2048), threshold: 50, sections: [] }
    const problems = formProblems(form, 1024)
    expect(problems.map((p) => [p.field, p.key])).toEqual([
      ['oldFile', 'problem_type'],
      ['newFile', 'problem_size'],
      ['threshold', 'problem_threshold'],
      ['sections', 'problem_sections'],
    ])
    expect(problems[1]?.params).toEqual({ name: 'neu.docx', size: '1 KiB' })
  })

  it('akzeptiert DOCX, DOCM und PDF unabhängig von der Schreibweise', () => {
    expect(['a.DOCX', 'b.docm', 'c.Pdf'].every(hasAcceptedExtension)).toBe(true)
    expect(hasAcceptedExtension('d.doc')).toBe(false)
    expect(formProblems({ ...DEFAULT_FORM, oldFile: file('a.DOCX'), newFile: file('b.pdf') })).toEqual([])
    expect(involvesPdf({ ...DEFAULT_FORM, newFile: file('b.PDF') })).toBe(true)
  })

  it('prüft Titel und ganzzahlige Schwelle wie der Server', () => {
    const base = { ...DEFAULT_FORM, oldFile: file('a.docx'), newFile: file('b.docx') }
    expect(formProblems({ ...base, threshold: 85.5 }).map((p) => p.key)).toEqual(['problem_threshold'])
    expect(formProblems({ ...base, threshold: 100, title: 'x'.repeat(256) }).map((p) => p.key)).toEqual(['problem_title'])
  })

  it('setzt das Formular in die Felder von POST /comparisons um', () => {
    expect(toCompareFields({ ...DEFAULT_FORM, title: '  Richtlinie  ', profile: 'audit_designer.document_compare' })).toEqual({
      comparison_type: 'standard',
      highlight_words: true,
      output_sections: ['changed', 'removed', 'added', 'moved'],
      title: 'Richtlinie',
      profile: 'audit_designer.document_compare',
      mode: 'auto',
      threshold: 85,
      include_answers: true,
      include_notes: true,
      include_editorial: false,
    })
    expect(toCompareFields({ ...DEFAULT_FORM, kind: 'article_law', highlightWords: false })).toEqual({
      comparison_type: 'article_law',
      highlight_words: false,
      output_sections: ['changed', 'removed', 'added', 'moved'],
    })
  })

  it('hält Abschnitte in Vertragsreihenfolge und wählt das Standardprofil', () => {
    expect(toggleSection(['moved', 'changed'], 'unchanged', true)).toEqual(['changed', 'moved', 'unchanged'])
    expect(toggleSection(['changed', 'moved'], 'changed', false)).toEqual(['moved'])
    expect(defaultProfile(profiles)?.id).toBe('auditcore.document_compare')
    expect(defaultProfile([])).toBeNull()
    expect(formatBytes(20 * 1024 * 1024)).toBe('20 MiB')
    expect(formatBytes(1536, 'en')).toBe('1.5 KiB')
    expect(formatBytes(12)).toBe('12 B')
  })
})
