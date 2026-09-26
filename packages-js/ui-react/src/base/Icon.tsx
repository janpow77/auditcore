import { ICONS, type IconName } from '@flowaudit/ui-core'

export interface IconProps {
  name: IconName
  size?: number | string
  /** Mit Beschriftung ist das Symbol bedeutungstragend (role="img"), sonst dekorativ. */
  label?: string
  /** Zusätzliche Klasse (wie ein durchgereichtes `class` in Vue). */
  className?: string
}

export function Icon({ name, size = 18, label = '', className }: IconProps) {
  const dimension = typeof size === 'number' ? `${size}px` : size
  return (
    <svg
      className={className ? `fa-icon ${className}` : 'fa-icon'}
      viewBox="0 0 24 24"
      width={dimension}
      height={dimension}
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? 'img' : undefined}
      aria-label={label || undefined}
      aria-hidden={label ? undefined : 'true'}
      focusable="false"
    >
      {ICONS[name].map((d, index) => (
        <path key={index} d={d} />
      ))}
    </svg>
  )
}
