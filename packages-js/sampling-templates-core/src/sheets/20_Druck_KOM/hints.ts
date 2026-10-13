/** Hinweise der Webfassung zu Blatt 20; sie verändern kein Rechenergebnis und werden nicht mitgedruckt. */
import { eq, isBlank, isNumber } from '../../excel/index'
import type { CellMap, WebHint } from '../../model/types'
import { CASE_ROWS } from './definition'

export function webHints(_inputs: CellMap, results: CellMap): WebHint[] {
  const hints: WebHint[] = [
    { id: 'fixed-programme', tone: 'neutral', text: 'Kopf- und Fußzeile nennen wie in der Vorlage fest das „EFRE-Programm Hessen 2021–2027“ und die Prüfbehörde in Wiesbaden; für andere Programme ist die Vorlage anzupassen' },
  ]
  const zero = CASE_ROWS.filter((row) => isNumber(results[`C${row}`]) && eq(results[`C${row}`] as number, 0) && !isBlank(results[`D${row}`]))
  if (zero.length) hints.push({ id: 'case-book-value-zero', tone: 'warning', text: `Fehlerfall ${zero.map((row) => row - CASE_ROWS[0] + 1).join(', ')}: Buchwert 0 – die Quote ist nicht bestimmbar (die Vorlage zeigt dort einen Fehlerwert)` })
  if (isBlank(results.G42) && isNumber(results.G32)) hints.push({ id: 'residual-rate-undefined', tone: 'warning', text: 'Die Restfehlerquote ist nicht bestimmbar: Beträge nach Artikel 98 Absatz 6 und Finanzkorrekturen erreichen zusammen die Hochrechnungsbasis' })
  return hints
}
