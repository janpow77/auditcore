/**
 * Rechenkern Blatt 17_Unterstichprobe: Hochrechnung des Fehlers einer
 * Stichprobeneinheit aus einer Unterstichprobe (Art. 7; Art. 8 Abs. 3 DelVO
 * (EU) 2023/67). Die Vorlage ist je Stichprobeneinheit zu kopieren; gerechnet
 * wird hier eine Einheit, die Liste führt die Webfassung.
 */
import { divide, guard, minus, n, required, sameText } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import type { CellMap, SheetContext } from '../../model/types'
import { definition } from './definition'

/** Berechnet alle Formelzellen einer Stichprobeneinheit. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  // Variante 1 – Auswahl mit gleicher Wahrscheinlichkeit (Verhältnisschätzung)
  c.C13 = guard(() => n(c.C9) + divide(minus(required(c.C6), n(c.C8)) * n(c.C12), required(c.C11)))
  c.C14 = guard(() => divide(required(c.C13), required(c.C6)))
  // Variante 2 – PPS-Auswahl
  c.C16 = guard(() => divide(required(c.C6), required(c.C15)))
  c.C20 = guard(() => divide(minus(required(c.C6), n(c.C18)), minus(required(c.C15), n(c.C17))))
  c.C22 = guard(() => n(c.C19) + required(c.C20) * n(c.C21))
  c.C23 = guard(() => divide(required(c.C22), required(c.C6)))
  // Hinweis der Webfassung: maßgebliche Variante für die Übernahme ins Methodenblatt
  const second = sameText(c.W6, 'Variante 2')
  c.W7 = (second ? c.C22 : c.C13) ?? null
  c.W8 = (second ? c.C23 : c.C14) ?? null
  return c
}
