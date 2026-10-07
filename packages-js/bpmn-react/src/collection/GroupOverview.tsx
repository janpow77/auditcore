/**
 * Overview of a folder (top level: the whole collection): one card per
 * subfolder with description and its diagrams, one card for the diagrams
 * directly in the folder. Legal basis coverage, expired validity and
 * collection issues sit in the collapsed section „Prüfhinweise“. Key
 * requirement coverage and status distribution stay available in
 * `groupOverview` but are no longer shown here. Three layouts – tiles, list
 * and thumbnails (with a `thumbnails` source) – are switched in one menu in
 * the head; the choice is kept per browser.
 */

import { useState } from 'react'
import { issueMessage, type CardDiagram, type FolderCard, type GroupOverview as Overview, type ProfileData, type ValidationIssue } from '@auditcore/bpmn-flowaudit'
import { diagramFacts, hintCount, isWideCard, overviewViews, readOverviewView, statusLabel, writeOverviewView, type FolderAction, type OverviewView, type Thumbnails } from '@auditcore/bpmn-flowaudit/ui'
import { useI18n } from '../i18n'
import { FaIcon } from '../base/FaIcon'
import { ToolbarMenu } from '../base/ToolbarMenu'
import { InlineDescription } from './InlineDescription'
import { InlineName } from './InlineName'
import { OverviewThumbnail } from './OverviewThumbnail'

