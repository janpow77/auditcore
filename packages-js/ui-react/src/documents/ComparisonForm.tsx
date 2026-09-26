import { useEffect, useRef, type ChangeEvent } from 'react'
import {
  ACCEPTED_EXTENSIONS,
  COMPARISON_KINDS,
  type CompareForm,
  type ComparisonsMessageKey,
  type ComparisonsTranslate,
  type ComparisonsView,
  type RowStatus,
  type UploadFile,
} from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import { TextField } from '../base/TextField'
import { classes, useElementId } from '../store'
import { ComparisonOptions } from './ComparisonOptions'

export interface ComparisonFormProps {
  form: CompareForm
  view: ComparisonsView
  t: ComparisonsTranslate
  busy?: boolean
  onFormUpdate: (patch: Partial<CompareForm>) => void
  onSectionToggle: (status: RowStatus, enabled: boolean) => void
  onFormSubmit: () => void
  onFormReset: () => void
}

type Side = 'oldFile' | 'newFile'
const ACCEPT = ACCEPTED_EXTENSIONS.join(',')

function errorOf(view: ComparisonsView, field: string): string {
  return view.problems.filter((problem) => problem.field === field).map((problem) => problem.text).join(' ')
}

/** Nach Anlegen oder Zurücksetzen auch die Dateiauswahl der Eingabefelder leeren (wie die Vue-Fassung). */
function useClearedFiles(form: CompareForm) {
  const inputs = useRef<Partial<Record<Side, HTMLInputElement | null>>>({})
  useEffect(() => {
    for (const side of ['oldFile', 'newFile'] as const) {
      const input = inputs.current[side]
      if (!form[side] && input) input.value = ''
    }
  }, [form])
  return inputs
}

function FileField(props: { side: Side; label: string; chosen: string; error: string; hint: string; id: string; inputRef: (el: HTMLInputElement | null) => void; onFile: (side: Side, file: UploadFile | null) => void }) {
  const { side, id, error } = props
  const onChange = (event: ChangeEvent<HTMLInputElement>): void => props.onFile(side, event.target.files?.[0] ?? null)
  return (
    <div className={classes('fa-comparisons-form__field', 'fa-comparisons-form__file', !!error && 'fa-comparisons-form__field--error')}>
      <label htmlFor={`${id}-${side}`}>{props.label}</label>
      <input
        ref={props.inputRef} id={`${id}-${side}`} type="file" accept={ACCEPT} data-testid={`comparisons-${side}`}
        aria-invalid={error ? 'true' : undefined} aria-describedby={`${id}-${side}-note`} onChange={onChange}
      />
      <p id={`${id}-${side}-note`} className={error ? 'fa-comparisons-form__error' : 'fa-comparisons-form__hint'}>{error || props.chosen || props.hint}</p>
    </div>
  )
}

/** Formular „Neuer Vergleich“ wie `ComparisonForm.vue`. */
export function ComparisonForm(props: ComparisonFormProps) {
  const { form, view, t, busy = false } = props
  const id = useElementId('fa-comparisons-form')
  const inputs = useClearedFiles(form)
  const files = [
    { side: 'oldFile' as const, label: view.oldFileLabel, chosen: view.oldFileText },
    { side: 'newFile' as const, label: view.newFileLabel, chosen: view.newFileText },
  ]
  const onFile = (side: Side, file: UploadFile | null): void => props.onFormUpdate({ [side]: file })
  return (
    <form className="fa-comparisons-form" aria-labelledby={`${id}-heading`} noValidate onSubmit={(event) => { event.preventDefault(); props.onFormSubmit() }}>
      <h3 id={`${id}-heading`} className="fa-comparisons__subheading">{t('formHeading')}</h3>
      <fieldset className="fa-comparisons-form__group fa-comparisons-form__group--kind">
        <legend>{t('typeLabel')}</legend>
        {COMPARISON_KINDS.map((kind) => (
          <label key={kind}>
            <input type="radio" name={`${id}-kind`} value={kind} checked={form.kind === kind} onChange={() => props.onFormUpdate({ kind })} /> {t(`kind_${kind}` as ComparisonsMessageKey)}
          </label>
        ))}
      </fieldset>
      <div className="fa-comparisons-form__row">
        {files.map((entry) => (
          <FileField key={entry.side} {...entry} error={errorOf(view, entry.side)} hint={view.sizeHint} id={id} inputRef={(el) => { inputs.current[entry.side] = el }} onFile={onFile} />
        ))}
      </div>
      {view.pdfHint ? <p className="fa-comparisons-form__hint">{t('pdfHint')}</p> : null}
      <TextField value={form.title} label={t('titleLabel')} placeholder={t('titlePlaceholder')} error={errorOf(view, 'title')} onChange={(title) => props.onFormUpdate({ title })} />
      <ComparisonOptions
        form={form} t={t} profileOptions={view.profileOptions} thresholdError={errorOf(view, 'threshold')} sectionsError={errorOf(view, 'sections')}
        onFormUpdate={props.onFormUpdate} onSectionToggle={props.onSectionToggle}
      />
      {view.problems.length ? (
        <div className="fa-comparisons-form__problems" role="alert">
          <p>{t('problemsHeading')}</p>
          <ul>{view.problems.map((problem) => <li key={problem.text}>{problem.text}</li>)}</ul>
        </div>
      ) : null}
      <div className="fa-comparisons-form__actions">
        <Button type="submit" variant="primary" icon="check" loading={busy}>{t('submit')}</Button>
        <Button variant="ghost" disabled={busy} onClick={props.onFormReset}>{t('reset')}</Button>
      </div>
    </form>
  )
}
