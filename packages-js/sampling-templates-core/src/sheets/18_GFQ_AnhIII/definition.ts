/**
 * Methodendefinition Blatt 18_GFQ_AnhIII. Erzeugt mit `scripts/generate-definition.mjs`
 * und von Hand geprüft: Bezeichnungen (Spalte B) und Fundstellen (Spalte D) wörtlich;
 * Formeln aus den Bezeichnungen der Zeilen 23 und 26 stehen in `formula`.
 *
 * Abweichend von der Vorlage ist C4 keine Auswahl: Das Methodenblatt ist das im
 * Arbeitsstand gewählte Verfahren; die Zelle zeigt dessen Blattnamen. Die Fundstelle
 * der Vorlage („Auswahlliste; …“) bleibt wörtlich stehen.
 */
import type { FieldDefinition, MethodDefinition } from '../../model/definition'
import { UPPER_LIMIT_INTERPRETATION } from '../shared/interpretations'

const EUR = '#,##0.00" €"'
const RATE = '0.00%'

const method: FieldDefinition[] = [
  { cell: 'C4', alias: 'methodSheet', kind: 'formula', type: 'text', format: '@', label: 'Angewandtes Methodenblatt', hint: 'Auswahlliste; Werte werden aus der Ergebnisübersicht (Spalten M:N) übernommen.' },
  { cell: 'C5', alias: 'methodBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Hochrechnungsbasis im Methodenblatt (BV)' },
  { cell: 'C6', alias: 'projectedError', kind: 'formula', type: 'amount', format: EUR, label: 'Extrapolierter Fehler (inkl. umfassende Schicht) (EE)' },
  { cell: 'C7', alias: 'exhaustiveError', kind: 'formula', type: 'amount', format: EUR, label: 'davon Fehler der umfassenden Schicht (EE_e)' },
  { cell: 'C8', alias: 'precision', kind: 'formula', type: 'amount', format: EUR, label: 'Genauigkeit der Stichprobe (SE)' },
  { cell: 'C9', alias: 'systemicErrors', kind: 'formula', type: 'amount', format: EUR, label: 'Abgegrenzte systembedingte Fehler' },
  { cell: 'C10', alias: 'anomalousErrors', kind: 'formula', type: 'amount', format: EUR, label: 'Nicht berichtigte anomale Fehler' },
  { cell: 'C11', alias: 'annexTable', kind: 'formula', type: 'text', format: '@', label: 'Verfahrensfamilie für Anhang III' },
]

const populations: FieldDefinition[] = [
  { cell: 'C12', alias: 'populationToAudit', kind: 'formula', type: 'amount', format: EUR, label: 'Zu prüfende Grundgesamtheit für die Gesamtfehlerquote (Art. 3 Abs. 5)' },
  { cell: 'C13', alias: 'technicalAssistanceFlatRate', kind: 'formula', type: 'amount', format: EUR, label: 'Pauschalfinanzierung technische Hilfe (Art. 36 Abs. 5 VO (EU) 2021/1060)' },
  { cell: 'C14', alias: 'originalBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Hochrechnungsbasis ohne technische Hilfe (Art. 8 Abs. 5) (BV_u)' },
  { cell: 'C15', alias: 'article80Treatment', kind: 'formula', type: 'text', format: '@', label: 'Behandlung der nach Art. 80 Abs. 3 nicht prüfbaren Einheiten' },
  { cell: 'C16', alias: 'unauditableBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der nach Art. 80 Abs. 3 nicht prüfbaren Einheiten' },
  { cell: 'C17', alias: 'reducedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Reduzierte Grundgesamtheit (BV_r)' },
  { cell: 'C18', alias: 'adjustmentFactor', kind: 'formula', type: 'decimal', format: '0.0000', label: 'Anpassungsfaktor BV_ursprünglich / BV_reduziert', hint: 'Anh. III Tabellen 1 und 2.' },
  { cell: 'C19', alias: 'checkBookValue', kind: 'formula', type: 'check', label: 'Abgleich der Hochrechnungsbasis des Methodenblatts' },
]

