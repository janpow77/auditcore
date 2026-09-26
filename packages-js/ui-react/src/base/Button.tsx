import type { MouseEvent, ReactNode } from 'react'
import type { ButtonSize, ButtonVariant, IconName } from '@auditcore/ui-core'
import { classes } from '../store'
import { Icon } from './Icon'

export interface ButtonProps {
  variant?: ButtonVariant
  size?: ButtonSize
  icon?: IconName
  /** Nur Symbol: `label` wird dann zur zugänglichen Beschriftung und zum Tooltip. */
  iconOnly?: boolean
  label?: string
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
  pressed?: boolean
  className?: string
  title?: string
  ariaLabel?: string
  ariaKeyshortcuts?: string
  /** Durchgereichte Attribute wie in Vue (Optionsgruppe aus Schaltflächen). */
  role?: string
  ariaChecked?: boolean
  /** `data-testid` (in Vue als durchgereichtes Attribut). */
  testId?: string
  children?: ReactNode
  onClick?: (event: MouseEvent<HTMLButtonElement>) => void
}

function buttonClass({ variant = 'secondary', size = 'md', iconOnly, loading, className }: ButtonProps): string {
  return classes('fa-button', `fa-button--${variant}`, `fa-button--${size}`, iconOnly && 'fa-button--icon-only', loading && 'fa-button--loading', className)
}

/** Beschriftung und Tooltip: bei reinem Symbol aus `label`, sonst nur auf ausdrücklichen Wunsch. */
function accessibleName({ iconOnly, label, ariaLabel, title }: ButtonProps): { ariaLabel?: string; title?: string } {
  const own = iconOnly ? label : undefined
  return { ariaLabel: ariaLabel ?? own, title: title ?? own }
}

/** Schaltfläche wie `FaButton` (gleiche Klassen, ARIA und Zustände). */
export function Button(props: ButtonProps) {
  const name = accessibleName(props)
  const content = props.children ?? props.label
  return (
    <button
      className={buttonClass(props)}
      type={props.type ?? 'button'}
      disabled={props.disabled || props.loading}
      aria-busy={props.loading || undefined}
      aria-pressed={props.pressed}
      aria-label={name.ariaLabel}
      aria-keyshortcuts={props.ariaKeyshortcuts}
      role={props.role}
      aria-checked={props.ariaChecked}
      title={name.title}
      data-testid={props.testId}
      onClick={props.onClick}
    >
      {props.icon ? <Icon name={props.icon} size={props.size === 'sm' ? 14 : 16} /> : null}
      {props.iconOnly ? null : <span className="fa-button__label">{content}</span>}
    </button>
  )
}
