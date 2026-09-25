/**
 * Creates the core editor with the FlowAudit layer. Tests and applications
 * may pass their own factory (e.g. a fake editor).
 */

import { BpmnEditor } from '@flowaudit/bpmn-editor'
import { flowauditEditorOptions, type FlowauditModuleOptions, type ServiceLocator } from '@flowaudit/bpmn-flowaudit'

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

export const defaultEditorFactory: EditorFactory = (options) => {
  const extension = flowauditEditorOptions(options.flowaudit)
  return new BpmnEditor({
    container: options.container,
    locale: options.locale,
    keyboard: { bindTo: options.keyboardTarget ?? options.container },
    additionalModules: extension.additionalModules,
    moddleExtensions: extension.moddleExtensions,
    config: extension.config,
  }) as unknown as EditorLike
}
