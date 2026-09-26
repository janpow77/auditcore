import { extrapolationCellLabel, extrapolationIssueText, UNIT_FIELDS, UNIT_FLAGS, type UnitRow } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { classes, useElementId } from '../store'
import type { UseExtrapolation } from './useExtrapolation'

function UnitLine({ view, row, index, names }: { view: UseExtrapolation; row: UnitRow; index: number; names: readonly string[] }) {
  const { state, controller, t } = view
  const issue = (key: string): string => extrapolationIssueText(state.issues, `units.${index}.${key}`, t)
  return (
    <tr>
      <td>
        <select className="fa-extrapolation__select" value={row.stratum} aria-label={extrapolationCellLabel(t, 'stratum', index + 1)} aria-invalid={issue('stratum') ? 'true' : undefined} onChange={(event) => controller.updateUnit(index, { stratum: event.target.value })}>
          <option value="">{t('choose')}</option>
          {names.map((name) => <option key={name} value={name}>{name}</option>)}
        </select>
      </td>
      {UNIT_FIELDS.map((field) => (
        <td key={field.key}>
          <input
            className={classes('fa-extrapolation__input', field.numeric && 'fa-extrapolation__input--number')}
            inputMode={field.numeric ? 'decimal' : undefined}
            value={row[field.key]}
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
  const names = state.form.strata.map((row) => row.name.trim()).filter(Boolean)
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
                <th scope="col">{t('stratum')}</th>
                {UNIT_FIELDS.map((field) => <th key={field.key} scope="col">{t(field.label)}</th>)}
                {UNIT_FLAGS.map((flag) => <th key={flag.key} scope="col">{t(flag.label)}</th>)}
                <th scope="col">{t('remove')}</th>
              </tr>
            </thead>
            <tbody>
              {state.form.units.map((row, index) => <UnitLine key={row.key} view={view} row={row} index={index} names={names} />)}
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
