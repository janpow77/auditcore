/**
 * Contract of `@flowaudit/bpmn-editor` (docs of the core package) for type
 * checking before the core exists in the checkout.
 */
declare module '@flowaudit/bpmn-editor' {
  export interface EditorOptions {
    container: HTMLElement
    additionalModules?: unknown[]
    moddleExtensions?: Record<string, unknown>
    keyboard?: { bindTo?: EventTarget }
    gridSize?: number
    locale?: 'de' | 'en'
    config?: Record<string, unknown>
  }
  export class BpmnEditor {
    constructor(options: EditorOptions)
    importXML(xml: string): Promise<{ warnings: string[] }>
    saveXML(opts?: { format?: boolean }): Promise<{ xml: string }>
    saveSVG(): Promise<{ svg: string }>
    createDiagram(): Promise<void>
    get<T = unknown>(service: string, strict?: boolean): T
    on(event: string, cb: (e: unknown) => void, priority?: number): void
    off(event: string, cb: (e: unknown) => void): void
    destroy(): void
  }
  export const translations: Record<string, string>
}
