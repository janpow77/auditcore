/**
 * Catalogue of validation rules: stable ids, severity and messages (de/en).
 *
 * Identical to the rule catalogue of `auditcore_bpmn` (same ids, same
 * texts), so issues from the UI and from the server read alike. A test
 * compares both catalogues when the Python package is present.
 */

export type Severity = 'fehler' | 'warnung' | 'hinweis'
export type RuleGroup = 'struktur' | 'fachlich' | 'pruefbehoerde' | 'funktionstrennung' | 'sammlung'

export interface Rule {
  id: string
  severity: Severity
  group: RuleGroup
  de: string
  en: string
}

export const SEVERITY_LABELS: Record<Severity, { de: string; en: string }> = {
  fehler: { de: 'Fehler', en: 'Error' },
  warnung: { de: 'Warnung', en: 'Warning' },
  hinweis: { de: 'Hinweis', en: 'Note' },
}

type Row = [string, string, string, string, string]

const ROWS: Row[] = [
  ["BPMN-S001", "fehler", "struktur", "Das Wurzelelement ist nicht bpmn:definitions im BPMN-2.0-Namensraum.", "The root element is not bpmn:definitions in the BPMN 2.0 namespace."],
  ["BPMN-S002", "fehler", "struktur", "Das Dokument enthält keinen Prozess.", "The document contains no process."],
  ["BPMN-S003", "fehler", "struktur", "Die Element-ID „{id}“ ist mehrfach vergeben.", "Element ID '{id}' is used more than once."],
  ["BPMN-S010", "fehler", "struktur", "Prozess „{name}“ hat kein Startereignis.", "Process '{name}' has no start event."],
  ["BPMN-S011", "fehler", "struktur", "Prozess „{name}“ hat kein Endereignis.", "Process '{name}' has no end event."],
  ["BPMN-S012", "warnung", "struktur", "„{name}“ ist mit keinem Sequenz- oder Nachrichtenfluss verbunden (verwaist).", "'{name}' is not connected by any sequence or message flow (orphaned)."],
  ["BPMN-S013", "warnung", "struktur", "„{name}“ hat keinen eingehenden Sequenzfluss.", "'{name}' has no incoming sequence flow."],
  ["BPMN-S014", "warnung", "struktur", "„{name}“ hat keinen ausgehenden Sequenzfluss.", "'{name}' has no outgoing sequence flow."],
  ["BPMN-S015", "fehler", "struktur", "Startereignis „{name}“ hat einen eingehenden Sequenzfluss.", "Start event '{name}' has an incoming sequence flow."],
  ["BPMN-S016", "fehler", "struktur", "Endereignis „{name}“ hat einen ausgehenden Sequenzfluss.", "End event '{name}' has an outgoing sequence flow."],
  ["BPMN-S020", "fehler", "struktur", "Sequenzfluss „{id}“ ist nicht verbunden (Quelle oder Ziel fehlt).", "Sequence flow '{id}' is not connected (source or target missing)."],
  ["BPMN-S021", "fehler", "struktur", "Sequenzfluss „{id}“ verweist auf das unbekannte Element „{ref}“.", "Sequence flow '{id}' refers to unknown element '{ref}'."],
  ["BPMN-S022", "fehler", "struktur", "Sequenzfluss „{id}“ überschreitet die Grenze eines Prozesses oder Unterprozesses.", "Sequence flow '{id}' crosses a process or sub-process boundary."],
  ["BPMN-S023", "fehler", "struktur", "Nachrichtenfluss „{id}“ verbindet Elemente desselben Pools.", "Message flow '{id}' connects elements of the same pool."],
  ["BPMN-S024", "fehler", "struktur", "Nachrichtenfluss „{id}“ ist nicht verbunden oder verweist auf ein unbekanntes Element.", "Message flow '{id}' is not connected or refers to an unknown element."],
  ["BPMN-S030", "warnung", "struktur", "Gateway „{name}“ hat bedingte ausgehende Flüsse, aber keinen Default-Fluss.", "Gateway '{name}' has conditional outgoing flows but no default flow."],
  ["BPMN-S031", "fehler", "struktur", "Der Default-Fluss „{flow}“ von „{name}“ ist kein ausgehender Fluss dieses Elements.", "Default flow '{flow}' of '{name}' is not an outgoing flow of this element."],
  ["BPMN-S032", "hinweis", "struktur", "Gateway „{name}“ verzweigt ohne Bedingungen und ohne Default-Fluss.", "Gateway '{name}' splits without conditions and without a default flow."],
  ["BPMN-S033", "hinweis", "struktur", "Gateway „{name}“ hat genau einen Ein- und einen Ausgang und ist entbehrlich.", "Gateway '{name}' has exactly one incoming and one outgoing flow and is redundant."],
  ["BPMN-S034", "fehler", "struktur", "Ereignisbasiertes Gateway „{name}“ führt zu „{ziel}“; zulässig sind nur fangende Zwischenereignisse und Empfangsaufgaben.", "Event-based gateway '{name}' leads to '{ziel}'; only catching intermediate events and receive tasks are allowed."],
  ["BPMN-S035", "fehler", "struktur", "Paralleles Gateway „{name}“ hat bedingte ausgehende Flüsse.", "Parallel gateway '{name}' has conditional outgoing flows."],
  ["BPMN-S040", "fehler", "struktur", "Randereignis „{name}“ hat keinen ausgehenden Sequenzfluss.", "Boundary event '{name}' has no outgoing sequence flow."],
  ["BPMN-S041", "fehler", "struktur", "Randereignis „{name}“ hat einen eingehenden Sequenzfluss.", "Boundary event '{name}' has an incoming sequence flow."],
  ["BPMN-S042", "fehler", "struktur", "Randereignis „{name}“ ist an keine bekannte Aktivität angeheftet.", "Boundary event '{name}' is not attached to a known activity."],
  ["BPMN-S050", "warnung", "struktur", "Aufgabe „{id}“ hat keinen Namen.", "Task '{id}' has no name."],
  ["BPMN-S051", "hinweis", "struktur", "Verzweigendes Gateway „{id}“ hat keine Beschriftung (Frage).", "Splitting gateway '{id}' has no label (question)."],
  ["BPMN-S060", "warnung", "struktur", "Link-Wurfereignis „{name}“ (Link „{link}“) hat kein passendes Fangereignis im Diagramm.", "Link throw event '{name}' (link '{link}') has no matching catch event in the diagram."],
  ["BPMN-S061", "warnung", "struktur", "Aufrufaktivität „{name}“ nennt kein aufgerufenes Element.", "Call activity '{name}' names no called element."],
  ["BPMN-S070", "fehler", "struktur", "Datenassoziation „{id}“ verweist auf das unbekannte Element „{ref}“.", "Data association '{id}' refers to unknown element '{ref}'."],
  ["BPMN-S071", "fehler", "struktur", "Assoziation „{id}“ verweist auf das unbekannte Element „{ref}“.", "Association '{id}' refers to unknown element '{ref}'."],
  ["BPMN-F001", "hinweis", "fachlich", "Aufgabe „{name}“ hat keine Rechtsgrundlage.", "Task '{name}' has no legal basis."],
  ["BPMN-F002", "warnung", "fachlich", "Das Diagramm hat keine Diagramm-Infos (flowaudit:diagrammInfo).", "The diagram has no diagram information (flowaudit:diagrammInfo)."],
  ["BPMN-F003", "warnung", "fachlich", "Die Diagramm-Infos nennen keinen Status.", "The diagram information states no status."],
  ["BPMN-F004", "fehler", "fachlich", "Der Status „{wert}“ ist unbekannt (zulässig: {zulaessig}).", "Status '{wert}' is unknown (allowed: {zulaessig})."],
  ["BPMN-F005", "warnung", "fachlich", "Die Gültigkeit ist am {datum} abgelaufen (Stichtag {stichtag}).", "Validity expired on {datum} (reference date {stichtag})."],
  ["BPMN-F006", "hinweis", "fachlich", "Die Gültigkeit beginnt erst am {datum} (Stichtag {stichtag}).", "Validity only starts on {datum} (reference date {stichtag})."],
  ["BPMN-F007", "fehler", "fachlich", "„gültig ab“ ({ab}) liegt nach „gültig bis“ ({bis}).", "'Valid from' ({ab}) is after 'valid until' ({bis})."],
  ["BPMN-F008", "warnung", "fachlich", "Das Diagramm ist freigegeben, aber Freigabe durch oder am fehlt.", "The diagram is approved, but approver or approval date is missing."],
  ["BPMN-F009", "fehler", "fachlich", "Das Feld „{feld}“ enthält kein gültiges Datum (JJJJ-MM-TT): „{wert}“.", "Field '{feld}' does not contain a valid date (YYYY-MM-DD): '{wert}'."],
  ["BPMN-F010", "warnung", "fachlich", "Die strukturierte Rechtsgrundlage an „{name}“ nennt keine Norm.", "The structured legal basis at '{name}' names no legal act."],
  ["BPMN-F011", "warnung", "fachlich", "Das Kennzeichen „{typ}“ an „{name}“ ist unbekannt.", "Marker '{typ}' at '{name}' is unknown."],
  ["BPMN-F012", "warnung", "fachlich", "„{name}“ trägt das Kennzeichen Rechtsgrundlage, hat aber keine Rechtsgrundlage.", "'{name}' carries the legal-basis marker but has no legal basis."],
  ["BPMN-F013", "warnung", "fachlich", "Die Farbe „{wert}“ in „{feld}“ ist keine #RRGGBB-Angabe.", "Colour '{wert}' in '{feld}' is not a #RRGGBB value."],
  ["BPMN-F014", "warnung", "fachlich", "Der Fonds „{wert}“ ist im Profil „{profil}“ nicht vorgesehen.", "Fund '{wert}' is not provided for in profile '{profil}'."],
  ["BPMN-F015", "warnung", "fachlich", "Die Förderperiode „{wert}“ passt nicht zum Profil „{profil}“ ({periode}).", "Programming period '{wert}' does not match profile '{profil}' ({periode})."],
  ["BPMN-F016", "warnung", "fachlich", "Das Profil „{wert}“ ist unbekannt; geprüft wird mit „{profil}“.", "Profile '{wert}' is unknown; checking with '{profil}'."],
  ["BPMN-F017", "warnung", "fachlich", "Der Wert „{wert}“ im Feld „{feld}“ ist unbekannt (zulässig: {zulaessig}).", "Value '{wert}' in field '{feld}' is unknown (allowed: {zulaessig})."],
  ["BPMN-F018", "hinweis", "fachlich", "Das Ist-Diagramm nennt kein Soll-Diagramm (bezugDiagramm).", "The actual-state diagram names no target diagram (bezugDiagramm)."],
  ["BPMN-F020", "hinweis", "fachlich", "{art} „{name}“ hat keine Akteur-Rolle.", "{art} '{name}' has no actor role."],
  ["BPMN-F021", "warnung", "fachlich", "Die Rolle „{rolle}“ an „{name}“ ist im Profil „{profil}“ unbekannt.", "Role '{rolle}' at '{name}' is unknown in profile '{profil}'."],
  ["BPMN-F022", "hinweis", "fachlich", "Die Rolle „{rolle}“ ({bezeichnung}) an „{name}“ ist für die Förderperiode {periode} nicht vorgesehen.", "Role '{rolle}' ({bezeichnung}) at '{name}' is not provided for in programming period {periode}."],
  ["BPMN-F023", "fehler", "fachlich", "Die Kernanforderung „{ka}“ an „{name}“ ist im Katalog „{profil}“ nicht enthalten (vorhanden: {vorhanden}).", "Key requirement '{ka}' at '{name}' is not in catalogue '{profil}' (available: {vorhanden})."],
  ["BPMN-F024", "fehler", "fachlich", "Das Bewertungskriterium „{bk}“ an „{name}“ passt nicht zur Kernanforderung {ka} (erwartet „{ka}.…“).", "Assessment criterion '{bk}' at '{name}' does not match key requirement {ka} (expected '{ka}.…')."],
  ["BPMN-F025", "warnung", "fachlich", "Das Bewertungskriterium „{bk}“ an „{name}“ ist im Katalog nicht enthalten.", "Assessment criterion '{bk}' at '{name}' is not in the catalogue."],
  ["BPMN-F026", "warnung", "fachlich", "Die Prüfart „{wert}“ an „{name}“ ist unbekannt.", "Audit type '{wert}' at '{name}' is unknown."],
  ["BPMN-F027", "warnung", "fachlich", "Der Verweis an „{name}“ hat die unbekannte Art „{wert}“ oder keinen Schlüssel.", "The reference at '{name}' has unknown type '{wert}' or no key."],
  ["BPMN-P001", "warnung", "pruefbehoerde", "Die Kontrolle „{kontrolle}“ an „{name}“ nennt keinen Nachweis.", "Control '{kontrolle}' at '{name}' names no evidence."],
  ["BPMN-P002", "warnung", "pruefbehoerde", "„{name}“ hat keinen Aufbewahrungsort (flowaudit:nachweis).", "'{name}' has no storage location (flowaudit:nachweis)."],
  ["BPMN-P003", "warnung", "pruefbehoerde", "Die Frist „{frist}“ an „{name}“ hat keine Rechtsgrundlage.", "Deadline '{frist}' at '{name}' has no legal basis."],
  ["BPMN-P004", "hinweis", "pruefbehoerde", "Die Schlüsselkontrolle „{kontrolle}“ an „{name}“ ist noch nicht getestet (kein Prüfschritt).", "Key control '{kontrolle}' at '{name}' has not been tested (no test step)."],
  ["BPMN-P005", "warnung", "pruefbehoerde", "Das Risiko „{risiko}“ an „{name}“ ist keiner Kontrolle zugeordnet.", "Risk '{risiko}' at '{name}' is not linked to any control."],
  ["BPMN-P006", "fehler", "pruefbehoerde", "Das Risiko „{risiko}“ verweist auf die unbekannte Kontrolle „{kontrolle}“.", "Risk '{risiko}' refers to unknown control '{kontrolle}'."],
  ["BPMN-P007", "warnung", "pruefbehoerde", "Der Wert „{wert}“ im Feld „{feld}“ an „{name}“ ist unbekannt (zulässig: {zulaessig}).", "Value '{wert}' in field '{feld}' at '{name}' is unknown (allowed: {zulaessig})."],
  ["BPMN-P008", "fehler", "pruefbehoerde", "Die ID „{id}“ ist für mehrere Kontrollen, Risiken, Prüfschritte oder Feststellungen vergeben.", "ID '{id}' is used for several controls, risks, test steps or findings."],
  ["BPMN-P009", "warnung", "pruefbehoerde", "Die Feststellung an „{name}“ nennt keine Art (formell/finanziell) oder keine Beschreibung.", "The finding at '{name}' states no type (formal/financial) or no description."],
  ["BPMN-P010", "hinweis", "pruefbehoerde", "Prüfschritt „{schritt}“ an „{name}“: nicht erfüllt.", "Test step '{schritt}' at '{name}': not met."],
  ["BPMN-P011", "warnung", "pruefbehoerde", "„{name}“ trägt das Kennzeichen Schlüsselkontrolle, hat aber keine Kontrolle mit schluesselkontrolle=\"true\".", "'{name}' carries the key-control marker but has no control with schluesselkontrolle=\"true\"."],
  ["BPMN-P012", "warnung", "pruefbehoerde", "Der Prüfschritt „{schritt}“ verweist auf die unbekannte Kontrolle „{kontrolle}“.", "Test step '{schritt}' refers to unknown control '{kontrolle}'."],
  ["BPMN-FT-STELLEN", "warnung", "funktionstrennung", "{titel}: „{a}“ und „{b}“ liegen in derselben Stelle „{stelle}“.", "{titel}: '{a}' and '{b}' are in the same body '{stelle}'."],
  ["BPMN-FT-ROLLE", "fehler", "funktionstrennung", "{titel}: „{name}“ liegt bei der Rolle „{rolle}“.", "{titel}: '{name}' is assigned to role '{rolle}'."],
  ["BPMN-FT-VIERAUGEN", "warnung", "funktionstrennung", "{titel}: „{name}“ hat keine zweite Stelle oder Rolle (Nachfolger in anderer Lane oder Kontrolle einer anderen Rolle).", "{titel}: '{name}' has no second body or role (successor in another lane or control by another role)."],
  ["BPMN-K001", "fehler", "sammlung", "Aufrufaktivität „{name}“ in „{diagramm}“ verweist auf „{ziel}“; kein Diagramm der Sammlung enthält diesen Prozess.", "Call activity '{name}' in '{diagramm}' refers to '{ziel}'; no diagram of the collection contains this process."],
  ["BPMN-K002", "warnung", "sammlung", "Link „{link}“ aus „{diagramm}“ hat in der Sammlung kein Fangereignis.", "Link '{link}' from '{diagramm}' has no catch event in the collection."],
  ["BPMN-K003", "warnung", "sammlung", "Die Prozess-ID „{prozess}“ kommt in mehreren Diagrammen vor ({diagramme}); Verweise sind mehrdeutig.", "Process ID '{prozess}' occurs in several diagrams ({diagramme}); references are ambiguous."],
  ["BPMN-K004", "fehler", "sammlung", "Ordner „{ordner}“ ist unbekannt oder bildet einen Zyklus.", "Folder '{ordner}' is unknown or forms a cycle."],
  ["BPMN-K005", "fehler", "sammlung", "Diagramm „{diagramm}“ verweist auf den unbekannten Tag „{tag}“.", "Diagram '{diagramm}' refers to unknown tag '{tag}'."],
  ["BPMN-K006", "fehler", "sammlung", "Die ID „{id}“ ist in der Sammlung mehrfach vergeben.", "ID '{id}' is used more than once in the collection."],
  ["BPMN-K007", "warnung", "sammlung", "Das Ist-Diagramm „{diagramm}“ verweist auf das unbekannte Soll-Diagramm „{bezug}“.", "Actual-state diagram '{diagramm}' refers to unknown target diagram '{bezug}'."],
  ["BPMN-K008", "fehler", "sammlung", "Der freigegebene Stand {version} von „{diagramm}“ wurde verändert (SHA-256 weicht ab).", "Approved version {version} of '{diagramm}' has been modified (SHA-256 differs)."],
]

export const RULES: Record<string, Rule> = Object.fromEntries(
  ROWS.map(([id, severity, group, de, en]) => [id, { id, severity, group, de, en } as Rule]),
)

/** Message of a rule; parameters `name_de`/`name_en` override `name`. */
export function ruleText(rule: Rule, locale: 'de' | 'en', params: Record<string, unknown>): string {
  const template = locale === 'en' ? rule.en : rule.de
  const suffix = locale === 'en' ? '_en' : '_de'
  const values: Record<string, unknown> = { ...params }
  for (const [key, value] of Object.entries(params)) {
    if (key.endsWith(suffix)) values[key.slice(0, -suffix.length)] = value
  }
  return template.replace(/\{(\w+)\}/g, (match, key: string) => (values[key] === undefined ? match : String(values[key])))
}
