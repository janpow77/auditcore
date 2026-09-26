/** Current step of the walk-through: navigation, key controls and recorded steps. */

import type { walkthroughSteps } from '@flowaudit/bpmn-flowaudit'
import { FaIcon } from '../base/FaIcon'
import { useI18n } from '../i18n'

type Step = ReturnType<typeof walkthroughSteps>[number]

export function CurrentStep({ step, index, count, onGo }: { step: Step; index: number; count: number; onGo: (index: number) => void }) {
  const { t } = useI18n()
  return (
    <>
      <div className="fa-walk__nav">
        <button type="button" className="fa-icon-btn" disabled={index === 0} aria-label={t('walk.previous')} onClick={() => onGo(index - 1)}><FaIcon name="step-back" /></button>
        <div className="fa-walk__current">
          <span className="fa-help">{index + 1} / {count}</span>
          <strong>{step.name}</strong>
          <span className="fa-badge">{t(`walk.status.${step.status}`)}</span>
        </div>
        <button type="button" className="fa-icon-btn" disabled={index >= count - 1} aria-label={t('walk.next')} onClick={() => onGo(index + 1)}><FaIcon name="step-forward" /></button>
      </div>
      {step.keyControls.length ? (
        <div className="fa-card fa-walk__controls">
          <h3 className="fa-section__title">{t('walk.keyControls')}</h3>
          {step.keyControls.map((control) => (
            <p key={control.id}>
              <FaIcon name="marker-schluesselkontrolle" size={14} /> {control.id} {control.label} <span className="fa-help">· {control.frequency}</span>
            </p>
          ))}
        </div>
      ) : null}
      <ul className="fa-walk__done">
        {step.steps.map((done) => <li key={done.id}>{done.id} · {done.case} · {done.result}</li>)}
      </ul>
    </>
  )
}
