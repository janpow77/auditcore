/**
 * Declarative description of the FlowAudit schema 1.1.
 *
 * One table drives three things: the moddle descriptor (`descriptor.ts`),
 * reading/writing extensions on business objects (`model/extensions.ts`) and
 * the JSON exchanged with `auditcore_bpmn` over REST.
 *
 * Every field has two names:
 * - `key` – property name of the TypeScript objects (English, camelCase; the
 *   JSON of `auditcore_bpmn` uses the same names in snake_case),
 * - `xml` – attribute or child element name in the XML (German, schema 1.1).
 *
 * Field kinds:
 * - `attr`     – unprefixed attribute (string, or `bool`)
 * - `list`     – attribute with space separated values
 * - `body`     – text content (1.0 alternative: attribute `value`)
 * - `text`     – one child element with text content
 * - `texts`    – several child elements with text content
 * - `elements` – several structured child elements
 */

export type FieldKind = 'attr' | 'list' | 'body' | 'text' | 'texts' | 'elements'

export interface FieldSpec {
  key: string
  xml: string
  kind: FieldKind
  /** `bool` for boolean attributes, the element type name for `elements`. */
  type?: string
}

export interface TypeSpec {
  /** Local XML name (lowerCamelCase), e.g. `rechtsgrundlage`. */
  xml: string
  /** moddle type name, e.g. `Rechtsgrundlage`. */
  moddle: string
  fields: FieldSpec[]
  /** Legacy form that is read but never written. */
  readOnly?: boolean
}

function attr(key: string, xml: string): FieldSpec {
  return { key, xml, kind: 'attr' }
}
function flag(key: string, xml: string): FieldSpec {
  return { key, xml, kind: 'attr', type: 'bool' }
}
function body(): FieldSpec {
  return { key: 'text', xml: '', kind: 'body' }
}
function child(key: string, xml: string): FieldSpec {
  return { key, xml, kind: 'text' }
}
function children(key: string, xml: string): FieldSpec {
  return { key, xml, kind: 'texts' }
}
function elements(key: string, type: string): FieldSpec {
  return { key, xml: type, kind: 'elements', type }
}

const confidential = flag('confidential', 'vertraulich')

