import type { ChangeEvent } from 'react'
import { bandTone, toggleMeasure, type DataProtectionProfile, type LevelView, type ScenarioInput, type ScenarioResult } from '@auditcore/ui-core'
import { Badge } from '../../base/Badge'
import { Button } from '../../base/Button'
import { classes, useElementId } from '../../store'
import { useDataProtectionText } from '../shared'

export interface DsfaScenarioProps {
  profile: DataProtectionProfile
  scenario: ScenarioInput
  index: number
  result?: ScenarioResult | null
  readonly?: boolean
  onScenarioChange: (scenario: ScenarioInput) => void
  onRemove: () => void
}

type Risk = DataProtectionProfile['risk']

const level = (event: ChangeEvent<HTMLSelectElement>): number | null => (event.target.value === '' ? null : Number(event.target.value))

function Levels({ levels }: { levels: readonly LevelView[] }) {
  return <>{levels.map((entry) => <option key={entry.value} value={entry.value}>{`${entry.value} – ${entry.label}`}</option>)}</>
}

function Base({ id, risk, props, patch }: { id: string; risk: Risk; props: DsfaScenarioProps; patch: (changes: Partial<ScenarioInput>) => void }) {
  const { t } = useDataProtectionText()
  const { scenario } = props
  return (
    <div className="fa-dataprotection__grid">
      <div className="fa-dataprotection__field">
        <label htmlFor={`${id}-dim`}>{t('dimension')}</label>
        <select id={`${id}-dim`} value={scenario.dimension} onChange={(event) => patch({ dimension: event.target.value })}>
          {risk.dimensions.map((dimension) => <option key={dimension.key} value={dimension.key}>{dimension.title}</option>)}
        </select>
      </div>
      <div className="fa-dataprotection__field fa-dataprotection__field--required">
        <label htmlFor={`${id}-text`}>{t('description')}</label>
        <textarea id={`${id}-text`} rows={2} value={scenario.description} onChange={(event) => patch({ description: event.target.value })} />
      </div>
      <div className="fa-dataprotection__field">
        <label htmlFor={`${id}-sev`}>{t('severity')}</label>
        <select id={`${id}-sev`} value={scenario.severity} onChange={(event) => patch({ severity: level(event) ?? scenario.severity })}>
          <Levels levels={risk.severity_levels} />
        </select>
      </div>
      <div className="fa-dataprotection__field">
        <label htmlFor={`${id}-lik`}>{t('likelihood')}</label>
        <select id={`${id}-lik`} value={scenario.likelihood} onChange={(event) => patch({ likelihood: level(event) ?? scenario.likelihood })}>
          <Levels levels={risk.likelihood_levels} />
        </select>
      </div>
    </div>
  )
}

function Measures({ risk, props }: { risk: Risk; props: DsfaScenarioProps }) {
  const { t } = useDataProtectionText()
  return (
    <fieldset className="fa-dataprotection__field">
      <legend>{t('measures')}</legend>
      <ul className="fa-dsfa__measures">
        {risk.measures.map((measure) => (
          <li key={measure.key}>
            <label className="fa-dataprotection__choice">
              <input type="checkbox" checked={props.scenario.measures.includes(measure.key)} onChange={() => props.onScenarioChange(toggleMeasure(props.scenario, measure.key))} /> {measure.title}
            </label>
          </li>
        ))}
      </ul>
    </fieldset>
  )
}

function Residual({ id, risk, scenario, patch }: { id: string; risk: Risk; scenario: ScenarioInput; patch: (changes: Partial<ScenarioInput>) => void }) {
  const { t } = useDataProtectionText()
  const residual = scenario.residual_severity !== null || scenario.residual_likelihood !== null
  return (
    <details open={residual}>
      <summary>{t('residual')}</summary>
      <div className="fa-dataprotection__grid">
        <div className="fa-dataprotection__field">
          <label htmlFor={`${id}-rsev`}>{t('residualSeverity')}</label>
          <select id={`${id}-rsev`} value={scenario.residual_severity ?? ''} onChange={(event) => patch({ residual_severity: level(event) })}>
            <option value="">{t('computed')}</option>
            <Levels levels={risk.severity_levels} />
          </select>
        </div>
        <div className="fa-dataprotection__field">
          <label htmlFor={`${id}-rlik`}>{t('residualLikelihood')}</label>
          <select id={`${id}-rlik`} value={scenario.residual_likelihood ?? ''} onChange={(event) => patch({ residual_likelihood: level(event) })}>
            <option value="">{t('computed')}</option>
            <Levels levels={risk.likelihood_levels} />
          </select>
        </div>
      </div>
      <div className={classes('fa-dataprotection__field', residual && 'fa-dataprotection__field--required')}>
        <label htmlFor={`${id}-why`}>{t('residualJustification')}</label>
        <textarea id={`${id}-why`} rows={2} value={scenario.residual_justification} onChange={(event) => patch({ residual_justification: event.target.value })} />
      </div>
    </details>
  )
}

function Result({ risk, props }: { risk: Risk; props: DsfaScenarioProps }) {
  const { t } = useDataProtectionText()
  const { result } = props
  return (
    <div className="fa-dsfa__result">
      {result ? (
        <>
          <Badge tone={bandTone(result.gross_band, risk.bands)}>{result.gross_band}</Badge>
          <span aria-hidden="true">→</span>
          <Badge tone={bandTone(result.net_band, risk.bands)}>{result.net_band}</Badge>
          <span>{t('scenarioResult', { gross: result.gross, grossBand: result.gross_band, net: result.net, netBand: result.net_band })}</span>
        </>
      ) : null}
      {props.readonly ? null : (
        <Button className="fa-dataprotection__actions" variant="ghost" size="sm" icon="trash" label={t('removeScenario', { index: props.index + 1 })} onClick={props.onRemove} />
      )}
    </div>
  )
}

/** Ein Risikoszenario mit Schwere, Wahrscheinlichkeit, Maßnahmen und optionalem Restrisiko. */
export function DsfaScenario(props: DsfaScenarioProps) {
  const { t } = useDataProtectionText()
  const id = useElementId('fa-dsfa-s')
  const risk = props.profile.risk
  const patch = (changes: Partial<ScenarioInput>): void => props.onScenarioChange({ ...props.scenario, ...changes })
  return (
    <fieldset className="fa-dsfa__scenario" disabled={!!props.readonly} data-scenario={props.index}>
      <legend className="fa-dataprotection__label">{t('scenario', { index: props.index + 1 })}</legend>
      <Base id={id} risk={risk} props={props} patch={patch} />
      <Measures risk={risk} props={props} />
      <Residual id={id} risk={risk} scenario={props.scenario} patch={patch} />
      <Result risk={risk} props={props} />
    </fieldset>
  )
}
