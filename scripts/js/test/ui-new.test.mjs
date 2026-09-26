// Test des Generators `npm run ui:neu`: in einer temporären Kopie des
// Workspaces erzeugen, dann Gate, Lint, Typprüfung und die erzeugten Tests.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { readFileSync, rmSync } from 'node:fs'
import { join } from 'node:path'
import { after, before, describe, it } from 'node:test'
import { generate, namesFor } from '../ui-new.mjs'
import { runGate } from '../ui-parity-gate.mjs'
import { copyWorkspace } from './workspace-copy.mjs'

const ROOT = join(import.meta.dirname, '..', '..', '..')
const PACKAGES = { corePackage: '@scope/ui-core', commonPackage: '@scope/common' }
const LONG = { timeout: 600_000 }

function run(cwd, command, args) {
  const result = spawnSync(command, args, { cwd, encoding: 'utf8', env: { ...process.env, FORCE_COLOR: '0' } })
  assert.equal(result.status, 0, `${command} ${args.join(' ')}\n${result.stdout}\n${result.stderr}`)
}

describe('ui:neu – Namen', () => {
  it('leitet alle Namen aus Gruppe und Komponente ab', () => {
    const n = namesFor('audittrail', 'AuditTrail', PACKAGES)
    assert.equal(n.tag, 'flowaudit-audit-trail')
    assert.equal(n.react, 'FlowauditAuditTrail')
    assert.equal(n.element, 'auditTrailElement')
    assert.equal(n.createController, 'createAudittrailController')
    assert.equal(n.corePackage, '@scope/ui-core')
  })

  it('weist ungültige Namen ab', () => {
    assert.throws(() => namesFor('Audit', 'AuditTrail', PACKAGES), /Gruppe/)
    assert.throws(() => namesFor('audit-trail', 'AuditTrail', PACKAGES), /Gruppe/)
    assert.throws(() => namesFor('audit', 'auditTrail', PACKAGES), /Komponente/)
    assert.throws(() => namesFor('audit', 'IDCheck', PACKAGES), /Komponente/)
  })
})

describe('ui:neu – Gerüst in einer Kopie des Workspaces', () => {
  let copy
  let result
  before(() => {
    copy = copyWorkspace(ROOT, 'ui-new-')
    result = generate(copy, 'probelauf', 'ProbeListe')
  })
  after(() => rmSync(copy, { recursive: true, force: true }))

  it('erzeugt alle Schichten und trägt sie ein', () => {
    assert.equal(result.created.length, 17)
    assert.match(readFileSync(join(copy, 'packages-js/ui/src/registry.ts'), 'utf8'), /probeListeElement\]/)
    assert.match(readFileSync(join(copy, 'packages-js/ui-core/styles/index.css'), 'utf8'), /@import '\.\/probelauf\.css';/)
    assert.match(readFileSync(join(copy, 'docs/ui/react-paritaet.md'), 'utf8'), /\| ProbeListe \| `ProbeListe` \| `FlowauditProbeListe` \|/)
    const scope = JSON.parse(readFileSync(join(copy, 'packages-js/ui-core/package.json'), 'utf8')).name
    assert.match(readFileSync(join(copy, 'packages-js/ui-react/src/probelauf/FlowauditProbeListe.tsx'), 'utf8'), new RegExp(`from '${scope}'`))
  })

  it('überschreibt nichts', () => {
    assert.throws(() => generate(copy, 'probelauf', 'ProbeListe'), /Bereits vorhanden/)
  })

  it('Paritäts-Gate grün', () => {
    const report = runGate({ root: copy })
    assert.equal(report.status, 'PASS', report.open.map((item) => item.message).join('\n'))
    assert.ok(report.families[0].groups.includes('probelauf'))
  })

  it('Lint grün', LONG, () => {
    run(copy, 'npx', ['eslint', ...result.created.filter((path) => /\.(ts|tsx|vue)$/.test(path)), ...result.changed.filter((path) => path.endsWith('.ts'))])
  })

  it('Typprüfung grün (Kern, React, Vue)', LONG, () => {
    run(join(copy, 'packages-js/ui-core'), 'npx', ['tsc', '--noEmit', '-p', 'tsconfig.json'])
    run(join(copy, 'packages-js/ui-react'), 'npx', ['tsc', '--noEmit', '-p', 'tsconfig.json'])
    run(join(copy, 'packages-js/ui'), 'npx', ['vue-tsc', '--noEmit', '-p', 'tsconfig.json'])
  })

  it('erzeugte Tests grün (Kern, Vue, React mit DOM-Vergleich)', LONG, () => {
    run(join(copy, 'packages-js/ui-core'), 'npx', ['vitest', 'run', 'test/probelauf'])
    run(join(copy, 'packages-js/ui'), 'npx', ['vitest', 'run', 'test/parity-probelauf.spec.ts', 'test/elements.spec.ts'])
    run(join(copy, 'packages-js/ui-react'), 'npx', ['vitest', 'run', 'test/parity/probelauf.spec.tsx'])
  })
})
