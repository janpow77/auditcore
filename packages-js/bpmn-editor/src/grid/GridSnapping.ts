/**
 * Einrasten am Raster mit einstellbarer Rasterweite (`gridSize`, Standard 10).
 */

import BaseGridSnapping from 'diagram-js/lib/features/grid-snapping/GridSnapping'

import type { ElementRegistry, EventBus } from '../types'

type SnapOptions = { min?: number; max?: number; offset?: number }

function quantize(value: number, spacing: number, fn: 'round' | 'ceil' | 'floor' = 'round'): number {
  return Math[fn](value / spacing) * spacing
}

export default class GridSnapping extends BaseGridSnapping {
  static $inject = ['elementRegistry', 'eventBus', 'config.gridSnapping', 'config.gridSize']

  private readonly spacing: number

  constructor(elementRegistry: ElementRegistry, eventBus: EventBus, config: { active?: boolean } | undefined, gridSize?: number) {
    super(elementRegistry as never, eventBus, config)
    this.spacing = gridSize && gridSize > 0 ? gridSize : 10
  }

  getGridSpacing(): number {
    return this.spacing
  }

  snapValue(value: number, options?: SnapOptions): number {
    const offset = options?.offset || 0
    let result = quantize(value + offset, this.spacing) - offset
    if (options?.min !== undefined) {
      const min = quantize(options.min + offset, this.spacing, 'ceil') - offset
      result = Math.max(result, min)
    }
    if (options?.max !== undefined) {
      const max = quantize(options.max + offset, this.spacing, 'floor') - offset
      result = Math.min(result, max)
    }
    return result
  }
}