export interface GroupOverviewProps {
  overview: Overview
  profile?: ProfileData | null
  issues: ValidationIssue[]
  title: string
  cards?: FolderCard[]
  topLevel?: boolean
  readonly?: boolean
  folderActions?: FolderAction[]
  /** Source of thumbnails; without it the „Vorschaubilder“ layout is not offered. */
  thumbnails?: Thumbnails | null
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

function TileList({ card, props }: { card: FolderCard; props: GroupOverviewProps }) {
  const { t, locale } = useI18n()
  return (
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
  )
}

function ListRow({ diagram, props }: { diagram: CardDiagram; props: GroupOverviewProps }) {
  const { t, locale } = useI18n()
  return (
    <div className="fa-diagram-list__row" role="row">
      <span role="cell" className="fa-diagram-list__name">
        <button type="button" className="fa-folder-card__open" onClick={() => props.onOpen?.(diagram.id)}>{diagram.name}</button>
        <InlineDescription text={diagram.description} name={diagram.name} readonly={props.readonly} onSave={(text) => props.onDescribeDiagram?.(diagram.id, text)} />
      </span>
      <span role="cell">{diagram.status ? <span className="fa-badge">{statusLabel(diagram.status, t, locale)}</span> : null}</span>
      <span role="cell" className="fa-diagram-list__facts">{diagramFacts(diagram, t, locale).join(' · ')}</span>
    </div>
  )
}

function DiagramList({ card, name, props }: { card: FolderCard; name: string; props: GroupOverviewProps }) {
  const { t } = useI18n()
  return (
    <div className="fa-diagram-list" role="table" aria-label={name}>
      <div className="fa-diagram-list__row fa-diagram-list__row--head" role="row">
        <span role="columnheader">{t('collection.overview.column.name')}</span>
        <span role="columnheader">{t('collection.overview.column.status')}</span>
        <span role="columnheader">{t('collection.overview.column.facts')}</span>
      </div>
      {card.diagrams.map((diagram) => (
        <ListRow key={diagram.id} diagram={diagram} props={props} />
      ))}
    </div>
  )
}

function ThumbGrid({ card, thumbnails, props }: { card: FolderCard; thumbnails: Thumbnails; props: GroupOverviewProps }) {
  const { t, locale } = useI18n()
  return (
    <ul className="fa-thumb-grid">
      {card.diagrams.map((diagram) => (
        <li key={diagram.id} className="fa-thumb">
          <button type="button" className="fa-thumb__open" title={diagram.name} onClick={() => props.onOpen?.(diagram.id)}>
            <OverviewThumbnail diagramId={diagram.id} name={diagram.name} thumbnails={thumbnails} />
            <span className="fa-thumb__name">{diagram.name}</span>
          </button>
          {diagram.status ? <span className="fa-badge fa-thumb__status">{statusLabel(diagram.status, t, locale)}</span> : null}
        </li>
      ))}
    </ul>
  )
}

function CardBody({ card, name, view, props }: { card: FolderCard; name: string; view: OverviewView; props: GroupOverviewProps }) {
  const { t } = useI18n()
  if (!card.diagrams.length) return <p className="fa-help">{t('collection.overview.emptyFolder')}</p>
  if (view === 'list') return <DiagramList card={card} name={name} props={props} />
  if (view === 'thumbnails' && props.thumbnails) return <ThumbGrid card={card} thumbnails={props.thumbnails} props={props} />
  return <TileList card={card} props={props} />
}

function Card({ card, view, props }: { card: FolderCard; view: OverviewView; props: GroupOverviewProps }) {
  const { t } = useI18n()
  const name = card.name || ((props.topLevel ?? true) ? t('collection.overview.loose') : props.title)
  const count = card.count === 1 ? t('collection.overview.diagram') : t('collection.overview.diagrams', { count: card.count })
  const wide = view !== 'tiles' || isWideCard(card.count, (props.cards ?? []).length)
  return (
    <article className={`fa-card fa-folder-card${wide ? ' fa-folder-card--wide' : ''}`}>
      <header className="fa-folder-card__head">
        <h3 className="fa-folder-card__name">
          {card.folderId ? <InlineName text={card.name} readonly={props.readonly} onSave={(text) => props.onRenameFolder?.(card.folderId ?? '', text)} /> : name}
        </h3>
        <span className="fa-folder-card__count">{count}</span>
        <FolderMenu card={card} props={props} />
      </header>
      {card.folderId ? <InlineDescription text={card.description} name={card.name} readonly={props.readonly} onSave={(text) => props.onDescribeFolder?.(card.folderId ?? '', text)} /> : null}
      <CardBody card={card} name={name} view={view} props={props} />
    </article>
  )
}

function ViewMenu({ views, view, onChoose }: { views: OverviewView[]; view: OverviewView; onChoose: (view: OverviewView) => void }) {
  const { t } = useI18n()
  return (
    <ToolbarMenu label={t('collection.overview.view')} icon="overview" align="right">
      {(close) =>
        views.map((option) => (
          <button key={option} type="button" role="menuitemradio" className="fa-menu-item" aria-checked={view === option} onClick={() => (onChoose(option), close())}>
            {view === option ? <FaIcon name="check" size={14} /> : <span className="fa-menu-item__spacer" />}
            <span>{t(`collection.overview.view.${option}`)}</span>
          </button>
        ))
      }
    </ToolbarMenu>
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
  const views = overviewViews(Boolean(props.thumbnails))
  const [chosen, setChosen] = useState<OverviewView>(() => readOverviewView(Boolean(props.thumbnails)))
  const view = views.includes(chosen) ? chosen : 'tiles'
  const choose = (next: OverviewView) => (setChosen(next), writeOverviewView(next))
  return (
    <section className={`fa-overview fa-overview--${view}`} aria-label={t('collection.overview')}>
      <header className="fa-overview__head">
        <h2>{props.title}</h2>
        {cards.length ? <ViewMenu views={views} view={view} onChoose={choose} /> : null}
      </header>
      {cards.length ? null : <p className="fa-help">{t('collection.overview.empty')}</p>}
      <div className="fa-overview__folders">
        {cards.map((card) => (
          <Card key={card.folderId ?? '_'} card={card} view={view} props={props} />
        ))}
      </div>
      <Hints overview={props.overview} issues={props.issues} onOpen={props.onOpen} />
    </section>
  )
}
