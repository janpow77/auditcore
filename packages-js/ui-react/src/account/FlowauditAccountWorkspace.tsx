import { useEffect, useRef, useState } from 'react'
import { createAccountController, accountMessages, accountRows, accountPreviewStyle, accountWelcomePreview, type AccountItem, type AccountPort, type Locale } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'
import { AccountFormField } from './AccountFormField'
import { AccountNavigation } from './AccountNavigation'
import { AccountStatus } from './AccountStatus'
import { AccountActions } from './AccountActions'
export interface FlowauditAccountWorkspaceProps {
  port?: AccountPort | null; locale?: Locale
  onItemSelect?: (item: AccountItem) => void; onError?: (message: string) => void
}
export function FlowauditAccountWorkspace(props: FlowauditAccountWorkspaceProps) {
  const { t, locale } = useTranslation(accountMessages, props.locale)
  const latest = useRef(props); latest.current = props
  const [controller] = useState(() => createAccountController({ port: () => latest.current.port, callbacks: () => ({
    selected: (item) => latest.current.onItemSelect?.(item), failed: (message) => latest.current.onError?.(message),
  }) }))
  const state = useStoreState(controller.store)
  useEffect(() => { void controller.load(); return controller.dispose }, [controller, props.port])
  const rows = accountRows(state)
  const document = state.document
  return <section className="fa-account" lang={locale} aria-label={t('title')}>
    <header className="fa-account__header"><span className="fa-account__eyebrow">FlowAudit</span><h2>{t('title')}</h2></header>
    <AccountStatus state={state} locale={locale} />
    <div className="fa-account__layout">
      <AccountNavigation state={state} controller={controller} label={t('title')} />
      {document ? <form key={document.id} className="fa-account__card" onSubmit={(event) => { event.preventDefault(); void controller.save() }}>
        <h3>{document.title}</h3><p className="fa-account__muted">{document.description}</p>
        {!document.editable ? <p>{t('readonly')}</p> : null}
        <fieldset disabled={!!state.busy || !document.editable} className="fa-account__fields">
          {document.fields.map((field) => <AccountFormField key={field.id} field={field} state={state} controller={controller} port={props.port} locale={locale} />)}
        </fieldset>
        {document.kind === 'branding' ? <aside className="fa-account__preview" style={accountPreviewStyle(state.draft)}><strong>{t('preview')}</strong><p>{state.draft.document_header}</p><p>{state.draft.document_footer}</p></aside> : null}
        {document.kind === 'welcome' ? <aside className="fa-account__welcome"><strong>{t('preview')}</strong><p>{accountWelcomePreview(document, state.draft)}</p></aside> : null}
        <AccountActions state={state} controller={controller} locale={locale} />
      </form> : rows.length && !state.busy ? <p className="fa-account__card fa-account__muted">{t('choose')}</p> : null}
    </div>
  </section>
}
