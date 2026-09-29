import { accountMessages, type AccountData, type AccountController, type Locale } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
export function AccountActions({ state, controller, locale }: { state: AccountData; controller: AccountController; locale: Locale }) {
  const { t } = useTranslation(accountMessages, locale)
  const document = state.document
  if (!document?.editable) return null
  return <footer className="fa-account__actions">
    <button type="button" disabled={!state.dirty || !!state.busy} onClick={controller.discard}>{t('discard')}</button>
    <button type="submit" className="fa-account__primary" disabled={!state.dirty || !!state.busy}>{document.submitLabel || t('save')}</button>
  </footer>
}
