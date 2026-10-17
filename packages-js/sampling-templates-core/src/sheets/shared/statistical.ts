/**
 * Formeln, die in den statistischen Blättern 03–12 wortgleich vorkommen
 * (nur die Zellbezüge unterscheiden sich): Prüfhinweise zu Konfidenzniveau,
 * Signifikanzschwelle und TE > AE, rechnerischer und anzuwendender
 * Stichprobenumfang, begrenzter Umfang, untere Fehlergrenze und Würdigung.
 * Jedes Blatt ruft sie mit seinen Zellen auf; so stehen die Texte der Vorlage
 * genau einmal im Quelltext.
 */
import { eq, ge, gt, guard, isNumber, le, lt, minus, n, ne, required, roundUp, sameNumber, sameText } from '../../excel/index'
import { unfounded } from '../../model/policy'
import type { CellValue, SheetContext } from '../../model/types'
import { SIZE_NOT_APPLICABLE } from './periods'

/** Prüfung Konfidenzniveau gegen Systembewertung (Anh. I Nr. 2). */
export function checkConfidence(reliability: CellValue | undefined, confidence: CellValue | undefined): CellValue {
  if (typeof reliability !== 'string' || reliability === '' || !isNumber(confidence)) return null
  if (sameText(reliability, 'gering')) return ge(confidence, 0.9) ? '✔ mind. 90 % eingehalten' : '✖ gering: mind. 90 % erforderlich'
  if (sameText(reliability, 'hoch')) return ge(confidence, 0.6) ? '✔ mind. 60 % eingehalten' : '✖ hoch: mind. 60 % erforderlich'
  return gt(confidence, 0.6) && lt(confidence, 0.9) ? '✔ mittel: Wert zwischen den Eckwerten' : '⚠ mittel: Wert zwischen 60 % und 90 % begründen'
}

/** Prüfung Signifikanzschwelle (höchstens 2 %). */
export function checkMateriality(materiality: CellValue | undefined): CellValue {
  if (!isNumber(materiality)) return null
  return le(materiality, 0.02) ? '✔ ≤ 2 %' : '✖ unzulässig: höchstens 2 %'
}

/** Prüfhinweis bei AE > TE (KOM-Leitfaden EGESIF_16-0014-01, 7.1); die Vorlage zeigt hier „✖ TE ≤ AE: Stichprobenumfang nicht bestimmbar“. */
export const ANTICIPATED_ABOVE_TOLERABLE = '⚠ AE > TE: Umfang mit der geplanten Genauigkeit |TE − AE| (KOM-Leitfaden EGESIF_16-0014-01, 7.1)'
/** Prüfhinweis bei AE = TE. */
export const TOLERABLE_EQUALS_ANTICIPATED = '✖ TE = AE: Stichprobenumfang nicht bestimmbar (Division durch null)'

/**
 * Prüfung TE > AE; `rate` ist die Eingabe der voraussichtlichen Fehlerquote.
 * Nach KOM-Leitfaden EGESIF_16-0014-01 (7.1, S. 183) plant die Prüfbehörde
 * auch bei AE > TE, mit der Genauigkeit |TE − AE|; nicht bestimmbar ist der
 * Umfang nur bei AE = TE. Die Vorlage zeigt für beides „✖ TE ≤ AE“.
 */
export function checkTolerableError(tolerable: CellValue | undefined, anticipated: CellValue | undefined, rate: CellValue | undefined): CellValue {
  if (eq(n(tolerable), 0) || !isNumber(rate)) return null
  if (gt(n(tolerable), n(anticipated))) return '✔ TE > AE'
  return eq(n(tolerable), n(anticipated)) ? TOLERABLE_EQUALS_ANTICIPATED : ANTICIPATED_ABOVE_TOLERABLE
}

/** Größen der Formel n = (z · BV · σ / (TE − AE))². */
export interface SizeTerms {
  z: CellValue | undefined
  bookValue: CellValue | undefined
  deviation: CellValue | undefined
  tolerable: CellValue | undefined
  anticipated: CellValue | undefined
}

/**
 * Rechnerischer Stichprobenumfang, aufgerundet. Bei AE > TE nach KOM-Leitfaden
 * EGESIF_16-0014-01 (7.1) mit |TE − AE| (die quadrierte Formel liefert das); die
 * Vorlage zeigt dort „TE ≤ AE“ und keinen Umfang. Bei AE = TE nicht anwendbar
 * (Division durch null).
 */
export function computedSampleSize(terms: SizeTerms): CellValue {
  if (eq(n(terms.tolerable), 0) || !isNumber(terms.anticipated)) return null
  if (eq(n(terms.tolerable), terms.anticipated)) return SIZE_NOT_APPLICABLE
  return guard(() => roundUp(((required(terms.z) * required(terms.bookValue) * required(terms.deviation)) / minus(n(terms.tolerable), n(terms.anticipated))) ** 2))
}