const highValue: FieldDefinition[] = [
  { cell: 'C20', alias: 'adjustHighValueStratum', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Hochrechnung für nicht geprüfte hochwertige Einheiten anwenden (Ja/Nein)' },
  { cell: 'C21', alias: 'highValueOriginalBookValue', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der ursprünglichen hochwertigen Schicht (BV_e,u)' },
  { cell: 'C22', alias: 'highValueAuditedBookValue', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der geprüften Einheiten der hochwertigen Schicht (BV_e,r)' },
  { cell: 'C23', alias: 'adjustedExhaustiveError', kind: 'formula', type: 'amount', format: EUR, label: 'EE_e', formula: 'EE_e,reduziert · BV_e,ursprünglich / BV_e,reduziert' },
]

/** Lage der berührten Einheiten nach KOM-Leitfaden (freiwillige Gruppe; nicht in der Vorlage). */
const LOCATION = 'article80Location'
const location: FieldDefinition[] = [
  { cell: 'C31', alias: 'locationExhaustiveUnits', kind: 'input', optional: LOCATION, type: 'integer', format: '#,##0', label: 'Einheiten der hochwertigen bzw. umfassenden Schicht der ursprünglichen Grundgesamtheit (N_e)', hint: 'Freiwillig; mit allen vier Angaben passt Blatt 18 nach KOM-Leitfaden EGESIF_16-0014-01 (7.10.3) je Schicht an. Gibt es keine solche Schicht, überall 0 eintragen.' },
  { cell: 'C32', alias: 'locationExhaustiveBookValue', kind: 'input', optional: LOCATION, type: 'amount', format: EUR, label: 'Buchwert der hochwertigen bzw. umfassenden Schicht der ursprünglichen Grundgesamtheit (BV_e)' },
  { cell: 'C33', alias: 'locationAffectedUnits', kind: 'input', optional: LOCATION, type: 'integer', format: '#,##0', label: 'davon nach Art. 80 Abs. 3 berührt: Anzahl (A_e)' },
  { cell: 'C34', alias: 'locationAffectedBookValue', kind: 'input', optional: LOCATION, type: 'amount', format: EUR, label: 'davon nach Art. 80 Abs. 3 berührt: Buchwert (BV_A,e)' },
  { cell: 'C35', alias: 'randomStratumAffectedUnits', kind: 'formula', type: 'integer', format: '#,##0', label: 'Berührte Einheiten der Zufallsschicht (A_s)', formula: 'A_s = A − A_e' },
  { cell: 'C36', alias: 'randomStratumOriginalBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Zufallsschicht, ursprünglich (BV_s)', formula: 'BV_s = BV_u − BV_e' },
  { cell: 'C37', alias: 'randomStratumReducedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Zufallsschicht, reduziert (BV_s,r)', formula: 'BV_s,r = BV_s − (BV_A − BV_A,e)' },
  { cell: 'C38', alias: 'randomStratumFactor', kind: 'formula', type: 'decimal', format: '0.0000', label: 'Anpassungsfaktor der Zufallsschicht BV_s / BV_s,r', hint: 'KOM-Leitfaden EGESIF_16-0014-01, 7.10.2 und 7.10.3.' },
]

const adjusted: FieldDefinition[] = [
  {
    cell: 'C24',
    alias: 'adjustedProjectedError',
    kind: 'result',
    type: 'amount',
    format: EUR,
    label: 'Angepasster extrapolierter Fehler (EE)',
    hint: 'Ausschluss: EE × Faktor; Ersetzung: Hochrechnung auf die ursprüngliche Grundgesamtheit. Bei Anwendung von C wird nur der Zufallsteil skaliert (Auslegung).',
    interpretation: 'Bei Anwendung von Abschnitt C wird nur der Zufallsteil des extrapolierten Fehlers mit dem Anpassungsfaktor skaliert.',
  },
  { cell: 'C25', alias: 'adjustedPrecision', kind: 'result', type: 'amount', format: EUR, label: 'Angepasste Genauigkeit (SE)', hint: 'Tabelle 2, Ersetzung: Genauigkeit für die reduzierte Grundgesamtheit berechnen und mit dem Faktor anpassen. Die Webfassung rechnet nach der DelVO: SE · N_r/N · BV/BV_r (die Vorlage passt nicht an).' },
]

const totalErrorRate: FieldDefinition[] = [
  { cell: 'C26', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: RATE, label: 'Gesamtfehlerquote', formula: '(EE + systembedingte + nicht berichtigte anomale Fehler) / BV ohne TH', hint: 'Art. 8 Abs. 1; nach Art. 8 Abs. 5 gilt die Quote auch für die Grundgesamtheit einschließlich TH.' },
  { cell: 'C27', alias: 'errorAmountIncludingFlatRate', kind: 'result', type: 'amount', format: EUR, label: 'Fehlerbetrag bezogen auf die zu prüfende Grundgesamtheit einschließlich TH' },
  { cell: 'C28', alias: 'upperErrorLimitRate', kind: 'formula', type: 'percent', format: RATE, label: 'Obere Fehlergrenze in % (inkl. Genauigkeit)', hint: 'Art. 2 Nr. 20.' },
  { cell: 'C29', alias: 'materiality', kind: 'input', type: 'percent', format: RATE, default: 0.02, label: 'Signifikanzschwelle' },
  { cell: 'C30', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung', interpretation: UPPER_LIMIT_INTERPRETATION },
]

export const definition: MethodDefinition = {
  sheet: '18_GFQ_AnhIII',
  number: '18',
  title: 'Gesamtfehlerquote, technische Hilfe und Einzige Prüfung',
  shortTitle: 'Gesamtfehlerquote',
  legalBasis: 'Art. 3 Abs. 5 und 6; Art. 8 Abs. 1, 4 und 5; Anhang III DelVO (EU) 2023/67; Art. 36 Abs. 5, Art. 80 Abs. 3 VO (EU) 2021/1060',
  sections: [
    { id: 'A', title: 'Übernahme aus dem Methodenblatt', fields: method },
    { id: 'B', title: 'Grundgesamtheiten', reference: 'aus Blatt 02', fields: populations },
    { id: 'C', title: 'Anpassung hochwertige Schicht', reference: 'Anhang III, optional', fields: highValue },
    { id: 'F', title: 'Lage der berührten Einheiten', reference: 'KOM-Leitfaden EGESIF_16-0014-01, 7.10; freiwillig', fields: location },
    { id: 'D', title: 'Angepasster extrapolierter Fehler und angepasste Genauigkeit', reference: 'Anhang III', fields: adjusted },
    { id: 'E', title: 'Gesamtfehlerquote', reference: 'Art. 8 Abs. 1 und 5', fields: totalErrorRate },
  ],
  summary: {
    primary: { cell: 'C26', label: 'Gesamtfehlerquote', unit: '' },
    rows: [
      { cell: 'C28', label: 'Obere Fehlergrenze (inkl. Genauigkeit)', strong: true },
      { cell: 'C24', label: 'Angepasster extrapolierter Fehler (EE)' },
      { cell: 'C25', label: 'Angepasste Genauigkeit (SE)' },
      { cell: 'C27', label: 'Fehlerbetrag einschließlich TH' },
      { cell: 'C14', label: 'Hochrechnungsbasis ohne technische Hilfe (BV_u)' },
    ],
    gauge: { threshold: 'C29', rate: 'C26', upper: 'C28' },
  },
}
