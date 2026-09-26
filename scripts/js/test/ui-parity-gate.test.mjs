// Tests des UI-Paritäts-Gates mit synthetischen Mini-Workspaces (positiv und negativ).
import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { after, describe, it } from 'node:test'
import { runGate } from '../ui-parity-gate.mjs'
import { applyExceptions, ratchetProblems } from '../ui-parity/exceptions.mjs'
import { FIXTURE_FAMILY, FIXTURE_FILES, removeFixture, writeFixture } from './ui-parity-fixture.mjs'

const TODAY = '2026-09-26'
const roots = []
after(() => roots.forEach(removeFixture))

function gate(changes, options = {}) {
  const root = writeFixture(changes)
  roots.push(root)
  return { root, report: runGate({ root, families: [FIXTURE_FAMILY], today: TODAY, ...options }) }
}

const openIds = (report) => report.open.map((item) => item.id)
const exceptionsFile = (entries) => JSON.stringify({ exceptions: entries })

describe('UI-Paritäts-Gate: vollständige Gruppe', () => {
  it('besteht und erkennt Komponenten, Web Component und Gruppe', () => {
    const { report } = gate({})
    assert.equal(report.status, 'PASS', JSON.stringify(report.open))
    assert.deepEqual(report.families[0], { family: 'ui', vueComponents: 2, reactComponents: 2, groups: ['demo'] })
  })
})

describe('UI-Paritäts-Gate: Lücken (fail closed)', () => {
  it('Vue-Komponente ohne React-Fassung', () => {
    const { report } = gate({ 'packages-js/ui-react/src/demo/index.ts': "export { DemoItem } from './DemoItem'\n" })
    assert.equal(report.status, 'FAIL')
    assert.deepEqual(openIds(report), ['react-missing:ui:DemoList'])
    assert.match(report.open[0].message, /erwartet: FlowauditDemoList/)
  })

  it('neue Web Component in ELEMENTS ohne React-Fassung', () => {
    const registry = FIXTURE_FILES['packages-js/ui/src/registry.ts'].replace('import { demoListElement }', "import { demoCardElement } from './demo/card'\nimport { demoListElement }").replace('[demoListElement]', '[demoListElement, demoCardElement]')
    const { report } = gate({
      'packages-js/ui/src/registry.ts': registry,
      'packages-js/ui/src/demo/DemoCard.vue': '<template><div /></template>\n',
      'packages-js/ui/src/demo/card.ts': "import DemoCard from './DemoCard.vue'\n\nexport const demoCardElement = { tag: 'flowaudit-demo-card', component: DemoCard }\n",
    })
    assert.deepEqual(openIds(report), ['react-missing:ui:demoCardElement'])
    assert.match(report.open[0].message, /FlowauditDemoCard/)
  })

  it('React-Komponente ohne Vue-Gegenstück', () => {
    const { report } = gate({
      'packages-js/ui-react/src/demo/index.ts': `${FIXTURE_FILES['packages-js/ui-react/src/demo/index.ts']}export { DemoExtra } from './DemoExtra'\n`,
      'packages-js/ui-react/src/demo/DemoExtra.tsx': 'export function DemoExtra() {\n  return null\n}\n',
    })
    assert.deepEqual(openIds(report), ['vue-missing:ui:DemoExtra'])
  })

  it('Kern ohne Controller, ohne Export, ohne Stil', () => {
    const { report } = gate({
      'packages-js/ui-core/src/demo/controller.ts': 'export const demo = 1\n',
      'packages-js/ui-core/src/index.ts': "export * from './store'\n",
      'packages-js/ui-core/styles/index.css': '',
    })
    assert.deepEqual(openIds(report), ['core-controller:ui:demo', 'core-export:ui:demo', 'style-missing:ui:demo'])
  })

  it('Kernmodul fehlt', () => {
    const { report } = gate({ 'packages-js/ui-core/src/demo/index.ts': null, 'packages-js/ui-core/src/demo/controller.ts': null })
    assert.deepEqual(openIds(report), ['core-controller:ui:demo', 'core-missing:ui:demo'])
  })

  it('Paritätsfälle nur im Vue-Test oder gar nicht', () => {
    const onlyVue = gate({ 'packages-js/ui-react/test/parity/demo.spec.tsx': "import { FlowauditDemoList } from '../../src/demo/FlowauditDemoList'\n\nexport const used = [FlowauditDemoList]\n" })
    assert.deepEqual(openIds(onlyVue.report), ['parity-cases:ui:demo'])
    assert.match(onlyVue.report.open[0].message, /nicht zugleich/)
    const none = gate({ 'packages-js/ui-core/test/parity/cases-demo.ts': null })
    assert.match(none.report.open[0].message, /keine Datei .*cases-demo\.ts/)
  })

  it('ein Test, der Vue und React rendert, genügt', () => {
    const { report } = gate({
      'packages-js/ui/test/parity-demo.spec.ts': null,
      'packages-js/ui-react/test/parity/demo.spec.tsx': "import DemoList from '../../../ui/src/demo/DemoList.vue'\nimport { demoCases } from '../../../ui-core/test/parity/cases-demo'\nimport { FlowauditDemoList } from '../../src/demo/FlowauditDemoList'\n\nexport const used = [DemoList, demoCases, FlowauditDemoList]\n",
    })
    assert.equal(report.status, 'PASS', JSON.stringify(report.open))
  })

  it('Vue im React-Paket: Import und Laufzeitabhängigkeit', () => {
    const { report } = gate({
      'packages-js/ui-react/src/demo/DemoItem.tsx': "import { ref } from 'vue'\n\nexport const DemoItem = () => <li>{String(ref)}</li>\n",
      'packages-js/ui-react/package.json': JSON.stringify({ name: '@fixture/ui-react', exports: { '.': { types: './dist/index.d.ts' } }, dependencies: { '@fixture/ui': '0.1.0' } }),
    })
    assert.deepEqual(openIds(report), ['vue-dependency:ui:@fixture/ui', 'vue-import:ui:src/demo/DemoItem.tsx:vue'])
  })
})

