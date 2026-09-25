/**
 * diagram-js modules of the FlowAudit layer, ready for
 * `new BpmnEditor({ additionalModules, moddleExtensions, config })`.
 */

import { flowauditModdleDescriptor } from '../schema/descriptor'
import { colorContextPadModule } from './colorContextPad'
import { decorationsModule, type DecorationConfig } from './decorations'
import { highlightModule } from './highlight'
import { rolePaletteModule } from './rolePalette'
import { unknownElementsModule } from './unknownElementsModule'

export interface FlowauditModuleOptions extends DecorationConfig {
  /** Palette entries per role (default: on). */
  rolePalette?: boolean
  /** Own colour context pad entry (default: off – the core has one). */
  colorContextPad?: boolean
}

export function flowauditModules(options: FlowauditModuleOptions = {}): unknown[] {
  return [unknownElementsModule, decorationsModule, highlightModule, rolePaletteModule, ...(options.colorContextPad ? [colorContextPadModule] : [])]
}

/** Everything the editor needs: modules, moddle extension and module config. */
export function flowauditEditorOptions(options: FlowauditModuleOptions = {}): {
  additionalModules: unknown[]
  moddleExtensions: Record<string, unknown>
  config: Record<string, unknown>
} {
  return {
    additionalModules: flowauditModules(options),
    moddleExtensions: { flowaudit: flowauditModdleDescriptor },
    config: { flowaudit: options },
  }
}
