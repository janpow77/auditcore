import { computed, type ComputedRef, type Ref } from 'vue'
import {
  createReportingController,
  reportingProfile,
  type FormatProfile,
  type ReportingCallbacks,
  type ReportingController,
  type ReportingData,
  type ReportingPort,
  type ReportTableInput,
} from '@flowaudit/ui-core'
import { useStore } from '../composables/useStore'

export type { ReportingCallbacks } from '@flowaudit/ui-core'

export interface UseReportExport {
  controller: ReportingController
  state: Readonly<Ref<ReportingData>>
  profile: ComputedRef<FormatProfile | null>
}

/** Vue-Anbindung des Tabellenexports aus `@flowaudit/ui-core` (`createReportingController`). */
export function useReportExport(
  port: () => ReportingPort | null,
  tables: () => readonly ReportTableInput[],
  callbacks: ReportingCallbacks = {},
): UseReportExport {
  const controller = createReportingController({ port, tables, callbacks: () => callbacks })
  const state = useStore(controller.store)
  return { controller, state, profile: computed(() => reportingProfile(state.value)) }
}
