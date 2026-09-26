/**
 * Paritätsfälle des Datei-Imports (Vue `TableImport` ↔ React `TableImport`).
 * Synthetische Belegwerte, keine Personendaten.
 */
import type { ParityCase } from './cases'

export interface TabularCaseProps {
  mode?: 'values' | 'items'
  locale?: 'de' | 'en'
}

/** Semikolon-getrennte Belegliste mit Kopfzeile und einer unlesbaren Zeile. */
export const TABULAR_CSV = 'Beleg;Betrag;Schicht\nR-1;1.250,50;A\nR-2;980,00;B\nR-3;abc;A\n'

export const tabularCases: ReadonlyArray<ParityCase<TabularCaseProps>> = [
  {
    name: 'Wertspalte ohne Datei',
    props: () => ({}),
    expect: { texts: ['Datei (CSV, TSV oder Text)'], counts: { 'input[type="file"]': 1, select: 0, '[data-testid="import-apply"]': 0 } },
  },
  {
    name: 'Stichprobenposten ohne Datei',
    props: () => ({ mode: 'items' }),
    expect: { texts: ['Datei (CSV, TSV oder Text)'], counts: { 'input[type="file"]': 1 } },
  },
  {
    name: 'englisch',
    props: () => ({ locale: 'en' }),
    expect: { texts: ['File (CSV, TSV or text)'] },
  },
]
