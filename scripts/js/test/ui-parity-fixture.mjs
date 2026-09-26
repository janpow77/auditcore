/**
 * Synthetische Mini-Workspaces für die Tests des UI-Paritäts-Gates: ein
 * Vue-Paket, ein React-Paket und ein Kern mit einer Gruppe `demo`
 * (Web Component `<flowaudit-demo-list>`), die alle Regeln erfüllt.
 * Einzelne Dateien lassen sich überschreiben oder entfernen (Negativfälle).
 */
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'

const manifest = (name) => JSON.stringify({ name, type: 'module', exports: { '.': { types: './dist/index.d.ts', import: './dist/index.js' } } })

export const FIXTURE_FILES = {
  'packages-js/ui/package.json': manifest('@fixture/ui'),
  'packages-js/ui/src/index.ts': "export * from './demo'\n",
  'packages-js/ui/src/elements/define.ts': 'export interface ElementDefinition { tag: string; component: unknown }\n',
  'packages-js/ui/src/registry.ts': "import type { ElementDefinition } from './elements/define'\nimport { demoListElement } from './demo/element'\n\nexport const ELEMENTS: readonly ElementDefinition[] = [demoListElement]\n",
  'packages-js/ui/src/demo/DemoList.vue': '<script setup lang="ts">\n</script>\n<template><ul class="fa-demo" /></template>\n',
  'packages-js/ui/src/demo/DemoItem.vue': '<template><li /></template>\n',
  'packages-js/ui/src/demo/element.ts': "import type { ElementDefinition } from '../elements/define'\nimport DemoList from './DemoList.vue'\n\nexport const demoListElement: ElementDefinition = { tag: 'flowaudit-demo-list', component: DemoList }\n",
  'packages-js/ui/src/demo/index.ts': "export { default as DemoList } from './DemoList.vue'\nexport { default as FaDemoItem } from './DemoItem.vue'\nexport { demoListElement } from './element'\n",
  'packages-js/ui/test/parity-demo.spec.ts': "import { demoCases } from '../../ui-core/test/parity/cases-demo'\nimport DemoList from '../src/demo/DemoList.vue'\n\nexport const used = [demoCases, DemoList]\n",
  'packages-js/ui-react/package.json': JSON.stringify({ name: '@fixture/ui-react', type: 'module', exports: { '.': { types: './dist/index.d.ts', import: './dist/index.js' } }, peerDependencies: { react: '^19.0.0' }, devDependencies: { vue: '^3.5.0' } }),
  'packages-js/ui-react/src/index.ts': "export * from './demo'\nexport { LocaleProvider } from './i18n'\n",
  'packages-js/ui-react/src/i18n.tsx': 'export function LocaleProvider() {\n  return null\n}\n',
  'packages-js/ui-react/src/demo/index.ts': "export { FlowauditDemoList, type FlowauditDemoListProps } from './FlowauditDemoList'\nexport { DemoItem } from './DemoItem'\n",
  'packages-js/ui-react/src/demo/FlowauditDemoList.tsx': "import { useState } from 'react'\n\nexport interface FlowauditDemoListProps { label?: string }\n\nexport function FlowauditDemoList(props: FlowauditDemoListProps) {\n  const [state] = useState(props.label)\n  return <ul className=\"fa-demo\">{state}</ul>\n}\n",
  'packages-js/ui-react/src/demo/DemoItem.tsx': 'export const DemoItem = () => <li />\n',
  'packages-js/ui-react/test/parity/demo.spec.tsx': "import { demoCases } from '../../../ui-core/test/parity/cases-demo'\nimport { FlowauditDemoList } from '../../src/demo/FlowauditDemoList'\n\nexport const used = [demoCases, FlowauditDemoList]\n",
  'packages-js/ui-core/package.json': manifest('@fixture/ui-core'),
  'packages-js/ui-core/src/index.ts': "export * from './demo'\n",
  'packages-js/ui-core/src/store.ts': 'export function createStore<S>(initial: S) {\n  return { get: () => initial }\n}\n',
  'packages-js/ui-core/src/demo/index.ts': "export * from './controller'\n",
  'packages-js/ui-core/src/demo/controller.ts': "import { createStore } from '../store'\n\nexport function createDemoController() {\n  return { store: createStore({ items: [] }) }\n}\n",
  'packages-js/ui-core/styles/index.css': "@import './demo.css';\n",
  'packages-js/ui-core/styles/demo.css': '.fa-demo { display: block; }\n',
  'packages-js/ui-core/test/parity/cases.ts': 'export interface ParityCase { name: string }\n',
  'packages-js/ui-core/test/parity/cases-demo.ts': "import type { ParityCase } from './cases'\n\nexport const demoCases: ParityCase[] = [{ name: 'leer' }]\n",
}

/** Familie des Mini-Workspaces (gleiche Struktur wie `ui` in families.mjs). */
export const FIXTURE_FAMILY = {
  id: 'ui',
  vue: 'packages-js/ui',
  react: 'packages-js/ui-react',
  core: 'packages-js/ui-core',
  coreLayout: 'group',
  coreSrc: 'src',
  styles: 'packages-js/ui-core/styles',
  cases: 'packages-js/ui-core/test/parity',
  registry: 'packages-js/ui/src/registry.ts',
  groupOf: (relative) => (relative.includes('/') ? relative.split('/')[0] : 'root'),
}

/**
 * Mini-Workspace schreiben; `changes` überschreibt Dateien (Text) oder entfernt sie (`null`).
 * @param {Record<string, string | null>} changes
 */
export function writeFixture(changes = {}) {
  const root = mkdtempSync(join(tmpdir(), 'ui-parity-fixture-'))
  for (const [path, content] of Object.entries({ ...FIXTURE_FILES, ...changes })) {
    if (content === null) continue
    mkdirSync(dirname(join(root, path)), { recursive: true })
    writeFileSync(join(root, path), content)
  }
  return root
}

export const removeFixture = (root) => rmSync(root, { recursive: true, force: true })
