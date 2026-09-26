import { Fragment } from 'react'
import type { DiffSegment } from '@auditcore/ui-core'

export interface SynopsisTextProps {
  segments?: readonly DiffSegment[]
  empty?: string
  srRemoved?: string
  srAdded?: string
  srEnd?: string
}

/**
 * Wortsegmente mit `<del>`/`<ins>`. Streichungen sind durchgestrichen,
 * Einfügungen unterstrichen (nicht nur Farbe); Bildschirmleser hören
 * „gestrichen: … Ende“ bzw. „eingefügt: … Ende“.
 */
export function SynopsisText({ segments = [], empty = '', srRemoved = '', srAdded = '', srEnd = '' }: SynopsisTextProps) {
  const marked = (Tag: 'del' | 'ins', prefix: string, text: string, key: number) => (
    <Tag key={key} className={Tag === 'del' ? 'fa-synopsis__del' : 'fa-synopsis__ins'}>
      <span className="fa-sr-only">{`${prefix} `}</span>
      {text}
      <span className="fa-sr-only">{` ${srEnd}`}</span>
    </Tag>
  )
  return (
    <p className="fa-synopsis__text">
      {segments.length === 0 ? <span className="fa-synopsis__empty">{empty}</span> : null}
      {segments.map((segment, index) => {
        if (segment.kind === 'removed') return marked('del', srRemoved, segment.text, index)
        if (segment.kind === 'added') return marked('ins', srAdded, segment.text, index)
        return <Fragment key={index}>{segment.text}</Fragment>
      })}
    </p>
  )
}
