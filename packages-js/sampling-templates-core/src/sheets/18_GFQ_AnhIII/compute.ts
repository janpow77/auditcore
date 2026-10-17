/**
 * Rechenkern Blatt 18_GFQ_AnhIII: Gesamtfehlerquote mit Pauschale der technischen
 * Hilfe (Art. 8 Abs. 5 DelVO (EU) 2023/67) und Anpassung nach Anhang III bei
 * Ausschluss oder Ersetzung nicht prüfbarer Einheiten (Art. 80 Abs. 3 VO (EU)
 * 2021/1060). Jede Zuweisung bildet die Formel der gleichnamigen Zelle nach.
 *
 * Die Vorlage liest das Methodenblatt über `INDIRECT("'"&C4&"'!N4")`. Hier ist
 * C4 das aktive Verfahren des Arbeitsstands; seine Ergebnisübersicht N3–N11
 * steht in `context.method`. Übernommen wird nur aus Blättern der Auswahlliste
 * der Vorlage (01_Parameter!I24:I37); Altvorlagen und Blatt 17 haben keine
 * Ergebnisübersicht.
 */
import { divide, gt, guard, isBlank, isNumber, left, lt, minus, n, plus, required, search, sameText } from '../../excel/index'
import { unfounded } from '../../model/policy'
import { resolveInputs } from '../../model/sheet'
import type { CellMap, CellValue, Cells, MethodSummary, SheetContext } from '../../model/types'
import { definition } from './definition'

/** Blatt, aus dem die Grundgesamtheiten stammen. */
export const POPULATION_SHEET = '02_Grundgesamtheit'

/** Text der Vorlage, wenn es keine Genauigkeit gibt (nichtstatistische Verfahren). */
export const NOT_APPLICABLE = 'n. a.'

/** Ergebnisübersicht des aktiven Verfahrens, wenn es in der Auswahlliste der Vorlage steht; sonst keine Übernahme. */
export function adoptedMethod(context: SheetContext): MethodSummary | undefined {
  const method = context.method
  return method && context.parameters.lists.methodSheets.includes(method.sheet) ? method : undefined
}

/** `LEFT($C$15;10)="Ausschluss"` */
const isExclusion = (c: Cells): boolean => sameText(left(c.C15, 10), 'Ausschluss')

/** `ISNUMBER(SEARCH(text;C4))` */
const contains = (text: string, value: CellValue): boolean => guard(() => search(text, value)) !== null

/** Zellen C5–C10 mit der Größe der Ergebnisübersicht (N4–N9), die sie übernehmen. */
const ADOPTED: readonly (readonly [cell: string, value: keyof MethodSummary])[] = [
  ['C5', 'bookValue'],
  ['C6', 'projectedError'],
  ['C7', 'exhaustiveError'],
  ['C8', 'precision'],
  ['C9', 'systemicErrors'],
  ['C10', 'anomalousErrors'],
]

/** Abschnitt A: Übernahme aus der Ergebnisübersicht des Methodenblatts (C4–C11). */
function method(c: Cells, context: SheetContext): void {
  const adopted = adoptedMethod(context)
  c.C4 = adopted?.sheet ?? null
  // =IFERROR(INDIRECT("'"&$C$4&"'!N4");""): Zahl bleibt Zahl, Text bleibt Text, "" bleibt leer.
  for (const [cell, value] of ADOPTED) c[cell] = adopted?.[value] ?? null
  if (isBlank(c.C4)) c.C11 = null
  else c.C11 = contains('MUS', c.C4) || contains('PPS', c.C4) ? 'Tabelle 1 (MUS/PPS)' : 'Tabelle 2 (SRS/gleiche Wahrscheinlichkeit)'
}

/** C19: Stimmt die Hochrechnungsbasis des Methodenblatts mit der erwarteten Grundgesamtheit überein? */
function checkBookValue(c: Cells): CellValue {
  if (isBlank(c.C5)) return null
  const difference = guard(() => Math.abs(minus(required(c.C5), required(isExclusion(c) ? c.C17 : c.C14))))
  if (difference === null) return null
  return lt(difference, 1)
    ? '✔ Basis stimmt mit der erwarteten Grundgesamtheit überein'
    : '⚠ Basis weicht ab – Ausschluss: reduzierte, Ersetzung/keine: ursprüngliche Grundgesamtheit'
}

