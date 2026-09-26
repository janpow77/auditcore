import type { ReactElement } from 'react'
import { render } from '@testing-library/react'
import type { ProfileData } from '@auditcore/bpmn-flowaudit'
import type { EditorPorts } from '@auditcore/bpmn-flowaudit/ui'
import { EditorContextProvider, type EditorContext } from '../src/context'

const store = <S extends object>(state: S) => ({ get: () => state, set: () => undefined, subscribe: () => () => undefined })

/** Renders a component inside a minimal editor context (no core editor) – counterpart of Vue's `mountInContext`. */
export function renderInContext(element: ReactElement, options: { readonly?: boolean; profile?: ProfileData | null; ports?: EditorPorts } = {}) {
  const context = {
    editor: { store: store({ ready: false, changes: 0, info: null }) },
    selection: { store: store({ element: null, version: 0 }) },
    validation: { store: store({ local: [], server: [], running: false, error: null }) },
    ports: options.ports ?? {},
    profile: () => options.profile ?? null,
    readonly: () => options.readonly ?? false,
  } as unknown as EditorContext
  return render(<EditorContextProvider value={context}>{element}</EditorContextProvider>)
}