/**
 * Der rechnerische Umfang ist offen, weil eine Angabe fehlt, mit der die
 * Vorlage als 0 weiterrechnen würde (voraussichtliche Fehlerquote,
 * Standardabweichung): TE und z liegen vor, der Umfang nicht.
 */
export function isSizePending(computed: CellValue | undefined, tolerable: CellValue | undefined, z: CellValue | undefined): boolean {
  return (computed ?? null) === null && ne(n(tolerable), 0) && isNumber(z)
}

/** Zulässigkeit und Höhe des begrenzten Stichprobenumfangs (Art. 5 Abs. 7; Art. 83 VO (EU) 2021/1060). */
export function limitedSampleSize(apply: CellValue | undefined, article83: CellValue | undefined, category: CellValue | undefined): [check: string, size: number | null] {
  if (!sameText(apply, 'Ja')) return ['Nicht angewandt – Anh. I und II gelten', null]
  if (sameText(article83, 'Ja')) return ['✔ 30 Einheiten (Art. 83 VO (EU) 2021/1060)', 30]
  if (sameNumber(category, 1) || sameNumber(category, 2)) return ['✔ 50 Einheiten zulässig (Art. 5 Abs. 7)', 50]
  return ['✖ unzulässig: nur Kategorie 1 oder 2', null]
}

/**
 * Anzuwendender Stichprobenumfang: mindestens 30, gegebenenfalls begrenzt.
 * `pending` (siehe `isSizePending`) lässt ihn offen statt auf 30 bzw. den
 * begrenzten Umfang zu fallen.
 */
export function appliedSampleSize(computed: CellValue | undefined, limit: number | null, pending: boolean): CellValue {
  if (pending) return null
  const atLeast30 = isNumber(computed) ? Math.max(computed, 30) : null
  if (limit === null) return atLeast30
  return atLeast30 === null ? limit : Math.min(atLeast30, limit)
}

/** Mindestens drei Einheiten in der Zufallsschicht (Art. 5 Abs. 5), ungeschichtete Blätter. */
export function checkMinimumUnits(units: CellValue | undefined): CellValue {
  if (!isNumber(units)) return null
  return ge(units, 3) ? '✔ ≥ 3 Einheiten' : '✖ < 3 Einheiten (Art. 5 Abs. 5)'
}

/**
 * Mindestens drei Einheiten je Zufallsschicht (Art. 5 Abs. 5), Schichtzeile:
 * `IF(n_h>=3;"✔ ≥ 3";"✖ < 3")`. Gibt es keinen Umfang je Schicht (`""`, etwa bei
 * „TE ≤ AE“), vergleicht die Vorlage eine leere Textzelle mit 3; ein Text ist im
 * Größenvergleich größer als jede Zahl, sie zeigt dann „✔ ≥ 3“. Das ist ein
 * Prüfhinweis ohne Grundlage (`unfounded`): Die Webfassung zeigt ihn nach der
 * geltenden Richtlinie nicht. `open`: Der Umfang fehlt nur, weil eine Angabe fehlt.
 */
export function checkStratumUnits(units: CellValue | undefined, open: boolean, context: Pick<SheetContext, 'policy'> | undefined): CellValue {
  if (isNumber(units)) return ge(units, 3) ? '✔ ≥ 3' : '✖ < 3'
  return open ? null : unfounded(context, '✔ ≥ 3')
}

/** Prüfung Iteration: Einheiten der Zufallsschicht mit BV über dem Auswahlintervall. */
export function checkIteration(units: CellValue | undefined): CellValue {
  if (!isNumber(units)) return null
  return eq(units, 0) ? '✔ keine weitere Iteration' : '⚠ Einheiten umgliedern und Intervall neu berechnen'
}

/** Untere Fehlergrenze: nur beim zweiseitigen Test. */
export function lowerErrorLimit(testType: CellValue | undefined, projected: CellValue | undefined, precision: CellValue | undefined, systemic: CellValue | undefined, anomalous: CellValue | undefined): CellValue {
  if (sameText(testType, 'einseitig')) return 'n. a. (einseitiger Test)'
  return guard(() => required(projected) - required(precision) + n(systemic) + n(anomalous))
}

/** Würdigung gegen die Signifikanzschwelle. */
export function assessment(totalErrorRate: CellValue | undefined, upperLimitRate: CellValue | undefined, materiality: CellValue | undefined): CellValue {
  if (!isNumber(totalErrorRate)) return null
  if (gt(totalErrorRate, n(materiality))) return '✖ Gesamtfehlerquote über der Signifikanzschwelle'
  // Wie in der Vorlage: Ein Text (hier die leere Zelle der oberen Fehlergrenze) ist im Vergleich größer als jede Zahl.
  if (!isNumber(upperLimitRate) || gt(upperLimitRate, n(materiality))) return '⚠ GFQ unter, obere Fehlergrenze über der Schwelle – weitere Würdigung'
  return '✔ GFQ und obere Fehlergrenze unter der Schwelle'
}
