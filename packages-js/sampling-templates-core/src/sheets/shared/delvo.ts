/**
 * Hinweise der Webfassung, wo die Vorlage von der Delegierten Verordnung (EU)
 * 2023/67 abweicht (DelVO-Abgleich vom 17.10.2026, `docs/abweichungen.md`
 * Nr. 16, Abweichungen 3 und 5). Die Rechenwerte bleiben dort wie in der
 * Vorlage; jeder Hinweis nennt die Fundstelle der DelVO und die Wirkung. Als Hinweis in Warnfarbe reist er mit
 * in Blatt 18, in den Bericht und in den Excel-Export (`view/limits.ts`).
 */
import { gt, isNumber, left, sameText } from '../../excel/index'
import type { SheetContext, WebHint } from '../../model/types'

const warning = (id: string, text: string): WebHint => ({ id, tone: 'warning', text })

/** Nr. 3 des Abgleichs: Zusatz zu den Hinweisen „Nenner der Standardneuberechnung ist nicht positiv“. */
const NOT_APPLICABLE = '. Nach Anhang II DelVO (EU) 2023/67 (Anmerkungen zu Nr. 1.2 und 2.2) ist der Standardansatz bei negativem Ergebnis nicht anwendbar; der Umfang des Folgezeitraums beruht dann auf keinem Ansatz der DelVO, die Vorlage rechnet mit der Untergrenze weiter'
const NOT_APPLICABLE_EN = '. Under Annex II to Delegated Regulation (EU) 2023/67 (notes to points 1.2 and 2.2), the standard approach cannot be applied where the result is negative; the sample size of the following period then rests on no approach of the Delegated Regulation, the template continues with the lower bound'

const isNotApplicable = (id: string): boolean => id.startsWith('negative-denominator')

/** Hinweise des Blatts mit dem DelVO-Zusatz an jedem Hinweis zum nicht positiven Nenner. */
export function withNotApplicableNote(hints: readonly WebHint[]): WebHint[] {
  return hints.map((hint) => (isNotApplicable(hint.id) ? { ...hint, text: `${hint.text}${NOT_APPLICABLE}` } : hint))
}

/** Englische Hinweistexte mit dem DelVO-Zusatz an jedem Hinweis zum nicht positiven Nenner. */
export function withNotApplicableNoteEn(texts: Readonly<Record<string, string>>): Record<string, string> {
  return Object.fromEntries(Object.entries(texts).map(([id, text]) => [id, isNotApplicable(id) ? `${text}${NOT_APPLICABLE_EN}` : text]))
}

/** Blatt 02 und die Behandlung der nach Art. 80 Abs. 3 nicht prüfbaren Einheiten. */
const POPULATION_SHEET = '02_Grundgesamtheit'

const EXCLUSION_REFERENCE =
  'Auslegungsfrage, Ausschluss nach Art. 80 Abs. 3: Die Vorlage berechnet den Stichprobenumfang aus der reduzierten Grundgesamtheit (Blatt 02). Nach Anhang III Tabellen 1 und 2 DelVO (EU) 2023/67 „entsprechen“ die Parameter zur Berechnung des Stichprobenumfangs „der ursprünglichen Grundgesamtheit“. Bei der einfachen Zufallsstichprobe hängt der Umfang von N und BV ab und kann sich dadurch ändern; ob die DelVO mit „Parameter“ auch BV, N und TE meint, lässt der Wortlaut offen. Die Webfassung rechnet wie die Vorlage'

const EXCLUSION_REFERENCE_EN =
  'Question of interpretation, exclusion under Art. 80(3): the template calculates the sample size from the reduced population (sheet 02). Under Annex III, Tables 1 and 2, to Delegated Regulation (EU) 2023/67, the parameters for the calculation of the sample size “correspond to the original population”. For simple random sampling the sample size depends on N and BV and may therefore change; whether “parameters” also covers BV, N and TE is left open by the wording. The web version calculates like the template'

/**
 * Nr. 5 des Abgleichs, nur einfache Zufallsstichprobe (08–12): In Blatt 02 ist
 * der Ausschluss gewählt und mindestens eine Einheit ist betroffen.
 */
export function exclusionReference(context: SheetContext | undefined): WebHint[] {
  const population = context?.sheets[POPULATION_SHEET]
  if (!population || !sameText(left(population.C49, 10), 'Ausschluss') || !isNumber(population.C47) || !gt(population.C47, 0)) return []
  return [warning('exclusion-reference-population', EXCLUSION_REFERENCE)]
}

/** Englische Fassungen der Hinweise dieses Moduls (ohne den Zusatz zum Nenner). */
const DELVO_HINTS_EN: Readonly<Record<string, string>> = {
  'exclusion-reference-population': EXCLUSION_REFERENCE_EN,
}

/** Englische Fassungen der genannten Hinweise dieses Moduls, für die Hinweistexte eines Blatts. */
export function delvoHintsEn(...ids: readonly string[]): Record<string, string> {
  return Object.fromEntries(ids.map((id) => [id, DELVO_HINTS_EN[id] ?? '']))
}
