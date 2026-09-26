/**
 * General tab: name, id, documentation, markers and the FlowStat task
 * fields of the selected element.
 */

import { FLOWSTAT_FIELDS, isActivity, type FlowstatField } from '@flowaudit/bpmn-flowaudit'
import { FLOWSTAT_KEYS, flowstatValue } from '@flowaudit/bpmn-flowaudit/ui'
import { useEditorContext, useSelectionState } from '../../context'
import { useI18n } from '../../i18n'
import { CommitField } from '../CommitField'
import { MarkerPicker } from './MarkerPicker'

function FlowstatSection() {
  const { t } = useI18n()
  const { selection, readonly } = useEditorContext()
  const flowstat = selection.flowstat()
  if (!flowstat) return null
  return (
    <section className="fa-section">
      <h3 className="fa-section__title">{t('props.flowstat')}</h3>
      <div className="fa-grid-2">
        {FLOWSTAT_KEYS.map((field: FlowstatField) => (
          <label key={field} className={field === 'resource' ? 'fa-field fa-field--wide' : 'fa-field'}>
            <span className="fa-label">{t(`props.flowstat.${field}`)}</span>
            <CommitField className="fa-input" type={FLOWSTAT_FIELDS[field].numeric ? 'number' : 'text'} min="0" value={String(flowstat[field] ?? '')} disabled={readonly()} onCommit={(raw) => selection.setFlowstat(field, flowstatValue(field, raw))} />
          </label>
        ))}
      </div>
    </section>
  )
}

export function GeneralTab() {
  const { t } = useI18n()
  const { selection, editor, readonly } = useEditorContext()
  const { element, type, extensions } = useSelectionState()
  if (!element) return null
  const kind = type ?? ''

  const setColor = (color: { fill: string; stroke: string }) => {
    if (element.di?.get('bioc:fill') || element.di?.get('color:background-color')) return
    editor.services().modeling.setColor([element], color)
  }

  return (
    <div className="fa-tab-general">
      <div className="fa-grid-2">
        <label className="fa-field fa-field--wide">
          <span className="fa-label">{t('props.name')}</span>
          <CommitField className="fa-input" value={selection.property('name')} disabled={readonly()} onCommit={(name) => selection.rename(name)} />
        </label>
        <label className="fa-field">
          <span className="fa-label">{t('props.id')}</span>
          <input className="fa-input" value={element.id} readOnly />
        </label>
        <label className="fa-field">
          <span className="fa-label">{t('props.type')}</span>
          <input className="fa-input" value={kind.replace('bpmn:', '')} readOnly />
        </label>
        <label className="fa-field fa-field--wide">
          <span className="fa-label">{t('props.documentation')}</span>
          <CommitField multiline className="fa-textarea" rows={4} value={selection.documentation()} disabled={readonly()} onCommit={(text) => selection.setDocumentation(text)} />
        </label>
      </div>
      <MarkerPicker className="fa-section" markers={extensions.markers} disabled={readonly()} onUpdate={(markers) => selection.write({ markers })} onColor={setColor} />
      {isActivity(kind) ? <FlowstatSection /> : null}
    </div>
  )
}
