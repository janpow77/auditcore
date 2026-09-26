import { defineMessages } from '../i18n'

/** Texte des Datei-Imports (Stichprobe, Benford). */
export const tabularMessages = defineMessages({
  de: {
    file: 'Datei (CSV, TSV oder Text)',
    header: 'Erste Zeile enthält Spaltennamen',
    valueColumn: 'Wertspalte',
    idColumn: 'Kennungsspalte',
    stratumColumn: 'Schichtspalte',
    none: '– keine –',
    decimal: 'Dezimaltrennzeichen',
    decimalComma: 'Komma (1.234,56)',
    decimalDot: 'Punkt (1,234.56)',
    column: 'Spalte',
    apply: 'Übernehmen',
    summary: '{file}: {rows} Zeilen, Trennzeichen „{delimiter}“',
    rejected: '{count} Zeilen nicht lesbar (Zeilen {lines}) – nicht übernommen.',
    tab: 'Tabulator',
  },
  en: {
    file: 'File (CSV, TSV or text)',
    header: 'First row contains column names',
    valueColumn: 'Value column',
    apply: 'Apply',
  },
})

export type TabularMessageKey = keyof typeof tabularMessages.de
