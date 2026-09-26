/**
 * Icon from the FlowAudit icon set (24 px grid, `currentColor`). Decorative
 * by default; pass `label` to make it meaningful for assistive technology.
 */

import { createElement } from 'react'
import { iconPrimitives } from '@auditcore/bpmn-flowaudit'

const camel = (key: string) => key.replace(/-([a-z])/g, (_, letter: string) => letter.toUpperCase())
const reactProps = (attrs: Record<string, string>) => Object.fromEntries(Object.entries(attrs).map(([key, value]) => [camel(key), value]))

export interface FaIconProps {
  name: string
  size?: number
  label?: string
  className?: string
}

export function FaIcon({ name, size = 18, label = '', className }: FaIconProps) {
  return (
    <svg
      className={className ? `fa-icon ${className}` : 'fa-icon'}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? 'img' : undefined}
      aria-label={label || undefined}
      aria-hidden={label ? undefined : 'true'}
      focusable="false"
    >
      {iconPrimitives(name).map(([tag, attrs], index) => createElement(tag, { key: index, ...reactProps(attrs) }))}
    </svg>
  )
}
