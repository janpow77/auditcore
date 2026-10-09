import { useEffect, useRef, useState } from 'react'
import {
  assistantView,
  createAssistantController,
  dataprotectionMessages,
  draftOf,
  questionFieldId,
  type AssistantController,
  type AssistantData,
  type AssistantMode,
  type AssistantPort,
  type AssistantTab,
  type AssistantView,
  type DataProtectionError,
  type DataProtectionTranslate,
  type Locale,
  type WorkspaceOverview,
} from '@auditcore/ui-core'
import { LocaleProvider, useTranslation } from '../i18n'
import { useStoreState } from '../store'
import { AssistantChecklist } from './assistant/AssistantChecklist'
import { AssistantQuestion } from './assistant/AssistantQuestion'
import { AssistantStatus } from './assistant/AssistantStatus'
import { AssistantSteps } from './assistant/AssistantSteps'
import { prefixedLabel } from './shared'

export interface FlowauditDatenschutzAssistentProps {
  /** Datenzugang, z. B. `createAssistantRestPort({ baseUrl: '/api/dataprotection' })`. */
  port?: AssistantPort | null
  /** Kennung der Verarbeitungstätigkeit im Verzeichnis. */
  activityId?: string
  locale?: Locale
  className?: string
  onChange?: (detail: WorkspaceOverview) => void
  onError?: (detail: DataProtectionError) => void
}

const TABS: AssistantTab[] = ['assistent', 'checkliste', 'status']
const TAB_TEXT = { assistent: 'tabAssistant', checkliste: 'tabChecklist', status: 'tabStatus' } as const

