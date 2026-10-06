/**
 * Palette in the left column (legacy: mirrored palette): tools, BPMN
 * elements and pools per role. Entries trigger the palette of the running
 * editor; icons come from the FlowAudit set. „Elemente“ and „Pool mit
 * Rolle“ are shown as icons, large tiles or a list; the choice is kept per
 * browser and switched in one menu in the head of the palette.
 */

import { useState, type SyntheticEvent } from 'react'
import { PALETTE_VIEWS, paletteCaption, paletteName, paletteSections, readPaletteView, writePaletteView, type PaletteItem, type PaletteView } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { ToolbarMenu } from '../base/ToolbarMenu'
import { classes } from '../hooks'
import { useI18n } from '../i18n'

export interface ToolPaletteProps {
  items: PaletteItem[]
  disabled?: boolean
  onTrigger: (id: string, event: Event) => void
}

function ItemIcon({ item, size }: { item: PaletteItem; size: number }) {
  if (item.icon && item.color) {
    return (
      <span className="fa-palette__role" style={{ color: item.color.stroke, background: item.color.fill }}>
        <FaIcon name={item.icon} size={size} />
      </span>
    )
  }
  return item.icon ? <FaIcon name={item.icon} size={size} /> : <span className="fa-palette__fallback">{item.title.slice(0, 2)}</span>
}

function ItemText({ item, view }: { item: PaletteItem; view: PaletteView }) {
  const { t, locale } = useI18n()
  if (view === 'tiles') return <span className="fa-palette__caption">{paletteCaption(item, t)}</span>
  if (view !== 'list') return null
  return (
    <span className="fa-palette__text">
      {item.short ? <strong className="fa-palette__short">{item.short}</strong> : null}
      <span className="fa-palette__name" lang={locale}>{paletteName(item, t, locale)}</span>
    </span>
  )
}

function ViewMenu({ view, onChoose }: { view: PaletteView; onChoose: (view: PaletteView) => void }) {
  const { t } = useI18n()
  return (
    <div className="fa-palette__head">
      <ToolbarMenu label={t('palette.view')} icon="overview">
        {(close) =>
          PALETTE_VIEWS.map((option) => (
            <button key={option} type="button" role="menuitemradio" className="fa-menu-item" aria-checked={view === option} onClick={() => (onChoose(option), close())}>
              {view === option ? <FaIcon name="check" size={14} /> : <span className="fa-menu-item__spacer" />}
              <span>{t(`palette.view.${option}`)}</span>
            </button>
          ))
        }
      </ToolbarMenu>
    </div>
  )
}

export function ToolPalette({ items, disabled, onTrigger }: ToolPaletteProps) {
  const { t } = useI18n()
  const [view, setView] = useState<PaletteView>(() => readPaletteView())
  const trigger = (id: string) => (event: SyntheticEvent) => onTrigger(id, event.nativeEvent)
  const choose = (next: PaletteView) => {
    setView(next)
    writePaletteView(next)
  }
  return (
    <nav className={classes('fa-palette', `fa-palette--${view}`)} aria-label={t('palette.label')}>
      <ViewMenu view={view} onChoose={choose} />
      {paletteSections(items).map((section) => {
        const sectionView: PaletteView = section.id === 'tools' ? 'icons' : view
        return (
          <section key={section.id} className={`fa-palette__section fa-palette__section--${section.id}`} style={section.items.length ? undefined : { display: 'none' }}>
            <h2 className="fa-palette__title">{t(section.title)}</h2>
            <div className={classes('fa-palette__grid', `fa-palette__grid--${sectionView}`)}>
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
                  <ItemIcon item={item} size={sectionView === 'tiles' ? 28 : 20} />
                  <ItemText item={item} view={sectionView} />
                </button>
              ))}
            </div>
          </section>
        )
      })}
      <p className="fa-help fa-palette__hint">{t('palette.hint')}</p>
    </nav>
  )
}
