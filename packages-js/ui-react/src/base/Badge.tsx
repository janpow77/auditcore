import type { ReactNode } from 'react'
import type { BadgeTone } from '@auditcore/ui-core'

export interface BadgeProps {
  tone?: BadgeTone
  label?: string
  children?: ReactNode
  /** `data-testid` (in Vue als durchgereichtes Attribut). */
  testId?: string
}

export function Badge({ tone = 'neutral', label = '', children, testId }: BadgeProps) {
  return <span className={`fa-badge fa-badge--${tone}`} data-testid={testId}>{children ?? label}</span>
}
