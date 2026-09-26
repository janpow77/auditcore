import { useEffect, useRef, useState } from 'react'
import {
  createIdentifierController,
  findIdentifierProfile,
  identifierBatchMapping,
  identifierMessages,
  identifierProfileKinds,
  type IdentifierBatchAnswer,
  type IdentifierBatchMapping,
  type IdentifierController,
  type IdentifierData,
  type IdentifierKindInfo,
  type IdentifierProfileInfo,
  type IdentifierResult,
  type IdentifiersPort,
  type IdentifierTranslate,
  type Locale,
  type TableImportData,
} from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

export interface IdentifierInputs {
  port?: IdentifiersPort | null
  locale?: Locale
  onIdentifierChecked?: (result: IdentifierResult) => void
  onBatchChecked?: (answer: IdentifierBatchAnswer) => void
  onError?: (message: string) => void
}

export interface UseIdentifierCheck {
  t: IdentifierTranslate
  locale: Locale
  controller: IdentifierController
  state: IdentifierData
  table: TableImportData
  profile: IdentifierProfileInfo | null
  kinds: IdentifierKindInfo[]
  mapping: IdentifierBatchMapping
}

/** React-Anbindung von „Kennung prüfen“ aus `@auditcore/ui-core` (dieselbe Logik wie `useIdentifierCheck` in Vue). */
export function useIdentifierCheck(props: IdentifierInputs): UseIdentifierCheck {
  const { t, locale } = useTranslation(identifierMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createIdentifierController({
      port: () => latest.current.port ?? null,
      callbacks: () => ({
        checked: (result) => latest.current.onIdentifierChecked?.(result),
        batchChecked: (answer) => latest.current.onBatchChecked?.(answer),
        failed: (message) => latest.current.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  const table = useStoreState(controller.table.store)
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  return {
    t,
    locale,
    controller,
    state,
    table,
    profile: findIdentifierProfile(state.catalogue, state.profileId),
    kinds: identifierProfileKinds(state.catalogue, state.profileId),
    mapping: identifierBatchMapping(state, table),
  }
}
