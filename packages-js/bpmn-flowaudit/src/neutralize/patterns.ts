/**
 * Patterns removed on neutralisation (same list as `auditcore_bpmn`).
 */

export type ReplacementKind =
  | 'anzeigename'
  | 'email'
  | 'iban'
  | 'kennnummer'
  | 'betrag'
  | 'unternehmen'
  | 'person'
  | 'feststellungsbezug'
  | 'entfernt'
  | 'befundfarbe'

export interface TextPattern {
  kind: ReplacementKind
  pattern: RegExp
  replacement: string
}

const W = String.raw`[\p{L}\p{N}_]`

export const TEXT_PATTERNS: TextPattern[] = [
  { kind: 'email', pattern: new RegExp(String.raw`[\p{L}\p{N}_.+-]+@[\p{L}\p{N}_-]+(?:\.[\p{L}\p{N}_-]+)+`, 'gu'), replacement: '[E-Mail entfernt]' },
  { kind: 'iban', pattern: /\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){3,7}(?: ?[A-Z0-9]{1,3})?\b/gu, replacement: '[IBAN entfernt]' },
  {
    kind: 'kennnummer',
    pattern:
      /\b(?:SAP|MaStR|Az\.|Aktenzeichen|Förderkennzeichen|FKZ|Projektnummer|Vorhabensnummer|Vorhabennummer)(?:-Nr\.|-Nummer| Nr\.| Nummer)?[\s.:]*[A-Z0-9][A-Z0-9./-]{3,}/gu,
    replacement: '[Kennnummer entfernt]',
  },
  { kind: 'kennnummer', pattern: /\b(?:SEE|SME|ABR|SNB|EEG)\d{9,}\b/gu, replacement: '[Kennnummer entfernt]' },
  {
    kind: 'betrag',
    pattern:
      /(?:(?:€|EUR)\s?\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?(?:\s?(?:Mio\.|Mrd\.|Tsd\.))?)|(?:\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?|\d+(?:,\d{1,2})?)\s?(?:Mio\.\s?|Mrd\.\s?|Tsd\.\s?)?(?:€|EUR\b|Euro\b)/gu,
    replacement: '[Betrag entfernt]',
  },
  {
    kind: 'unternehmen',
    pattern: new RegExp(
      String.raw`(?:[A-ZÄÖÜ](?:${W}|[&.'-])*\s){0,5}[A-ZÄÖÜ](?:${W}|[&.'-])*\s(?:GmbH & Co\. KG|gGmbH|GmbH|mbH|AG|KG|OHG|e\.\s?V\.|eG|GbR|SE|UG(?: \(haftungsbeschränkt\))?|Ltd\.?)(?=[\s,.;:)\]]|$)`,
      'gu',
    ),
    replacement: '[Unternehmen]',
  },
  {
    kind: 'person',
    pattern: /\b(?:Herr|Frau|Hr\.|Fr\.|Dr\.|Prof\.)\s+(?:Dr\.\s+)?[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?/gu,
    replacement: '[Person]',
  },
  {
    kind: 'feststellungsbezug',
    pattern: /(?:Feststellung(?:en)?|Themenvermerk(?:e)?)\s+T\d+(?:\s+F\d+)?(?:(?:\s*,\s*|\s+und\s+)(?:T\d+\s+)?F?\d+)*/gu,
    replacement: '',
  },
  { kind: 'feststellungsbezug', pattern: /\s?\((?:F\d+(?:,\s*)?)+\)/gu, replacement: '' },
]

/** Markers that express a finding. */
export const FINDING_MARKERS = new Set(['feststellung', 'feststellung_formell', 'feststellung_finanziell', 'offener_nachweis', 'ohne_befund', 'soll_ohne_regelung'])
/** Fill/stroke values of finding colours. */
export const FINDING_COLORS = new Set(['#fce8e6', '#b3261e', '#ffcdd2', '#b71c1c', '#ffe0e0', '#cc0000'])
/** Sources that are internal working material. */
export const INTERNAL_SOURCES = new Set(['interview', 'arbeitspapier', 'durchlauftest'])
/** Elements removed completely. */
export const REMOVED_ELEMENTS = new Set(['interneNotiz', 'notiz', 'pruefschritt', 'feststellung'])
/** Person fields at diagram info. */
export const PERSON_ATTRIBUTES = ['autor', 'freigegebenDurch']
/** flowaudit attributes that are codes, never cleaned. */
export const CODE_ATTRIBUTES = new Set(['id', 'typ', 'art', 'ka', 'bk', 'rolle', 'status', 'kontrollen', 'kontrolle', 'schemaVersion', 'profil'])
