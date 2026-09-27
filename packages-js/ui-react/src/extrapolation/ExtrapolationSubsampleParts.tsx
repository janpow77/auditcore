import { extrapolationCellLabel, extrapolationIssueText, SUB_ITEM_FIELDS, SUB_STRATUM_FIELDS, type SubItemRow, type SubsampleEditorView } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { classes } from '../store'
import type { UseExtrapolation } from './useExtrapolation'

interface PartProps {
  view: UseExtrapolation
  editor: SubsampleEditorView
}

/** Teilschichten der Teilstichprobe (wie `ExtrapolationSubsampleStrata.vue`). */
export function SubsampleStrata({ view, editor }: PartProps) {
  const { state, controller, t } = view
  const issue = (key: string): string => extrapolationIssueText(state.issues, `${editor.prefix}.${key}`, t)
  return (
    <>
      <h4 className="fa-extrapolation__heading">{t('subStrata')}</h4>
      <p className="fa-extrapolation__hint">{t('subStrataHint')}</p>
      {issue('strata') ? <p className="fa-extrapolation__error">{issue('strata')}</p> : null}
      {editor.rows.strata.length ? (
        <div className="fa-extrapolation__scroll">
          <table className="fa-extrapolation__grid" data-testid="extrapolation-substrata">
            <thead>
              <tr>
                {SUB_STRATUM_FIELDS.map((field) => <th key={field.key} scope="col">{t(field.label)}</th>)}
                <th scope="col">{t('remove')}</th>
              </tr>
            </thead>
            <tbody>
              {editor.rows.strata.map((row, position) => (
                <tr key={row.key}>
                  {SUB_STRATUM_FIELDS.map((field) => (
                    <td key={field.key}>
                      <input
                        className={classes('fa-extrapolation__input', field.numeric && 'fa-extrapolation__input--number')}
                        inputMode={field.numeric ? 'decimal' : undefined}
                        value={row[field.key]}
                        aria-label={extrapolationCellLabel(t, field.label, position + 1)}
                        aria-invalid={issue(`strata.${position}.${field.key}`) ? 'true' : undefined}
                        onChange={(event) => controller.updateSubStratum(position, { [field.key]: event.target.value })}
                      />
                    </td>
                  ))}
                  <td>
                    <Button size="sm" variant="ghost" icon="trash" iconOnly label={t('removeRow', { what: t('subStratum'), row: position + 1 })} onClick={() => controller.removeSubStratum(position)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      <div className="fa-extrapolation__actions">
        <Button size="sm" icon="plus" testId="extrapolation-add-substratum" onClick={controller.addSubStratum}>{t('addSubStratum')}</Button>
      </div>
    </>
  )
}

function NestedCell({ view, item, position }: { view: UseExtrapolation; item: SubItemRow; position: number }) {
  const { controller, t } = view
  return (
    <td className="fa-extrapolation__nowrap">
      {item.subsample ? (
        <>
          <Button size="sm" variant="ghost" icon="edit" iconOnly label={t('nestedOpen', { row: position + 1 })} onClick={() => controller.editNestedSubsample(position)} />
          <Button size="sm" variant="ghost" icon="trash" iconOnly label={t('nestedDrop', { row: position + 1 })} onClick={() => controller.toggleNestedSubsample(position)} />
        </>
      ) : (
        <Button size="sm" variant="ghost" icon="plus" iconOnly label={t('nestedCreate', { row: position + 1 })} onClick={() => controller.toggleNestedSubsample(position)} />
      )}
    </td>
  )
}

function ItemLine({ view, editor, item, position, names }: PartProps & { item: SubItemRow; position: number; names: readonly string[] }) {
  const { state, controller, t } = view
  const issue = (key: string): string => extrapolationIssueText(state.issues, `${editor.prefix}.items.${position}.${key}`, t)
  return (
    <tr>
      {names.length ? (
        <td>
          <select className="fa-extrapolation__select" value={item.stratum} aria-label={extrapolationCellLabel(t, 'subStratum', position + 1)} aria-invalid={issue('stratum') ? 'true' : undefined} onChange={(event) => controller.updateSubItem(position, { stratum: event.target.value })}>
            <option value="">{t('choose')}</option>
            {names.map((name) => <option key={name} value={name}>{name}</option>)}
          </select>
        </td>
      ) : null}
      {SUB_ITEM_FIELDS.map((field) => (
        <td key={field.key}>
          <input
            className={classes('fa-extrapolation__input', field.numeric && 'fa-extrapolation__input--number')}
            inputMode={field.numeric ? 'decimal' : undefined}
            value={field.key === 'random' && item.subsample ? t('fromSubsample') : item[field.key]}
            disabled={field.key === 'random' && item.subsample !== null}
            aria-label={extrapolationCellLabel(t, field.label, position + 1)}
            aria-invalid={issue(field.key) ? 'true' : undefined}
            onChange={(event) => controller.updateSubItem(position, { [field.key]: event.target.value })}
          />
        </td>
      ))}
      <td>
        <input type="checkbox" className="fa-extrapolation__check" checked={item.exhaustive} aria-label={extrapolationCellLabel(t, 'exhaustive', position + 1)} onChange={(event) => controller.updateSubItem(position, { exhaustive: event.target.checked })} />
      </td>
      {editor.allowNested ? <NestedCell view={view} item={item} position={position} /> : null}
      <td>
        <Button size="sm" variant="ghost" icon="trash" iconOnly label={t('removeRow', { what: t('subItemId'), row: position + 1 })} onClick={() => controller.removeSubItem(position)} />
      </td>
    </tr>
  )
}

/** Geprüfte Teileinheiten (wie `ExtrapolationSubsampleItems.vue`). */
export function SubsampleItems({ view, editor }: PartProps) {
  const { state, t } = view
  const names = editor.rows.strata.map((row) => row.name.trim()).filter(Boolean)
  const issue = extrapolationIssueText(state.issues, `${editor.prefix}.items`, t)
  return (
    <>
      <h4 className="fa-extrapolation__heading">{t('subItems')}</h4>
      {issue ? <p className="fa-extrapolation__error">{issue}</p> : null}
      <div className="fa-extrapolation__scroll">
        <table className="fa-extrapolation__grid" data-testid="extrapolation-subsample-items">
          <thead>
            <tr>
              {names.length ? <th scope="col">{t('subStratum')}</th> : null}
              {SUB_ITEM_FIELDS.map((field) => <th key={field.key} scope="col">{t(field.label)}</th>)}
              <th scope="col">{t('exhaustive')}</th>
              {editor.allowNested ? <th scope="col">{t('subsample')}</th> : null}
              <th scope="col">{t('remove')}</th>
            </tr>
          </thead>
          <tbody>
            {editor.rows.items.map((item, position) => <ItemLine key={item.key} view={view} editor={editor} item={item} position={position} names={names} />)}
          </tbody>
        </table>
      </div>
    </>
  )
}
