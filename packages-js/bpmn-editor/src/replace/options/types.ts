/**
 * Typen der Ersetzungsziele.
 */

export interface ReplaceTarget {
  type: string
  eventDefinitionType?: string
  isExpanded?: boolean
  triggeredByEvent?: boolean
  isInterrupting?: boolean
  cancelActivity?: boolean
  eventGatewayType?: 'Exclusive' | 'Parallel'
  instantiate?: boolean
}

export interface ReplaceOption {
  id: string
  label: string
  icon: string
  target: ReplaceTarget
  group?: string
}
