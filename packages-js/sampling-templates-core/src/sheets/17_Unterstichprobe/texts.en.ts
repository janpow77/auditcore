/**
 * Englische Fassung zu Blatt 17_Unterstichprobe.
 * Vermerk: nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage.
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67 (Art. 2
 * Nr. 12 und 13, Art. 7, Art. 8 Abs. 3): subsampling, subsampling unit,
 * subsample, high value subsampling units, interval of selection, error
 * extrapolated to the sampling unit.
 *
 * Die Spalten der Übersicht (`listColumns`) zeigen die Bezeichnungen der
 * Felder; sie sind mit `fields` übersetzt. Der Rechenkern liefert keine
 * eigenen Texte; `values` übersetzt die Auswahlwerte der Felder W5 und W6.
 */
import type { SheetTexts } from '../../model/texts'

export const en: SheetTexts = {
  title: 'Subsampling – error of a sampling unit',
  shortTitle: 'Subsamples',
  legalBasis: 'Art. 2(12) and (13); Art. 7; Art. 8(3) of Delegated Regulation (EU) 2023/67',
  sections: {
    A: { title: 'Sampling unit' },
    B: { title: 'Option 1 – equal probability selection', reference: 'ratio estimation' },
    C: { title: 'Option 2 – PPS selection', reference: 'MUS standard approach' },
    W: { title: 'Assignment in the method sheet', reference: 'note of the web version' },
  },
  fields: {
    C5: { label: 'Identifier of the sampling unit (operation / declaration of expenditure)' },
    C6: { label: 'Book value of the sampling unit (BV_i)' },
    C7: { label: 'Number of subsampling units (e.g. invoices) (M)', hint: 'Art. 2(13) DR.' },
    C8: { label: 'Book value of exhaustively audited subsampling units (optional) (BV_e)' },
    C9: { label: 'Errors in exhaustively audited subsampling units (ΣE_e)' },
    C10: { label: 'Size of the subsample (random part)' },
    C11: { label: 'Sum of book values of the subsample (Σ BV_j)' },
    C12: { label: 'Sum of errors of the subsample (Σ E_j)' },
    C13: { label: 'Extrapolated error of the sampling unit (E_i)', formula: 'E_i = E_e + (BV_i − BV_e) · Σ E_j / Σ BV_j' },
    C14: { label: 'Error rate of the sampling unit (for MUS: input into Σ E_i/BV_i)' },
    C15: { label: 'Size of the subsample (including high value subsampling units)' },
    C16: { label: 'Cut-off value (BV_i/m)', hint: 'Art. 7, second subparagraph, third sentence: high value subsampling units above the interval of selection are audited.' },
    C17: { label: 'Number of high value subsampling units (m_e)' },
    C18: { label: 'Book value of the high value subsampling units (BV_e)' },
    C19: { label: 'Errors of the high value subsampling units (ΣE_e)' },
    C20: { label: 'Interval of selection (SI)', formula: 'SI = (BV_i − BV_e) / (m − m_e)' },
    C21: { label: 'Sum of error rates of the random selection (Σ E_j/BV_j)' },
    C22: { label: 'Extrapolated error of the sampling unit (E_i)', formula: 'E_i = ΣE_e + SI · Σ E_j/BV_j' },
    C23: { label: 'Error rate of the sampling unit (E_i/BV_i)' },
    W5: { label: 'Stratum of the sampling unit in the method sheet', hint: 'High value units enter ΣE_e with their error, units of the random stratum enter Σ E_i/BV_i with their error rate.' },
    W6: { label: 'Applicable subsampling option', hint: 'Option 1: equal probability selection; option 2: PPS selection.' },
    W9: { label: 'Number of the stratum in the method sheet (stratified methods only)', hint: 'Of the stratified methods, sheet 04 currently takes over the sums per stratum; without a number the unit is not taken over there. In sheets 06, 09, 11, 14 and 16 the sums have to be entered by hand.' },
    W10: { label: 'Sampling period in the method sheet (multi-period methods only)', hint: 'Assigns the unit to a sampling period (1, 2 or 3). The multi-period methods (sheets 05–07 and 10–12) currently do not take over sums from the subsamples; they have to be entered there by hand.' },
    W7: { label: 'Applicable extrapolated error (E_i)' },
    W8: { label: 'Applicable error rate (E_i/BV_i)' },
  },
  summary: {
    primary: 'Applicable extrapolated error of the unit',
    unit: '',
    rows: { W8: 'Error rate of the unit', C13: 'Option 1: extrapolated error', C22: 'Option 2: extrapolated error' },
  },
  values: {
    Zufallsschicht: 'random stratum',
    'hochwertige Einheit': 'high value unit',
    'Variante 1': 'Option 1',
    'Variante 2': 'Option 2',
  },
}
