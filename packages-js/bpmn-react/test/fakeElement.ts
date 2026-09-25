/** Stand-in for `<flowaudit-bpmn-editor>` that records what the wrapper sets. */

export class FakeEditorElement extends HTMLElement {
  xml?: string
  storage?: unknown
  ports?: unknown
  profileData?: unknown
  comments?: unknown
  propertyWrites: string[] = []

  async getXml(): Promise<string> {
    return this.xml ?? ''
  }

  async getSvg(): Promise<string> {
    return '<svg/>'
  }

  selected: string | null = null

  select(elementId: string): void {
    this.selected = elementId
  }

  emit(name: string, detail: unknown): void {
    this.dispatchEvent(new CustomEvent(name, { detail, bubbles: true }))
  }
}

export function defineFakeElement(): void {
  if (!customElements.get('flowaudit-bpmn-editor')) customElements.define('flowaudit-bpmn-editor', FakeEditorElement)
}
