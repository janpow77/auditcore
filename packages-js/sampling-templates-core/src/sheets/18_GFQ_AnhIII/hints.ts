/**
 * Hinweise der Webfassung zu Blatt 18; sie verändern kein Rechenergebnis. Sie
 * sagen ausdrücklich, wenn aus dem Methodenblatt oder aus Blatt 02 nichts
 * übernommen wird – die betroffenen Zellen blieben sonst wortlos leer.
 */
import { gt, isBlank, isNumber, le, sameText } from '../../excel/index'
import type { CellMap, SheetContext, WebHint } from '../../model/types'
import { allExhaustiveAffected, hasExhaustiveStratum, isExclusion, isReplacementTable2, locationOf, locationViolations } from './annex'
import { adoptedMethod } from './compute'
import { APPROXIMATION_ID, APPROXIMATION_TEXT } from '../shared/kom'

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

const TEMPLATE_REPLACEMENT = 'Die Vorlage rechnet hier anders (sie übernimmt die Genauigkeit des Methodenblatts, gerechnet für die ursprüngliche Grundgesamtheit, ohne Anpassung; ihr Vergleich mit „Tabelle 2“ trifft nie zu); Entscheidung des Inhabers vom 17.10.2026'
const REPLACEMENT_BY_STRATUM = `Berechnet nach DelVO (EU) 2023/67, Anhang III Tabelle 2 (Ersetzung: Genauigkeit für die reduzierte Grundgesamtheit, angepasst mit BV(h) ursprünglich / BV(h) reduziert), bezogen auf die Zufallsschicht nach KOM-Leitfaden EGESIF_16-0014-01 (7.10.2 mit Fußnote 70, 7.10.3.4): Genauigkeit des Methodenblatts mal (N_s − A_s)/N_s und BV_s / BV_s,r; obere Fehlergrenze und Würdigung beruhen darauf. ${TEMPLATE_REPLACEMENT}`
const REPLACEMENT_WITHOUT_EXHAUSTIVE = `Berechnet nach DelVO (EU) 2023/67, Anhang III Tabelle 2 (Ersetzung): Genauigkeit für die reduzierte Grundgesamtheit (Genauigkeit des Methodenblatts mal (N − A)/N), angepasst mit BV/BV_r; obere Fehlergrenze und Würdigung beruhen darauf. ${TEMPLATE_REPLACEMENT}`
const REPLACEMENT_APPROXIMATION = `Ersetzung (DelVO (EU) 2023/67, Anhang III Tabelle 2) mit Gesamt-Näherung: Genauigkeit des Methodenblatts mal (N − A)/N und BV/BV_r. Das ist nicht KOM-konform: Es gibt eine umfassende Schicht, und der KOM-Leitfaden EGESIF_16-0014-01 (7.10.2, 7.10.3.4) bezieht Anzahl und Buchwert auf die Zufallsschicht. Die Lage der berührten Einheiten fehlt; bitte in Abschnitt F erfassen. ${TEMPLATE_REPLACEMENT}`
const EXCLUSION_BY_STRATUM =
  'Ausschluss, berechnet nach KOM-Leitfaden EGESIF_16-0014-01 (7.10.3.2, 7.10.3.4) zu Anhang III DelVO (EU) 2023/67: Zufallsteil von Hochrechnung und Genauigkeit mit dem Verhältnis der Zufallsschicht BV_s / BV_s,r, umfassende Schicht über EE_e = EE_e,r · BV_e / BV_e,r. Die Vorlage rechnet hier anders (mit dem Gesamtfaktor BV/BV_r, bei Abschnitt C nur für den Zufallsteil); Entscheidung des Inhabers vom 17.10.2026'
const EXCLUSION_LOCATION_MISSING =
  'Ausschluss wie die Vorlage mit dem Gesamtfaktor BV/BV_r (bei Abschnitt C nur für den Zufallsteil). Das ist nicht KOM-konform: Es gibt eine umfassende Schicht, und der KOM-Leitfaden EGESIF_16-0014-01 (7.10.3.2, 7.10.3.4) passt den Zufallsteil mit dem Verhältnis der Zufallsschicht und die umfassende Schicht über EE_e an (Beispiel 7.10.3.4: nach KOM 1,44 %; wie die Vorlage ohne Abschnitt C 1,49 %, mit Abschnitt C 1,50 %). Die Lage der berührten Einheiten fehlt; bitte in Abschnitt F erfassen'

/** Ausschluss mit mindestens einer berührten Einheit bzw. Ersetzung bei Tabelle 2 mit Genauigkeit. */
const excludes = (c: CellMap): boolean => isExclusion(c) && isNumber(c.C16) && gt(c.C16, 0)
const replacesTable2 = (c: CellMap): boolean => isReplacementTable2(c) && isNumber(c.C8)

