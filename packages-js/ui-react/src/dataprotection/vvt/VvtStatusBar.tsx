import { statusTone, type DataProtectionTranslate, type RegisterState, type VersionView, type VvtExportFormat } from '@flowaudit/ui-core'
import { Badge } from '../../base/Badge'
import { Button, type ButtonProps } from '../../base/Button'
import { statusLabel, useDataProtectionText } from '../shared'

export interface VvtStatusBarProps {
  state: RegisterState | null
  version: VersionView | null
  showing: 'draft' | 'released'
  editing: boolean
  editable: boolean
  dirty: boolean
  fourEyes: boolean
  busy: string | null
  history: boolean
  onSave: () => void
  onDiscard: () => void
  onRelease: () => void
  onNewDraft: () => void
  onShow: (which: 'draft' | 'released') => void
  onToggleHistory: () => void
  onExport: (format: VvtExportFormat) => void
}

function VersionInfo({ version, editing, hasDraft }: { version: VersionView | null; editing: boolean; hasDraft: boolean }) {
  const { t, when } = useDataProtectionText()
  if (version && !(editing && !hasDraft)) {
    return (
      <>
        <Badge tone={statusTone(version.status)}>{t('versionLabel', { version: version.version, status: statusLabel(t, version.status) })}</Badge>
        <span className="fa-dataprotection__muted">{t('createdBy', { person: version.created_by, date: when(version.created_at) })}</span>
        {version.released_by ? <span className="fa-dataprotection__muted">{t('releasedBy', { person: version.released_by, date: when(version.released_at) })}</span> : null}
        <span className="fa-dataprotection__muted">{t('revision', { revision: version.revision })}</span>
      </>
    )
  }
  if (editing) return <Badge tone="warning">{t('newDraft')}</Badge>
  return <span className="fa-dataprotection__muted">{t('noVersion')}</span>
}

interface Action {
  key: string
  show: boolean
  props: ButtonProps
}

/** Ansicht wechseln, Entwurf anlegen, Änderungen verwerfen. */
function viewActions(props: VvtStatusBarProps, t: DataProtectionTranslate): Action[] {
  const { state, showing, editing, editable, dirty } = props
  const draft = !!state?.draft
  const toReleased = showing === 'draft'
  return [
    { key: 'show', show: draft && !!state?.released, props: { variant: 'ghost', size: 'sm', label: toReleased ? t('showReleased') : t('showDraft'), onClick: () => props.onShow(toReleased ? 'released' : 'draft') } },
    { key: 'new', show: editable && !draft && !editing, props: { size: 'sm', icon: 'plus', label: t('newDraft'), onClick: props.onNewDraft } },
    { key: 'discard', show: editing && dirty, props: { size: 'sm', label: t('discard'), onClick: props.onDiscard } },
  ]
}

/** Speichern und Freigeben (Vier-Augen-Vorprüfung, maßgeblich bleibt der Server). */
function writeActions(props: VvtStatusBarProps, releaseHint: string, t: DataProtectionTranslate): Action[] {
  const { state, busy, dirty, editable } = props
  const draft = !!state?.draft
  const saving = busy === 'save'
  const canRelease = editable && props.showing === 'draft' && draft && !dirty && !props.fourEyes
  return [
    { key: 'save', show: props.editing, props: { variant: 'primary', size: 'sm', loading: saving, disabled: !dirty, label: saving ? t('saving') : t('save'), onClick: props.onSave } },
    { key: 'release', show: editable && draft, props: { size: 'sm', icon: 'lock', label: t('release'), disabled: !canRelease, loading: busy === 'release', title: releaseHint || undefined, onClick: props.onRelease } },
  ]
}

function EditButtons(props: VvtStatusBarProps & { releaseHint: string }) {
  const { t } = useDataProtectionText()
  return (
    <>
      {[...viewActions(props, t), ...writeActions(props, props.releaseHint, t)].filter((action) => action.show).map((action) => <Button key={action.key} {...action.props} />)}
    </>
  )
}

/** Fassung, Bearbeitungsstand und Aktionen des Verzeichnisses (wie VvtStatusBar.vue). */
export function VvtStatusBar(props: VvtStatusBarProps) {
  const { t } = useDataProtectionText()
  const draft = props.state?.draft ?? null
  const releaseHint = props.dirty ? t('saveFirst') : props.fourEyes ? t('fourEyesHint') : ''
  return (
    <div className="fa-dataprotection__panel fa-dataprotection__bar" data-testid="vvt-status">
      <VersionInfo version={props.version} editing={props.editing} hasDraft={!!draft} />
      {props.dirty ? <Badge tone="accent">{t('unsaved')}</Badge> : null}
      <div className="fa-dataprotection__actions">
        <EditButtons {...props} releaseHint={releaseHint} />
        <Button variant="ghost" size="sm" icon="clock" pressed={props.history} label={props.history ? t('hideHistory') : t('history')} onClick={props.onToggleHistory} />
        <Button variant="ghost" size="sm" label={t('exportPrint')} onClick={() => props.onExport('print')} />
        <Button variant="ghost" size="sm" label={t('exportMarkdown')} onClick={() => props.onExport('markdown')} />
        <Button variant="ghost" size="sm" label={t('exportCsv')} onClick={() => props.onExport('csv')} />
      </div>
      {props.editable && draft && releaseHint ? <p className="fa-dataprotection__muted" data-testid="vvt-release-hint">{releaseHint}</p> : null}
    </div>
  )
}
