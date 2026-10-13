/**
 * Englische Arbeitsübersetzung zu Blatt 15_NS_PPS (nicht amtlich). Maßgeblich
 * ist der deutsche Wortlaut der Vorlage in `definition.ts` und im Rechenkern.
 * Fachbegriffe folgen der englischen Fassung der DelVO (EU) 2023/67 (Art. 2, 5–8,
 * Anhang II): extrapolated error, exhaustive/random stratum, high value units,
 * interval of selection, sampling precision, audit population.
 */
import type { SheetTexts } from '../../model/texts'
import { HINTS_EN, VALUES_EN } from '../shared/nonstatistical'

export const en: SheetTexts = {
  title: 'Non-statistical sampling – PPS selection, not stratified',
  shortTitle: 'Non-statistical, PPS',
  legalBasis: 'Art. 6(1)(a), (2) and (3); Art. 8(2); Annex II point 1.1 of Delegated Regulation (EU) 2023/67',
  sections: {
    H: { title: 'Audit population', reference: 'Art. 3' },
    I: { title: 'Sample', reference: 'selection approach under Art. 5(2)' },
    J: { title: 'Audit results' },
    K: { title: 'Extrapolation', reference: 'Art. 8(2)' },
  },
  fields: {
    C4: { label: 'Programme(s) / CCI', hint: 'Art. 3(1) and (2) DR.' },
    C5: { label: 'Accounting year' },
    C6: { label: 'Sampling unit (e.g. operation, declaration of expenditure, payment claim)' },
    C7: { label: 'Book value of the adjusted audit population (BV)', hint: 'Pre-filled from sheet 02.' },
    C8: { label: 'Number of sampling units (N)', hint: 'Pre-filled from sheet 02.' },
    C9: { label: 'Admissibility of non-statistical sampling (N < 300)' },
    C10: { label: 'Sample size (professional judgement, including high value units)' },
    C11: { label: 'Minimum coverage 10 % of the sampling units (rounded up)', hint: 'Art. 79(2) of Regulation (EU) 2021/1060; Art. 6(2) DR: units of exhaustive strata are included. Where the method is changed under Art. 6(3), the minimum size refers to the whole accounting year.' },
    C12: { label: 'Check of minimum coverage' },
    C13: { label: 'Cut-off for high value units (BV1/n1) (BV/n)', hint: 'Art. 5(2), second subparagraph: high value units above the interval of selection are audited in full.' },
    C14: { label: 'Number of high value units (BV > cut-off) (n_e)' },
    C15: { label: 'Book value of the high value units (BV_e)' },
    C16: { label: 'Book value of the random stratum (low-value units) (BV_s)' },
    C17: { label: 'Number of units to be selected in the random stratum (n_s)' },
    C18: { label: 'At least three units in the random stratum' },
    C19: { label: 'Interval of selection (SI)', hint: 'Art. 2(9); Art. 5(2), second subparagraph DR.' },
    C20: { label: 'Units of the random stratum with BV > interval of selection (iteration)', hint: 'Such units are to be assigned to the high value stratum; cut-off and interval are to be recalculated.' },
    C21: { label: 'Check of iteration' },
    C22: { label: 'Sum of errors in the high value units (ΣE_e)' },
    C23: { label: 'Sum of error rates of the random stratum (Σ E_i/BV_i)' },
    C24: { label: 'Error of the exhaustive stratum (EE_e)' },
    C25: { label: 'Extrapolated error (EE_s)' },
    C26: { label: 'Extrapolated error EE' },
    C27: { label: 'Delimited systemic errors (amount)', hint: 'Art. 2(20), (21); Art. 8(1) DR.' },
    C28: { label: 'Uncorrected anomalous errors (amount)', hint: 'Art. 2(20), (21); Art. 8(1) DR.' },
    C29: { label: 'Extrapolated random error rate', formula: 'EE / BV' },
    C30: { label: 'Total error rate', formula: '(EE + systemic + uncorrected anomalous errors) / BV', hint: 'Art. 8(1) DR; final calculation including the flat rate for technical assistance and Annex III in sheet 18.' },
    C31: { label: 'Materiality threshold', hint: 'Annex I point 1 DR.' },
    C32: { label: 'Assessment against the materiality threshold', hint: 'For non-statistical sampling, sampling precision and upper error limit are not calculated (Art. 8(2)).' },
  },
  summary: {
    primary: 'Total error rate (sheet-related)',
    unit: '',
    rows: { C10: 'Sample size', C11: 'Minimum coverage (10 %)', C14: 'of which high value', C17: 'Random stratum n_s', C19: 'Interval of selection', C26: 'Extrapolated error EE', C29: 'Extrapolated random error rate' },
  },
  values: { ...VALUES_EN, 'Nichtstatistisch, PPS': 'Non-statistical, PPS' },
  webHints: {
    'size-exceeds-population': HINTS_EN['size-exceeds-population'],
  },
}