const ALL_AFFECTED =
  'Alle Einheiten der umfassenden Schicht sind nach Art. 80 Abs. 3 berührt (BV_e = BV_A,e, also BV_e,r = 0): EE_e = EE_e,r · BV_e / BV_e,r ist nicht bestimmbar (Division durch null), der angepasste Fehler bleibt offen („—“). Nach KOM-Leitfaden EGESIF_16-0014-01 (7.10.3.1 b) werden berührte Einheiten der hochwertigen Schicht durch Einheiten der Zufallsschicht ersetzt, weil in der hochwertigen Schicht keine Einheit zur Ersetzung bleibt; ihr Fehler fließt dann über die Zufallsschicht ein. Bitte Stichprobe und Abschnitt F prüfen'

/** Abschnitt F unplausibel: verletzte Bedingungen nennen, keine Rechnung nach Lage. */
function implausibleHints(results: CellMap, context: SheetContext): WebHint[] {
  const violations = locationViolations(results, context)
  return violations.length ? [warning('location-implausible', `Eingabe unplausibel in Abschnitt F (Lage der berührten Einheiten): ${violations.join('; ')}. Angepasster Fehler und angepasste Genauigkeit bleiben offen („—“)`)] : []
}

/** Ersetzung bei Tabelle 2: je Zufallsschicht (mit Lage), exakt ohne umfassende Schicht oder Gesamt-Näherung (nicht KOM-konform). */
function replacementHint(located: boolean, exhaustive: boolean): WebHint {
  if (located) return warning('replacement-precision-not-scaled', REPLACEMENT_BY_STRATUM)
  return exhaustive ? warning('replacement-location-missing', REPLACEMENT_APPROXIMATION) : warning('replacement-precision-reduced', REPLACEMENT_WITHOUT_EXHAUSTIVE)
}

/** Anpassung nach Anhang III je nach erfasster Lage (Abschnitt F) und umfassender Schicht (n_e bzw. BV_e des Methodenblatts). */
function annexHints(results: CellMap, context: SheetContext): WebHint[] {
  if (locationViolations(results, context).length) return implausibleHints(results, context)
  const location = locationOf(results)
  if (allExhaustiveAffected(location) && (replacesTable2(results) || excludes(results))) return [warning('exhaustive-all-affected', ALL_AFFECTED)]
  const exhaustive = hasExhaustiveStratum(results, context)
  if (replacesTable2(results)) return [replacementHint(location !== null, exhaustive)]
  if (!excludes(results)) return []
  if (location) return [warning('exclusion-by-stratum', EXCLUSION_BY_STRATUM)]
  return exhaustive ? [warning('exclusion-location-missing', EXCLUSION_LOCATION_MISSING)] : []
}

/** Unvollständige hochwertige Schicht (Abschnitt C). */
function highValueHints(results: CellMap): WebHint[] {
  if (!sameText(results.C20, 'Ja') || (!isBlank(results.C21) && !isBlank(results.C22))) return []
  return [warning('high-value-incomplete', 'Anpassung der hochwertigen Schicht gewählt, aber der Buchwert der ursprünglichen (BV_e,u) oder der geprüften hochwertigen Schicht (BV_e,r) fehlt')]
}

/** Verfahren mit mehreren Schichten oder Zeiträumen: Der KOM-Leitfaden passt je Schicht bzw. Zeitraum an. */
const SEVERAL: ReadonlySet<string> = new Set(['04_MUS_1Z_S', '05_MUS_2Z', '06_MUS_2Z_S', '07_MUS_3Z', '09_SRS_1Z_S', '10_SRS_2Z', '11_SRS_2Z_S', '12_SRS_3Z', '14_NS_GW_S', '16_NS_PPS_S'])

/** Nr. 4 des DelVO-Abgleichs: Ausschluss oder Ersetzung (Tabelle 2) bei mehreren Schichten oder Zeiträumen – anteilige Näherung. */
function approximationHints(results: CellMap, context: SheetContext): WebHint[] {
  const adjusts = excludes(results) || replacesTable2(results)
  if (!context.method || !SEVERAL.has(context.method.sheet) || !adjusts || !isNumber(results.C18)) return []
  return [warning(APPROXIMATION_ID, APPROXIMATION_TEXT)]
}

/** Hinweise der Webfassung zu Blatt 18. */
export function webHints(_inputs: CellMap, results: CellMap, context: SheetContext): WebHint[] {
  return [...methodHints(results, context), ...populationHints(results), ...annexHints(results, context), ...highValueHints(results), ...approximationHints(results, context)]
}
