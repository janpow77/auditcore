import type { SynopsisTranslate, SynopsisView } from '@auditcore/ui-core'
import { Icon } from '../base/Icon'

export interface SynopsisHeaderProps {
  view: SynopsisView
  selectedText: string
  editable: boolean
  headingId: string
  t: SynopsisTranslate
}

export function SynopsisHeader({ view, selectedText, editable, headingId, t }: SynopsisHeaderProps) {
  return (
    <header className="fa-synopsis-header">
      <h2 id={headingId} className="fa-synopsis-header__title">{view.title}</h2>
      <p className="fa-synopsis-header__files">{view.filesText}</p>
      <p className="fa-synopsis-header__counts">{view.countsText}</p>
      <p className="fa-synopsis-header__meta">{view.detectedText}</p>
      <p className="fa-synopsis-header__meta fa-synopsis-header__hash">{view.hashesText}</p>
      {editable ? <p className="fa-synopsis-header__meta">{selectedText}</p> : null}
      {view.isArticleLaw ? (
        <p className="fa-synopsis-header__commands">{t('commands', { recognised: view.recognisedCommands, open: view.openCommands.length })}</p>
      ) : null}
      <ul className="fa-synopsis-header__notices">
        {view.notices.map((notice) => (
          <li key={notice}>
            <Icon name="info" size={16} /> <span>{notice}</span>
          </li>
        ))}
      </ul>
    </header>
  )
}
