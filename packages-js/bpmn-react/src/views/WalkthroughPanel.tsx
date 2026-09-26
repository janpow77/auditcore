/**
 * Walk-through test: go through the diagram step by step, record per step
 * case, voucher, result and remark (`flowaudit:pruefschritt`); key controls
 * of the step with sample size for the control test. Steps are highlighted
 * in the diagram (current, met, not met).
 */

import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { nextStepId, recordStep, walkthroughProgress, walkthroughSteps, type AuditStep, type FlowauditHighlight } from '@flowaudit/bpmn-flowaudit'
import { clampStep, progressPercent, stepDraft, WALK_FIELDS, walkthroughClasses } from '@flowaudit/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { useEditorContext, useEditorState } from '../context'
import { useI18n } from '../i18n'
import { FieldForm } from '../panels/FieldForm'
import { useOptions } from '../panels/useOptions'
import { CurrentStep } from './WalkthroughStep'

type Step = ReturnType<typeof walkthroughSteps>[number]

function useSteps(): Step[] {
  const { editor } = useEditorContext()
  const state = useEditorState()
  return useMemo(() => (state.ready && state.changes >= 0 ? walkthroughSteps(editor.model()) : []), [editor, state.ready, state.changes])
}

function useHighlight(steps: Step[], currentId: string | undefined): void {
  const { editor } = useEditorContext()
  const layer = () => editor.instance()?.get<FlowauditHighlight>('flowauditHighlight', false)
  useEffect(() => {
    if (editor.store.get().ready) layer()?.apply('walkthrough', walkthroughClasses(steps, currentId))
  })
  useEffect(() => () => editor.instance()?.get<FlowauditHighlight>('flowauditHighlight', false)?.clear('walkthrough'), [editor])
}

/** Selects the first step once (Vue: `go(0)` during setup). */
function useInitialSelection(steps: Step[]): void {
  const { editor } = useEditorContext()
  const done = useRef(false)
  useEffect(() => {
    if (done.current) return
    done.current = true
    if (steps[0]) editor.select(steps[0].elementId)
  }, [editor, steps])
}

export function WalkthroughPanel({ tester }: { tester?: string }) {
  const { editor, readonly } = useEditorContext()
  const { t } = useI18n()
  const optionsFor = useOptions()
  const steps = useSteps()
  const [index, setIndex] = useState(0)
  const [draft, setDraft] = useState<AuditStep>(() => stepDraft(tester))
  const current = steps[index]
  const progress = walkthroughProgress(steps)
  useHighlight(steps, current?.elementId)
  useInitialSelection(steps)

  const go = (step: number) => {
    const next = clampStep(step, steps.length)
    setIndex(next)
    setDraft(stepDraft(tester))
    const target = steps[next]
    if (target) editor.select(target.elementId)
  }
  const save = () => {
    if (!current) return
    recordStep(editor.access(), current.elementId, { id: nextStepId(editor.model()), ...draft })
    go(index + 1)
  }

  return (
    <section className="fa-walk" aria-label={t('walk.title')}>
      <p className="fa-help" role="status">{t('walk.progress', { ...progress })}</p>
      <div className="fa-walk__bar" style={{ '--done': progressPercent(progress) } as CSSProperties} aria-hidden="true" />
      {!steps.length ? <p className="fa-help">{t('walk.noSteps')}</p> : null}
      {steps.length && current ? (
        <>
          <CurrentStep step={current} index={index} count={steps.length} onGo={go} />
          <h3 className="fa-section__title fa-section">{t('walk.record')}</h3>
          <FieldForm value={draft as Record<string, unknown>} fields={WALK_FIELDS} optionsFor={optionsFor} disabled={readonly()} onUpdate={(value) => setDraft(value as AuditStep)} />
          <button type="button" className="fa-btn fa-btn--primary fa-section" disabled={readonly()} onClick={save}><FaIcon name="check" size={16} />{t('walk.record')}</button>
        </>
      ) : null}
      <ol className="fa-walk__list">
        {steps.map((step, position) => (
          <li key={step.elementId}>
            <button type="button" className="fa-menu-item" aria-current={position === index} onClick={() => go(position)}>
              <span className={`fa-walk__dot fa-walk__dot--${step.status}`} />
              {step.name}
            </button>
          </li>
        ))}
      </ol>
    </section>
  )
}
