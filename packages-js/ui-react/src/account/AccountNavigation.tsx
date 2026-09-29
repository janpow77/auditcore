import { accountRows, type AccountController, type AccountData } from '@auditcore/ui-core'
import { classes } from '../store'
function group(state: AccountData, index: number) {
  const value = state.items[index]?.group
  return value && (index === 0 || value !== state.items[index - 1]?.group) ? value : null
}
export function AccountNavigation({ state, controller, label }: { state: AccountData; controller: AccountController; label: string }) {
  return <nav aria-label={label}><ul className="fa-account__list">{accountRows(state).map((row, index) => <li key={row.id}>
    {group(state, index) ? <small className="fa-account__group">{group(state, index)}</small> : null}
    <button type="button" className={classes('fa-account__item', row.selected && 'fa-account__item--selected')} aria-pressed={row.selected} disabled={state.dirty || !!state.busy} onClick={() => void controller.select(row.id)}>{row.label}</button>
  </li>)}</ul></nav>
}
