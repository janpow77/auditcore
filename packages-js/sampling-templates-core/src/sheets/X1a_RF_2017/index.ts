/**
 * Blatt X1a_RF_2017: Tabelle der Zuverlässigkeitsfaktoren der Vorlage von 2017.
 * Das Blatt hat weder Eingaben noch Formeln und ist deshalb kein Rechenblatt;
 * es steht im Register als Datentabelle (`tableSheet`) und wird aus Blatt X1 heraus geöffnet. Die Tabelle liegt als geprüfte
 * Daten in `table.ts` (docs/blatt-ergaenzen.md); `table` gibt sie als
 * Nachschlagetabelle aus, die sich ohne Kenntnis des Blatts anzeigen lässt.
 */
import { tableSheet } from '../../model/sheet'
import { table } from './table'

export { ERRORS_LABEL, FIRST_ROW, RELIABILITY_FACTORS, RISK_COLUMNS, RISK_LABEL, RISK_LEVELS, TABLE_TITLE, reliabilityFactor, table, tableCells } from './table'

export const sheet = tableSheet('X1a_RF_2017', table)
