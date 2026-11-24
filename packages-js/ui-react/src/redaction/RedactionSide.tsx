import type { RedactionGroupView, RedactionItemView, RedactionReviewView } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { classes } from '../store'
import type { UseRedaction } from './useRedaction'

interface Part {
  hook: UseRedaction
  view: RedactionReviewView
}

function Summary({ hook, view }: Part) {
  const { controller, t } = hook
  return (
    <div className="fa-redaction__summary">
      <p className="fa-redaction__summary-text" data-testid="redaction-summary">{view.summary}</p>
      <div className="fa-redaction__buttons">
        <Button size="sm" disabled={!view.hasCandidates} testId="redaction-select-all" onClick={() => controller.setAll(true)}>{t('selectAll')}</Button>
        <Button size="sm" disabled={!view.hasCandidates} testId="redaction-deselect-all" onClick={() => controller.setAll(false)}>{t('deselectAll')}</Button>
      </div>
      {view.sources.length > 1 ? (
        <div className="fa-redaction__sources" role="group" aria-label={t('sources')}>
          {view.sources.map((entry) => (
            <button key={entry.source} type="button" className={classes('fa-redaction__source', `fa-redaction__source--${entry.state}`)} aria-pressed={entry.state === 'all'} title={entry.title} data-source={entry.source} onClick={() => controller.setSource(entry.source, entry.state !== 'all')}>{entry.text}</button>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function Item({ hook, item }: { hook: UseRedaction; item: RedactionItemView }) {
  const { controller, t } = hook
  return (
    <li>
      <span className="fa-redaction__number">{`${item.number}.`}</span>
      <input type="checkbox" checked={item.checked} aria-label={item.label} onChange={() => controller.toggle(item.id)} />
      {item.page ? <button type="button" className="fa-redaction__link" onClick={() => void controller.showPage(item.page as number)}>{t('itemPage', { page: item.page })}</button> : null}
      {item.text ? <span className="fa-redaction__item-text">{item.text}</span> : null}
      {item.extra ? <span className="fa-redaction__item-text">{item.extra}</span> : null}
    </li>
  )
}

function Group({ hook, group }: { hook: UseRedaction; group: RedactionGroupView }) {
  const { controller } = hook
  const indeterminate = (element: HTMLInputElement | null): void => {
    if (element) element.indeterminate = group.state === 'some'
  }
  return (
    <li className="fa-redaction__group">
      <div className="fa-redaction__group-head">
        <input type="checkbox" checked={group.state === 'all'} ref={indeterminate} aria-label={group.label} onChange={(event) => controller.setGroup(group.key, event.target.checked)} />
        <button type="button" className="fa-redaction__group-toggle" aria-expanded={group.expanded} onClick={() => controller.toggleExpanded(group.key)}>
          <span className={classes('fa-redaction__text', group.state === 'none' && 'fa-redaction__text--off')}>{group.text}</span>
          <span className="fa-redaction__meta">{group.meta}</span>
        </button>
      </div>
      {group.expanded ? <ul className="fa-redaction__items">{group.items.map((item) => <Item key={item.id} hook={hook} item={item} />)}</ul> : null}
    </li>
  )
}

function Notices({ hook, view }: Part) {
  const { controller, state, t } = hook
  return (
    <>
      {view.noText ? <p className="fa-redaction__notice fa-redaction__notice--warning">{view.noText}</p> : null}
      {view.outside ? <p className="fa-redaction__notice">{view.outside}</p> : null}
      {view.showFilter ? (
        <label className="fa-redaction__field">
          <span className="fa-redaction__label">{t('filter')}</span>
          <input className="fa-redaction__input" type="search" placeholder={t('filterPlaceholder')} value={state.filter} data-testid="redaction-filter" onChange={(event) => controller.setFilter(event.target.value)} />
        </label>
      ) : null}
      {!view.hasCandidates ? <p className="fa-redaction__muted">{t('noCandidates')}</p> : null}
      {view.noMatch ? <p className="fa-redaction__muted">{view.noMatch}</p> : null}
    </>
  )
}

function Groups({ hook, view }: Part) {
  return (
    <>
      {view.groups.length ? <ul className="fa-redaction__groups">{view.groups.map((group) => <Group key={group.key} hook={hook} group={group} />)}</ul> : null}
      {view.more ? (
        <div>
          <Button size="sm" variant="ghost" testId="redaction-more" onClick={() => hook.controller.showMore()}>{view.more}</Button>
        </div>
      ) : null}
      {view.hiddenText ? (
        <div className="fa-redaction__hidden">
          <p><strong>{hook.t('hiddenHeading')}</strong></p>
          <p>{view.hiddenText}</p>
        </div>
      ) : null}
    </>
  )
}

function Actions({ hook }: { hook: UseRedaction }) {
  const { controller, state, t } = hook
  return (
    <>
      <label className="fa-redaction__check">
        <input type="checkbox" data-testid="redaction-sanitize" checked={state.sanitize} onChange={(event) => controller.setOption('sanitize', event.target.checked)} />
        <span>{t('sanitize')}</span>
      </label>
      <p className="fa-redaction__muted">{t('applyHelp')}</p>
      <div className="fa-redaction__actions">
        <Button testId="redaction-back" onClick={() => controller.back()}>{t('back')}</Button>
        <Button variant="primary" loading={state.busy === 'apply'} testId="redaction-apply" onClick={() => void controller.apply()}>{t('apply')}</Button>
      </div>
    </>
  )
}

/** Seitenleiste: Zusammenfassung, Quellen, Filter, Gruppen, Bereinigung und Schwärzen. */
export function RedactionSide({ hook, view }: Part) {
  return (
    <aside className="fa-redaction__side" aria-label={hook.t('findings')}>
      <Summary hook={hook} view={view} />
      <Notices hook={hook} view={view} />
      <Groups hook={hook} view={view} />
      <Actions hook={hook} />
    </aside>
  )
}
