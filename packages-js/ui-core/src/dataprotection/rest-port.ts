import { requestFile, requestJson, type RestOptions } from '@auditcore/common'
import type { DataProtectionPort } from './types'

const segment = encodeURIComponent

/** Port auf den REST-Vertrag `dataprotection_ui/1` von `auditcore_dataprotection.web`. */
export function createDataProtectionRestPort(options: RestOptions): DataProtectionPort {
  const one = (id: string, action = ''): string => `/assessments/${segment(id)}${action}`
  return {
    profile: () => requestJson(options, '/profile'),
    register: () => requestJson(options, '/register'),
    checkRegister: (content) => requestJson(options, '/register/check', { content }),
    saveDraft: (content, expectedRevision) =>
      requestJson(options, '/register/draft', { content, expected_revision: expectedRevision }),
    releaseRegister: (expectedRevision) => requestJson(options, '/register/release', { expected_revision: expectedRevision }),
    exportRegister: (format, source) =>
      requestFile(options, '/register/export', { format, source }, `verarbeitungsverzeichnis.${format === 'markdown' ? 'md' : format}`),
    overview: () => requestJson(options, '/assessments'),
    startAssessment: (activityId) => requestJson(options, '/assessments', { activity_id: activityId }),
    assessment: (id) => requestJson(options, one(id)),
    calculate: (answers, scenarios) => requestJson(options, '/calculate', { answers, scenarios }),
    updateAssessment: (id, expectedRevision, survey) => requestJson(options, one(id), { expected_revision: expectedRevision, ...survey }),
    decide: (id, expectedRevision, decision) => requestJson(options, one(id, '/decide'), { expected_revision: expectedRevision, ...decision }),
    requestDpo: (id, expectedRevision, requestedFrom, requestedOn) =>
      requestJson(options, one(id, '/dpo-request'), {
        expected_revision: expectedRevision,
        requested_from: requestedFrom,
        requested_on: requestedOn,
      }),
    releaseAssessment: (id, expectedRevision) => requestJson(options, one(id, '/release'), { expected_revision: expectedRevision }),
    reassess: (id) => requestJson(options, one(id, '/reassess'), {}),
    exportAssessment: (id, format) => requestFile(options, one(id, '/export'), { format }, `dsfa.${format === 'markdown' ? 'md' : 'html'}`),
  }
}
