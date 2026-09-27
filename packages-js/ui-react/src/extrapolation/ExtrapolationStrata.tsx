import { extrapolationCellLabel, extrapolationIssueText, STRATUM_FIELDS, type StratumRow } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { classes, useElementId } from '../store'
import type { UseExtrapolation } from './useExtrapolation'

function StratumLine({ view, row, index }: { view: UseExtrapolation; row: StratumRow; index: number }) {
  const { state, controller, t } = view
  const part = state.form.design === 'periods' ? 'period' : 'group'
  const partIssue = extrapolationIssueText(state.issues, `strata.${index}.part`, t)
  const groupIssue = extrapolationIssueText(state.issues, `strata.${index}.group`, t)
  return (
    <tr>
      {state.form.design !== 'single' ? (
        <td>
          <input className="fa-extrapolation__input" value={row.part} aria-label={extrapolationCellLabel(t, part, index + 1)} aria-invalid={partIssue ? 'true' : undefined} title={partIssue || undefined} onChange={(event) => controller.updateStratum(index, { part: event.target.value })} />
        </td>
      ) : null}
      {state.form.design === 'periods' ? (
        <td>
          <input className="fa-extrapolation__input" value={row.group} aria-label={extrapolationCellLabel(t, 'groupOptional', index + 1)} aria-invalid={groupIssue ? 'true' : undefined} title={groupIssue || undefined} onChange={(event) => controller.updateStratum(index, { group: event.target.value })} />
        </td>
      ) : null}
      {STRATUM_FIELDS.map((field) => {
        const issue = extrapolationIssueText(state.issues, `strata.${index}.${field.key}`, t)
        return (
          <td key={field.key}>
            <input
              className={classes('fa-extrapolation__input', field.numeric && 'fa-extrapolation__input--number')}
              inputMode={field.numeric ? 'decimal' : undefined}
              value={row[field.key]}
              aria-label={extrapolationCellLabel(t, field.label, index + 1)}
              aria-invalid={issue ? 'true' : undefined}
              title={issue || undefined}
              onChange={(event) => controller.updateStratum(index, { [field.key]: event.target.value })}
            />
          </td>
        )
      })}
      <td>
        <Button size="sm" variant="ghost" icon="trash" iconOnly label={t('removeRow', { what: t('stratumName'), row: index + 1 })} disabled={state.form.strata.length <= 1} onClick={() => controller.removeStratum(index)} />
      </td>
    </tr>
  )
}

/** Schichten der Grundgesamtheit als bearbeitbare Tabelle (wie `ExtrapolationStrata.vue`). */
export function ExtrapolationStrata({ view }: { view: UseExtrapolation }) {
  const { state, controller, t } = view
  const id = useElementId('fa-extrapolation-strata')
  return (
    <section className="fa-extrapolation__card" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className="fa-extrapolation__heading">{t('strata')}</h3>
      <p className="fa-extrapolation__hint">{t('strataHint')}</p>
      <div className="fa-extrapolation__scroll">
        <table className="fa-extrapolation__grid" data-testid="extrapolation-strata">
          <thead>
            <tr>
              {state.form.design !== 'single' ? <th scope="col">{t(state.form.design === 'periods' ? 'period' : 'group')}</th> : null}
              {state.form.design === 'periods' ? <th scope="col">{t('groupOptional')}</th> : null}
              {STRATUM_FIELDS.map((field) => <th key={field.key} scope="col">{t(field.label)}</th>)}
              <th scope="col">{t('remove')}</th>
            </tr>
          </thead>
          <tbody>
            {state.form.strata.map((row, index) => <StratumLine key={row.key} view={view} row={row} index={index} />)}
          </tbody>
        </table>
      </div>
      <div className="fa-extrapolation__actions">
        <Button size="sm" icon="plus" testId="extrapolation-add-stratum" onClick={controller.addStratum}>{t('addStratum')}</Button>
      </div>
    </section>
  )
}
