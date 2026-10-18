/**
 * Hinweise zur Planung bei voraussichtlichem Fehler über oder auf der
 * Signifikanzschwelle, nach den Vorgaben der KOM (Entscheidung des Inhabers vom
 * 17.10.2026: „Es gelten die Vorgaben der KOM“, `docs/abweichungen.md` Nr. 16).
 *
 * - Anhang II DelVO (EU) 2023/67 enthält keine Bedingung TE > AE. Der
 *   KOM-Leitfaden EGESIF_16-0014-01 (Abschnitt 7.1, S. 183, Fußnote 59) plant
 *   auch bei AE > TE, mit der geplanten Genauigkeit |TE − AE| (erster
 *   Zeitraum, Standard- und globale Neuberechnung); ab 4,0 % bei 2 % Schwelle
 *   empfiehlt er, mit 4,0 % zu rechnen. Die Webfassung löst diesen Hinweis
 *   beim Doppelten der Signifikanzschwelle aus (Auslegung), rechnet mit dem
 *   eingegebenen Wert und weist nur darauf hin.
 * - Bei AE = TE teilt die Formel durch null; der Umfang ist nicht bestimmbar.
 *
 * Die Zellen findet das Modul über die Aliasse der Blattdefinitionen 03–12.
 */
import { ge, gt, isBlank, isNumber, left, sameText } from '../../excel/index'
import { fieldsOf, type MethodDefinition } from '../../model/definition'
import type { CellMap, CellValue, SheetContext, WebHint } from '../../model/types'
import { SIZE_NOT_APPLICABLE } from './periods'

/** Rechnung, zu der ein Schritt gehört: erster Zeitraum oder gewählter Ansatz der Neuberechnung. */
type Approach = 'first' | 'global' | 'standard'

/** Ein Berechnungsschritt mit TE, AE, Umfang (bzw. Nenner) und Fehlerquote (Aliasse) und dem Zusatz der Hinweiskennung. */
interface Step {
  suffix: string
  approach: Approach
  tolerable: string
  anticipated: string
  size: string
  rates: readonly string[]
}

const UPDATED = ['updatedAnticipatedErrorRate', 'anticipatedErrorRate']
const FINAL = ['finalAnticipatedErrorRate', 'updatedAnticipatedErrorRate', 'anticipatedErrorRate']
const STEPS: readonly Step[] = [
  { suffix: '', approach: 'first', tolerable: 'tolerableError', anticipated: 'anticipatedError', size: 'computedSampleSize', rates: ['anticipatedErrorRate'] },
  { suffix: '-global', approach: 'global', tolerable: 'updatedTolerableError', anticipated: 'updatedAnticipatedError', size: 'globalComputedSampleSize', rates: UPDATED },
  { suffix: '-global-3', approach: 'global', tolerable: 'finalTolerableError', anticipated: 'finalAnticipatedError', size: 'finalGlobalComputedSampleSize', rates: FINAL },
  { suffix: '-standard', approach: 'standard', tolerable: 'updatedTolerableError', anticipated: 'updatedAnticipatedError', size: 'standardDenominator', rates: UPDATED },
  { suffix: '-standard-3', approach: 'standard', tolerable: 'finalTolerableError', anticipated: 'finalAnticipatedError', size: 'finalStandardDenominator', rates: FINAL },
]

const ABOVE_FIRST =
  'AE > TE: Der Stichprobenumfang ist mit der geplanten Genauigkeit |TE − AE| berechnet (nach KOM-Leitfaden EGESIF_16-0014-01, Abschnitt 7.1, S. 183 mit Fußnote 59). Die Vorlage rechnet hier anders (sie zeigt „TE ≤ AE“ und keinen Umfang). Nahe der Schwelle wird der Umfang sehr groß; der Leitfaden empfiehlt dann, die Grundgesamtheit zu teilen'
const ABOVE_GLOBAL =
  'AE > TE bei der globalen Neuberechnung: Der Umfang beruht auf der geplanten Genauigkeit |TE − AE| (nach KOM-Leitfaden EGESIF_16-0014-01, Abschnitt 7.1, S. 183 mit Fußnote 59); die Vorlage rechnet ebenso'
const ABOVE_STANDARD =
  'AE > TE bei der Standardneuberechnung: Der Nenner (TE − AE)² − … beruht auf der geplanten Genauigkeit |TE − AE| (nach KOM-Leitfaden EGESIF_16-0014-01, Abschnitt 7.1, S. 183 mit Fußnote 59); die Vorlage rechnet ebenso'
const AT_LEAST_DOUBLE =
  'Auslegung der Webfassung – voraussichtliche Fehlerquote ab dem Doppelten der Signifikanzschwelle (KOM-Leitfaden EGESIF_16-0014-01, Abschnitt 7.1, S. 183: 4,0 % bei 2 % Schwelle): Der Leitfaden empfiehlt, den Stichprobenumfang dann mit 4,0 % zu berechnen (geplante Genauigkeit höchstens 2 %); bei einer niedrigeren Schwelle löst die Webfassung den Hinweis beim Doppelten der Schwelle aus. Die Webfassung rechnet mit dem eingegebenen Wert und ersetzt ihn nicht'
