import { statusTone, type AssessmentView, type DsfaController } from '@flowaudit/ui-core'
import { Badge } from '../../base/Badge'
import { Button } from '../../base/Button'
import { statusLabel, useDataProtectionText } from '../shared'

export interface DsfaHeadProps {
  view: AssessmentView
  dirty: boolean
  readonly: boolean
  editable: boolean
  busy: string | null
  controller: DsfaController
}

/** Kopf der geöffneten Abschätzung: Fassung, Status, Speichern, Neubewertung, Bericht. */
export function DsfaHead({ view, dirty, readonly, editable, busy, controller }: DsfaHeadProps) {
  const { t } = useDataProtectionText()
  const reassess = editable && view.locked && view.status === 'freigegeben'
  return (
    <div className="fa-dataprotection__panel fa-dataprotection__bar" data-testid="dsfa-head">
      <h3>{view.activity_name}</h3>
      <Badge tone={statusTone(view.status)}>{t('versionLabel', { version: view.version, status: statusLabel(t, view.status) })}</Badge>
      {dirty ? <Badge tone="accent">{t('unsaved')}</Badge> : null}
      <div className="fa-dataprotection__actions">
        {readonly ? null : <Button variant="primary" size="sm" disabled={!dirty} loading={busy === 'saved'} label={t('save')} onClick={() => void controller.save()} />}
        {reassess ? <Button size="sm" label={t('reassess')} onClick={() => void controller.reassess()} /> : null}
        <Button variant="ghost" size="sm" label={t('reportHtml')} onClick={() => void controller.exportReport('html')} />
        <Button variant="ghost" size="sm" label={t('reportMarkdown')} onClick={() => void controller.exportReport('markdown')} />
      </div>
      {view.locked ? <p className="fa-dataprotection__muted">{t('lockedNotice')}</p> : null}
    </div>
  )
}
