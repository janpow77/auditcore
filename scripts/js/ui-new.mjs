#!/usr/bin/env node
/**
 * Gerüst einer neuen Oberflächenkomponente in Vue UND React mit gemeinsamem
 * Kern und gemeinsamen Paritätsfällen – ohne Handarbeit, ohne LLM.
 *
 *   npm run ui:neu -- <gruppe> <Komponente>
 *   npm run ui:neu -- audittrail AuditTrail
 *
 * Erzeugt Kern (ui-core/src/<gruppe>/: messages, types, port, view, controller,
 * index + Test), Stil (ui-core/styles/<gruppe>.css + index.css), Vue-SFC mit
 * useStore, Web Component (registry.ts ELEMENTS), React-Komponente mit
 * useStoreState, Exporte in allen index.ts, cases-<gruppe>.ts, Vue- und
 * React-Paritätstest und einen Doku-Stub. Danach gilt: lint, typecheck, test
 * und das UI-Paritäts-Gate laufen grün. Vorhandene Dateien werden nie
 * überschrieben.
 */
import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import * as core from './ui-new/core-templates.mjs'
import * as view from './ui-new/view-templates.mjs'

const DEFAULT_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
const GROUP = /^[a-z][a-z0-9]{1,29}$/
const COMPONENT = /^(?:[A-Z][a-z0-9]+)+$/

const kebab = (pascal) => pascal.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase()
const upperFirst = (text) => text.charAt(0).toUpperCase() + text.slice(1)
const lowerFirst = (text) => text.charAt(0).toLowerCase() + text.slice(1)

/** npm-Namen der Kernpakete aus dem Workspace (Scope nicht fest verdrahtet). */
export function workspacePackages(root) {
  const nameOf = (dir) => JSON.parse(readFileSync(join(root, 'packages-js', dir, 'package.json'), 'utf8')).name
  return { corePackage: nameOf('ui-core'), commonPackage: nameOf('common') }
}

/** Alle abgeleiteten Namen aus Gruppe und Komponente. */
export function namesFor(group, component, packages) {
  if (!GROUP.test(group)) throw new Error(`Gruppe "${group}": kurz, klein, englisch, nur a-z und 0-9 (z. B. audittrail).`)
  if (!COMPONENT.test(component)) throw new Error(`Komponente "${component}": PascalCase aus Wörtern (z. B. AuditTrail).`)
  const Group = upperFirst(group)
  return {
    ...packages,
    group,
    Group,
    component,
    vue: component,
    react: `Flowaudit${component}`,
    tag: `flowaudit-${kebab(component)}`,
    element: `${lowerFirst(component)}Element`,
    css: `fa-${group}`,
    messages: `${group}Messages`,
    createController: `create${Group}Controller`,
    initial: `INITIAL_${group.toUpperCase()}`,
    cases: `${group}Cases`,
  }
}

/** Neue Dateien relativ zur Wurzel. */
export function plannedFiles(n) {
  const coreDir = `packages-js/ui-core/src/${n.group}`
  return {
    [`${coreDir}/messages.ts`]: core.coreMessages(n),
    [`${coreDir}/types.ts`]: core.coreTypes(n),
    [`${coreDir}/port.ts`]: core.corePort(n),
    [`${coreDir}/view.ts`]: core.coreView(n),
    [`${coreDir}/controller.ts`]: core.coreController(n),
    [`${coreDir}/index.ts`]: core.coreIndex(n),
    [`packages-js/ui-core/test/${n.group}/controller.spec.ts`]: core.coreTest(n),
    [`packages-js/ui-core/styles/${n.group}.css`]: core.coreStyle(n),
    [`packages-js/ui-core/test/parity/cases-${n.group}.ts`]: core.parityCases(n),
    [`packages-js/ui/src/${n.group}/${n.vue}.vue`]: view.vueComponent(n),
    [`packages-js/ui/src/${n.group}/element.ts`]: view.vueElement(n),
    [`packages-js/ui/src/${n.group}/index.ts`]: view.vueIndex(n),
    [`packages-js/ui/test/parity-${n.group}.spec.ts`]: view.vueParitySpec(n),
    [`packages-js/ui-react/src/${n.group}/${n.react}.tsx`]: view.reactComponent(n),
    [`packages-js/ui-react/src/${n.group}/index.ts`]: view.reactIndex(n),
    [`packages-js/ui-react/test/parity/${n.group}.spec.tsx`]: view.reactParitySpec(n),
    [`docs/ui/${n.group}.md`]: view.docStub(n),
  }
}

/** Zeile hinter der letzten Zeile einfügen, die `pattern` erfüllt. */
export function insertAfterLast(text, pattern, line) {
  const lines = text.split('\n')
  const index = lines.findLastIndex((entry) => pattern.test(entry))
  if (index < 0) throw new Error(`Einfügestelle ${pattern} nicht gefunden`)
  lines.splice(index + 1, 0, line)
  return lines.join('\n')
}

