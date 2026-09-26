/**
 * Palette in the left column (legacy: mirrored palette): tools, BPMN
 * elements and pools per role. Entries trigger the palette of the running
 * editor; icons come from the FlowAudit set.
 */

import type { SyntheticEvent } from 'react'
import { paletteSections, type PaletteItem } from '@flowaudit/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { classes } from '../hooks'
import { useI18n } from '../i18n'

export interface ToolPaletteProps {
  items: PaletteItem[]
  disabled?: boolean
  onTrigger: (id: string, event: Event) => void
}

function ItemIcon({ item }: { item: PaletteItem }) {
  if (item.icon && item.color) {
    return (
      <span className="fa-palette__role" style={{ color: item.color.stroke, background: item.color.fill }}>
        <FaIcon name={item.icon} size={20} />
      </span>
    )
  }
  return item.icon ? <FaIcon name={item.icon} size={20} /> : <span className="fa-palette__fallback">{item.title.slice(0, 2)}</span>
}

export function ToolPalette({ items, disabled, onTrigger }: ToolPaletteProps) {
  const { t } = useI18n()
  const trigger = (id: string) => (event: SyntheticEvent) => onTrigger(id, event.nativeEvent)
  return (
    <nav className="fa-palette" aria-label={t('palette.label')}>
      {paletteSections(items).map((section) => (
        <section key={section.id} className="fa-palette__section" style={section.items.length ? undefined : { display: 'none' }}>
          <h2 className="fa-palette__title">{t(section.title)}</h2>
          <div className="fa-palette__grid">
            {section.items.map((item) => (
              <button
                key={item.id}
                type="button"
                className={classes('fa-palette__item', section.id === 'roles' && 'fa-palette__item--role')}
                title={item.title}
                aria-label={item.title}
                disabled={Boolean(disabled && section.id !== 'tools')}
                draggable="true"
                onClick={trigger(item.id)}
                onDragStart={trigger(item.id)}
              >
                <ItemIcon item={item} />
              </button>
            ))}
          </div>
        </section>
      ))}
      <p className="fa-help fa-palette__hint">{t('palette.hint')}</p>
    </nav>
  )
}
