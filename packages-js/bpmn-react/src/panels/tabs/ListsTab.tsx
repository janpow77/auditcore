/**
 * Generic tab for FlowAudit lists (controls, risks, evidence, deadlines,
 * findings, audit steps, sources, references) – from the descriptors.
 */

import type { Extensions, ListExtensionKey } from '@auditcore/bpmn-flowaudit'
import { isDescribedList, LISTS } from '@auditcore/bpmn-flowaudit/ui'
import { useEditorContext, useSelectionState } from '../../context'
import { ListEditor } from '../ListEditor'
import { useOptions } from '../useOptions'

export function ListsTab({ lists }: { lists: ListExtensionKey[] }) {
  const { selection, readonly } = useEditorContext()
  const { extensions } = useSelectionState()
  const optionsFor = useOptions()
  return (
    <div className="fa-tab-lists">
      {lists.filter(isDescribedList).map((key) => (
        <ListEditor
          key={key}
          descriptor={LISTS[key]}
          items={extensions[key] as unknown as Record<string, unknown>[]}
          optionsFor={optionsFor}
          disabled={readonly()}
          onUpdate={(value) => selection.write({ [key]: value } as Partial<Extensions>)}
        />
      ))}
    </div>
  )
}