export const TYPES: Record<string, TypeSpec> = {
  rechtsgrundlage: {
    xml: 'rechtsgrundlage',
    moddle: 'Rechtsgrundlage',
    fields: [
      body(),
      attr('id', 'id'),
      attr('act', 'norm'),
      attr('article', 'artikel'),
      attr('section', 'paragraph'),
      attr('annex', 'anhang'),
      attr('paragraph', 'absatz'),
      attr('subparagraph', 'unterabsatz'),
      attr('sentence', 'satz'),
      attr('point', 'buchstabe'),
      attr('number', 'nummer'),
      attr('version', 'fassung'),
      attr('eli', 'eli'),
      attr('celex', 'celex'),
      attr('url', 'url'),
      attr('shortTitle', 'kurzbezeichnung'),
      attr('note', 'anmerkung'),
      confidential,
    ],
  },
  interneNotiz: { xml: 'interneNotiz', moddle: 'InterneNotiz', fields: [body()] },
  notiz: { xml: 'notiz', moddle: 'Notiz', readOnly: true, fields: [body()] },
  kennzeichen: {
    xml: 'kennzeichen',
    moddle: 'Kennzeichen',
    fields: [attr('type', 'typ'), attr('text', 'text'), confidential],
  },
  pruefbezug: {
    xml: 'pruefbezug',
    moddle: 'Pruefbezug',
    fields: [attr('keyRequirement', 'ka'), attr('assessmentCriterion', 'bk'), attr('auditType', 'art'), attr('note', 'anmerkung'), confidential],
  },
  akteur: { xml: 'akteur', moddle: 'Akteur', fields: [attr('role', 'rolle'), attr('displayName', 'anzeigename')] },
  esiAnforderungen: {
    xml: 'esiAnforderungen',
    moddle: 'EsiAnforderungen',
    fields: [attr('profile', 'profil'), elements('requirements', 'esiAnforderung')],
  },
  esiAnforderung: {
    xml: 'esiAnforderung',
    moddle: 'EsiAnforderung',
    fields: [attr('code', 'code'), children('criteria', 'kriterium')],
  },
  kontrolle: {
    xml: 'kontrolle',
    moddle: 'Kontrolle',
    fields: [
      attr('id', 'id'),
      attr('label', 'bezeichnung'),
      flag('keyControl', 'schluesselkontrolle'),
      attr('controlType', 'art'),
      attr('execution', 'durchfuehrung'),
      attr('frequency', 'haeufigkeit'),
      attr('evidence', 'nachweis'),
      attr('responsible', 'verantwortlich'),
      child('description', 'beschreibung'),
      confidential,
    ],
  },
  risiko: {
    xml: 'risiko',
    moddle: 'Risiko',
    fields: [
      attr('id', 'id'),
      attr('label', 'bezeichnung'),
      attr('category', 'kategorie'),
      attr('inherent', 'inhaerent'),
      attr('controlRisk', 'kontrollrisiko'),
      attr('residual', 'restrisiko'),
      { key: 'controls', xml: 'kontrollen', kind: 'list' },
      child('description', 'beschreibung'),
      confidential,
    ],
  },
  nachweis: {
    xml: 'nachweis',
    moddle: 'Nachweis',
    fields: [
      attr('documentType', 'dokumentart'),
      attr('storageLocation', 'aufbewahrungsort'),
      attr('itSystem', 'itSystem'),
      attr('retentionPeriod', 'aufbewahrungsfrist'),
      attr('note', 'anmerkung'),
      confidential,
    ],
  },
  pruefschritt: {
    xml: 'pruefschritt',
    moddle: 'Pruefschritt',
    fields: [
      attr('id', 'id'),
      attr('case', 'fall'),
      attr('document', 'beleg'),
      attr('result', 'ergebnis'),
      attr('date', 'datum'),
      attr('tester', 'pruefer'),
      attr('control', 'kontrolle'),
      attr('sampleSize', 'stichprobe'),
      attr('population', 'grundgesamtheit'),
      child('remark', 'bemerkung'),
      confidential,
    ],
  },
  feststellung: {
    xml: 'feststellung',
    moddle: 'Feststellung',
    fields: [
      attr('id', 'id'),
      attr('reference', 'kennung'),
      attr('findingType', 'art'),
      attr('severity', 'einstufung'),
      attr('keyRequirement', 'ka'),
      attr('assessmentCriterion', 'bk'),
      attr('deadline', 'frist'),
      attr('status', 'status'),
      child('description', 'beschreibung'),
      child('recommendation', 'empfehlung'),
      confidential,
    ],
  },
  quelle: {
    xml: 'quelle',
    moddle: 'Quelle',
    fields: [attr('sourceType', 'art'), attr('location', 'fundstelle'), attr('date', 'datum'), attr('reference', 'referenz'), body(), confidential],
  },
  verweis: {
    xml: 'verweis',
    moddle: 'Verweis',
    fields: [attr('kind', 'art'), attr('key', 'schluessel'), attr('document', 'dokument'), confidential],
  },
  frist: {
    xml: 'frist',
    moddle: 'Frist',
    fields: [
      attr('value', 'wert'),
      attr('unit', 'einheit'),
      attr('basis', 'bezug'),
      attr('note', 'anmerkung'),
      elements('legalBases', 'rechtsgrundlage'),
    ],
  },
  diagrammInfo: {
    xml: 'diagrammInfo',
    moddle: 'DiagrammInfo',
    fields: [
      attr('schemaVersion', 'schemaVersion'),
      attr('profile', 'profil'),
      attr('title', 'titel'),
      attr('subtitle', 'untertitel'),
      attr('processOwner', 'prozessverantwortlich'),
      attr('processType', 'prozesstyp'),
      attr('version', 'version'),
      attr('status', 'status'),
      attr('validFrom', 'gueltigAb'),
      attr('validUntil', 'gueltigBis'),
      attr('author', 'autor'),
      attr('approvedBy', 'freigegebenDurch'),
      attr('approvedOn', 'freigegebenAm'),
      attr('headerColor', 'kopfzeilenfarbe'),
      attr('headerTextColor', 'kopfzeilenTextfarbe'),
      attr('programmingPeriod', 'foerderperiode'),
      attr('programme', 'programm'),
      attr('cci', 'cci'),
      attr('confidentiality', 'vertraulichkeit'),
      attr('variant', 'variante'),
      attr('referenceDiagram', 'bezugDiagramm'),
      attr('systemCutoffDate', 'vksStichtag'),
      child('description', 'beschreibung'),
      children('keywords', 'schlagwort'),
      children('funds', 'fonds'),
      elements('legalBases', 'rechtsgrundlage'),
      elements('auditReferences', 'pruefbezug'),
      elements('risks', 'risiko'),
      elements('findings', 'feststellung'),
      elements('sources', 'quelle'),
      elements('crossReferences', 'verweis'),
    ],
  },
}

/** Child elements with plain text content; each needs its own moddle type. */
export const TEXT_TYPES: Record<string, string> = {
  beschreibung: 'Beschreibung',
  empfehlung: 'Empfehlung',
  bemerkung: 'Bemerkung',
  schlagwort: 'Schlagwort',
  fonds: 'Fonds',
  kriterium: 'Kriterium',
}

/**
 * Order of FlowAudit children inside `extensionElements` (same as
 * `_REIHENFOLGE` in `auditcore_bpmn.flowaudit`), so both sides write alike.
 */
export const WRITE_ORDER = [
  'diagrammInfo',
  'akteur',
  'rechtsgrundlage',
  'interneNotiz',
  'kennzeichen',
  'pruefbezug',
  'kontrolle',
  'risiko',
  'nachweis',
  'frist',
  'verweis',
  'pruefschritt',
  'feststellung',
  'quelle',
  'esiAnforderungen',
] as const

export function typeByModdleName(moddleType: string): TypeSpec | undefined {
  const local = moddleType.startsWith('flowaudit:') ? moddleType.slice('flowaudit:'.length) : moddleType
  return Object.values(TYPES).find((spec) => spec.moddle === local)
}
