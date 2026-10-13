import { useMemo, useState } from 'react'
import { checklistBranchIds, checklistProgress, checklistTree, toggleChecklistNode, type ChecklistChange, type ChecklistItemView } from '@auditcore/ui-core'
import { useDataProtectionText } from '../shared'
import { AssistantChecklistNode } from './AssistantChecklistNode'

export function AssistantChecklist({ items, busy, onChange }: { items: ChecklistItemView[]; busy: boolean; onChange: (itemId: string, change: ChecklistChange) => void }) {
  const { t } = useDataProtectionText()
  const tree = useMemo(() => checklistTree(items), [items])
  const progress = checklistProgress(tree)
  // Bereiche sind anfangs offen, Prüfpunkte zu; der Zustand übersteht neue Serverstände.
  const [expanded, setExpanded] = useState<ReadonlySet<string>>(() => new Set(checklistBranchIds(tree)))
  const toggle = (id: string): void => setExpanded((current) => toggleChecklistNode(current, id))
  return (
    <section className="fa-dataprotection__panel fa-checklist" data-testid="assistant-checklist" aria-labelledby="fa-assistant-checklist" role="tabpanel">
      <div className="fa-dataprotection__bar fa-checklist__head">
        <h3 id="fa-assistant-checklist">{t('checklistTitle')}</h3>
        <span className="fa-dataprotection__muted">{t('checklistProgress', { settled: progress.settled, total: progress.total })}</span>
        {progress.attention ? <span className="fa-checklist__status fa-checklist__status--attention">{t('checklistAttention', { count: progress.attention })}</span> : null}
        <div className="fa-dataprotection__actions">
          <button type="button" onClick={() => setExpanded(new Set(checklistBranchIds(tree)))}>{t('checklistExpandAll')}</button>
          <button type="button" onClick={() => setExpanded(new Set())}>{t('checklistCollapseAll')}</button>
        </div>
      </div>
      <ul className="fa-checklist__tree">
        {tree.map((node) => <AssistantChecklistNode key={node.id} node={node} expanded={expanded} busy={busy} onToggle={toggle} onChange={onChange} />)}
      </ul>
    </section>
  )
}