describe('UI-Paritäts-Gate: Ausnahmen', () => {
  const missingReact = { 'packages-js/ui-react/src/demo/index.ts': "export { DemoItem } from './DemoItem'\n" }
  const entry = { id: 'react-missing:ui:DemoList', reason: 'React-Fassung folgt mit der nächsten Ausbaustufe.', expires: '2027-01-31' }

  it('gültige Ausnahme lässt die Lücke durch', () => {
    const { report } = gate({ ...missingReact, 'quality/ui-parity-exceptions.json': exceptionsFile([entry]) })
    assert.equal(report.status, 'PASS')
    assert.deepEqual(report.excepted.map((item) => item.id), [entry.id])
  })

  it('abgelaufene, zu lange, unbegründete und überflüssige Ausnahmen schlagen fehl', () => {
    const today = new Date(`${TODAY}T00:00:00Z`)
    const violations = [{ id: entry.id }]
    const expired = applyExceptions(violations, [{ ...entry, expires: '2026-09-25' }], today)
    assert.deepEqual(expired.open.map((item) => item.id), [entry.id])
    assert.match(expired.problems[0], /abgelaufen/)
    assert.match(applyExceptions(violations, [{ ...entry, expires: '2028-01-01' }], today).problems[0], /366 Tage/)
    assert.match(applyExceptions(violations, [{ ...entry, reason: 'kurz' }], today).problems[0], /Begründung/)
    assert.match(applyExceptions([], [entry], today).problems[0], /besteht nicht mehr/)
  })

  it('Ratchet: keine neuen Ausnahmen, keine Verlängerung', () => {
    assert.deepEqual(ratchetProblems([entry], null), [])
    assert.match(ratchetProblems([entry], [])[0], /neue Ausnahme/)
    assert.match(ratchetProblems([{ ...entry, expires: '2027-02-28' }], [entry])[0], /verlängert/)
    assert.deepEqual(ratchetProblems([], [entry]), [])
  })

  it('Ratchet gegen einen Git-Vergleichsstand', () => {
    const { root } = gate({ ...missingReact, 'quality/ui-parity-exceptions.json': exceptionsFile([]) })
    const git = (...args) => execFileSync('git', args, { cwd: root, stdio: 'ignore' })
    git('init', '-q')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-q', '--allow-empty', '-m', 'basis')
    git('add', '-A')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-q', '-m', 'ohne Ausnahmen')
    writeFileSync(join(root, 'quality/ui-parity-exceptions.json'), exceptionsFile([entry]))
    const report = runGate({ root, families: [FIXTURE_FAMILY], today: TODAY, compareRef: 'HEAD' })
    assert.equal(report.status, 'FAIL')
    assert.match(report.problems.join('\n'), /neue Ausnahme/)
    const bootstrap = runGate({ root, families: [FIXTURE_FAMILY], today: TODAY, compareRef: 'HEAD~1' })
    assert.equal(bootstrap.status, 'PASS')
    assert.throws(() => runGate({ root, families: [FIXTURE_FAMILY], today: TODAY, compareRef: 'gibt-es-nicht' }), /unbekannt/)
  })
})

describe('UI-Paritäts-Gate: Bestand', () => {
  it('der Workspace besteht (mit den befristeten Ausnahmen)', () => {
    const report = runGate({ root: join(import.meta.dirname, '..', '..', '..') })
    assert.equal(report.status, 'PASS', [...report.open.map((item) => item.message), ...report.problems].join('\n'))
    assert.ok(report.families.find((family) => family.family === 'ui').vueComponents >= 17)
  })
})
