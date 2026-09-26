/**
 * Notes: internal note in the XML (`flowaudit:interneNotiz`) and comments
 * per element (kept by the application).
 */

import { useState } from 'react'
import type { Comment } from '@auditcore/bpmn-flowaudit'
import { commentsOf, newComment, toggleResolved } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../../base/FaIcon'
import { useEditorContext, useSelectionState } from '../../context'
import { classes } from '../../hooks'
import { useI18n } from '../../i18n'
import { CommitField } from '../CommitField'

export interface NotesTabProps {
  comments: Comment[]
  author: string
  onCommentsChange: (comments: Comment[]) => void
}

export function NotesTab({ comments, author, onCommentsChange }: NotesTabProps) {
  const { t } = useI18n()
  const { selection, readonly } = useEditorContext()
  const { element, extensions } = useSelectionState()
  const [draft, setDraft] = useState('')
  const elementId = element?.id ?? ''

  const addComment = () => {
    if (!draft.trim() || !elementId) return
    onCommentsChange([...comments, newComment(elementId, draft, author)])
    setDraft('')
  }

  return (
    <div className="fa-tab-notes">
      <label className="fa-field">
        <span className="fa-label">{t('props.internalNote')}</span>
        <CommitField multiline className="fa-textarea" rows={4} value={extensions.internalNote ?? ''} disabled={readonly()} onCommit={(internalNote) => selection.write({ internalNote })} />
        <span className="fa-help">{t('props.internalNoteHelp')}</span>
      </label>
      <section className="fa-section">
        <h3 className="fa-section__title">{t('props.comments')}</h3>
        <ul className="fa-comments">
          {commentsOf(comments, elementId).map((comment) => (
            <li key={comment.id} className={classes('fa-card fa-comment', comment.resolved && 'fa-comment--resolved')}>
              <p>{comment.text}</p>
              <footer>
                <span className="fa-help">
                  {comment.author} · {new Date(comment.timestamp).toLocaleString()}
                </span>
                <label className="fa-check">
                  <input type="checkbox" checked={comment.resolved} onChange={() => onCommentsChange(toggleResolved(comments, comment.id))} />
                  {t('props.commentResolved')}
                </label>
              </footer>
            </li>
          ))}
        </ul>
        <div className="fa-comments__new">
          <input className="fa-input" value={draft} placeholder={t('props.commentAdd')} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && (event.preventDefault(), addComment())} />
          <button type="button" className="fa-btn" disabled={!draft.trim()} onClick={addComment}>
            <FaIcon name="comment" size={16} />
            {t('common.add')}
          </button>
        </div>
      </section>
    </div>
  )
}
