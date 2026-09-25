/** Declarative sections and fields of the diagram info dialog. */

import type { FieldDescriptor } from '../../panels/descriptors'

const info = (key: string, kind: FieldDescriptor['kind'] = 'text', extra: Partial<FieldDescriptor> = {}): FieldDescriptor => ({ key, label: `info.field.${key}`, kind, ...extra })

export interface InfoSection {
  id: string
  title: string
  fields: FieldDescriptor[]
}

export const INFO_SECTIONS: InfoSection[] = [
  {
    id: 'general',
    title: 'info.section.general',
    fields: [
      info('title', 'text', { wide: true }),
      info('subtitle', 'text', { wide: true }),
      info('description', 'textarea', { wide: true }),
      info('processOwner'),
      info('processType'),
      info('author'),
      info('keywords', 'tokens', { wide: true, placeholder: 'VerwK, Zahlungsantrag' }),
    ],
  },
  {
    id: 'scope',
    title: 'info.section.scope',
    fields: [info('programmingPeriod', 'select', { options: 'programmingPeriods' }), info('programme'), info('cci'), info('confidentiality', 'select', { options: 'confidentiality' }), info('variant', 'select', { options: 'variants' }), info('referenceDiagram'), info('systemCutoffDate', 'date')],
  },
  {
    id: 'status',
    title: 'info.section.status',
    fields: [info('version'), info('status', 'select', { options: 'diagramStatus' }), info('validFrom', 'date'), info('validUntil', 'date'), info('approvedBy'), info('approvedOn', 'date')],
  },
]
