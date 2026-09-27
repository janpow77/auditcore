import type { RunnerController, RunnerData, RunnerMessageKey, Translate } from '@auditcore/ui-core'

export interface BereichProps {
  state: RunnerData
  controller: RunnerController
  t: Translate<RunnerMessageKey>
}
