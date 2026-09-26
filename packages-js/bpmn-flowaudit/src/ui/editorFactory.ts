/**
 * Creates the core editor with the FlowAudit layer. The core class is passed
 * in (`@flowaudit/bpmn-editor` is a peer of the UI packages), so this module
 * stays free of the core and of any UI framework. Tests and applications may
 * pass their own factory (e.g. a fake editor).
 */

import { flowauditEditorOptions, type FlowauditModuleOptions } from '../diagram/modules'
import type { ServiceLocator } from '../diagram/services'

/** The part of `BpmnEditor` the UI uses (contract of @flowaudit/bpmn-editor). */
export interface EditorLike extends ServiceLocator {
  importXML(xml: string): Promise<{ warnings: string[] }>
  saveXML(options?: { format?: boolean }): Promise<{ xml: string }>
  saveSVG(): Promise<{ svg: string }>
  on(event: string, callback: (event: unknown) => void, priority?: number): void
  off(event: string, callback: (event: unknown) => void): void
  destroy(): void
}

export interface CreateEditorOptions {
  container: HTMLElement
  locale: 'de' | 'en'
  flowaudit: FlowauditModuleOptions
  keyboardTarget?: EventTarget
}

export type EditorFactory = (options: CreateEditorOptions) => EditorLike

/** Constructor options of `BpmnEditor` used by the factory. */
export interface CoreEditorOptions {
  container: HTMLElement
  locale: 'de' | 'en'
  keyboard: { bindTo: EventTarget }
  additionalModules: unknown[]
  moddleExtensions: Record<string, unknown>
  config: Record<string, unknown>
}

/** Factory for the given core editor class (`BpmnEditor` of @flowaudit/bpmn-editor). */
export function createEditorFactory(Editor: new (options: CoreEditorOptions) => unknown): EditorFactory {
  return (options) => {
    const extension = flowauditEditorOptions(options.flowaudit)
    return new Editor({
      container: options.container,
      locale: options.locale,
      keyboard: { bindTo: options.keyboardTarget ?? options.container },
      additionalModules: extension.additionalModules,
      moddleExtensions: extension.moddleExtensions,
      config: extension.config,
    }) as EditorLike
  }
}
