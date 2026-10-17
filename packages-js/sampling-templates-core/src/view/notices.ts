/** Texte zu Hinweisen und Fehlern beim Öffnen einer Datei. */
import type { MessageKey, Translate } from '../i18n/messages'
import type { OpenError, OpenErrorCode, OpenNotice } from '../workspace/types'

const ERROR_KEYS: Readonly<Record<OpenErrorCode, MessageKey>> = {
  'too-large': 'errorTooLarge',
  'invalid-json': 'errorInvalidJson',
  'unsafe-key': 'errorUnsafeKey',
  'not-a-workspace': 'errorNotWorkspace',
  'newer-version': 'errorNewerVersion',
  'invalid-structure': 'errorInvalidStructure',
}

/** Fehlermeldung: was falsch ist und wie es sich beheben lässt. */
export function describeOpenError(error: OpenError, t: Translate): string {
  return t(ERROR_KEYS[error.code], { detail: error.detail ?? '' })
}

/** Hinweis nach dem Öffnen als Satz. */
export function describeNotice(notice: OpenNotice, t: Translate): string {
  if (notice.kind === 'checksum-mismatch') return t('noticeChecksum')
  if (notice.kind === 'unknown-fields') return t('noticeUnknown', { fields: notice.fields.join(', ') })
  if (notice.kind === 'migrated') return t('noticeMigrated', { from: notice.from, to: notice.to })
  const cells = notice.differences.map((entry) => `${entry.label} (${entry.sheet}!${entry.cell})`).join(', ')
  return t('noticeResults', { stored: notice.storedEngine, current: notice.currentEngine, cells })
}
