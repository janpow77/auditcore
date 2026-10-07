/**
 * Example property catalogue (`profile.properties`) for the demo: the
 * audit attributes of the systems audits (`pb_*`, stored as
 * `camunda:property`). Value lists as in the audit authority's catalogue.
 */

import type { PropertyCatalogue } from '@auditcore/bpmn-flowaudit'

const TESTS = ['Durchlauftest', 'Kontrolltest']

export const DEMO_PROPERTIES: PropertyCatalogue = {
  title: { de: 'Prüfungsmerkmale', en: 'Audit attributes' },
  entries: [
    {
      name: 'pb_art',
      label: { de: 'Art der Prüfungshandlung', en: 'Type of audit procedure' },
      kind: 'choice',
      values: ['Planung', 'Kommunikation', 'Dokumentenanalyse', 'Interview', 'Durchlauftest', 'Kontrolltest', 'Bewertung', 'Bericht', 'Qualitätssicherung', 'Follow-up'],
    },
    {
      name: 'pb_ka',
      label: { de: 'Kernanforderung', en: 'Key requirement' },
      kind: 'multi_choice',
      values: Array.from({ length: 10 }, (_, i) => ({ value: String(i + 1), label: `KA ${i + 1}` })),
    },
    {
      name: 'pb_coso',
      label: { de: 'COSO-Komponente', en: 'COSO component' },
      kind: 'multi_choice',
      values: ['Kontrollumfeld', 'Risikobeurteilung', 'Kontrollaktivitäten', 'Information und Kommunikation', 'Überwachung'],
      depends_on: { property: 'pb_art', values: TESTS },
    },
    { name: 'pb_ziel', label: { de: 'Ziel', en: 'Objective' }, kind: 'multi_choice', values: ['Programmumsetzung', 'Berichterstattung', 'Ordnungsmäßigkeit'] },
    { name: 'pb_stelle', label: { de: 'Geprüfte Stelle', en: 'Audited body' }, kind: 'multi_choice', values: ['VB', 'ZGS', 'RFS'] },
    { name: 'pb_rechtsgrundlage', label: { de: 'Rechtsgrundlage', en: 'Legal basis' }, kind: 'text' },
    { name: 'pb_offen', label: { de: 'Offener Punkt', en: 'Open point' }, kind: 'yes_no', values: ['ja'], help: { de: 'Wert unsicher, im Abschlussbericht aufführen.' } },
    { name: 'pb_gj', label: { de: 'Geschäftsjahr der Prüfung', en: 'Audit year' }, kind: 'text', applies_to: ['event'] },
  ],
}
