/**
 * Rechenkern Blatt 02_Grundgesamtheit: Weg vom Gesamtbetrag des letzten
 * Zahlungsantrags über die Datensätze zur zu prüfenden und zur angepassten
 * Grundgesamtheit (Art. 3 DelVO (EU) 2023/67). Jede Zuweisung bildet die Formel
 * der gleichnamigen Zelle nach. Buchwert und Anzahl (C51, C52) fließen als
 * Verknüpfung in die Methodenblätter.
 */
import { eq, gt, guard, isBlank, isNumber, le, left, lt, minus, n, plus, required, roundUp, sameNumber, sameText } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import type { CellMap, CellValue, Cells, SheetContext } from '../../model/types'
import { definition } from './definition'

/** Rundungsgrenze der Abstimmungen: Abweichungen unter einem Cent gelten als abgestimmt. */
const CENT = 0.01

/** Abschnitt B: Abstimmung mit dem letzten Zahlungsantrag (C17–C22). */
function paymentClaim(c: Cells): void {
  c.C17 = guard(() => minus(required(c.C16), required(c.C15)))
  if (isBlank(c.C15) || isBlank(c.C16)) c.C19 = null
  else if (lt(Math.abs(n(c.C17)), CENT)) c.C19 = '✔ Datenbestand und SFC2021 stimmen überein'
  else c.C19 = isBlank(c.C18) ? '✖ Differenz nicht erläutert' : '⚠ Differenz erläutert – Erläuterung fachlich würdigen'
  c.C22 = guard(() => (sameText(c.C21, 'Ja') ? minus(required(c.C16), n(c.C20)) : required(c.C16)))
}

/** Abschnitt C: Datensätze und ihre Abstimmung (C28–C31). */
function records(c: Cells): void {
  if (isBlank(c.C23)) c.C28 = null
  else c.C28 = sameNumber(n(c.C24) + n(c.C26), c.C23) ? '✔ Anzahl abgestimmt' : '✖ Anzahl nicht abgestimmt'
  if (isBlank(c.C27)) c.C29 = null
  else c.C29 = le(n(c.C27), 0) ? '✔ Summe ≤ 0' : '✖ Summe der negativen Datensätze ist positiv'
  c.C30 = guard(() => minus(plus(n(c.C25), n(c.C27)), required(c.C22)))
  if (isBlank(c.C25) || isBlank(c.C16)) c.C31 = null
  else c.C31 = lt(Math.abs(n(c.C30)), CENT) ? '✔ Datensätze stimmen mit SFC2021 überein' : '✖ Differenz – Datensätze und SFC2021 nicht abgestimmt'
}

/** Abschnitt D: zu prüfende Grundgesamtheit (C37–C39). */
function populationToAudit(c: Cells): void {
  const resubmitted = sameText(c.C36, 'Nein')
  c.C37 = guard(() => minus(required(c.C25), n(c.C33)) + (resubmitted ? n(c.C35) : 0))
  c.C38 = guard(() => minus(required(c.C24), n(c.C32)) + (resubmitted ? n(c.C34) : 0))
  c.C39 = guard(() => required(c.C37) + n(c.C20))
}

/** C50: Passt die gewählte Behandlung zu den erfassten Einheiten? */
function checkTreatment(c: Cells): CellValue {
  const none = sameText(left(c.C49, 5), 'keine')
  if (gt(n(c.C48), 0) && none) return '✖ betroffene Einheiten vorhanden – Ausschluss oder Ersetzung festlegen'
  if (eq(n(c.C48), 0) && !none) return '⚠ Ansatz gewählt, aber keine Einheiten erfasst'
  return '✔ schlüssig'
}

/** Abschnitte E und F: Einzige Prüfung und angepasste Grundgesamtheit (C47–C54). */
function adjustedPopulation(c: Cells): void {
  c.C47 = n(c.C42) + n(c.C45)
  c.C48 = n(c.C43) + n(c.C46)
  c.C50 = checkTreatment(c)
  const excluded = sameText(left(c.C49, 10), 'Ausschluss')
  c.C51 = guard(() => minus(required(c.C37), excluded ? n(c.C48) : 0))
  c.C52 = guard(() => minus(required(c.C38), excluded ? n(c.C47) : 0))
  const units = c.C52
  if (!isNumber(units) || eq(units, 0)) {
    c.C53 = null
    c.C54 = null
    return
  }
  c.C53 =
    lt(units, 300)
      ? '✔ weniger als 300 Einheiten: nichtstatistisches Verfahren zulässig (Art. 79 Abs. 2 VO (EU) 2021/1060)'
      : '⚠ 300 Einheiten oder mehr: statistisches Verfahren (Ausnahme Art. 6 Abs. 3)'
  c.C54 = roundUp(0.1 * units)
}

/** Berechnet alle Formelzellen des Blatts 02. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  paymentClaim(c)
  records(c)
  populationToAudit(c)
  adjustedPopulation(c)
  c.C55 = n(c.C26)
  c.C56 = n(c.C27)
  return c
}
