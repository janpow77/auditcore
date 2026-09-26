/**
 * Target/actual check and version comparison against another diagram (from
 * the collection or a file): synopsis table, binary result per element with
 * reasons, graphical diff in the canvas.
 */

import { useEffect, useState, type ChangeEvent } from 'react'
import type { FlowauditHighlight } from '@flowaudit/bpmn-flowaudit'
import { compareClasses, runComparison, type CompareMode, type CompareResult, type CompareSource } from '@flowaudit/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { useEditorContext } from '../context'
import { useI18n } from '../i18n'
import { CheckResults, ComparisonTable } from './CompareResults'

function useComparison(sources: CompareSource[]) {
  const { editor } = useEditorContext()
  const [mode, setMode] = useState<CompareMode>('targetActual')
  const [sourceId, setSourceId] = useState('')
  const [fileXml, setFileXml] = useState<string | null>(null)
  const [result, setResult] = useState<CompareResult>({ comparison: null, check: null })
  const [error, setError] = useState<string | null>(null)
  const layer = () => editor.instance()?.get<FlowauditHighlight>('flowauditHighlight', false)

  useEffect(() => () => editor.instance()?.get<FlowauditHighlight>('flowauditHighlight', false)?.clear('diff'), [editor])

  async function run(): Promise<void> {
    setError(null)
    try {
      const xml = fileXml ?? (await sources.find((source) => source.id === sourceId)?.load()) ?? null
      if (!xml) return
      const next = await runComparison(mode, xml, editor.model())
      setResult(next)
      layer()?.apply('diff', compareClasses(next))
    } catch (caught) {
      setError((caught as Error).message)
    }
  }

  async function onFile(event: ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = event.target.files?.[0]
    setFileXml(file ? await file.text() : null)
    setSourceId('')
  }

  const choose = (id: string) => {
    setSourceId(id)
    setFileXml(null)
  }

  return { mode, setMode, sourceId, choose, fileXml, result, error, run, onFile }
}

export function ComparePanel({ sources }: { sources: CompareSource[] }) {
  const { t } = useI18n()
  const state = useComparison(sources)
  const { comparison, check } = state.result
  return (
    <section className="fa-compare" aria-label={t('compare.title')}>
      <div className="fa-segmented" role="radiogroup">
        <button type="button" role="radio" className="fa-btn fa-btn--ghost" aria-checked={state.mode === 'targetActual'} onClick={() => state.setMode('targetActual')}>{t('compare.mode.targetActual')}</button>
        <button type="button" role="radio" className="fa-btn fa-btn--ghost" aria-checked={state.mode === 'version'} onClick={() => state.setMode('version')}>{t('compare.mode.version')}</button>
      </div>
      <label className="fa-field fa-section">
        <span className="fa-label">{t('compare.other')} ({t('compare.fromCollection')})</span>
        <select className="fa-select" value={state.sourceId} onChange={(event) => state.choose(event.target.value)}>
          <option value="">{t('common.none')}</option>
          {sources.map((source) => <option key={source.id} value={source.id}>{source.name}</option>)}
        </select>
      </label>
      <label className="fa-btn fa-section"><FaIcon name="import" size={16} />{t('compare.fromFile')}<input type="file" accept=".bpmn,.xml" className="fa-sr-only" onChange={(event) => void state.onFile(event)} /></label>
      <button type="button" className="fa-btn fa-btn--primary fa-section" disabled={!state.sourceId && !state.fileXml} onClick={() => void state.run()}><FaIcon name="compare" size={16} />{t('compare.run')}</button>
      <p className="fa-help">{t('compare.hint')}</p>
      {state.error ? <p className="fa-badge fa-badge--danger">{state.error}</p> : null}
      {check ? <CheckResults check={check} /> : null}
      {comparison ? <ComparisonTable comparison={comparison} /> : null}
    </section>
  )
}
