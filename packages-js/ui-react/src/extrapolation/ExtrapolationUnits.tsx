import { extrapolationCellLabel, extrapolationIssueText, periodNames, UNIT_FIELDS, UNIT_FLAGS, type ExtrapolationData, type UnitRow } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { classes, useElementId } from '../store'
import type { UseExtrapolation } from './useExtrapolation'

function namesFor(state: ExtrapolationData, period: string): string[] {
  const periodic = state.form.design === 'periods'
  return [...new Set(state.form.strata.filter((row) => !periodic || row.part.trim() === period.trim()).map((row) => row.name.trim()).filter(Boolean))]
}

function SubsampleCell({ view, row, index }: { view: UseExtrapolation; row: UnitRow; index: number }) {
  const { controller, t } = view
  return (
    <td className="fa-extrapolation__nowrap">
      {row.subsample ? (
        <>
          <Button size="sm" variant="ghost" icon="edit" iconOnly label={t('subsampleOpen', { row: index + 1 })} onClick={() => controller.editSubsample(index)} />
          <Button size="sm" variant="ghost" icon="trash" iconOnly label={t('subsampleDrop', { row: index + 1 })} onClick={() => controller.toggleSubsample(index)} />
        </>
      ) : (
        <Button size="sm" variant="ghost" icon="plus" iconOnly label={t('subsampleCreate', { row: index + 1 })} onClick={() => controller.toggleSubsample(index)} />
      )}
    </td>
  )
}

function UnitLine({ view, row, index, periods }: { view: UseExtrapolation; row: UnitRow; index: number; periods: readonly string[] }) {
  const { state, controller, t } = view
  const issue = (key: string): string => extrapolationIssueText(state.issues, `units.${index}.${key}`, t)
  return (
    <tr>
      {state.form.design === 'periods' ? (
        <td>
          <select className="fa-extrapolation__select" value={row.period} aria-label={extrapolationCellLabel(t, 'period', index + 1)} onChange={(event) => controller.updateUnit(index, { period: event.target.value })}>
            <option value="">{t('choose')}</option>
            {periods.map((name) => <option key={name} value={name}>{name}</option>)}
          </select>
        </td>
      ) : null}
      <td>
        <select className="fa-extrapolation__select" value={row.stratum} aria-label={extrapolationCellLabel(t, 'stratum', index + 1)} aria-invalid={issue('stratum') ? 'true' : undefined} onChange={(event) => controller.updateUnit(index, { stratum: event.target.value })}>
          <option value="">{t('choose')}</option>
          {namesFor(state, row.period).map((name) => <option key={name} value={name}>{name}</option>)}
        </select>
      </td>
      {UNIT_FIELDS.map((field) => (
        <td key={field.key}>
          <input
            className={classes('fa-extrapolation__input', field.numeric && 'fa-extrapolation__input--number')}
            inputMode={field.numeric ? 'decimal' : undefined}
            value={field.key === 'random' && row.subsample ? t('fromSubsample') : row[field.key]}
            disabled={field.key === 'random' && row.subsample !== null}
            aria-label={extrapolationCellLabel(t, field.label, index + 1)}
            aria-invalid={issue(field.key) ? 'true' : undefined}
            title={issue(field.key) || undefined}
            onChange={(event) => controller.updateUnit(index, { [field.key]: event.target.value })}
          />
        </td>
      ))}
      {UNIT_FLAGS.map((flag) => (
        <td key={flag.key}>
          <input type="checkbox" className="fa-extrapolation__check" checked={row[flag.key]} aria-label={extrapolationCellLabel(t, flag.label, index + 1)} onChange={(event) => controller.updateUnit(index, { [flag.key]: event.target.checked })} />
        </td>
      ))}
      <SubsampleCell view={view} row={row} index={index} />
      <td>
        <Button size="sm" variant="ghost" icon="trash" iconOnly label={t('removeRow', { what: t('unitId'), row: index + 1 })} onClick={() => controller.removeUnit(index)} />
      </td>
    </tr>
  )
}

/** Geprüfte Einheiten mit Fehlerklassen als bearbeitbare Tabelle (wie `ExtrapolationUnits.vue`). */
export function ExtrapolationUnits({ view }: { view: UseExtrapolation }) {
  const { state, controller, t } = view
  const id = useElementId('fa-extrapolation-units')
  const periods = periodNames(state.form.strata.map((row) => row.part))
  return (
    <section className="fa-extrapolation__card" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className="fa-extrapolation__heading">{t('units')}</h3>
      <p className="fa-extrapolation__hint">{t('unitsHint')}</p>
      {state.form.units.length === 0 ? (
        <p className="fa-extrapolation__muted">{t('noUnits')}</p>
      ) : (
        <div className="fa-extrapolation__scroll">
          <table className="fa-extrapolation__grid" data-testid="extrapolation-units">
            <thead>
              <tr>
                {state.form.design === 'periods' ? <th scope="col">{t('period')}</th> : null}
                <th scope="col">{t('stratum')}</th>
                {UNIT_FIELDS.map((field) => <th key={field.key} scope="col">{t(field.label)}</th>)}
                {UNIT_FLAGS.map((flag) => <th key={flag.key} scope="col">{t(flag.label)}</th>)}
                <th scope="col">{t('subsample')}</th>
                <th scope="col">{t('remove')}</th>
              </tr>
            </thead>
            <tbody>
              {state.form.units.map((row, index) => <UnitLine key={row.key} view={view} row={row} index={index} periods={periods} />)}
            </tbody>
          </table>
        </div>
      )}
      <div className="fa-extrapolation__actions">
        <Button size="sm" icon="plus" testId="extrapolation-add-unit" onClick={controller.addUnit}>{t('addUnit')}</Button>
      </div>
    </section>
  )
}
