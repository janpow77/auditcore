/**
 * Overview of a folder (top level: the whole collection): one card per
 * subfolder with description and its diagrams, one card for the diagrams
 * directly in the folder. Legal basis coverage, expired validity and
 * collection issues sit in the collapsed section „Prüfhinweise“. Key
 * requirement coverage and status distribution stay available in
 * `groupOverview` but are no longer shown here.
 */

import { issueMessage, type FolderCard, type GroupOverview as Overview, type ProfileData, type ValidationIssue } from '@auditcore/bpmn-flowaudit'
import { hintCount, statusLabel, type FolderAction } from '@auditcore/bpmn-flowaudit/ui'
import { useI18n } from '../i18n'
import { ToolbarMenu } from '../base/ToolbarMenu'
import { InlineDescription } from './InlineDescription'
import { InlineName } from './InlineName'

export interface GroupOverviewProps {
  overview: Overview
  profile?: ProfileData | null
  issues: ValidationIssue[]
  title: string
  cards?: FolderCard[]
  topLevel?: boolean
  readonly?: boolean
  folderActions?: FolderAction[]
  onOpen?: (id: string) => void
  onFolderAction?: (id: string, folderId: string, diagramIds: string[]) => void
  onDescribeFolder?: (id: string, text: string) => void
  onRenameFolder?: (id: string, name: string) => void
  onDescribeDiagram?: (id: string, text: string) => void
}

function FolderMenu({ card, props }: { card: FolderCard; props: GroupOverviewProps }) {
  const { t } = useI18n()
  const folderId = card.folderId
  const actions = props.folderActions ?? []
  if (!folderId || !actions.length) return null
  return (
    <ToolbarMenu label={t('collection.folderActions', { name: card.name })} icon="more" align="right">
      {(close) =>
        actions.map((action) => (
          <button
            key={action.id}
            type="button"
            role="menuitem"
            className="fa-menu-item"
            onClick={() => (props.onFolderAction?.(action.id, folderId, card.diagrams.map((diagram) => diagram.id)), close())}
          >
            <span>{action.label}</span>
          </button>
        ))
      }
    </ToolbarMenu>
  )
}

function Card({ card, props }: { card: FolderCard; props: GroupOverviewProps }) {
  const { t, locale } = useI18n()
  const name = card.name || ((props.topLevel ?? true) ? t('collection.overview.loose') : props.title)
  const count = card.count === 1 ? t('collection.overview.diagram') : t('collection.overview.diagrams', { count: card.count })
  return (
    <article className="fa-card fa-folder-card">
      <header className="fa-folder-card__head">
        <h3 className="fa-folder-card__name">
          {card.folderId ? <InlineName text={card.name} readonly={props.readonly} onSave={(text) => props.onRenameFolder?.(card.folderId ?? '', text)} /> : name}
        </h3>
        <span className="fa-folder-card__count">{count}</span>
        <FolderMenu card={card} props={props} />
      </header>
      {card.folderId ? <InlineDescription text={card.description} name={card.name} readonly={props.readonly} onSave={(text) => props.onDescribeFolder?.(card.folderId ?? '', text)} /> : null}
      {card.diagrams.length ? (
        <ul className="fa-folder-card__list">
          {card.diagrams.map((diagram) => (
            <li key={diagram.id} className="fa-folder-card__item">
              <div className="fa-folder-card__row">
                <button type="button" className="fa-folder-card__open" onClick={() => props.onOpen?.(diagram.id)}>{diagram.name}</button>
                {diagram.status ? <span className="fa-badge">{statusLabel(diagram.status, t, locale)}</span> : null}
              </div>
              <InlineDescription text={diagram.description} name={diagram.name} readonly={props.readonly} onSave={(text) => props.onDescribeDiagram?.(diagram.id, text)} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="fa-help">{t('collection.overview.emptyFolder')}</p>
      )}
    </article>
  )
}

function Hints({ overview, issues, onOpen }: Pick<GroupOverviewProps, 'overview' | 'issues' | 'onOpen'>) {
  const { t, locale } = useI18n()
  const percent = Math.round((overview.legalBasisCoverage ?? 0) * 100)
  const hints = hintCount(overview, issues)
  return (
    <details className="fa-overview__hints">
      <summary>{t('collection.overview.hints', { count: hints })}</summary>
      <div className="fa-overview__hints-body">
        <div className="fa-overview__legal">
          <span className="fa-label">{t('collection.overview.legal')}</span>
          <strong>{overview.legalBasisCoverage === null ? '–' : `${percent} %`}</strong>
          <div className="fa-meter" role="meter" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${percent}%` }} /></div>
          <span className="fa-help">{t('collection.overview.legalValue', { with: overview.activitiesWithLegalBasis, total: overview.activities, percent })}</span>
        </div>
        {overview.expired.length ? (
          <>
            <h3 className="fa-section__title fa-section">{t('collection.overview.expired')}</h3>
            {overview.expired.map((id) => (
              <button key={id} type="button" className="fa-chip" onClick={() => onOpen?.(id)}>{id}</button>
            ))}
          </>
        ) : null}
        {issues.length ? (
          <>
            <h3 className="fa-section__title fa-section">{t('collection.overview.issues')}</h3>
            <ul className="fa-overview__issues">
              {issues.map((item, index) => (
                <li key={index}>{issueMessage(item, locale)}</li>
              ))}
            </ul>
          </>
        ) : null}
        {hints ? null : <p className="fa-help">{t('collection.overview.noHints')}</p>}
      </div>
    </details>
  )
}

export function GroupOverview(props: GroupOverviewProps) {
  const { t } = useI18n()
  const cards = props.cards ?? []
  return (
    <section className="fa-overview" aria-label={t('collection.overview')}>
      <h2>{props.title}</h2>
      {cards.length ? null : <p className="fa-help">{t('collection.overview.empty')}</p>}
      <div className="fa-overview__folders">
        {cards.map((card) => (
          <Card key={card.folderId ?? '_'} card={card} props={props} />
        ))}
      </div>
      <Hints overview={props.overview} issues={props.issues} onOpen={props.onOpen} />
    </section>
  )
}
