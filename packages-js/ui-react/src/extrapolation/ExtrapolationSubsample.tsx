import { extrapolationIssueText, subsampleEditorView, subsampleEstimatorChoices, type SubsampleEditorView, type SubsampleEstimator } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { classes, useElementId } from '../store'
import { SubsampleItems, SubsampleStrata } from './ExtrapolationSubsampleParts'
import type { UseExtrapolation } from './useExtrapolation'

function SubsampleSettings({ view, editor }: { view: UseExtrapolation; editor: SubsampleEditorView }) {
  const { state, controller, t } = view
  const issue = (key: string): string => extrapolationIssueText(state.issues, `${editor.prefix}.${key}`, t)
  return (
    <div className="fa-extrapolation__settings">
      <label className="fa-extrapolation__field">
        <span className="fa-extrapolation__label">{t('estimator')}</span>
        <select className="fa-extrapolation__select" value={editor.rows.estimator} data-testid="extrapolation-subsample-estimator" onChange={(event) => controller.updateSubsample({ estimator: event.target.value as SubsampleEstimator })}>
          {subsampleEstimatorChoices(t).map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
        </select>
      </label>
      {editor.rows.estimator === 'mean_per_unit' && editor.rows.strata.length === 0 ? (
        <label className="fa-extrapolation__field">
          <span className="fa-extrapolation__label">{t('subPopulation')}</span>
          <input className={classes('fa-extrapolation__input', 'fa-extrapolation__input--number')} inputMode="numeric" value={editor.rows.populationSize} aria-invalid={issue('populationSize') ? 'true' : undefined} data-testid="extrapolation-subsample-size" onChange={(event) => controller.updateSubsample({ populationSize: event.target.value })} />
          {issue('populationSize') ? <span className="fa-extrapolation__error">{issue('populationSize')}</span> : null}
        </label>
      ) : null}
    </div>
  )
}

/** Teilstichprobe der gewählten Einheit bzw. Teileinheit (wie `ExtrapolationSubsample.vue`; Leitfaden 7.6, 6.5.3). */
export function ExtrapolationSubsample({ view }: { view: UseExtrapolation }) {
  const { state, controller, t } = view
  const id = useElementId('fa-extrapolation-subsample')
  const editor = subsampleEditorView(state, t)
  if (!editor) return null
  return (
    <section className="fa-extrapolation__card" aria-labelledby={`${id}-title`} data-testid="extrapolation-subsample">
      <h3 id={`${id}-title`} className="fa-extrapolation__heading">{editor.title}</h3>
      <p className="fa-extrapolation__hint">{t('subsampleHint')}</p>
      <SubsampleSettings view={view} editor={editor} />
      <SubsampleStrata view={view} editor={editor} />
      <SubsampleItems view={view} editor={editor} />
      <div className="fa-extrapolation__actions">
        <Button size="sm" icon="plus" testId="extrapolation-add-subitem" onClick={controller.addSubItem}>{t('addSubItem')}</Button>
        {editor.nested ? <Button size="sm" variant="ghost" testId="extrapolation-subsample-back" onClick={() => controller.editNestedSubsample(null)}>{t('backToUnit')}</Button> : null}
        <Button size="sm" variant="ghost" testId="extrapolation-subsample-close" onClick={() => controller.editSubsample(null)}>{t('close')}</Button>
      </div>
    </section>
  )
}