function addToRegistry(text, n) {
  const withImport = insertAfterLast(text, /^import /, `import { ${n.element} } from './${n.group}/element'`)
  const list = /(export const ELEMENTS: readonly ElementDefinition\[\] = \[)([\s\S]*?)(\])/
  if (!list.test(withImport)) throw new Error('ELEMENTS in registry.ts nicht gefunden')
  return withImport.replace(list, (_, open, body, close) => `${open}${body.trimEnd()}, ${n.element}${close}`)
}

function addParityRow(text, n) {
  const lines = text.split('\n')
  const header = lines.findIndex((line) => line.startsWith('| Komponente | Vue | React (nativ) |'))
  if (header < 0) return text
  let end = header
  while (lines[end + 1]?.startsWith('|')) end += 1
  lines.splice(end + 1, 0, `| ${n.component} | \`${n.vue}\` | \`${n.react}\` | – ([${n.group}.md](${n.group}.md)) | 3 + Interaktionsfolge |`)
  return lines.join('\n')
}

/** Änderungen an bestehenden Dateien (Exporte, Registrierung, Stil, Doku). */
export function plannedEdits(n) {
  const groupExport = /^export \* from '\.\/[a-z0-9]+'$/
  return {
    'packages-js/ui-core/src/index.ts': (text) => insertAfterLast(text, groupExport, `export * from './${n.group}'`),
    'packages-js/ui-core/styles/index.css': (text) => insertAfterLast(text, /^@import /, `@import './${n.group}.css';`),
    'packages-js/ui/src/index.ts': (text) => insertAfterLast(text, groupExport, `export * from './${n.group}'`),
    'packages-js/ui/src/registry.ts': (text) => addToRegistry(text, n),
    'packages-js/ui-react/src/index.ts': (text) => insertAfterLast(text, groupExport, `export * from './${n.group}'`),
    'docs/ui/react-paritaet.md': (text) => addParityRow(text, n),
  }
}

/** Gerüst schreiben; bricht ab, bevor irgendetwas geschrieben wird, wenn die Gruppe schon existiert. */
export function generate(root, group, component) {
  const n = namesFor(group, component, workspacePackages(root))
  const files = plannedFiles(n)
  const taken = [`packages-js/ui/src/${group}`, `packages-js/ui-core/src/${group}`, `packages-js/ui-react/src/${group}`, ...Object.keys(files)]
    .filter((path) => existsSync(join(root, path)))
  if (taken.length) throw new Error(`Bereits vorhanden: ${taken.join(', ')}`)
  const edits = Object.entries(plannedEdits(n)).map(([path, edit]) => [path, edit(readFileSync(join(root, path), 'utf8'))])
  for (const [path, content] of Object.entries(files)) {
    mkdirSync(dirname(join(root, path)), { recursive: true })
    writeFileSync(join(root, path), content)
  }
  for (const [path, content] of edits) writeFileSync(join(root, path), content)
  return { names: n, created: Object.keys(files), changed: edits.map(([path]) => path) }
}

function refreshApiOverview(root) {
  const packages = ['packages-js/ui', 'packages-js/ui-core', 'packages-js/ui-react']
  const result = spawnSync('python3', ['scripts/docs/api_overview.py', '--write', ...packages], { cwd: root, stdio: 'inherit' })
  if (result.status !== 0) console.warn('Hinweis: README-API-Überblick nicht erneuert – python3 scripts/docs/api_overview.py --write --js ausführen.')
}

function parseArgs(argv) {
  const options = { root: DEFAULT_ROOT, apiOverview: true, positional: [] }
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '--root') {
      options.root = resolve(argv[index + 1])
      index += 1
    } else if (arg === '--no-api-overview') options.apiOverview = false
    else options.positional.push(arg)
  }
  return options
}

function main(argv) {
  const { root, apiOverview, positional } = parseArgs(argv)
  const [group, component] = positional
  if (!group || !component) {
    console.error('Aufruf: npm run ui:neu -- <gruppe> <Komponente>   (z. B. npm run ui:neu -- audittrail AuditTrail)')
    return 2
  }
  const result = generate(root, group, component)
  if (apiOverview) refreshApiOverview(root)
  console.log(`Erzeugt (${result.created.length}):\n  ${result.created.join('\n  ')}`)
  console.log(`Ergänzt (${result.changed.length}):\n  ${result.changed.join('\n  ')}`)
  console.log(`\nVue ${result.names.vue} · Web Component <${result.names.tag}> · React ${result.names.react}`)
  console.log('Weiter: npm run lint && npm run typecheck && npm test && npm run ui:gate')
  return 0
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    process.exit(main(process.argv.slice(2)))
  } catch (error) {
    console.error(`ui:neu: ${error instanceof Error ? error.message : String(error)}`)
    process.exit(1)
  }
}
