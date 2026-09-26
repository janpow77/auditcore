/** Right column: properties, issue list, walk-through and comparison as tabs. */

import type { Comment, PaletteColor } from '@flowaudit/bpmn-flowaudit'
import { SIDE_VIEWS, type CompareSource, type SideView } from '@flowaudit/bpmn-flowaudit/ui'
import { FaIcon } from './base/FaIcon'
import { useValidationView } from './context'
import { useI18n } from './i18n'
import { PropertiesPanel } from './panels/PropertiesPanel'
import { ComparePanel } from './views/ComparePanel'
import { IssueList } from './views/IssueList'
import { WalkthroughPanel } from './views/WalkthroughPanel'

export interface EditorSidePanelProps {
  view: SideView
  comments: Comment[]
  author: string
  compareSources: CompareSource[]
  palette?: readonly PaletteColor[]
  onViewChange: (view: SideView) => void
  onCommentsChange?: (comments: Comment[]) => void
  onJump: (id: string) => void
}

function SideBody({ view, comments, author, compareSources, palette, onCommentsChange, onJump }: EditorSidePanelProps) {
  const validation = useValidationView()
  if (view === 'properties') return <PropertiesPanel comments={comments} author={author} palette={palette} onCommentsChange={onCommentsChange ?? (() => undefined)} />
  return (
    <div className="fa-side__pad">
      {view === 'issues' ? <IssueList issues={validation.issues} running={validation.running} error={validation.error} onJump={onJump} /> : null}
      {view === 'walkthrough' ? <WalkthroughPanel tester={author} /> : null}
      {view === 'compare' ? <ComparePanel sources={compareSources} /> : null}
    </div>
  )
}

export function EditorSidePanel(props: EditorSidePanelProps) {
  const { t } = useI18n()
  const errors = useValidationView().count.fehler
  return (
    <div className="fa-side">
      <div className="fa-side__tabs" role="tablist">
        {SIDE_VIEWS.map((entry) => (
          <button key={entry.id} type="button" role="tab" className="fa-side__tab" aria-selected={props.view === entry.id} title={t(entry.label)} onClick={() => props.onViewChange(entry.id)}>
            <FaIcon name={entry.icon} size={16} />
            <span className="fa-side__tab-label">{t(entry.label)}</span>
            {entry.id === 'issues' && errors ? <span className="fa-badge fa-badge--danger">{errors}</span> : null}
          </button>
        ))}
      </div>
      <div className="fa-side__body" role="tabpanel">
        <SideBody {...props} />
      </div>
    </div>
  )
}
