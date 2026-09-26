import { computed, type ComputedRef, type Ref } from 'vue'
import {
  createIdentifierController,
  findIdentifierProfile,
  identifierBatchMapping,
  identifierProfileKinds,
  type IdentifierBatchMapping,
  type IdentifierCallbacks,
  type IdentifierController,
  type IdentifierData,
  type IdentifierKindInfo,
  type IdentifierProfileInfo,
  type IdentifiersPort,
  type TableImportData,
} from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export type { IdentifierCallbacks } from '@auditcore/ui-core'

export interface UseIdentifierCheck {
  controller: IdentifierController
  state: Readonly<Ref<IdentifierData>>
  table: Readonly<Ref<TableImportData>>
  profile: ComputedRef<IdentifierProfileInfo | null>
  kinds: ComputedRef<IdentifierKindInfo[]>
  mapping: ComputedRef<IdentifierBatchMapping>
}

/** Vue-Anbindung von „Kennung prüfen“ aus `@auditcore/ui-core` (`createIdentifierController`). */
export function useIdentifierCheck(port: () => IdentifiersPort | null, callbacks: IdentifierCallbacks = {}): UseIdentifierCheck {
  const controller = createIdentifierController({ port, callbacks: () => callbacks })
  const state = useStore(controller.store)
  const table = useStore(controller.table.store)
  return {
    controller,
    state,
    table,
    profile: computed(() => findIdentifierProfile(state.value.catalogue, state.value.profileId)),
    kinds: computed(() => identifierProfileKinds(state.value.catalogue, state.value.profileId)),
    mapping: computed(() => identifierBatchMapping(state.value, table.value)),
  }
}
