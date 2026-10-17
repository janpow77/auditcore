/**
 * Englische Fassung zu Blatt X4_DiffSch_2Z_2017. Die Bezeichnungen der Vorlage von 2017
 * sind bereits englisch und bleiben unverändert (Wortlaut der Vorlage von 2017).
 * Vermerk: nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage.
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67
 * nur in den eigenen Hinweisen der Webfassung.
 */
import { legacyTexts } from '../shared/legacy'

export const en = legacyTexts('F1', 'Difference estimation, two periods (template 12 of the 2017 templates, unchanged)', 'Difference estimation, 2 periods (2017)', {
  'tolerable-error-not-above-anticipated-1': 'TE ≤ AE in the first period: the legacy template does not check this. The sample size and the values derived from it are, as far as shown as in the template, not reliable; please check the anticipated error rate',
  'tolerable-error-not-above-anticipated-2': 'TE ≤ AE in the second period: the legacy template does not check this. The recalculated sample size and the values derived from it are, as far as shown as in the template, not reliable; please check the anticipated error rate of the second period',
  'negative-denominator': 'Negative denominator in the recalculation of the sample size for the second period: the legacy template does not check this. Size and derived values are shown as in the template but are not reliable; please check the entries of both periods',
  'size-exceeds-population-2': 'Recalculated sample size exceeds the number of units of the second period',
  'below-three-units': 'Sample of a period with fewer than three units (footnote of the legacy template: minimum of 3)',
})