function useAssistant(props: FlowauditDatenschutzAssistentProps) {
  const { t, locale } = useTranslation(dataprotectionMessages, props.locale)
  const latest = useRef({ t, props })
  latest.current = { t, props }
  const [controller] = useState(() =>
    createAssistantController({
      port: () => latest.current.props.port ?? null,
      activityId: () => latest.current.props.activityId ?? '',
      t: () => latest.current.t,
      onChange: (overview) => latest.current.props.onChange?.(overview),
      onError: (error) => latest.current.props.onError?.(error),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    if (props.port && props.activityId) void controller.load()
  }, [controller, props.port, props.activityId])
  return { t, locale, controller, state, view: assistantView(state) }
}

interface PartProps {
  controller: AssistantController
  state: AssistantData
  view: AssistantView
  t: DataProtectionTranslate
}

function StepPanel({ controller, state, view, t }: PartProps) {
  const heading = useRef<HTMLHeadingElement | null>(null)
  const shown = useRef(view.step?.id)
  // Fokus auf die Schrittüberschrift, wenn der Schritt wechselt (Tastatur, Screenreader).
  useEffect(() => {
    if (shown.current && shown.current !== view.step?.id) heading.current?.focus()
    shown.current = view.step?.id
  }, [view.step?.id])
  const busy = !!state.busy
  const step = view.step
  if (!step) return null
  const hidden = state.overview?.assistent.hidden_answers ?? []
  return (
    <div>
      <h3 ref={heading} tabIndex={-1}>{t('stepOf', { position: view.position, total: view.steps.length })}: {step.title}</h3>
      <p className="fa-dataprotection__muted">{step.goal} <span className="fa-assistant__badge">{prefixedLabel(t, 'stepStatus', step.status)}</span></p>
      {hidden.length ? <p className="fa-dataprotection__alert fa-dataprotection__alert--info">{t('hiddenAnswers', { ids: hidden.join(', ') })}</p> : null}
      {step.questions.map((question) => (
        <AssistantQuestion
          key={question.id}
          question={question}
          draft={draftOf(state, question)}
          error={state.fieldErrors[question.id]}
          busy={busy}
          onChange={(draft) => controller.setDraft(question.id, draft)}
          onSave={() => void controller.answer(question.id)}
          onConfirm={() => void controller.confirm(question.id)}
        />
      ))}
      <div className="fa-assistant__nav">
        <button type="button" disabled={busy || !view.previous} onClick={() => void controller.previous()}>{t('previousStep')}</button>
        <button type="button" disabled={busy || !view.next} onClick={() => void controller.next()}>{t('nextStep')}</button>
      </div>
    </div>
  )
}

function AssistantPanel(props: PartProps) {
  const { controller, state, view, t } = props
  const busy = !!state.busy
  return (
    <div className="fa-assistant__layout" role="tabpanel">
      <div>
        <label>
          {t('modeLabel')}{' '}
          <select value={view.mode} disabled={busy} onChange={(event) => void controller.setMode(event.target.value as AssistantMode)}>
            <option value="gefuehrt">{t('mode_gefuehrt')}</option>
            <option value="frei">{t('mode_frei')}</option>
          </select>
        </label>
        <p className="fa-dataprotection__muted">{t('stepsDone', { done: view.completed, total: view.steps.length })}</p>
        <AssistantSteps view={view} busy={busy} onSelect={(step) => void controller.goTo(step)} />
      </div>
      <StepPanel {...props} />
    </div>
  )
}

function Errors({ state, t }: { state: AssistantData; t: DataProtectionTranslate }) {
  const errors = Object.entries(state.fieldErrors)
  if (!errors.length) return null
  return (
    <div className="fa-dataprotection__alert" role="alert">
      {t('errorSummary')}
      <ul>
        {errors.map(([id, message]) => (
          <li key={id}><a href={`#${questionFieldId({ id })}`}>{t('goToField', { id })}</a>: {message}</li>
        ))}
      </ul>
    </div>
  )
}

function Workspace(props: PartProps & { overview: WorkspaceOverview }) {
  const { controller, state, t, overview } = props
  const tasks = overview.assistent.tasks
  return (
    <>
      <p className="fa-dataprotection__muted">{t('assistantIntro')}</p>
      <div className="fa-assistant__tabs" role="tablist" aria-label={t('tabsLabel')}>
        {TABS.map((tab) => (
          <button key={tab} type="button" role="tab" aria-selected={state.tab === tab} onClick={() => controller.setTab(tab)}>{t(TAB_TEXT[tab])}</button>
        ))}
      </div>
      <Errors state={state} t={t} />
      {state.tab === 'assistent' ? <AssistantPanel {...props} /> : null}
      {state.tab === 'checkliste' ? <AssistantChecklist items={overview.pruefpunkte} busy={!!state.busy} onChange={(id, change) => void controller.changeItem(id, change)} /> : null}
      {state.tab === 'status' ? <AssistantStatus axes={overview.status} gates={overview.sperren} /> : null}
      <section className="fa-dataprotection__panel" aria-label={t('tasksTitle', { count: tasks.length })}>
        <h3>{t('tasksTitle', { count: tasks.length })}</h3>
        <ul>{tasks.map((task) => <li key={task.question}>{task.question} – {prefixedLabel(t, 'task', task.kind)}</li>)}</ul>
      </section>
    </>
  )
}

/**
 * Datenschutz-Assistent als native React-Komponente (Vertrag wie
 * `<flowaudit-datenschutz-assistent>`): auf Wunsch geführt Schritt für Schritt,
 * sonst frei; Checkliste, getrennte Status und Sperren aus dem Backend.
 */
export function FlowauditDatenschutzAssistent(props: FlowauditDatenschutzAssistentProps) {
  const { t, locale, controller, state, view } = useAssistant(props)
  const overview = state.overview
  const fieldErrors = Object.keys(state.fieldErrors).length
  return (
    <LocaleProvider locale={locale}>
      <section className={props.className ? `fa-dataprotection fa-assistant ${props.className}` : 'fa-dataprotection fa-assistant'} aria-busy={!!state.busy} data-testid="assistant">
        <header className="fa-dataprotection__header">
          <h2>{t('assistantTitle')}</h2>
          {overview ? <span className="fa-dataprotection__muted">{t('profile', { id: overview.profil.id, version: overview.profil.version })}</span> : null}
        </header>
        {!props.port ? <p className="fa-dataprotection__alert" role="alert">{t('noPort')}</p> : null}
        {props.port && !props.activityId ? <p className="fa-dataprotection__alert" role="alert">{t('noActivity')}</p> : null}
        {state.error && !fieldErrors ? <p className="fa-dataprotection__alert" role="alert">{state.error.message}</p> : null}
        <p className="fa-dataprotection__live" aria-live="polite">{state.busy === 'load' ? t('loading') : state.notice}</p>
        {overview ? <Workspace controller={controller} state={state} view={view} t={t} overview={overview} /> : null}
      </section>
    </LocaleProvider>
  )
}
