import { Fragment, useEffect, useState } from 'react'
import { CHECKLIST_STATUSES, checklistChange, checklistEdit, checklistMeta, type ChecklistChange, type ChecklistEdit, type ChecklistItemView, type ChecklistStatus } from '@auditcore/ui-core'
import { prefixedLabel, useDataProtectionText } from '../shared'

export function AssistantChecklistDetail({ item, busy, onChange }: { item: ChecklistItemView; busy: boolean; onChange: (itemId: string, change: ChecklistChange) => void }) {
  const { t, when } = useDataProtectionText()
  const [edit, setEdit] = useState<ChecklistEdit>(() => checklistEdit(item))
  // Ein neuer Serverstand setzt die Eingaben zurück (wie in der Vue-Fassung).
  useEffect(() => setEdit(checklistEdit(item)), [item])
  const save = (): void => onChange(item.id, checklistChange(item, edit))
  return (
    <div className="fa-checklist__detail">
      <dl className="fa-dataprotection__dl">
        {checklistMeta(t, item, (value, withTime) => when(value, withTime)).map((row) => (
          <Fragment key={row.key}>
            <dt>{row.label}</dt>
            <dd>{row.value}</dd>
          </Fragment>
        ))}
      </dl>
      <div className="fa-checklist__form">
        <label className="fa-dataprotection__field">
          {t('checklistStatus', { id: item.id })}
          <select value={edit.status} onChange={(event) => setEdit({ ...edit, status: event.target.value as ChecklistStatus })}>
            {CHECKLIST_STATUSES.map((status) => <option key={status} value={status}>{prefixedLabel(t, 'item', status)}</option>)}
          </select>
        </label>
        <label className="fa-dataprotection__field">{t('evidenceIds')}<input type="text" value={edit.evidence} onChange={(event) => setEdit({ ...edit, evidence: event.target.value })} /></label>
        <label className="fa-dataprotection__field">{t('checklistOwner')}<input type="text" value={edit.owner} onChange={(event) => setEdit({ ...edit, owner: event.target.value })} /></label>
        <label className="fa-dataprotection__field">{t('checklistDue')}<input type="date" value={edit.due} onChange={(event) => setEdit({ ...edit, due: event.target.value })} /></label>
        <label className="fa-dataprotection__field fa-checklist__wide">{t('answerJustification')}<textarea rows={2} value={edit.justification} onChange={(event) => setEdit({ ...edit, justification: event.target.value })} /></label>
        <button type="button" className="fa-checklist__save" disabled={busy} onClick={save}>{t('saveItem')}</button>
      </div>
    </div>
  )
}
