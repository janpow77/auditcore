/** ESI requirements per element (legacy `EsiRequirementsDialog`), loaded through the ESI port. */

import { useCallback, useEffect, useMemo, useState } from 'react'
import { groupByElement, summarize, type EsiPort, type EsiRequirementResult } from '@auditcore/bpmn-flowaudit'
import { ESI_STATUS, loadEsi } from '@auditcore/bpmn-flowaudit/ui'
import { BaseDialog } from '../base/BaseDialog'
import { FaIcon } from '../base/FaIcon'
import { useI18n } from '../i18n'

export interface EsiDialogProps {
  open: boolean
  port?: EsiPort
  xml: () => Promise<string>
  diagramId?: string
  onOpenChange: (open: boolean) => void
  onJump: (elementId: string) => void
}

function Requirement({ item }: { item: EsiRequirementResult }) {
  const { t } = useI18n()
  const status = ESI_STATUS[item.status]
  return (
    <li>
      <span className={`fa-badge ${status.badge}`}><FaIcon name={status.icon} size={12} />{t(status.label)}</span>
      <span>{item.description}</span>
      {item.expected !== null ? <span className="fa-help">{t('esi.expected')}: {item.expected}</span> : null}
      {item.actual !== null ? <span className="fa-help">{t('esi.actual')}: {item.actual}</span> : item.expected !== null ? <span className="fa-help">{t('esi.actualMissing')}</span> : null}
    </li>
  )
}

type Group = ReturnType<typeof groupByElement>[number]

function EsiGroup({ group, onJump }: { group: Group; onJump: () => void }) {
  const { t } = useI18n()
  return (
    <section className="fa-card fa-esi__group">
      <header className="fa-esi__head">
        <div>
          <strong>{group.elementName}</strong>
          <span className="fa-help"> · {group.elementId} · {group.fulfilledCount}/{group.totalCount}</span>
        </div>
        <button type="button" className="fa-btn fa-btn--ghost" onClick={onJump}>{t('issues.jump')}</button>
      </header>
      <ul className="fa-esi__list">
        {group.requirements.map((item) => <Requirement key={item.requirementId} item={item} />)}
      </ul>
    </section>
  )
}

function useEsi(open: boolean, port: EsiPort | undefined, xml: () => Promise<string>, diagramId?: string) {
  const [list, setList] = useState<EsiRequirementResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => {
    if (!port) return
    setLoading(true)
    setError(null)
    try {
      setList(await loadEsi(port, xml, diagramId))
    } catch (caught) {
      setError((caught as Error).message)
    } finally {
      setLoading(false)
    }
  }, [port, xml, diagramId])
  useEffect(() => {
    if (open) void load()
  }, [open, load])
  return { list, loading, error, load }
}

export function EsiDialog({ open, port, xml, diagramId, onOpenChange, onJump }: EsiDialogProps) {
  const { t } = useI18n()
  const { list, loading, error, load } = useEsi(open, port, xml, diagramId)
  const groups = useMemo(() => groupByElement(list), [list])
  const summary = useMemo(() => summarize(list), [list])
  const jump = (id: string) => {
    onJump(id)
    onOpenChange(false)
  }

  return (
    <BaseDialog open={open} title={t('esi.title')} subtitle={t('esi.subtitle')} width="760px" onOpenChange={onOpenChange}>
      {!port ? (
        <p className="fa-help">{t('esi.noPort')}</p>
      ) : (
        <>
          <div className="fa-esi__summary">
            <span className="fa-badge">{t('esi.total')} {summary.total}</span>
            <span className="fa-badge fa-badge--success">{t('esi.fulfilled')} {summary.fulfilled}</span>
            <span className="fa-badge fa-badge--warning">{t('esi.unclear')} {summary.unclear}</span>
            <span className="fa-badge fa-badge--danger">{t('esi.missing')} {summary.missing}</span>
            <button type="button" className="fa-btn fa-btn--ghost" disabled={loading} onClick={() => void load()}>{loading ? t('common.loading') : t('esi.reload')}</button>
          </div>
          {error ? <p className="fa-badge fa-badge--danger">{error}</p> : !loading && !groups.length ? <p className="fa-help">{t('esi.none')}</p> : null}
          {groups.map((group) => <EsiGroup key={group.elementId} group={group} onJump={() => jump(group.elementId)} />)}
        </>
      )}
    </BaseDialog>
  )
}
