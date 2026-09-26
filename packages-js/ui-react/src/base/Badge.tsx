import type { ReactNode } from 'react'
import type { BadgeTone } from '@flowaudit/ui-core'

export interface BadgeProps {
  tone?: BadgeTone
  label?: string
  children?: ReactNode
}

export function Badge({ tone = 'neutral', label = '', children }: BadgeProps) {
  return <span className={`fa-badge fa-badge--${tone}`}>{children ?? label}</span>
}
