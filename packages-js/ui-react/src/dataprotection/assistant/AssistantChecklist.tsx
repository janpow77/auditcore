import { useEffect, useState } from 'react'
import type { ChecklistChange, ChecklistItemView, ChecklistStatus } from '@auditcore/ui-core'
import { prefixedLabel, useDataProtectionText } from '../shared'

const STATUSES: ChecklistStatus[] = ['offen', 'in_bearbeitung', 'zur_pruefung', 'nachgewiesen', 'klaerungsbedarf', 'nicht_erfuellt', 'nicht_anwendbar', 'erneut_zu_pruefen']

interface Edit { status: ChecklistStatus; justification: string; evidence: string }

function Row({ item, busy, onChange }: { item: ChecklistItemView; busy: boolean; onChange: (itemId: string, change: ChecklistChange) => void }) {
  const { t } = useDataProtectionText()
  const initial = (): Edit => ({ status: item.status, justification: item.justification, evidence: item.evidence_ids.join(', ') })
  const [edit, setEdit] = useState<Edit>(initial)
  // Ein neuer Serverstand setzt die Eingaben zurück (wie in der Vue-Fassung).
  useEffect(() => setEdit({ status: item.status, justification: item.justification, evidence: item.evidence_ids.join(', ') }), [item])
  const save = (): void => {
    const evidence = edit.evidence.split(',').map((entry) => entry.trim()).filter(Boolean)
    onChange(item.id, { status: edit.status, justification: edit.justification, evidence_ids: evidence })
  }
  return (
    <tr data-item={item.id}>
      <th scope="row">{item.id}</th>
      <td>
        {item.titel} {item.sperrt ? <span className="fa-assistant__badge">{t('itemBlocks', { gate: item.sperrt })}</span> : null}
        <br />
        <span className="fa-dataprotection__muted">{prefixedLabel(t, 'item', item.status)} · {item.zustaendig}</span>
      </td>
      <td>
        <label>
          {t('checklistStatus', { id: item.id })}{' '}
          <select value={edit.status} onChange={(event) => setEdit({ ...edit, status: event.target.value as ChecklistStatus })}>
            {STATUSES.map((status) => <option key={status} value={status}>{prefixedLabel(t, 'item', status)}</option>)}
          </select>
        </label>
        <label>{t('evidenceIds')} <input type="text" value={edit.evidence} onChange={(event) => setEdit({ ...edit, evidence: event.target.value })} /></label>
        <label>{t('answerJustification')} <textarea rows={2} value={edit.justification} onChange={(event) => setEdit({ ...edit, justification: event.target.value })} /></label>
        <button type="button" disabled={busy} onClick={save}>{t('saveItem')}</button>
      </td>
    </tr>
  )
}

export function AssistantChecklist({ items, busy, onChange }: { items: ChecklistItemView[]; busy: boolean; onChange: (itemId: string, change: ChecklistChange) => void }) {
  const { t } = useDataProtectionText()
  return (
    <section className="fa-dataprotection__panel" data-testid="assistant-checklist" aria-labelledby="fa-assistant-checklist" role="tabpanel">
      <h3 id="fa-assistant-checklist">{t('checklistTitle')}</h3>
      <table className="fa-dataprotection__table">
        <tbody>
          {items.map((item) => <Row key={item.id} item={item} busy={busy} onChange={onChange} />)}
        </tbody>
      </table>
    </section>
  )
}
