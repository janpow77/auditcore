import type { ChecklistChange, ChecklistTreeNode } from '@auditcore/ui-core'
import { prefixedLabel, useDataProtectionText } from '../shared'
import { AssistantChecklistDetail } from './AssistantChecklistDetail'

interface NodeProps {
  node: ChecklistTreeNode
  expanded: ReadonlySet<string>
  busy: boolean
  onToggle: (id: string) => void
  onChange: (itemId: string, change: ChecklistChange) => void
}

function RowLabel({ node }: { node: ChecklistTreeNode }) {
  const { t } = useDataProtectionText()
  if (node.item) {
    return (
      <>
        <span className="fa-checklist__key">{node.item.id}</span>
        <span className="fa-checklist__title">{node.label}</span>
        {node.item.sperrt ? <span className="fa-assistant__badge">{t('itemBlocks', { gate: node.item.sperrt })}</span> : null}
        <span className={`fa-checklist__status fa-checklist__status--${node.tone}`}>{prefixedLabel(t, 'item', node.item.status)}</span>
      </>
    )
  }
  return (
    <>
      <span className="fa-checklist__title">{t('checklistArea', { area: node.label })}</span>
      {node.progress.attention ? <span className="fa-checklist__status fa-checklist__status--attention">{t('checklistAttention', { count: node.progress.attention })}</span> : null}
      <span className={`fa-checklist__status fa-checklist__status--${node.tone}`}>{t('checklistProgress', { settled: node.progress.settled, total: node.progress.total })}</span>
    </>
  )
}

/** Rekursiver Knoten: Bereiche zeigen ihre Kinder, Prüfpunkte ihre Detailansicht. */
export function AssistantChecklistNode({ node, expanded, busy, onToggle, onChange }: NodeProps) {
  const open = expanded.has(node.id)
  return (
    <li className={`fa-checklist__node fa-checklist__node--${node.kind}`} data-node={node.id} data-item={node.item?.id}>
      <button type="button" className="fa-checklist__row" aria-expanded={open} onClick={() => onToggle(node.id)}>
        <span className="fa-checklist__chevron" aria-hidden="true">▸</span>
        <span className={`fa-checklist__dot fa-checklist__dot--${node.tone}`} aria-hidden="true" />
        <RowLabel node={node} />
      </button>
      {open && node.item ? <AssistantChecklistDetail item={node.item} busy={busy} onChange={onChange} /> : null}
      {open && !node.item ? (
        <ul className="fa-checklist__children">
          {node.children.map((child) => <AssistantChecklistNode key={child.id} node={child} expanded={expanded} busy={busy} onToggle={onToggle} onChange={onChange} />)}
        </ul>
      ) : null}
    </li>
  )
}
