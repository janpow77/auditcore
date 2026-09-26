import { useEffect, useRef, useState } from 'react'
import {
  createVvtController,
  dataprotectionMessages,
  deliverExport,
  vvtFourEyes,
  vvtView,
  type DataProtectionError,
  type DataProtectionTranslate,
  type DataProtectionPort,
  type Locale,
  type VvtController,
  type VvtData,
  type VvtExport,
  type VvtExportFormat,
  type VvtView,
} from '@auditcore/ui-core'
import { LocaleProvider, useTranslation } from '../i18n'
import { useStoreState } from '../store'
import { VvtActivityDetail } from './vvt/VvtActivityDetail'
import { VvtActivityList } from './vvt/VvtActivityList'
import { VvtCover } from './vvt/VvtCover'
import { VvtHistory } from './vvt/VvtHistory'
import { VvtIssues } from './vvt/VvtIssues'
import { VvtStatusBar } from './vvt/VvtStatusBar'

export interface FlowauditVvtProps {
  /** Datenzugang (Vertrag dataprotection_ui/1), z. B. `createDataProtectionRestPort({ baseUrl: '/api/dataprotection' })`. */
  port?: DataProtectionPort | null
  /** Kennung der angemeldeten Person; nur für den Vier-Augen-Hinweis, geprüft wird auf dem Server. */
  actor?: string
  /** `false`: nur Ansicht, keine Bearbeitung und Freigabe. */
  editable?: boolean
  locale?: Locale
  className?: string
  onDraftSaved?: (detail: { version: number; revision: number }) => void
  onReleased?: (detail: { version: number }) => void
  onExported?: (detail: VvtExport) => void
  onError?: (detail: DataProtectionError) => void
}

type Handlers = Pick<FlowauditVvtProps, 'onDraftSaved' | 'onReleased' | 'onError'>

function useVvt(props: FlowauditVvtProps) {
  const { t, locale } = useTranslation(dataprotectionMessages, props.locale)
  const editable = props.editable ?? true
  const latest = useRef({ t, editable, port: props.port ?? null, handlers: props as Handlers })
  latest.current = { t, editable, port: props.port ?? null, handlers: props }
  const [controller] = useState(() =>
    createVvtController({
      port: () => latest.current.port,
      t: () => latest.current.t,
      onSaved: (version) => latest.current.handlers.onDraftSaved?.({ version: version.version, revision: version.revision }),
      onReleased: (version) => latest.current.handlers.onReleased?.({ version: version.version }),
      onError: (error) => latest.current.handlers.onError?.(error),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    // Nur bei neuem Port laden (wie `watch(() => props.port)` in Vue); `editable` wird dabei gelesen.
    if (props.port) void controller.load(latest.current.editable)
  }, [controller, props.port])
  useEffect(() => controller.dispose, [controller])
  return { t, locale, controller, state, view: vvtView(state), editable }
}

function Body({ controller, state, view, t }: { controller: VvtController; state: VvtData; view: VvtView; t: DataProtectionTranslate }) {
  const content = view.content
  const selected = state.selected
  const activity = selected === null ? null : content.taetigkeiten[selected] ?? null
  const columns = state.profile?.register.columns ?? []
  return (
    <>
      {state.history ? <VvtHistory versions={state.register?.versions ?? []} /> : null}
      <VvtCover content={content} issues={view.issues} editing={view.editing} onPersonChange={controller.changePerson} onDepartmentsChange={controller.changeDepartments} />
      <div className="fa-vvt__layout">
        <VvtActivityList content={content} issues={view.issues} selected={selected} editing={view.editing} onActivitySelect={controller.select} onAdd={controller.addActivity} />
        {activity ? (
          <VvtActivityDetail activity={activity} columns={columns} issues={view.issues} departments={content.referate} editing={view.editing} onFieldChange={controller.changeField} onRemove={controller.removeActivity} />
        ) : (
          <p className="fa-dataprotection__panel fa-dataprotection__muted">{t('selectActivity')}</p>
        )}
      </div>
      <VvtIssues issues={view.issues} />
    </>
  )
}

/**
 * Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO) als native
 * React-Komponente (Vertrag wie `<flowaudit-vvt>`): Entwurf bearbeiten,
 * Vollständigkeitsprüfung der Bibliothek, Vier-Augen-Freigabe, Historie, Exporte.
 */
export function FlowauditVvt(props: FlowauditVvtProps) {
  const { t, locale, controller, state, view, editable } = useVvt(props)
  const fourEyes = vvtFourEyes(state, props.actor ?? '')
  const runExport = (format: VvtExportFormat): void => {
    const payload = controller.exportAs(format, locale)
    deliverExport(payload)
    props.onExported?.(payload)
  }
  return (
    <LocaleProvider locale={locale}>
      <section className={props.className ? `fa-dataprotection fa-vvt ${props.className}` : 'fa-dataprotection fa-vvt'} aria-busy={!!state.busy} data-testid="vvt">
        <header className="fa-dataprotection__header">
          <h2>{t('vvtTitle')} <span className="fa-dataprotection__muted">{t('vvtNorm')}</span></h2>
          {state.profile ? <span className="fa-dataprotection__muted">{t('profile', { id: state.profile.profile.id, version: state.profile.profile.version })}</span> : null}
        </header>
        {props.port ? null : <p className="fa-dataprotection__alert" role="alert">{t('noPort')}</p>}
        {state.error ? <p className="fa-dataprotection__alert" role="alert">{state.error.message}</p> : null}
        <p className="fa-dataprotection__live" aria-live="polite">{state.busy === 'load' ? t('loading') : state.notice}</p>
        <VvtStatusBar
          state={state.register}
          version={view.version}
          showing={state.showing}
          editing={view.editing}
          editable={editable}
          dirty={view.dirty}
          fourEyes={fourEyes}
          busy={state.busy}
          history={state.history}
          onSave={() => void controller.save()}
          onDiscard={controller.discard}
          onRelease={() => void controller.release()}
          onNewDraft={controller.startDraft}
          onShow={controller.show}
          onToggleHistory={controller.toggleHistory}
          onExport={runExport}
        />
        <Body controller={controller} state={state} view={view} t={t} />
      </section>
    </LocaleProvider>
  )
}
