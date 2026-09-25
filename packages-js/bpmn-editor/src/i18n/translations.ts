/**
 * Deutsche Übersetzungstabelle der Oberfläche (englische Vorlage → Deutsch).
 * Begriffe wie im audit_designer: „Bahn“ für Lane, „Teilprozess“ für
 * Sub-Process, „Pool“ für Participant.
 */

const EVENT_KINDS: Record<string, string> = {
  Message: 'Nachricht',
  Timer: 'Zeitgeber',
  Escalation: 'Eskalation',
  Conditional: 'Bedingung',
  Link: 'Link',
  Error: 'Fehler',
  Cancel: 'Abbruch',
  Compensation: 'Kompensation',
  Signal: 'Signal',
  Terminate: 'Terminierung',
}

/** Ereignisvarianten werden aus den Arten zusammengesetzt, damit sie einheitlich heißen. */
function eventTranslations(): Record<string, string> {
  const result: Record<string, string> = {}
  for (const [english, german] of Object.entries(EVENT_KINDS)) {
    result[`${english} start event`] = `Startereignis (${german})`
    result[`${english} start event (non-interrupting)`] = `Startereignis (${german}, nicht unterbrechend)`
    result[`${english} intermediate catch event`] = `Eintretendes Zwischenereignis (${german})`
    result[`${english} intermediate throw event`] = `Auslösendes Zwischenereignis (${german})`
    result[`${english} end event`] = `Endereignis (${german})`
    result[`${english} boundary event`] = `Randereignis (${german})`
    result[`${english} boundary event (non-interrupting)`] = `Randereignis (${german}, nicht unterbrechend)`
    result[english] = german
  }
  return result
}

