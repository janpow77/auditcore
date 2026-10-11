import { axisValueLabel, type GateView, type StatusAxes } from '@auditcore/ui-core'
import { prefixedLabel, useDataProtectionText } from '../shared'

export function AssistantStatus({ axes, gates }: { axes: StatusAxes; gates: GateView[] }) {
  const { t } = useDataProtectionText()
  return (
    <section className="fa-dataprotection__panel" data-testid="assistant-status" aria-labelledby="fa-assistant-axes" role="tabpanel">
      <h3 id="fa-assistant-axes">{t('axesTitle')}</h3>
      <p className="fa-dataprotection__muted">{t('axesNotice')}</p>
      <dl className="fa-assistant__axes">
        {Object.entries(axes).map(([key, value]) => [
          <dt key={`${key}-t`}>{prefixedLabel(t, 'axis', key)}</dt>,
          <dd key={`${key}-d`}>{axisValueLabel(value)}</dd>,
        ])}
      </dl>
      <h3>{t('gatesTitle')}</h3>
      {gates.length ? (
        <ul>
          {gates.map((gate) => (
            <li key={gate.id} data-gate={gate.id}>
              <strong>{gate.id}</strong> – {gate.reason}
              <br />
              <span className="fa-dataprotection__muted">{t('gateRole', { role: gate.role })} · {t('gateNext', { step: gate.next_step })}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p>{t('noGates')}</p>
      )}
    </section>
  )
}
