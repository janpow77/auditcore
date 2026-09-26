/**
 * Vorlagen der Oberflächen für `npm run ui:neu`: Vue-SFC mit `useStore`,
 * Web Component, native React-Komponente mit `useStoreState`, Paritätstests
 * beider Fassungen und Doku-Stub. Gleiches Markup (Klassen, ARIA, Texte) in
 * Vue und React – der React-Paritätstest vergleicht das DOM.
 */

export const vueComponent = (n) => `<!-- ${n.component}: Liste mit Auswahl; Logik im Kern (${n.createController}). -->
<script setup lang="ts">
import { computed, watch } from 'vue'
import { ${n.createController}, ${n.messages}, ${n.group}IsEmpty, ${n.group}Rows, type ${n.Group}Item, type ${n.Group}Port } from '${n.corePackage}'
import { useStore } from '../composables/useStore'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. \`create${n.Group}MemoryPort([...])\`. */
  port?: ${n.Group}Port | null
  locale?: Locale
}>(), { port: null, locale: undefined })

const emit = defineEmits<{
  'item-select': [item: ${n.Group}Item]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(${n.messages}, () => props.locale)
const controller = ${n.createController}({
  port: () => props.port,
  callbacks: () => ({
    selected: (item) => emit('item-select', item),
    failed: (message) => emit('error', message),
  }),
})
const state = useStore(controller.store)
const rows = computed(() => ${n.group}Rows(state.value))
const empty = computed(() => ${n.group}IsEmpty(state.value))

watch(() => props.port, () => void controller.load(), { immediate: true })
</script>

<template>
  <section class="${n.css}" :lang="active" :aria-label="t('title')">
    <p v-if="state.busy === 'load'" class="${n.css}__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="${n.css}__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <p v-if="empty" class="${n.css}__muted">{{ t('empty') }}</p>
    <ul v-if="rows.length" class="${n.css}__list">
      <li v-for="row in rows" :key="row.id">
        <button type="button" :class="['${n.css}__item', row.selected && '${n.css}__item--selected']" :aria-pressed="row.selected" @click="controller.select(row.id)">{{ row.label }}</button>
      </li>
    </ul>
  </section>
</template>
`

export const vueElement = (n) => `import type { ElementDefinition } from '../elements/define'
import ${n.vue} from './${n.vue}.vue'

/** \`<${n.tag}>\`: Eigenschaften \`port\`, \`locale\`; Ereignisse \`item-select\`, \`error\`. */
export const ${n.element}: ElementDefinition = { tag: '${n.tag}', component: ${n.vue} }
`

export const vueIndex = (n) => `export { default as ${n.vue} } from './${n.vue}.vue'
export { ${n.element} } from './element'
/** Kern (Texte, Port, Zustandsautomat, Anzeige) aus \`${n.corePackage}\`. */
export {
  ${n.messages},
  ${n.createController},
  create${n.Group}MemoryPort,
  ${n.initial},
  type ${n.Group}Controller,
  type ${n.Group}Data,
  type ${n.Group}Item,
  type ${n.Group}Port,
} from '${n.corePackage}'
`

export const reactComponent = (n) => `import { useEffect, useRef, useState } from 'react'
import { ${n.createController}, ${n.messages}, ${n.group}IsEmpty, ${n.group}Rows, type ${n.Group}Item, type ${n.Group}Port, type Locale } from '${n.corePackage}'
import { useTranslation } from '../i18n'
import { classes, useStoreState } from '../store'

export interface ${n.react}Props {
  port?: ${n.Group}Port | null
  locale?: Locale
  onItemSelect?: (item: ${n.Group}Item) => void
  onError?: (message: string) => void
}

/**
 * ${n.component} als native React-Komponente (Vertrag wie \`<${n.tag}>\`):
 * Liste mit Auswahl. Ereignisse: \`onItemSelect\`, \`onError\`.
 */
export function ${n.react}(props: ${n.react}Props) {
  const { t, locale } = useTranslation(${n.messages}, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    ${n.createController}({
      port: () => latest.current.port ?? null,
      callbacks: () => ({
        selected: (item) => latest.current.onItemSelect?.(item),
        failed: (message) => latest.current.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  const rows = ${n.group}Rows(state)
  return (
    <section className="${n.css}" lang={locale} aria-label={t('title')}>
      {state.busy === 'load' ? <p className="${n.css}__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="${n.css}__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {${n.group}IsEmpty(state) ? <p className="${n.css}__muted">{t('empty')}</p> : null}
      {rows.length ? (
        <ul className="${n.css}__list">
          {rows.map((row) => (
            <li key={row.id}>
              <button type="button" className={classes('${n.css}__item', row.selected && '${n.css}__item--selected')} aria-pressed={row.selected} onClick={() => controller.select(row.id)}>{row.label}</button>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}
`