const UI: Record<string, string> = {
  // Editor
  'BPMN diagram editor': 'BPMN-Diagrammeditor',
  'Invalid BPMN XML': 'Ungültiges BPMN-XML',
  'No diagram loaded': 'Kein Diagramm geladen',
  'Edit label': 'Beschriftung bearbeiten',
  Minimap: 'Übersichtskarte',
  'Open minimap': 'Übersichtskarte öffnen',
  'Close minimap': 'Übersichtskarte schließen',
  'Diagram levels': 'Diagrammebenen',
  'Open sub-process': 'Teilprozess öffnen',
  Process: 'Prozess',
  'Sub-process': 'Teilprozess',

  // Import
  'No diagram interchange (DI) found; elements without position are not displayed':
    'Keine Diagramm-Information (DI) gefunden; Elemente ohne Lage werden nicht angezeigt',
  'Additional diagram {id} is kept but not displayed': 'Weiteres Diagramm {id} bleibt erhalten, wird aber nicht angezeigt',
  'Diagram plane without BPMN element is skipped': 'Diagrammebene ohne BPMN-Element wird übersprungen',
  'Unsupported diagram root {type}': 'Nicht unterstützte Diagrammwurzel {type}',
  'Element {id} ({type}) has no diagram information and is not displayed':
    'Element {id} ({type}) hat keine Diagramm-Information und wird nicht angezeigt',
  'Connection {id} is not displayed: source or target is missing': 'Verbindung {id} wird nicht angezeigt: Quelle oder Ziel fehlt',
  'Boundary event {id} has no displayed host': 'Randereignis {id} hat kein angezeigtes Trägerelement',
  'Element {id} exists more than once': 'Element {id} ist mehrfach vorhanden',

  // Palette und Werkzeuge
  'Activate create/remove space tool': 'Platz schaffen oder entfernen',
  'Activate global connect tool': 'Verbindungswerkzeug',
  'Activate hand tool': 'Hand-Werkzeug',
  'Activate lasso tool': 'Lasso-Werkzeug',
  'Create start event': 'Startereignis anlegen',
  'Create intermediate/boundary event': 'Zwischen-/Randereignis anlegen',
  'Create end event': 'Endereignis anlegen',
  'Create gateway': 'Gateway anlegen',
  'Create task': 'Aufgabe anlegen',
  'Create expanded sub-process': 'Aufgeklappten Teilprozess anlegen',
  'Create data object reference': 'Datenobjekt anlegen',
  'Create data store reference': 'Datenspeicher anlegen',
  'Create pool/participant': 'Pool anlegen',
  'Create group': 'Gruppe anlegen',
  'Create text annotation': 'Textanmerkung anlegen',

  // Kontextpad
  'Append end event': 'Endereignis anhängen',
  'Append gateway': 'Gateway anhängen',
  'Append task': 'Aufgabe anhängen',
  'Append intermediate/boundary event': 'Zwischen-/Randereignis anhängen',
  'Append receive task': 'Empfangsaufgabe anhängen',
  'Append message intermediate catch event': 'Eintretendes Nachrichten-Zwischenereignis anhängen',
  'Append timer intermediate catch event': 'Eintretendes Zeitereignis anhängen',
  'Append conditional intermediate catch event': 'Bedingtes eintretendes Zwischenereignis anhängen',
  'Append signal intermediate catch event': 'Eintretendes Signal-Zwischenereignis anhängen',
  'Append compensation activity': 'Kompensationsaktivität anhängen',
  'Add text annotation': 'Textanmerkung hinzufügen',
  'Add lane above': 'Bahn oberhalb einfügen',
  'Add lane below': 'Bahn unterhalb einfügen',
  'Add lane to the left': 'Bahn links einfügen',
  'Add lane to the right': 'Bahn rechts einfügen',
  'Divide into two lanes': 'In zwei Bahnen teilen',
  'Divide into three lanes': 'In drei Bahnen teilen',
  'Change element': 'Elementtyp ändern',
  'Connect to other element': 'Mit anderem Element verbinden',
  'Connect using association': 'Über Assoziation verbinden',
  'Set color': 'Farbe festlegen',
  Delete: 'Löschen',

  // Ausrichten und Verteilen
  Align: 'Ausrichten',
  'Align elements': 'Elemente ausrichten',
  'Align left': 'Links ausrichten',
  'Align center': 'Zentriert ausrichten',
  'Align right': 'Rechts ausrichten',
  'Align top': 'Oben ausrichten',
  'Align middle': 'Mittig ausrichten',
  'Align bottom': 'Unten ausrichten',
  Distribute: 'Verteilen',
  'Distribute horizontally': 'Waagerecht verteilen',
  'Distribute vertically': 'Senkrecht verteilen',

  // Farben
  Default: 'Standard',
  Blue: 'Blau',
  Green: 'Grün',
  Yellow: 'Gelb',
  Orange: 'Orange',
  Red: 'Rot',
  Purple: 'Violett',
  Grey: 'Grau',

  // Ersetzen: Ereignisse
  'Start events': 'Startereignisse',
  'Intermediate events': 'Zwischenereignisse',
  'End events': 'Endereignisse',
  'Boundary events': 'Randereignisse',
  'Start event': 'Startereignis',
  'Intermediate throw event': 'Auslösendes Zwischenereignis',
  'End event': 'Endereignis',

  // Ersetzen: Gateways, Aktivitäten, Daten, Pools, Flüsse
  'Exclusive gateway': 'Exklusives Gateway',
  'Parallel gateway': 'Paralleles Gateway',
  'Inclusive gateway': 'Inklusives Gateway',
  'Complex gateway': 'Komplexes Gateway',
  'Event-based gateway': 'Ereignisbasiertes Gateway',
  'Event-based gateway (instantiating)': 'Ereignisbasiertes Gateway (instanziierend)',
  'Parallel event-based gateway': 'Paralleles ereignisbasiertes Gateway',
  Task: 'Aufgabe',
  'User task': 'Benutzeraufgabe',
  'Manual task': 'Manuelle Aufgabe',
  'Service task': 'Serviceaufgabe',
  'Script task': 'Skriptaufgabe',
  'Business rule task': 'Geschäftsregelaufgabe',
  'Send task': 'Sendeaufgabe',
  'Receive task': 'Empfangsaufgabe',
  'Call activity': 'Aufrufaktivität',
  'Sub-process (collapsed)': 'Teilprozess (zugeklappt)',
  'Sub-process (expanded)': 'Teilprozess (aufgeklappt)',
  Transaction: 'Transaktion',
  'Transaction (collapsed)': 'Transaktion (zugeklappt)',
  'Event sub-process': 'Ereignis-Teilprozess',
  'Ad-hoc sub-process': 'Ad-hoc-Teilprozess',
  'Ad-hoc sub-process (collapsed)': 'Ad-hoc-Teilprozess (zugeklappt)',
  'Data object reference': 'Datenobjekt',
  'Data store reference': 'Datenspeicher',
  'Data input': 'Dateneingang',
  'Data output': 'Datenausgang',
  'Expanded pool/participant': 'Aufgeklappter Pool',
  'Empty pool/participant': 'Leerer Pool',
  'Sequence flow': 'Sequenzfluss',
  'Default flow': 'Standardfluss',
  'Conditional flow': 'Bedingter Fluss',
  'Message flow': 'Nachrichtenfluss',
  Association: 'Assoziation',
  'Data association': 'Datenassoziation',
  'Text annotation': 'Textanmerkung',
  Group: 'Gruppe',
  Lane: 'Bahn',
  'Pool/participant': 'Pool',
  Collaboration: 'Kollaboration',
  'Intermediate catch event': 'Eintretendes Zwischenereignis',
  'Boundary event': 'Randereignis',
  Gateway: 'Gateway',

  // Marker (Kopfleiste des Ersetzen-Menüs)
  Loop: 'Schleife',
  'Parallel multi-instance': 'Parallele Mehrfachausführung',
  'Sequential multi-instance': 'Sequenzielle Mehrfachausführung',
  Collection: 'Sammlung',
  'Participant multiplicity': 'Mehrfachbeteiligung',
  'Toggle non-interrupting': 'Nicht unterbrechend umschalten',
}

export const translations: Record<string, string> = { ...eventTranslations(), ...UI }
