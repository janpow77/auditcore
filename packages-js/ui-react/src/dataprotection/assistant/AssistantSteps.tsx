import { stepReachable, type AssistantView } from '@auditcore/ui-core'
import { prefixedLabel, useDataProtectionText } from '../shared'

export function AssistantSteps({ view, busy, onSelect }: { view: AssistantView; busy: boolean; onSelect: (step: string) => void }) {
  const { t } = useDataProtectionText()
  return (
    <nav className="fa-assistant__steps" aria-label={t('stepsNav')}>
      <ol>
        {view.steps.map((step, index) => (
          <li key={step.id}>
            <button
              type="button"
              aria-current={step.id === view.step?.id ? 'step' : undefined}
              disabled={busy || !stepReachable(view, index)}
              onClick={() => onSelect(step.id)}
            >
              {index + 1}. {step.title} <span className="fa-assistant__badge">{prefixedLabel(t, 'stepStatus', step.status)}</span>
            </button>
          </li>
        ))}
      </ol>
    </nav>
  )
}
