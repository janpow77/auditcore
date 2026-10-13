/**
 * Englische Arbeitsübersetzung zu Blatt 14_NS_GW_S (nicht amtlich). Maßgeblich
 * ist der deutsche Wortlaut der Vorlage in `definition.ts` und im Rechenkern.
 * Fachbegriffe folgen der englischen Fassung der DelVO (EU) 2023/67 (Art. 2, 5–8,
 * Anhang II): extrapolated error, exhaustive/random stratum, high value units,
 * interval of selection, sampling precision, audit population.
 */
import type { SheetTexts } from '../../model/texts'
import { HINTS_EN, STRATA_HINTS_EN, VALUES_EN } from '../shared/nonstatistical'

export const en: SheetTexts = {
  title: 'Non-statistical sampling – selection with equal probability, stratified',
  shortTitle: 'Non-statistical, equal probability, stratified',
  legalBasis: 'Art. 6(1), second and third subparagraphs, (2); Art. 8(2); Annex II point 2.1 (stratified) of Delegated Regulation (EU) 2023/67',
  sections: {
    H: { title: 'Audit population', reference: 'Art. 3, Art. 4' },
    I: { title: 'Sample' },
    J: { title: 'Audit results' },
    K: { title: 'Extrapolation', reference: 'ratio estimation; Art. 8(2)' },
  },
  fields: {
    C4: { label: 'Programme(s) / CCI', hint: 'Art. 3(1) and (2) DR.' },
    C5: { label: 'Accounting year' },
    C6: { label: 'Sampling unit (e.g. operation, declaration of expenditure, payment claim)' },
    C8: { label: 'Book value of the exhaustive stratum (optional) (BV_e)' },
    C9: { label: 'Number of units of the exhaustive stratum (N_e)' },
    D11: { label: 'Number of units per stratum (N_h)', hint: 'Sampling periods may be recorded like strata (Art. 6(1), second subparagraph), as the extrapolation per period is additive.' },
    D12: { label: 'Book value per stratum (BV_h)' },
    C13: { label: 'Book value of the population (BV)' },
    C14: { label: 'Number of units of the population (N)' },
    C15: { label: 'Admissibility of non-statistical sampling (N < 300)' },
    C16: { label: 'Size of the random sample (professional judgement)' },
    D18: { label: 'Sample size per stratum' },
    C19: { label: 'Total sample' },
    C20: { label: 'Minimum coverage 10 % of the sampling units (rounded up)', hint: 'Art. 79(2) of Regulation (EU) 2021/1060; Art. 6(2) DR: units of exhaustive strata are included. Where the method is changed under Art. 6(3), the minimum size refers to the whole accounting year.' },
    C21: { label: 'Check of minimum coverage' },
    C22: { label: 'Sum of errors in the exhaustive stratum (ΣE_e)' },
    D24: { label: 'Sum of book values of the sample (Σ BV_i)' },
    D25: { label: 'Sum of errors of the sample (Σ E_i)' },
    D27: { label: 'Extrapolated error per stratum (EE_sh)' },
    C28: { label: 'Error of the exhaustive stratum (EE_e)' },
    C29: { label: 'Extrapolated error EE' },
    C30: { label: 'Delimited systemic errors (amount)', hint: 'Art. 2(20), (21); Art. 8(1) DR.' },
    C31: { label: 'Uncorrected anomalous errors (amount)', hint: 'Art. 2(20), (21); Art. 8(1) DR.' },
    C32: { label: 'Extrapolated random error rate', formula: 'EE / BV' },
    C33: { label: 'Total error rate', formula: '(EE + systemic + uncorrected anomalous errors) / BV', hint: 'Art. 8(1) DR; final calculation including the flat rate for technical assistance and Annex III in sheet 18.' },
    C34: { label: 'Materiality threshold', hint: 'Annex I point 1 DR.' },
    C35: { label: 'Assessment against the materiality threshold', hint: 'For non-statistical sampling, sampling precision and upper error limit are not calculated (Art. 8(2)).' },
  },
  summary: {
    primary: 'Total error rate (sheet-related)',
    unit: '',
    rows: { C14: 'Units of the population (N)', C19: 'Total sample', C20: 'Minimum coverage (10 %)', C27: 'Extrapolated error of the random strata', C29: 'Extrapolated error EE', C32: 'Extrapolated random error rate' },
  },
  values: { ...VALUES_EN, 'Nichtstatistisch, gleiche Wahrscheinlichkeit, geschichtet': 'Non-statistical, equal probability, stratified' },
  webHints: {
    'size-exceeds-population': HINTS_EN['size-exceeds-population'],
    'strata-sum-exceeds-size': HINTS_EN['strata-sum-exceeds-size'],
    'strata-beyond-template': HINTS_EN['strata-beyond-template'],
    ...STRATA_HINTS_EN,
  },
}
