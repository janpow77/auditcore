import type { DataProtectionError, DataProtectionPort, Locale } from '@flowaudit/ui'
import { createElementComponent } from './createElementComponent'

export type FlowauditDataProtectionError = DataProtectionError

export interface FlowauditVvtProps {
  /** `createDataProtectionRestPort({ baseUrl: '/api/dataprotection' })` oder eigener Port. */
  port: DataProtectionPort | null
  /** Angemeldete Person (nur Vier-Augen-Hinweis; geprüft wird auf dem Server). */
  actor?: string
  editable?: boolean
  locale?: Locale
}

/** `<flowaudit-vvt>` als React-Komponente: Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO). */
export const FlowauditVvt = createElementComponent<
  FlowauditVvtProps,
  { onDraftSaved: string; onReleased: string; onExported: string; onError: string }
>('flowaudit-vvt', {
  properties: ['port', 'actor', 'editable', 'locale'],
  events: { onDraftSaved: 'draft-saved', onReleased: 'released', onExported: 'exported', onError: 'error' },
})

export interface FlowauditDsfaProps {
  port: DataProtectionPort | null
  /** Beim Laden zu öffnende Tätigkeit. */
  activityId?: string
  actor?: string
  editable?: boolean
  locale?: Locale
}

/** `<flowaudit-dsfa>` als React-Komponente: Schwellwertanalyse, Risiko, Entscheidung, Freigabe (Art. 35 DSGVO). */
export const FlowauditDsfa = createElementComponent<FlowauditDsfaProps, { onAssessmentChange: string; onError: string }>(
  'flowaudit-dsfa',
  {
    properties: ['port', 'activityId', 'actor', 'editable', 'locale'],
    events: { onAssessmentChange: 'assessment-change', onError: 'error' },
  },
)
