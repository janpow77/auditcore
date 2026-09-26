import { createShareSearch, initials, shareName, type Share, type SharePermission, type UserRef } from '@auditcore/kanban-core'
import type { Locale } from '@auditcore/ui-core'
import { useEffect, useRef, useState } from 'react'
import { Button } from '../base/Button'
import { Dialog } from '../base/Dialog'
import { TextField } from '../base/TextField'
import { useStoreState } from '../store'
import { useKanbanDialogText } from './text'

const PERMISSIONS: readonly SharePermission[] = ['read', 'edit']

export interface KanbanShareDialogProps {
  open: boolean
  shares: readonly Share[]
  search?: ((query: string) => Promise<UserRef[]>) | null
  users?: readonly UserRef[]
  locale?: Locale
  onClose: () => void
  onShare: (userId: string, permission: SharePermission) => void
  onRevoke: (userId: string) => void
}

type Text = ReturnType<typeof useKanbanDialogText>['t']

function PermissionOptions({ t }: { t: Text }) {
  return <>{PERMISSIONS.map((entry) => <option key={entry} value={entry}>{t(`permission_${entry}`)}</option>)}</>
}

function ShareRow({ share, name, props, confirming, onRevoke }: { share: Share; name: string; props: KanbanShareDialogProps; confirming: boolean; onRevoke: () => void }) {
  const { t } = useKanbanDialogText(props.locale)
  return (
    <div className="fa-kanban-share__person" data-share={share.user_id}>
      <span className="fa-kanban-share__avatar" aria-hidden="true">{initials(name)}</span>
      <span className="fa-kanban-share__name">{name}</span>
      <select className="fa-kanban-select" value={share.permission} aria-label={t('permission')} onChange={(event) => props.onShare(share.user_id, event.target.value as SharePermission)}>
        <PermissionOptions t={t} />
      </select>
      <Button size="sm" variant={confirming ? 'danger' : 'ghost'} icon="trash" iconOnly={!confirming} label={confirming ? t('confirmRevoke') : t('revoke', { name })} onClick={onRevoke} />
    </div>
  )
}

/** Freigaben eines Boards wie `KanbanShareDialog.vue` (Personensuche, Rechte, Entfernen mit Bestätigung). */
export function KanbanShareDialog(props: KanbanShareDialogProps) {
  const { t } = useKanbanDialogText(props.locale)
  const [finder] = useState(createShareSearch)
  const found = useStoreState(finder.store)
  const [query, setQuery] = useState('')
  const [permission, setPermission] = useState<SharePermission>('read')
  const [confirming, setConfirming] = useState<string | null>(null)
  const { search } = props
  const inputs = useRef(props)
  inputs.current = props
  // Wie der Vue-watch auf den Suchtext: nur eine neue Eingabe sucht neu.
  useEffect(() => void finder.query(query, inputs.current.search, inputs.current.shares), [finder, query])
  if (!props.open && (query || confirming)) {
    setQuery('')
    setConfirming(null)
  }
  const add = (user: UserRef): void => {
    props.onShare(user.id, permission)
    setQuery('')
  }
  const revoke = (userId: string): void => {
    setConfirming(confirming === userId ? null : userId)
    if (confirming === userId) props.onRevoke(userId)
  }
  const name = (userId: string): string => shareName(userId, found.known, props.users ?? [])
  return (
    <Dialog open={props.open} title={t('shareTitle')} description={t('shareDescription')} locale={props.locale} onClose={props.onClose}>
      {search ? (
        <div className="fa-kanban-detail__row">
          <TextField value={query} type="search" label={t('searchUser')} style={{ flex: 1 }} autoFocus onChange={setQuery} />
          <label className="fa-field">
            <span className="fa-field__label">{t('permission')}</span>
            <select value={permission} className="fa-kanban-select" onChange={(event) => setPermission(event.target.value as SharePermission)}>
              <PermissionOptions t={t} />
            </select>
          </label>
        </div>
      ) : null}
      {found.results.length ? (
        <ul className="fa-kanban-share__results" role="listbox" aria-label={t('searchUser')}>
          {found.results.map((user) => (
            <li key={user.id} role="option" aria-selected="false">
              <button type="button" onClick={() => add(user)}>{user.name} {user.email ? <small>· {user.email}</small> : null}</button>
            </li>
          ))}
        </ul>
      ) : null}
      {props.shares.length === 0 ? <p className="fa-kanban-settings__hint">{t('noShares')}</p> : null}
      {props.shares.map((share) => (
        <ShareRow key={share.user_id} share={share} name={name(share.user_id)} props={props} confirming={confirming === share.user_id} onRevoke={() => revoke(share.user_id)} />
      ))}
    </Dialog>
  )
}