export const reactIndex = (n) => `export { ${n.react}, type ${n.react}Props } from './${n.react}'
export { create${n.Group}MemoryPort, type ${n.Group}Item, type ${n.Group}Port } from '${n.corePackage}'
`

export const vueParitySpec = (n) => `// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-${n.group}.ts) gegen
// die Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht
// zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { ${n.cases} } from '../../ui-core/test/parity/cases-${n.group}'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import ${n.vue} from '../src/${n.group}/${n.vue}.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle ${n.component} (Vue)', () => {
  for (const entry of ${n.cases}) {
    it(entry.name, async () => {
      const wrapper = mount(${n.vue}, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
`

export const reactParitySpec = (n) => `import { describe, expect, it } from 'vitest'
import ${n.vue} from '../../../ui/src/${n.group}/${n.vue}.vue'
import { create${n.Group}MemoryPort } from '../../../ui-core/src'
import { ${n.cases}, ${n.group}Items } from '../../../ui-core/test/parity/cases-${n.group}'
import { ${n.react} } from '../../src/${n.group}/${n.react}'
import { both } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität ${n.component} Vue ↔ React', () => {
  for (const entry of ${n.cases}) {
    it(entry.name, async () => {
      const rendered = await renderBoth(${n.vue}, { ...entry.props() }, <${n.react} {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität ${n.component} nach Interaktion', () => {
  it('Eintrag auswählen', async () => {
    const port = create${n.Group}MemoryPort(${n.group}Items)
    const rendered = await renderBoth(${n.vue}, { port }, <${n.react} port={port} />)
    await both(rendered, (root) => root.querySelectorAll('button')[1], { kind: 'click' })
    expect(rendered.react.querySelectorAll('[aria-pressed="true"]')).toHaveLength(1)
  })
})
`

export const docStub = (n) => `# ${n.component} (\`${n.vue}\` ↔ \`${n.react}\`)

Gerüst erzeugt mit \`npm run ui:neu -- ${n.group} ${n.component}\`; Fachinhalt ergänzen.

| Schicht | Datei |
|---|---|
| Kern | \`packages-js/ui-core/src/${n.group}/\` (\`${n.createController}\`, \`${n.messages}\`, Port, Anzeige) |
| Stil | \`packages-js/ui-core/styles/${n.group}.css\` |
| Vue / Web Component | \`${n.vue}\` / \`<${n.tag}>\` (\`packages-js/ui/src/${n.group}/\`) |
| React | \`${n.react}\` (\`packages-js/ui-react/src/${n.group}/\`) |
| Paritätsfälle | \`packages-js/ui-core/test/parity/cases-${n.group}.ts\` |

## Vertrag

Eigenschaften: \`port\`, \`locale\`. Ereignisse: \`item-select\` (React \`onItemSelect\`),
\`error\` (React \`onError\`).

## Offen

- REST-Vertrag des Backends und Port-Umsetzung beschreiben.
- Demo-Seite (\`packages-js/ui/demo/pages/${n.group}/\`) und Browser-Test (\`packages-js/ui/e2e/${n.group}.e2e.ts\`).
`
