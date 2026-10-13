/**
 * Methodendefinition Blatt 02_Grundgesamtheit. Erzeugt mit `scripts/generate-definition.mjs`
 * und von Hand geprüft: Bezeichnungen (Spalte B) und Fundstellen (Spalte D) wörtlich,
 * Titel und Rechtsgrundlagen aus A5/A6, Abschnitt E ohne die Klammer im Titel.
 * `optional` kennzeichnet freiwillige Angaben und Gruppen (Anzahl und Betrag gehören zusammen).
 */
import type { MethodDefinition } from '../../model/definition'

export const definition: MethodDefinition = {
  sheet: '02_Grundgesamtheit',
  number: '02',
  title: 'Aufbereitung der Grundgesamtheit',
  shortTitle: 'Grundgesamtheit',
  legalBasis: 'Art. 2 Nr. 15 und 16, Art. 3 DelVO (EU) 2023/67; Art. 15 Abs. 5, Art. 36 Abs. 5, Art. 79 Abs. 2, Art. 80 Abs. 3, Art. 98 Abs. 4 und 6 VO (EU) 2021/1060',
  sections: [
    {
      id: 'A', title: 'Abdeckung und Bezugszeitraum',
      fields: [
        { cell: 'C9', alias: 'cci', kind: 'input', type: 'text', format: '@', label: 'CCI-Nummer(n)', hint: 'Art. 3 Abs. 1: Programm oder Programmgruppe.' },
        { cell: 'C10', alias: 'funds', kind: 'input', type: 'text', format: '@', label: 'Fonds', hint: 'Art. 3 Abs. 2: gemeinsame statistische Stichprobe nur für EFRE, ESF+, KF und JTF.' },
        { cell: 'C11', alias: 'programmingPeriod', kind: 'input', type: 'text', format: '@', label: 'Programmplanungszeitraum / -zeiträume', hint: 'Art. 3 Abs. 2 DelVO.' },
        { cell: 'C12', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr / Bezugszeitraum (z. B. 01.07.2021–30.06.2022)' },
        { cell: 'C13', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Zahlungsantrag des Begünstigten, Vorhaben)' },
        { cell: 'C14', alias: 'dataSource', kind: 'input', type: 'text', format: '@', label: 'Datenquelle und Stichtag des Datenauszugs', hint: 'Prüfpfad: Herkunft der Datensätze.' },
      ],
    },
    {
      id: 'B', title: 'Abstimmung mit dem letzten Zahlungsantrag des Geschäftsjahres', reference: 'Art. 3 Abs. 1',
      fields: [
        { cell: 'C15', alias: 'paymentClaimOwnRecords', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Gesamtbetrag des letzten Zahlungsantrags laut Datenbestand der Prüfbehörde' },
        { cell: 'C16', alias: 'paymentClaimSfc', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Gesamtbetrag des letzten Zahlungsantrags laut SFC2021', hint: 'Maßgeblich ist der der Kommission vorgelegte Betrag (Art. 3 Abs. 1).' },
        { cell: 'C17', alias: 'claimDifference', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Differenz SFC2021 abzüglich Datenbestand' },
        { cell: 'C18', alias: 'differenceExplanation', kind: 'input', type: 'text', format: '@', label: 'Erläuterung der Differenz' },
        { cell: 'C19', alias: 'checkClaimReconciliation', kind: 'formula', type: 'check', label: 'Prüfung Abstimmung Zahlungsantrag' },
        { cell: 'C20', alias: 'technicalAssistanceFlatRate', kind: 'input', optional: true, type: 'amount', format: '#,##0.00" €"', label: 'Pauschalfinanzierung technische Hilfe (Art. 36 Abs. 5 VO (EU) 2021/1060)', hint: 'Nicht auf Ebene von Datensätzen; nicht Teil der angepassten Grundgesamtheit (Art. 3 Abs. 6 UAbs. 1 Buchst. a), Fehlerquote gilt nach Art. 8 Abs. 5 mit.' },
        { cell: 'C21', alias: 'flatRateIncluded', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'TH-Pauschale im Gesamtbetrag laut SFC2021 enthalten (Ja/Nein)', hint: 'In SFC2021 wird die Pauschale regelmäßig auf die förderfähigen Ausgaben (Spalte A) aufgeschlagen und ist dann nicht enthalten.' },
        { cell: 'C22', alias: 'amountInRecords', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Auf Datensätze entfallender Betrag (SFC2021, ggf. abzüglich enthaltener TH-Pauschale)' },
      ],
    },
    {
      id: 'C', title: 'Datensätze', reference: 'Art. 2 Nr. 15 und 16; Art. 3 Abs. 4',
      fields: [
        { cell: 'C23', alias: 'recordCount', kind: 'input', type: 'integer', format: '#,##0', label: 'Anzahl Datensätze insgesamt' },
        { cell: 'C24', alias: 'positiveRecordCount', kind: 'input', type: 'integer', format: '#,##0', label: 'Anzahl Datensätze mit positivem Wert (> 0)' },
        { cell: 'C25', alias: 'positiveRecordSum', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Summe der Datensätze mit positivem Wert' },
        { cell: 'C26', alias: 'negativeRecordCount', kind: 'input', optional: 'negativeRecords', type: 'integer', format: '#,##0', label: 'Anzahl Datensätze mit negativem Wert oder Wert 0 (≤ 0)' },
        { cell: 'C27', alias: 'negativeRecordSum', kind: 'input', optional: 'negativeRecords', type: 'amount', format: '#,##0.00" €"', label: 'Summe der Datensätze mit negativem Wert oder Wert 0', hint: 'Negative Grundgesamtheit, keine Fehlerquote (ErwG 5).' },
        { cell: 'C28', alias: 'checkRecordCount', kind: 'formula', type: 'check', label: 'Prüfung Anzahl (positiv + negativ = insgesamt)' },
        { cell: 'C29', alias: 'checkNegativeSign', kind: 'formula', type: 'check', label: 'Prüfung Vorzeichen der negativen Datensätze' },
        { cell: 'C30', alias: 'recordDifference', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Differenz Datensätze (positiv + negativ) zum Betrag laut SFC2021 ohne TH' },
        { cell: 'C31', alias: 'checkRecordReconciliation', kind: 'formula', type: 'check', label: 'Prüfung Abstimmung Datensätze mit SFC2021' },
      ],
    },
    {
      id: 'D', title: 'Herleitung der zu prüfenden Grundgesamtheit', reference: 'Art. 3 Abs. 3–5',
      fields: [
        { cell: 'C32', alias: 'excludedRecordCount', kind: 'input', optional: 'excludedRecords', type: 'integer', format: '#,##0', label: 'Anzahl positiver Datensätze spezifischer Ziele mit nicht erfüllten grundlegenden Voraussetzungen' },
        { cell: 'C33', alias: 'excludedRecordSum', kind: 'input', optional: 'excludedRecords', type: 'amount', format: '#,##0.00" €"', label: 'abzüglich: deren Betrag', hint: 'Art. 3 Abs. 3 DelVO i. V. m. Art. 15 Abs. 5 VO (EU) 2021/1060; ausgenommen Vorhaben, die zur Erfüllung beitragen (ErwG 4); Ausschluss bis zum Geschäftsjahr der Aufnahme.' },
        { cell: 'C34', alias: 'resubmittedRecordCount', kind: 'input', optional: 'resubmittedRecords', type: 'integer', format: '#,##0', label: 'Anzahl wieder aufgenommener Datensätze nach Abschluss der Bewertung (Art. 98 Abs. 6 VO (EU) 2021/1060)' },
        { cell: 'C35', alias: 'resubmittedRecordSum', kind: 'input', optional: 'resubmittedRecords', type: 'amount', format: '#,##0.00" €"', label: 'Betrag der nach Bestätigung der Recht- und Ordnungsmäßigkeit wieder aufgenommenen Ausgaben', hint: 'Die Wiederaufnahme erfolgt über einen Zahlungsantrag des laufenden Geschäftsjahres; diese Ausgaben gehören zur Grundgesamtheit (Art. 3 Abs. 1).' },
        { cell: 'C36', alias: 'resubmittedIncluded', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Ja', label: 'Wieder aufgenommene Ausgaben bereits in den Datensätzen enthalten (Ja/Nein)', hint: '„Ja“: nur nachrichtlich, keine Doppelerfassung; „Nein“: Betrag und Anzahl werden hinzugerechnet.' },
        { cell: 'C37', alias: 'bookValueBeforeArticle80', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert vor Anwendung des Art. 80 (positive Grundgesamtheit ohne TH-Pauschale) (BV)' },
        { cell: 'C38', alias: 'unitsBeforeArticle80', kind: 'result', type: 'integer', format: '#,##0', label: 'Anzahl Stichprobeneinheiten vor Anwendung des Art. 80 (N)' },
        { cell: 'C39', alias: 'populationToAudit', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Zu prüfende Grundgesamtheit (Art. 3 Abs. 5) einschließlich TH-Pauschale (BV)', hint: 'Bezugsgröße der Gesamtfehlerquote (Art. 3 Abs. 5; Art. 8 Abs. 1 und 5).' },
      ],
    },
    {
      id: 'E', title: 'Vorkehrungen für die Einzige Prüfung', reference: 'Art. 80 Abs. 3 VO (EU) 2021/1060; Art. 3 Abs. 6 UAbs. 1 Buchst. b DelVO',
      fields: [
        { cell: 'C40', alias: 'article80Threshold', kind: 'input', type: 'amount', format: '#,##0.00" €"', default: 400000, label: 'Schwellenwert der förderfähigen Gesamtkosten nach Art. 80 Abs. 3', hint: 'EFRE und KF 400.000 €, ESF+ 350.000 €, EMFAF, AMIF, ISF und BMVI 200.000 €.' },
        { cell: 'C41', alias: 'auditedBelowThresholdOperations', kind: 'input', optional: 'auditedBelowThreshold', type: 'integer', format: '#,##0', label: 'Vorhaben unterhalb des Schwellenwerts, die bereits geprüft wurden: Anzahl Vorhaben', hint: 'Höchstens eine Prüfung vor Vorlage der Rechnungslegung mit den abschließenden Ausgaben des abgeschlossenen Vorhabens.' },
        { cell: 'C42', alias: 'auditedBelowThresholdUnits', kind: 'input', optional: 'auditedBelowThreshold', type: 'integer', format: '#,##0', label: '… davon betroffene Stichprobeneinheiten', hint: 'Ist die Stichprobeneinheit der Zahlungsantrag des Begünstigten, weicht diese Zahl von der Zahl der Vorhaben ab.' },
        { cell: 'C43', alias: 'auditedBelowThresholdBookValue', kind: 'input', optional: 'auditedBelowThreshold', type: 'amount', format: '#,##0.00" €"', label: '… Buchwert der betroffenen Stichprobeneinheiten' },
        { cell: 'C44', alias: 'auditedOtherOperations', kind: 'input', optional: 'auditedOther', type: 'integer', format: '#,##0', label: 'Sonstige Vorhaben, die im Geschäftsjahr bereits geprüft wurden: Anzahl Vorhaben', hint: 'Höchstens eine Prüfung je Geschäftsjahr (Art. 80 Abs. 3 UAbs. 1 Satz 2).' },
        { cell: 'C45', alias: 'auditedOtherUnits', kind: 'input', optional: 'auditedOther', type: 'integer', format: '#,##0', label: '… davon betroffene Stichprobeneinheiten' },
        { cell: 'C46', alias: 'auditedOtherBookValue', kind: 'input', optional: 'auditedOther', type: 'amount', format: '#,##0.00" €"', label: '… Buchwert der betroffenen Stichprobeneinheiten' },
        { cell: 'C47', alias: 'unauditableUnits', kind: 'formula', type: 'integer', format: '#,##0', label: 'Summe der nach Art. 80 Abs. 3 nicht prüfbaren Stichprobeneinheiten (Anzahl)' },
        { cell: 'C48', alias: 'unauditableBookValue', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Summe der nach Art. 80 Abs. 3 nicht prüfbaren Stichprobeneinheiten (Buchwert)' },
        { cell: 'C49', alias: 'article80Treatment', kind: 'input', type: 'choice', format: '@', list: 'article80', default: 'keine betroffenen Einheiten', label: 'Behandlung der nach Art. 80 Abs. 3 nicht prüfbaren Einheiten (Ausschluss / Ersetzung)', hint: 'Pflichtgemäßes Ermessen (ErwG 7); gilt auch, wenn ausnahmsweise keine Belege vorliegen (Art. 3 Abs. 6 UAbs. 3). Hochrechnung nach Anh. III (Blatt 18).' },
        { cell: 'C50', alias: 'checkTreatment', kind: 'formula', type: 'check', label: 'Prüfung Behandlung' },
      ],
    },
    {
      id: 'F', title: 'Angepasste Grundgesamtheit für die Stichprobenauswahl', reference: 'Art. 3 Abs. 6',
      fields: [
        { cell: 'C51', alias: 'adjustedBookValue', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert der angepassten Grundgesamtheit (BV)' },
        { cell: 'C52', alias: 'adjustedUnits', kind: 'result', type: 'integer', format: '#,##0', label: 'Anzahl Einheiten der angepassten Grundgesamtheit (N)' },
        { cell: 'C53', alias: 'checkNonStatistical', kind: 'formula', type: 'check', label: 'Zulässigkeit eines nichtstatistischen Verfahrens' },
        { cell: 'C54', alias: 'nonStatisticalMinimum', kind: 'formula', type: 'integer', format: '#,##0', label: 'Mindestumfang bei nichtstatistischem Verfahren (10 % der Einheiten)', hint: 'Art. 6 Abs. 2 DelVO.' },
      ],
    },
    {
      id: 'G', title: 'Negative Grundgesamtheit', reference: 'Art. 2 Nr. 15; ErwG 5',
      fields: [
        { cell: 'C55', alias: 'negativeUnits', kind: 'formula', type: 'integer', format: '#,##0', label: 'Anzahl Einheiten der negativen Grundgesamtheit' },
        { cell: 'C56', alias: 'negativeBookValue', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert der negativen Grundgesamtheit' },
        { cell: 'C57', alias: 'negativeTreatment', kind: 'input', type: 'choice', format: '@', list: 'negativePopulation', label: 'Behandlung der negativen Grundgesamtheit', hint: 'Einbeziehung in die Prüfung der Rechnungslegung oder gesondertes Verfahren.' },
      ],
    },
  ],
  summary: { primary: { cell: 'C51', label: 'Buchwert der angepassten Grundgesamtheit (BV)', unit: '' }, rows: [{ cell: 'C52', label: 'Einheiten der angepassten Grundgesamtheit (N)', strong: true }, { cell: 'C39', label: 'Zu prüfende Grundgesamtheit einschl. TH-Pauschale' }, { cell: 'C37', label: 'Buchwert vor Anwendung des Art. 80' }, { cell: 'C38', label: 'Einheiten vor Anwendung des Art. 80' }, { cell: 'C48', label: 'Nicht prüfbar nach Art. 80 Abs. 3 (Buchwert)' }, { cell: 'C54', label: 'Mindestumfang nichtstatistisch (10 %)' }] },
}