const EQUAL_GLOBAL =
  'Globale Neuberechnung bei AE = TE nicht anwendbar: Die Formel des Stichprobenumfangs nach Anhang II DelVO (EU) 2023/67 teilt durch TE − AE (Division durch null). Anzuwendender Umfang, Folgezeiträume und Würdigung bleiben offen. Auch ein begrenzter Stichprobenumfang wird so nicht bestätigt; als andere Maßnahme sieht Art. 5 Abs. 7 UAbs. 4 Buchst. a DelVO die Erhöhung des Stichprobenumfangs vor. Die Vorlage zeigt keinen Umfang und rechnet mit dem begrenzten Umfang bzw. den Untergrenzen weiter'

const ABOVE_FIRST_EN =
  'AE > TE: the sample size is calculated with the planned precision |TE − AE| (in accordance with Commission guidance EGESIF_16-0014-01, section 7.1, p. 183 with footnote 59). The template calculates differently here (it shows “TE ≤ AE” and no sample size). Close to the threshold the sample size becomes very large; the guidance then recommends dividing the population'
const ABOVE_GLOBAL_EN =
  'AE > TE in the global recalculation: the sample size rests on the planned precision |TE − AE| (in accordance with Commission guidance EGESIF_16-0014-01, section 7.1, p. 183 with footnote 59); the template calculates likewise'
const ABOVE_STANDARD_EN =
  'AE > TE in the standard recalculation: the denominator (TE − AE)² − … rests on the planned precision |TE − AE| (in accordance with Commission guidance EGESIF_16-0014-01, section 7.1, p. 183 with footnote 59); the template calculates likewise'
const AT_LEAST_DOUBLE_EN =
  'Interpretation of the web version – anticipated error rate of twice the materiality threshold or more (Commission guidance EGESIF_16-0014-01, section 7.1, p. 183: 4.0 % with a 2 % threshold): the guidance then recommends calculating the sample size with 4.0 % (planned precision of maximum 2 %); with a lower threshold the web version raises the note at twice the threshold. The web version calculates with the value entered and does not replace it'
const EQUAL_GLOBAL_EN =
  'Global recalculation not applicable where AE = TE: the sample size formula of Annex II to Delegated Regulation (EU) 2023/67 divides by TE − AE (division by zero). The sample size to be applied, the following periods and the assessment remain open. A capped sample size is not confirmed either; as another measure, Art. 5(7), fourth subparagraph, point (a) of the Delegated Regulation provides for increasing the sample size. The template shows no sample size and continues with the capped sample size or the lower bounds'

const ABOVE: Readonly<Record<Approach, readonly [string, string]>> = { first: [ABOVE_FIRST, ABOVE_FIRST_EN], global: [ABOVE_GLOBAL, ABOVE_GLOBAL_EN], standard: [ABOVE_STANDARD, ABOVE_STANDARD_EN] }

/** Kennungen eines Schritts mit deutscher und englischer Fassung. */
function stepTexts(step: Step): [string, string, string][] {
  const [above, aboveEn] = ABOVE[step.approach]
  return [
    [`anticipated-above-tolerable${step.suffix}`, above, aboveEn],
    [`anticipated-at-least-4${step.suffix}`, AT_LEAST_DOUBLE, AT_LEAST_DOUBLE_EN],
    ...(step.approach === 'global' ? [[`size-not-applicable${step.suffix}`, EQUAL_GLOBAL, EQUAL_GLOBAL_EN] as [string, string, string]] : []),
  ]
}

const cellOf = (definition: MethodDefinition, alias: string): string | undefined => fieldsOf(definition).find((field) => field.alias === alias)?.cell

function value(definition: MethodDefinition, results: CellMap, alias: string): CellValue {
  const cell = cellOf(definition, alias)
  return cell ? (results[cell] ?? null) : null
}

/** AE > TE mit berechnetem Umfang bzw. Nenner. */
function anticipatedAbove(tolerable: CellValue, anticipated: CellValue, size: CellValue): boolean {
  return isNumber(size) && isNumber(tolerable) && isNumber(anticipated) && gt(anticipated, tolerable)
}

/** Werte eines Berechnungsschritts: TE, AE, Umfang und die zuerst eingetragene Fehlerquote. */
function stepValues(definition: MethodDefinition, results: CellMap, step: Step): [CellValue, CellValue, CellValue, CellValue] {
  const [tolerable, anticipated, size] = [step.tolerable, step.anticipated, step.size].map((alias) => value(definition, results, alias))
  const rate = step.rates.map((alias) => value(definition, results, alias)).find((entry) => !isBlank(entry))
  return [tolerable ?? null, anticipated ?? null, size ?? null, rate ?? null]
}

