import { extrapolationCellLabel, extrapolationIssueText, SUB_ITEM_FIELDS, subsampleEstimatorChoices, type SubItemRow, type SubsampleEstimator, type SubsampleRows } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { classes, useElementId } from '../store'
import type { UseExtrapolation } from './useExtrapolation'

function ItemLine({ view, item, position, issue }: { view: UseExtrapolation; item: SubItemRow; position: number; issue: (key: string) => string }) {
  const { controller, t } = view
  return (
    <tr>
      {SUB_ITEM_FIELDS.map((field) => (
        <td key={field.key}>
          <input
            className={classes('fa-extrapolation__input', field.numeric && 'fa-extrapolation__input--number')}
            inputMode={field.numeric ? 'decimal' : undefined}
            value={item[field.key]}
            aria-label={extrapolationCellLabel(t, field.label, position + 1)}
            aria-invalid={issue(`items.${position}.${field.key}`) ? 'true' : undefined}
            onChange={(event) => controller.updateSubItem(position, { [field.key]: event.target.value })}
          />
        </td>
      ))}
      <td>
        <input type="checkbox" className="fa-extrapolation__check" checked={item.exhaustive} aria-label={extrapolationCellLabel(t, 'exhaustive', position + 1)} onChange={(event) => controller.updateSubItem(position, { exhaustive: event.target.checked })} />
      </td>
      <td>
        <Button size="sm" variant="ghost" icon="trash" iconOnly label={t('removeRow', { what: t('subItemId'), row: position + 1 })} onClick={() => controller.removeSubItem(position)} />
      </td>
    </tr>
  )
}

function SubsampleSettings({ view, rows, issue }: { view: UseExtrapolation; rows: SubsampleRows; issue: (key: string) => string }) {
  const { controller, t } = view
  return (
    <div className="fa-extrapolation__settings">
      <label className="fa-extrapolation__field">
        <span className="fa-extrapolation__label">{t('estimator')}</span>
        <select className="fa-extrapolation__select" value={rows.estimator} data-testid="extrapolation-subsample-estimator" onChange={(event) => controller.updateSubsample({ estimator: event.target.value as SubsampleEstimator })}>
          {subsampleEstimatorChoices(t).map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
        </select>
      </label>
      {rows.estimator === 'mean_per_unit' ? (
        <label className="fa-extrapolation__field">
          <span className="fa-extrapolation__label">{t('subPopulation')}</span>
          <input className={classes('fa-extrapolation__input', 'fa-extrapolation__input--number')} inputMode="numeric" value={rows.populationSize} aria-invalid={issue('populationSize') ? 'true' : undefined} data-testid="extrapolation-subsample-size" onChange={(event) => controller.updateSubsample({ populationSize: event.target.value })} />
          {issue('populationSize') ? <span className="fa-extrapolation__error">{issue('populationSize')}</span> : null}
        </label>
      ) : null}
    </div>
  )
}

/** Teilstichprobe der gerade gewählten Einheit (wie `ExtrapolationSubsample.vue`; Leitfaden 7.6, 6.5.3). */
export function ExtrapolationSubsample({ view }: { view: UseExtrapolation }) {
  const { state, controller, t } = view
  const id = useElementId('fa-extrapolation-subsample')
  const index = state.subsampleUnit
  const unit = index === null ? null : state.form.units[index] ?? null
  const rows = unit?.subsample ?? null
  if (!unit || !rows || index === null) return null
  const issue = (key: string): string => extrapolationIssueText(state.issues, `units.${index}.subsample.${key}`, t)
  return (
    <section className="fa-extrapolation__card" aria-labelledby={`${id}-title`} data-testid="extrapolation-subsample">
      <h3 id={`${id}-title`} className="fa-extrapolation__heading">{t('subsampleTitle', { unit: unit.id || String(index + 1) })}</h3>
      <p className="fa-extrapolation__hint">{t('subsampleHint')}</p>
      <SubsampleSettings view={view} rows={rows} issue={issue} />
      <h4 className="fa-extrapolation__heading">{t('subItems')}</h4>
      {issue('items') ? <p className="fa-extrapolation__error">{issue('items')}</p> : null}
      <div className="fa-extrapolation__scroll">
        <table className="fa-extrapolation__grid" data-testid="extrapolation-subsample-items">
          <thead>
            <tr>
              {SUB_ITEM_FIELDS.map((field) => <th key={field.key} scope="col">{t(field.label)}</th>)}
              <th scope="col">{t('exhaustive')}</th>
              <th scope="col">{t('remove')}</th>
            </tr>
          </thead>
          <tbody>
            {rows.items.map((item, position) => <ItemLine key={item.key} view={view} item={item} position={position} issue={issue} />)}
          </tbody>
        </table>
      </div>
      <div className="fa-extrapolation__actions">
        <Button size="sm" icon="plus" testId="extrapolation-add-subitem" onClick={controller.addSubItem}>{t('addSubItem')}</Button>
        <Button size="sm" variant="ghost" testId="extrapolation-subsample-close" onClick={() => controller.editSubsample(null)}>{t('close')}</Button>
      </div>
    </section>
  )
}
