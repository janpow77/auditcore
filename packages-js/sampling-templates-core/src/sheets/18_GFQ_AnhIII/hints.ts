/**
 * Hinweise der Webfassung zu Blatt 18; sie verändern kein Rechenergebnis. Sie
 * sagen ausdrücklich, wenn aus dem Methodenblatt oder aus Blatt 02 nichts
 * übernommen wird – die betroffenen Zellen blieben sonst wortlos leer.
 */
import { isBlank, isNumber, le, left, sameText } from '../../excel/index'
import type { CellMap, SheetContext, WebHint } from '../../model/types'
import { adoptedMethod } from './compute'

const warning = (id: string, text: string): WebHint => ({ id, tone: 'warning', text })

/** Übernahme aus dem Methodenblatt: kein Verfahren, Blatt ohne Ergebnisübersicht oder unvollständige Übersicht. */
function methodHints(results: CellMap, context: SheetContext): WebHint[] {
  if (!context.method) return [warning('no-method', 'Kein Verfahren gewählt: Aus einem Methodenblatt wird nichts übernommen; die Zeilen 4 bis 11 bleiben leer')]
  if (!adoptedMethod(context)) {
    return [warning('method-without-summary', `Blatt ${context.method.sheet} hat keine Ergebnisübersicht und steht nicht in der Auswahlliste der Vorlage (Altvorlage von 2017 bzw. Hilfsblatt): Es wird nichts übernommen; die Zeilen 4 bis 11 bleiben leer`)]
  }
  const open = [
    ...(isBlank(results.C5) ? ['Buchwert der Hochrechnungsbasis (BV)'] : []),
    ...(isBlank(results.C6) ? ['extrapolierter Fehler (EE)'] : []),
    ...(isBlank(results.C8) ? ['Genauigkeit (SE)'] : []),
  ]
  return open.length ? [warning('method-incomplete', `Das Methodenblatt ${context.method.sheet} liefert noch keinen Wert für: ${open.join(', ')}. Dort fehlen Angaben`)] : []
}

/** Grundgesamtheiten aus Blatt 02: fehlende Grundgesamtheit, fehlende Behandlung, nicht positive reduzierte Grundgesamtheit. */
function populationHints(results: CellMap): WebHint[] {
  const hints: WebHint[] = []
  if (isBlank(results.C12)) hints.push(warning('population-missing', 'Blatt 02 liefert keine zu prüfende Grundgesamtheit (dort fehlen Angaben); Hochrechnungsbasis, Anpassungsfaktor und Gesamtfehlerquote bleiben offen'))
  if (isBlank(results.C15)) hints.push(warning('treatment-missing', 'In Blatt 02 ist keine Behandlung der nach Art. 80 Abs. 3 nicht prüfbaren Einheiten gewählt; gerechnet wird wie in der Vorlage ohne Ausschluss und ohne Ersetzung'))
  if (isNumber(results.C17) && le(results.C17, 0)) hints.push(warning('reduced-population-not-positive', 'Die reduzierte Grundgesamtheit (BV_r) ist nicht positiv; der Anpassungsfaktor ist dann nicht aussagekräftig'))
  return hints
}

/** Anpassung nach Anhang III: Genauigkeit bei Ersetzung (Tabelle 2) und unvollständige hochwertige Schicht. */
function adjustmentHints(results: CellMap): WebHint[] {
  const hints: WebHint[] = []
  if (isNumber(results.C8) && sameText(left(results.C15, 9), 'Ersetzung') && sameText(left(results.C11, 9), 'Tabelle 2')) {
    hints.push(warning('replacement-precision-not-scaled', 'Ersetzung bei einem Verfahren der Tabelle 2: Nach dem Hinweis der Vorlage ist die Genauigkeit mit dem Anpassungsfaktor anzupassen; die Formel der Vorlage tut das nicht (ihr Vergleich mit „Tabelle 2“ trifft nie zu). Die Webfassung rechnet wie die Vorlage – angepasste Genauigkeit und obere Fehlergrenze fachlich würdigen'))
  }
  if (sameText(results.C20, 'Ja') && (isBlank(results.C21) || isBlank(results.C22))) {
    hints.push(warning('high-value-incomplete', 'Anpassung der hochwertigen Schicht gewählt, aber der Buchwert der ursprünglichen (BV_e,u) oder der geprüften hochwertigen Schicht (BV_e,r) fehlt'))
  }
  return hints
}

/** Hinweise der Webfassung zu Blatt 18. */
export function webHints(_inputs: CellMap, results: CellMap, context: SheetContext): WebHint[] {
  return [...methodHints(results, context), ...populationHints(results), ...adjustmentHints(results)]
}
