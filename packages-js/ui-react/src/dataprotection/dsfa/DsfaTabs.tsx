import type { KeyboardEvent, ReactNode } from 'react'
import type { TabItem } from '@auditcore/ui-core'
import { useElementId } from '../../store'

export interface DsfaTabsProps {
  tabs: readonly TabItem[]
  active: string
  label: string
  onTabChange: (key: string) => void
  children?: ReactNode
}

const MOVES: Readonly<Record<string, (index: number, count: number) => number>> = {
  ArrowRight: (index) => index + 1,
  ArrowLeft: (index) => index - 1,
  Home: () => 0,
  End: (_index, count) => count - 1,
}

/** Abschnitte der Abschätzung als WAI-ARIA-Tabs (Pfeiltasten, Pos1, Ende). */
export function DsfaTabs({ tabs, active, label, onTabChange, children }: DsfaTabsProps) {
  const base = useElementId('fa-dsfa-tab')
  function onKey(event: KeyboardEvent<HTMLDivElement>): void {
    const move = MOVES[event.key]
    if (!move) return
    event.preventDefault()
    const index = tabs.findIndex((tab) => tab.key === active)
    const next = tabs[(move(index, tabs.length) + tabs.length) % tabs.length]
    if (!next) return
    onTabChange(next.key)
    event.currentTarget.querySelector<HTMLElement>(`#${base}-${next.key}`)?.focus()
  }
  return (
    <>
      <div className="fa-dsfa__tabs" role="tablist" aria-label={label} onKeyDown={onKey}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            id={`${base}-${tab.key}`}
            type="button"
            role="tab"
            className="fa-dsfa__tab"
            aria-selected={tab.key === active ? 'true' : 'false'}
            aria-controls={`${base}-panel`}
            tabIndex={tab.key === active ? 0 : -1}
            onClick={() => onTabChange(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div id={`${base}-panel`} role="tabpanel" aria-labelledby={`${base}-${active}`} tabIndex={0}>
        {children}
      </div>
    </>
  )
}
