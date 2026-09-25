import { defineComponent, h, type Component } from 'vue'
import { mount } from '@vue/test-utils'
import type { ProfileData } from '@flowaudit/bpmn-flowaudit'
import { provideEditorContext, type EditorContext, type EditorPorts } from '../src/stores/context'

/** Mounts a component inside a minimal editor context (no core editor). */
export function mountInContext(component: Component, props: Record<string, unknown>, options: { readonly?: boolean; profile?: ProfileData | null; ports?: EditorPorts } = {}) {
  const context = {
    editor: { state: { ready: false, changes: 0 } },
    selection: {},
    validation: {},
    ports: options.ports ?? {},
    profile: () => options.profile ?? null,
    readonly: () => options.readonly ?? false,
  } as unknown as EditorContext
  const Host = defineComponent({
    setup(_, { attrs }) {
      provideEditorContext(context)
      return () => h(component, attrs)
    },
  })
  return mount(Host, { props, attachTo: document.body })
}
