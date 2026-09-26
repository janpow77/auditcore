import { defineMessages } from '../i18n'

/** Texte des Tabellenexports (Berichtsexport nach Excel). */
export const reportingMessages = defineMessages({
  de: {
    title: 'Tabellenexport (Excel)',
    loading: 'Formatprofile werden geladen …',
    noPort: 'Kein Port übergeben: Vorschau und Export sind nicht verfügbar.',
    failed: 'Anfrage abgelehnt: {message}',
    data: 'Daten',
    tablesSummary: '{tables} Tabelle(n), {rows} Zeilen',
    noTables: 'Keine Tabellen übergeben. Die Anwendung setzt sie als Eigenschaft „tables“.',
    profile: 'Formatprofil',
    choose: 'Bitte wählen',
    profileSource: 'Herkunft des Profils',
    profileVersion: 'Version {version}, Status {status}',
    filename: 'Dateiname',
    preview: 'Vorschau',
    export: 'Als Excel exportieren',
    errornoTables: 'Keine Tabellen vorhanden.',
    errorprofile: 'Formatprofil wählen.',
    excelMissing: 'XLSX-Export auf dem Server nicht verfügbar (Extra „excel“ fehlt). Die Vorschau zeigt nur die Formate.',
    previewStale: 'Eingaben geändert – Vorschau neu anfordern.',
    workbook: 'Probelauf: {filename}, {size}',
    sheetHeading: 'Blatt „{name}“ – {rows} Zeilen',
    columns: 'Spaltenformate',
    colName: 'Spalte',
    colType: 'Typ',
    colFormat: 'Excel-Format',
    colSource: 'Herkunft',
    sourceprofile: 'Profil',
    sourceoverride: 'ausdrücklich',
    sample: 'Erste Zeilen',
    sampleMore: 'Vorschau zeigt {shown} von {rows} Zeilen.',
    exported: 'Exportiert: {filename}',
    notice: 'Texte werden als Text gespeichert, auch wenn sie mit „=“ beginnen; es entstehen keine Formeln, Makros oder Verknüpfungen.',
  },
  en: {
    title: 'Table export (Excel)',
    profile: 'Format profile',
    preview: 'Preview',
    export: 'Export as Excel',
    filename: 'File name',
  },
})

export type ReportingMessageKey = keyof typeof reportingMessages.de
