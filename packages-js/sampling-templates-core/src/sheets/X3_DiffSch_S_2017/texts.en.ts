/**
 * Englische Fassung zu Blatt X3_DiffSch_S_2017. Die Bezeichnungen der Vorlage von 2017
 * sind bereits englisch und bleiben unverändert (Wortlaut der Vorlage von 2017).
 * Vermerk: nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage.
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67
 * nur in den eigenen Hinweisen der Webfassung.
 */
import { legacyTexts, strataHintsEn } from '../shared/legacy'

export const en = legacyTexts('M1', 'Difference estimation, stratified (template 11 of the 2017 templates, unchanged)', 'Difference estimation, stratified (2017)', {
  'strata-sum-exceeds-size': 'Sum of the rounded-up stratum sample sizes is larger than the planned sample size',
  ...strataHintsEn(),
  'strata-gap': 'Empty stratum between used strata (the used strata are listed in the German hint)',
  'strata-beyond-template': 'More than seven strata: the template provides seven columns; strata 8 to 20 are an extension of the web version',
})
