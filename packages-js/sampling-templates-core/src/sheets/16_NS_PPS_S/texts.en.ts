/**
 * Englische Fassung zu Blatt 16_NS_PPS_S.
 * Vermerk: nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage.
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67 (Art. 2, 5–8,
 * Anhang II): extrapolated error, exhaustive/random stratum, high value units,
 * interval of selection, sampling precision, audit population.
 */
import type { SheetTexts } from '../../model/texts'
import { HINTS_EN, STRATA_HINTS_EN, VALUES_EN } from '../shared/nonstatistical'

export const en: SheetTexts = {
  title: 'Non-statistical sampling – PPS selection, stratified',
  shortTitle: 'Non-statistical, PPS, stratified',
  legalBasis: 'Art. 6(1)(a) and second and third subparagraphs, (2); Art. 8(2); Annex II point 1.1 (stratified) of Delegated Regulation (EU) 2023/67',
  sections: {
    H: { title: 'Audit population', reference: 'Art. 3, Art. 4' },
    I: { title: 'Sample' },
    J: { title: 'Audit results' },
    K: { title: 'Extrapolation', reference: 'Art. 8(2)' },
  },
  fields: {
    C4: { label: 'Programme(s) / CCI', hint: 'Art. 3(1) and (2) DR.' },
    C5: { label: 'Accounting year' },
    C6: { label: 'Sampling unit (e.g. operation, declaration of expenditure, payment claim)' },
    D9: { label: 'Book value per stratum (BV_h)', hint: 'Sampling periods may be recorded like strata (Art. 6(1), second subparagraph).' },
    D10: { label: 'Number of units per stratum (N_h)' },
    C11: { label: 'Number of units of the population (N)' },
    C12: { label: 'Admissibility of non-statistical sampling (N < 300)' },
    C13: { label: 'Sample size (professional judgement)' },
    D15: { label: 'Sample size per stratum' },
    C16: { label: 'Minimum coverage 10 % of the sampling units (rounded up)', hint: 'Art. 79(2) of Regulation (EU) 2021/1060; Art. 6(2) DR: units of exhaustive strata are included. Where the method is changed under Art. 6(3), the minimum size refers to the whole accounting year.' },
    C17: { label: 'Check of minimum coverage' },
    D18: { label: 'Cut-off value per stratum (BV/n)' },
    D19: { label: 'Number of high value units (n_eh)' },
    D20: { label: 'Book value of the high value units (BV_eh)' },
    D21: { label: 'Book value of the random stratum (BV_hs)' },
    D22: { label: 'Random units to be selected (n_hs)' },
    D23: { label: 'Interval of selection (SI_h)' },
    D25: { label: 'Sum of the errors in high value units (ΣE_eh)' },
    D26: { label: 'Sum of the error rates of the random stratum (Σ E/BV)' },
    D28: { label: 'Extrapolated error per stratum (EE_h)' },
    C29: { label: 'Error of the exhaustive strata (EE_e)' },
    C30: { label: 'Extrapolated error EE' },
    C31: { label: 'Delimited systemic errors (amount)', hint: 'Art. 2(20), (21); Art. 8(1) DR.' },
    C32: { label: 'Uncorrected anomalous errors (amount)', hint: 'Art. 2(20), (21); Art. 8(1) DR.' },
    C33: { label: 'Extrapolated random error rate', formula: 'EE / BV' },
    C34: { label: 'Total error rate', formula: '(EE + delimited systemic + uncorrected anomalous errors) / BV', hint: 'Art. 8(1) DR; final calculation including the flat rate for technical assistance and Annex III in sheet 18.' },
    C35: { label: 'Materiality threshold', hint: 'Annex I point 1 DR.' },
    C36: { label: 'Assessment against the materiality threshold', hint: 'For non-statistical sampling, sampling precision and upper error limit are not calculated (Art. 8(2)).' },
  },
  summary: {
    primary: 'Total error rate (sheet-related)',
    unit: '',
    rows: { C11: 'Units of the population (N)', C15: 'Sum of the sample sizes per stratum n_h', C16: 'Minimum coverage (10 %)', C19: 'of which high value', C22: 'Random strata n_hs', C30: 'Extrapolated error EE', C33: 'Extrapolated random error rate' },
  },
  values: { ...VALUES_EN, 'Nichtstatistisch, PPS, geschichtet': 'Non-statistical, PPS, stratified' },
  webHints: {
    'size-exceeds-population': HINTS_EN['size-exceeds-population'],
    'strata-sum-exceeds-size': HINTS_EN['strata-sum-exceeds-size'],
    'strata-beyond-template': HINTS_EN['strata-beyond-template'],
    ...STRATA_HINTS_EN,
  },
}
