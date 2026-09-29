import { accountIsEmpty, accountMessages, type AccountData, type Locale } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
export function AccountStatus({ state, locale }: { state: AccountData; locale: Locale }) {
  const { t } = useTranslation(accountMessages, locale)
  return <>
    {state.busy ? <p role="status">{t('loading')}</p> : null}
    {state.error ? <p className="fa-account__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
    {state.notice ? <p role="status">{t('saved')}</p> : null}
    {state.dirty ? <p className="fa-account__muted" role="status">{t('dirty')}</p> : null}
    {accountIsEmpty(state) ? <p className="fa-account__muted">{t('empty')}</p> : null}
  </>
}