/** Auslöser der Empfehlung des Leitfadens: das Doppelte der Signifikanzschwelle (4,0 % bei 2 %; ohne Schwelle 4 %). */
function doubleThreshold(definition: MethodDefinition, results: CellMap): number {
  const threshold = value(definition, results, 'materiality')
  return isNumber(threshold) && gt(threshold, 0) ? 2 * threshold : 0.04
}

/** Hinweise eines Berechnungsschritts. */
function stepHints(definition: MethodDefinition, results: CellMap, step: Step): WebHint[] {
  if (!cellOf(definition, step.size)) return []
  const [tolerable, anticipated, size, rate] = stepValues(definition, results, step)
  const [above, double, equal] = stepTexts(step)
  const hints: WebHint[] = []
  if (above && anticipatedAbove(tolerable, anticipated, size)) hints.push({ id: above[0], tone: 'neutral', text: above[1] })
  if (double && isNumber(size) && isNumber(rate) && ge(rate, doubleThreshold(definition, results))) hints.push({ id: double[0], tone: 'neutral', text: double[1] })
  if (equal && size === SIZE_NOT_APPLICABLE) hints.push({ id: equal[0], tone: 'warning', text: equal[1] })
  return hints
}

/** Gewählter Ansatz der Neuberechnung (`LEFT(x;6)="Global"` bzw. `LEFT(x;8)="Standard"`). */
function chosenApproach(definition: MethodDefinition, results: CellMap): Approach | null {
  const chosen = value(definition, results, 'recalculationApproach')
  if (sameText(left(chosen, 6), 'Global')) return 'global'
  return sameText(left(chosen, 8), 'Standard') ? 'standard' : null
}

/** Hinweise zur Planung bei AE > TE, AE ab dem Doppelten der Schwelle und AE = TE; die der Neuberechnung nur für den gewählten Ansatz. */
export function komPlanningHints(definition: MethodDefinition, results: CellMap): WebHint[] {
  const chosen = chosenApproach(definition, results)
  return STEPS.filter((step) => step.approach === 'first' || step.approach === chosen).flatMap((step) => stepHints(definition, results, step))
}

/** Englische Fassungen der Planungshinweise, die ein Blatt erzeugen kann (nach seinen Aliassen). */
export function komHintsEn(definition: MethodDefinition): Record<string, string> {
  const present = STEPS.filter((step) => cellOf(definition, step.size))
  return Object.fromEntries(present.flatMap((step) => stepTexts(step).map(([id, , en]) => [id, en])))
}

const APPROXIMATION =
  'Anhang III, Ausschluss bzw. Ersetzung bei mehreren Schichten oder Zeiträumen: Der KOM-Leitfaden EGESIF_16-0014-01 (Abschnitt 7.10.2) passt je Schicht bzw. Zeitraum an (BV(h)); Blatt 18 rechnet mit einem Verhältnis über die ganze Zufallsschicht (mit erfasster Lage, Abschnitt F) bzw. über die ganze Grundgesamtheit (ohne Lage), weil die Lage der berührten Einheiten je Schicht bzw. Zeitraum nicht erfasst wird. Das Ergebnis in Blatt 18 ist insoweit eine anteilige Näherung'
const APPROXIMATION_EN =
  'Annex III, exclusion or replacement with several strata or periods: Commission guidance EGESIF_16-0014-01 (section 7.10.2) adjusts per stratum or period (BV(h)); sheet 18 calculates with one ratio for the whole random stratum (location recorded, section F) or for the whole population (without location) because the location of the affected units per stratum or period is not recorded. To that extent the result in sheet 18 is a proportional approximation'

/** Kennung des Hinweises zur anteiligen Näherung nach Anhang III. */
export const APPROXIMATION_ID = 'annex-iii-approximation'

/** Deutscher Text des Hinweises zur anteiligen Näherung (auch in Blatt 18). */
export const APPROXIMATION_TEXT = APPROXIMATION

/**
 * Hinweis an geschichteten bzw. mehrzeitigen Verfahren, wenn in Blatt 02
 * Ausschluss oder (bei der einfachen Zufallsstichprobe, Tabelle 2) Ersetzung
 * gewählt und mindestens eine Einheit berührt ist.
 */
export function annexIIIApproximation(context: SheetContext | undefined, replacementAdjusts: boolean): WebHint[] {
  const population = context?.sheets['02_Grundgesamtheit']
  if (!population || !isNumber(population.C47) || !gt(population.C47, 0)) return []
  const exclusion = sameText(left(population.C49, 10), 'Ausschluss')
  const replacement = sameText(left(population.C49, 9), 'Ersetzung')
  return exclusion || (replacement && replacementAdjusts) ? [{ id: APPROXIMATION_ID, tone: 'warning', text: APPROXIMATION }] : []
}

/** Englische Fassung des Hinweises zur anteiligen Näherung. */
export const APPROXIMATION_EN_TEXT: Readonly<Record<string, string>> = { [APPROXIMATION_ID]: APPROXIMATION_EN }
