import { requestJson, type RestOptions } from '@flowaudit/common'
import type { RunQuery, ScreeningPort } from './types'

const segment = encodeURIComponent

function withQuery(path: string, query: RunQuery = {}): string {
  const params = new URLSearchParams(Object.entries(query).filter(([, value]) => value !== undefined && value !== ''))
  const text = params.toString()
  return text ? `${path}?${text}` : path
}

/** Port auf den REST-Vertrag `screening_review/1` von `auditcore_registry_sources.web`. */
export function createScreeningRestPort(options: RestOptions): ScreeningPort {
  const hit = (runId: string, hitId: string): string => `/runs/${segment(runId)}/hits/${segment(hitId)}`
  return {
    settings: () => requestJson(options, '/settings'),
    sources: () => requestJson(options, '/sources'),
    runs: () => requestJson(options, '/runs'),
    createRun: (request) => requestJson(options, '/runs', request),
    run: (runId, query) => requestJson(options, withQuery(`/runs/${segment(runId)}`, query)),
    log: (runId) => requestJson(options, `/runs/${segment(runId)}/log`),
    decide: (runId, hitId, decision) => requestJson(options, `${hit(runId, hitId)}/decision`, decision),
    secondReview: (runId, hitId, review) => requestJson(options, `${hit(runId, hitId)}/second-review`, review),
  }
}
