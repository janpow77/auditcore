import type { AccountController, AccountData, AccountField, AccountPort, Locale } from '@auditcore/ui-core'
import { accountImageUrl } from '@auditcore/ui-core'
import { classes } from '../store'
import { AccountImageField } from './AccountImageField'
interface Props { field: AccountField; state: AccountData; controller: AccountController; port?: AccountPort | null; locale: Locale }
function ImageControl({ field, state, controller, port, locale }: Props) {
  const value = state.draft[field.id] ?? ''
  const edit = (next: string) => controller.edit(field.id, next)
  return <AccountImageField allowCamera={state.document?.id === 'profile'} label={field.label} url={state.images[field.id] ?? accountImageUrl(port, value)}
    disabled={!!state.busy || !state.document?.editable || !!field.readonly} locale={locale}
    onUpload={(file) => void controller.upload(field.id, file)} onRemove={() => edit('')} />
}
function Control({ field, state, controller, port, locale }: Props) {
  const value = state.draft[field.id] ?? ''
  const edit = (next: string) => controller.edit(field.id, next)
  if (field.type === 'image') return <ImageControl {...{ field, state, controller, port, locale }} />
  if (field.type === 'textarea') return <textarea value={value} readOnly={field.readonly} required={field.required} rows={6} onChange={(event) => edit(event.target.value)} />
  if (field.type === 'select' || field.type === 'multiselect') return <Selection field={field} value={value} edit={edit} />
  return <input type={field.type ?? 'text'} value={value} readOnly={field.readonly} required={field.required} autoComplete={field.autocomplete ?? 'off'} onChange={(event) => edit(event.target.value)} />
}
export function AccountFormField(props: Props) {
  const { field } = props
  const Wrapper = field.type === 'image' ? 'div' : 'label'
  return <Wrapper className={classes('fa-account__field', ['textarea', 'image'].includes(field.type ?? '') && 'fa-account__wide')}>
    <span>{field.label}{field.required ? ' *' : ''}</span>
    <Control {...props} />
    {field.hint ? <small>{field.hint}</small> : null}
  </Wrapper>
}

function Selection({ field, value, edit }: { field: AccountField; value: string; edit: (value: string) => void }) {
  const multiple = field.type === 'multiselect'
  return <select multiple={multiple} value={multiple ? value.split('\n') : value} disabled={field.readonly} required={field.required}
    onChange={(event) => edit(multiple ? Array.from(event.target.selectedOptions, (option) => option.value).join('\n') : event.target.value)}>
    <option value="">—</option>{field.options?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
  </select>
}
