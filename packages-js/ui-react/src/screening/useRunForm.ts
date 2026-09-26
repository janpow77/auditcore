import { useState } from 'react'
import { buildRunRequest, runFormDefaults, type RunRequest, type ScreeningKind, type ScreeningRunFormState, type SettingsView, type SourceView, type ViewMessage } from '@auditcore/ui-core'

type Basis = { settings: SettingsView; sources: readonly SourceView[] }

function initial(basis: Basis, kind: ScreeningKind, previous?: ScreeningRunFormState): ScreeningRunFormState {
  return {
    subjectsText: previous?.subjectsText ?? '',
    caseReference: previous?.caseReference ?? '',
    kind,
    ...runFormDefaults(basis.settings, basis.sources, kind),
  }
}

/** Formularzustand „Neuer Prüflauf“; Vorbelegung bei neuer Prüfart oder neuen Einstellungen wie der `watch` der Vue-Fassung. */
export function useRunForm(settings: SettingsView, sources: readonly SourceView[], onSubmit: (request: RunRequest) => void) {
  const [basis, setBasis] = useState<Basis>({ settings, sources })
  const [form, setForm] = useState<ScreeningRunFormState>(() => initial({ settings, sources }, 'sanctions'))
  const [errors, setErrors] = useState<ViewMessage[]>([])
  if (basis.settings !== settings || basis.sources !== sources) {
    setBasis({ settings, sources })
    setForm(initial({ settings, sources }, form.kind, form))
  }
  return {
    form,
    errors,
    update: (patch: Partial<ScreeningRunFormState>) => setForm((current) => ({ ...current, ...patch })),
    setKind: (kind: ScreeningKind) => setForm((current) => initial({ settings, sources }, kind, current)),
    toggleList: (key: string, checked: boolean) =>
      setForm((current) => ({ ...current, lists: checked ? [...current.lists, key] : current.lists.filter((item) => item !== key) })),
    submit(): void {
      const result = buildRunRequest(settings, form)
      setErrors(result.errors)
      if (result.request) onSubmit(result.request)
    },
  }
}
