/**
 * Properties panel with tabs (General, Role, Legal bases, Audit reference,
 * Control & risk, Evidence, Findings, Source, Notes, Colour). Tabs follow the
 * WAI-ARIA tabs pattern (arrow keys, Home/End).
 */

import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import type { Comment, PaletteColor } from '@flowaudit/bpmn-flowaudit'
import { listsFor, tabMove, tabsFor, type TabDefinition, type TabId } from '@flowaudit/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { useSelectionState } from '../context'
import { useI18n } from '../i18n'
import { ColorTab } from './tabs/ColorTab'
import { GeneralTab } from './tabs/GeneralTab'
import { LegalTab } from './tabs/LegalTab'
import { ListsTab } from './tabs/ListsTab'
import { NotesTab } from './tabs/NotesTab'
import { RoleTab } from './tabs/RoleTab'

export interface PropertiesPanelProps {
  comments: Comment[]
  author: string
  palette?: readonly PaletteColor[]
  onCommentsChange: (comments: Comment[]) => void
}

function TabContent({ tab, type, props }: { tab: TabDefinition; type: string; props: PropertiesPanelProps }) {
  if (tab.id === 'general') return <GeneralTab />
  if (tab.id === 'role') return <RoleTab />
  if (tab.id === 'legal') return <LegalTab />
  if (tab.id === 'notes') return <NotesTab comments={props.comments} author={props.author} onCommentsChange={props.onCommentsChange} />
  if (tab.id === 'color') return <ColorTab palette={props.palette} />
  return <ListsTab lists={listsFor(tab, type)} />
}

export function PropertiesPanel(props: PropertiesPanelProps) {
  const { t } = useI18n()
  const { element, type } = useSelectionState()
  const [active, setActive] = useState<TabId>('general')
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([])
  const tabs = tabsFor(type)
  const known = tabs.some((tab) => tab.id === active)
  const current = tabs.find((tab) => tab.id === (known ? active : 'general')) ?? tabs[0]

  useEffect(() => {
    if (!known) setActive('general')
  }, [known])

  const onKey = (event: KeyboardEvent, index: number) => {
    const next = tabMove(event.key, index, tabs.length)
    if (next === null) return
    event.preventDefault()
    const tab = tabs[next]
    if (tab) setActive(tab.id)
    tabRefs.current[next]?.focus()
  }

  return (
    <aside className="fa-props" aria-label={t('props.label')}>
      {!element ? (
        <p className="fa-props__empty">{t('editor.noSelection')}</p>
      ) : (
        <>
          <div className="fa-props__tabs" role="tablist" aria-orientation="vertical" aria-label={t('props.label')}>
            {tabs.map((tab, index) => (
              <button
                id={`fa-tab-${tab.id}`}
                key={tab.id}
                ref={(node) => void (tabRefs.current[index] = node)}
                type="button"
                role="tab"
                className="fa-props__tab"
                aria-selected={current?.id === tab.id}
                aria-controls={`fa-tabpanel-${tab.id}`}
                tabIndex={current?.id === tab.id ? 0 : -1}
                title={t(tab.label)}
                onClick={() => setActive(tab.id)}
                onKeyDown={(event) => onKey(event, index)}
              >
                <FaIcon name={tab.icon} size={18} />
                <span className="fa-props__tab-label">{t(tab.label)}</span>
              </button>
            ))}
          </div>
          {current ? (
            <section id={`fa-tabpanel-${current.id}`} className="fa-props__panel" role="tabpanel" aria-labelledby={`fa-tab-${current.id}`} tabIndex={0}>
              <h2 className="fa-props__title">{t(current.label)}</h2>
              <TabContent tab={current} type={type ?? ''} props={props} />
            </section>
          ) : null}
        </>
      )}
    </aside>
  )
}