/** Abschnitt B: Grundgesamtheiten aus Blatt 02 und Anpassungsfaktor (C12–C19). */
function populations(c: Cells, context: SheetContext): void {
  const population = context.sheets[POPULATION_SHEET] ?? {}
  c.C12 = population.C39 ?? null
  c.C13 = n(population.C20)
  c.C14 = guard(() => minus(required(c.C12), required(c.C13)))
  // =IFERROR(02_Grundgesamtheit!$C$49;""): Die Vorlage zeigt für die leere Zelle 0; die Webfassung zeigt „Angabe fehlt“.
  c.C15 = population.C49 ?? null
  c.C16 = n(population.C48)
  c.C17 = guard(() => minus(required(c.C14), required(c.C16)))
  c.C18 = guard(() => divide(required(c.C14), required(c.C17)))
  c.C19 = checkBookValue(c)
}

/** C24: angepasster extrapolierter Fehler nach Anhang III. */
function adjustedError(c: Cells): CellValue {
  const exclusion = isExclusion(c)
  if (!sameText(c.C20, 'Ja')) return exclusion ? guard(() => required(c.C6) * required(c.C18)) : (c.C6 ?? null)
  return guard(() => {
    const random = minus(required(c.C6), required(c.C7))
    return plus(exclusion ? random * required(c.C18) : random, required(c.C23))
  })
}

/** C25: angepasste Genauigkeit; ohne Genauigkeit im Methodenblatt „n. a.“. */
function adjustedPrecision(c: Cells, context: SheetContext): CellValue {
  // Ohne Wert in C8 zeigt die Vorlage „n. a.“ – auch dann, wenn das Methodenblatt nur noch keine Genauigkeit liefert.
  if (isBlank(c.C8)) return unfounded(context, NOT_APPLICABLE)
  if (!isNumber(c.C8)) return NOT_APPLICABLE
  // Wortgleich zur Vorlage: `LEFT($C$11;10)="Tabelle 2"` vergleicht zehn Zeichen („Tabelle 2 “) mit neun und trifft
  // deshalb nie zu – bei Ersetzung wird die Genauigkeit auch in Tabelle 2 nicht angepasst (Auffälligkeit der Vorlage).
  const scaled = isExclusion(c) || (sameText(left(c.C15, 9), 'Ersetzung') && sameText(left(c.C11, 10), 'Tabelle 2'))
  return scaled ? guard(() => required(c.C8) * required(c.C18)) : c.C8
}

/** C28: obere Fehlergrenze in Prozent; ohne Genauigkeit „n. a.“. */
function upperLimit(c: Cells, context: SheetContext): CellValue {
  if (isBlank(c.C25)) return unfounded(context, NOT_APPLICABLE)
  if (!isNumber(c.C25)) return NOT_APPLICABLE
  return guard(() => divide(plus(plus(plus(required(c.C24), required(c.C25)), n(c.C9)), n(c.C10)), required(c.C14)))
}

/** C30: Würdigung gegen die Signifikanzschwelle. */
function assessment(c: Cells, context: SheetContext): CellValue {
  if (!isNumber(c.C26) || !isNumber(c.C29)) return null
  if (gt(c.C26, c.C29)) return '✖ Gesamtfehlerquote über der Signifikanzschwelle'
  if (isNumber(c.C28)) return gt(c.C28, c.C29) ? '⚠ GFQ unter, obere Fehlergrenze über der Schwelle' : '✔ unter der Signifikanzschwelle'
  // Ohne obere Fehlergrenze (Text „n. a.“) prüft die Vorlage nur die Gesamtfehlerquote. Fehlt sie nur, weil das
  // Methodenblatt noch keine Genauigkeit liefert, hätte der bestandene Hinweis keine Grundlage.
  return isBlank(c.C28) ? unfounded(context, '✔ unter der Signifikanzschwelle') : '✔ unter der Signifikanzschwelle'
}

/** Abschnitte C bis E: hochwertige Schicht, Anpassung nach Anhang III, Gesamtfehlerquote und Würdigung (C23–C30). */
function totalErrorRate(c: Cells, context: SheetContext): void {
  c.C23 = guard(() => divide(required(c.C7) * required(c.C21), required(c.C22)))
  c.C24 = adjustedError(c)
  c.C25 = adjustedPrecision(c, context)
  c.C26 = guard(() => divide(plus(plus(required(c.C24), n(c.C9)), n(c.C10)), required(c.C14)))
  c.C27 = guard(() => required(c.C26) * required(c.C12))
  c.C28 = upperLimit(c, context)
  c.C30 = assessment(c, context)
}

/** Berechnet alle Formelzellen des Blatts 18; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  method(c, context)
  populations(c, context)
  totalErrorRate(c, context)
  return c
}
