/** Beispieldaten der Kanban-Demo (fiktive Personen und Vorhaben). */
import { findTemplate, SCHEMA_VERSION, spreadRanks, type Board, type Card, type Column, type UserRef } from '@auditcore/kanban-core'

export const DEMO_USERS: readonly UserRef[] = [
  { id: 'anna', name: 'Anna Becker', email: 'anna.becker@example.invalid' },
  { id: 'markus', name: 'Markus Weber', email: 'markus.weber@example.invalid' },
  { id: 'lena', name: 'Lena Schmidt', email: 'lena.schmidt@example.invalid' },
  { id: 'tobias', name: 'Tobias Keller', email: 'tobias.keller@example.invalid' },
]

type Seed = Partial<Card> & { title: string }

function day(offset: number): string {
  const date = new Date()
  date.setDate(date.getDate() + offset)
  return date.toISOString().slice(0, 10)
}

function cards(columnId: string, seeds: readonly Seed[]): Card[] {
  const ranks = spreadRanks(seeds.length)
  return seeds.map((seed, index) => ({
    id: `${columnId}-${index + 1}`, column_id: columnId, rank: ranks[index] ?? 'V', description: '', priority: 'mittel', tags: [], assignees: [],
    due: null, color: null, image: null, badge: null, checklist: [], links: [], attachments: [], created_at: new Date(Date.now() - (index + 1) * 36e5 * 30).toISOString(),
    updated_at: new Date().toISOString(), extra: {}, ...seed,
  }))
}

function board(id: string, title: string, icon: string, columns: Column[], content: Card[], extra: Partial<Board> = {}): Board {
  return {
    schema_version: SCHEMA_VERSION, id, title, icon, owner_id: 'anna', version: 1, pinned: false, archived: false,
    created_at: new Date().toISOString(), updated_at: new Date().toISOString(), columns, cards: content, labels: [],
    shares: [{ user_id: 'markus', permission: 'edit', shared_by: 'anna', created_at: null }, { user_id: 'lena', permission: 'read', shared_by: 'anna', created_at: null }],
    transitions: { mode: 'free', allowed: [], locked_columns: [], fixed_order_columns: [] }, wip_mode: 'block', extra: {}, ...extra,
  }
}

export function demoBoards(): Board[] {
  const audit = findTemplate('vorhabenpruefung')?.columns ?? []
  const pruefung = board('vp-2026', 'Vorhabenprüfung 2026', '🔍', audit.map((column) => (column.id === 'pruefung' ? { ...column, wip_limit: 3 } : column)), [
    ...cards('auswahl', [
      { title: 'Stichprobe Q3 ziehen', badge: 'VP-21', priority: 'hoch', due: day(2), tags: ['Stichprobe', 'EFRE'], assignees: ['anna'] },
      { title: 'Belegliste Breitbandausbau anfordern', badge: 'VP-22', description: 'Gesamtbelegliste mit Zahlungsnachweisen beim Begünstigten anfordern.', due: day(9) },
    ]),
    ...cards('pruefung', [
      { title: 'Vergabeakte Innovationslabor sichten', badge: 'VP-19', priority: 'hoch', due: day(-1), tags: ['Vergabe'], assignees: ['markus'], checklist: [{ text: 'Bekanntmachung', done: true }, { text: 'Wertung', done: false }, { text: 'Zuschlag', done: false }], links: [{ kind: 'notebook-page', target: 'page-vp19', title: 'Prüfnotiz VP-19' }] },
      { title: 'Förderfähigkeit Personalkosten prüfen', badge: 'VP-20', tags: ['Personalkosten'], attachments: [{ id: 'f1', filename: 'Stundennachweise.pdf', mime_type: 'application/pdf', size: 482113 }] },
    ]),
    ...cards('entwurf', [{ title: 'Prüfbericht Gründerzentrum Fulda', badge: 'VP-17', color: '#1e293b', description: 'Feststellungen formell und finanziell zusammenfassen.', due: day(5) }]),
    ...cards('kontradiktorisch', [{ title: 'Stellungnahme Stadt Fulda einholen', badge: 'VP-15', priority: 'niedrig', due: day(14) }]),
    ...cards('abschluss', [{ title: 'Abschlussvermerk VP-12', badge: 'VP-12', priority: 'niedrig' }]),
    ...cards('followup', []),
  ])
  const cockpitTemplate = findTemplate('cockpit-auftraege')
  const cockpit = board('auftraege', 'Aufträge (cockpit)', '🤖', (cockpitTemplate?.columns ?? []).map((column) => (column.id === 'laeuft' ? { ...column, wip_limit: 2 } : column)), [
    ...cards('eingang', [{ title: 'Repo prüfen: regulierung', tags: ['Bericht'] }, { title: 'GUI verbessern: Synopse', tags: ['Oberfläche'] }]),
    ...cards('geplant', [{ title: 'Tests ergänzen: auditcore_risk', priority: 'hoch' }]),
    ...cards('laeuft', [{ title: 'Sicherheitsprüfung flowinvoice', priority: 'hoch', extra: { agent: 'claude' } }]),
    ...cards('rueckfrage', [{ title: 'Plan liegt vor: Debian-Paket', badge: 'PRJ-3' }]),
    ...cards('fertig', [{ title: 'Doku aktualisieren: harvest' }]),
  ], { transitions: cockpitTemplate?.transitions ?? { mode: 'free', allowed: [], locked_columns: [], fixed_order_columns: [] }, pinned: true })
  return [pruefung, cockpit]
}
