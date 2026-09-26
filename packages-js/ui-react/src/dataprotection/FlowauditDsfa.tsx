import { useEffect, useRef, useState } from 'react'
import {
  createDsfaController,
  dataprotectionMessages,
  dsfaDerived,
  dsfaReadonly,
  dsfaTabs,
  type AssessmentView,
  type DataProtectionError,
  type DataProtectionPort,
  type DataProtectionProfile,
  type DataProtectionTranslate,
  type DsfaController,
  type DsfaData,
  type DsfaStep,
  type Locale,
  type Proposal,
  type SurveyInput,
} from '@auditcore/ui-core'
import { LocaleProvider, useTranslation } from '../i18n'
import { useStoreState } from '../store'
import { DsfaDecision } from './dsfa/DsfaDecision'
import { DsfaHead } from './dsfa/DsfaHead'
import { DsfaOverview } from './dsfa/DsfaOverview'
import { DsfaProposal } from './dsfa/DsfaProposal'
import { DsfaRisk } from './dsfa/DsfaRisk'
import { DsfaScreening } from './dsfa/DsfaScreening'
import { DsfaTabs } from './dsfa/DsfaTabs'
import { DsfaVersions } from './dsfa/DsfaVersions'

export interface FlowauditDsfaProps {
  /** Datenzugang (Vertrag dataprotection_ui/1), z. B. `createDataProtectionRestPort({ baseUrl: '/api/dataprotection' })`. */
  port?: DataProtectionPort | null
  /** Beim Laden zu öffnende Tätigkeit (Kennung aus dem Verzeichnis). */
  activityId?: string
  /** Kennung der angemeldeten Person; nur für den Vier-Augen-Hinweis, geprüft wird auf dem Server. */
  actor?: string
  editable?: boolean
  locale?: Locale
  className?: string
  onAssessmentChange?: (detail: { step: DsfaStep; id: string; version: number; status: string }) => void
  onError?: (error: DataProtectionError) => void
}

interface Opened {
  view: AssessmentView
  profile: DataProtectionProfile
  survey: SurveyInput
  proposal: Proposal
}

function useController(props: FlowauditDsfaProps, t: DataProtectionTranslate): DsfaController {
  const latest = useRef({ props, t })
  latest.current = { props, t }
  const [controller] = useState(() =>
    createDsfaController({
      port: () => latest.current.props.port ?? null,
      t: () => latest.current.t,
      onChanged: (step, view) => latest.current.props.onAssessmentChange?.({ step, id: view.id, version: view.version, status: view.status }),
      onError: (error) => latest.current.props.onError?.(error),
    }),
  )
  useEffect(() => {
    if (props.port) void controller.connect(latest.current.props.activityId ?? '')
  }, [controller, props.port])
  useEffect(() => () => controller.dispose(), [controller])
  return controller
}

function opened(state: DsfaData): Opened | null {
  const proposal = dsfaDerived(state).proposal
  const { view, profile, survey } = state
  return view && profile && survey && proposal ? { view, profile, survey, proposal } : null
}

function Assessment({ open, state, controller, props }: { open: Opened; state: DsfaData; controller: DsfaController; props: FlowauditDsfaProps }) {
  const { t } = useTranslation(dataprotectionMessages)
  const editable = props.editable ?? true
  const derived = dsfaDerived(state)
  const readonly = dsfaReadonly(state, editable)
  const survey = { profile: open.profile, survey: open.survey, proposal: open.proposal, preview: derived.showPreview, readonly, onSurveyChange: controller.edit }
  return (
    <>
      <DsfaHead view={open.view} dirty={derived.dirty} readonly={readonly} editable={editable} busy={state.busy} controller={controller} />
      <DsfaTabs tabs={dsfaTabs(t)} active={state.tab} label={t('steps')} onTabChange={controller.setTab}>
        {state.tab === 'screening' ? <DsfaScreening {...survey} /> : null}
        {state.tab === 'risk' ? <DsfaRisk {...survey} /> : null}
        {state.tab === 'result' ? (
          <>
            <DsfaProposal profile={open.profile} proposal={open.proposal} preview={derived.showPreview} openPoints={open.view.locked ? [] : open.view.open_points} />
            <DsfaDecision
              profile={open.profile}
              view={open.view}
              proposal={open.proposal}
              dirty={derived.dirty}
              actor={props.actor ?? ''}
              busy={state.busy}
              onDecide={(decision) => void controller.decide(decision)}
              onDpoRequest={(from, on) => void controller.requestDpo(from, on)}
              onRelease={() => void controller.release()}
            />
          </>
        ) : null}
      </DsfaTabs>
      <DsfaVersions versions={open.view.versions} profile={open.profile} current={open.view.id} onOpen={(id) => void controller.open(id)} />
    </>
  )
}

/**
 * Datenschutz-Folgenabschätzung (Art. 35 DSGVO) als native React-Komponente –
 * Vertrag, Texte und Ablauf wie `<flowaudit-dsfa>`: Übersicht, Schwellwertanalyse,
 * Risiko, Vorschlag der Bibliothek, Entscheidung, DSB-Stellungnahme, Freigabe.
 */
export function FlowauditDsfa(props: FlowauditDsfaProps) {
  const { t, locale } = useTranslation(dataprotectionMessages, props.locale)
  const controller = useController(props, t)
  const state = useStoreState(controller.store)
  const open = opened(state)
  const profile = state.profile
  return (
    <LocaleProvider locale={locale}>
      <section className={props.className ? `fa-dataprotection fa-dsfa ${props.className}` : 'fa-dataprotection fa-dsfa'} aria-busy={!!state.busy} data-testid="dsfa">
        <header className="fa-dataprotection__header">
          <h2>{t('dsfaTitle')} <span className="fa-dataprotection__muted">{t('dsfaNorm')}</span></h2>
          {profile ? <span className="fa-dataprotection__muted">{t('profile', { id: profile.profile.id, version: profile.profile.version })}</span> : null}
        </header>
        {props.port ? null : <p className="fa-dataprotection__alert" role="alert">{t('noPort')}</p>}
        {state.error ? <p className="fa-dataprotection__alert" role="alert">{state.error.message}</p> : null}
        <p className="fa-dataprotection__live" aria-live="polite">{state.busy === 'load' ? t('loading') : state.notice}</p>
        <DsfaOverview rows={state.rows} profile={profile} selected={state.view?.id ?? null} editable={props.editable ?? true} busy={!!state.busy} onOpen={(id) => void controller.open(id)} onStart={(id) => void controller.start(id)} />
        {open ? <Assessment open={open} state={state} controller={controller} props={props} /> : null}
      </section>
    </LocaleProvider>
  )
}
