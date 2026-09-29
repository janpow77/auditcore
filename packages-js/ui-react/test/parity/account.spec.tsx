import { describe, expect, it } from 'vitest'
import AccountWorkspace from '../../../ui/src/account/AccountWorkspace.vue'
import { createAccountMemoryPort } from '../../../ui-core/src'
import { accountCases, accountItems } from '../../../ui-core/test/parity/cases-account'
import { FlowauditAccountWorkspace } from '../../src/account/FlowauditAccountWorkspace'
import { both } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität AccountWorkspace Vue ↔ React', () => {
  for (const entry of accountCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(AccountWorkspace, { ...entry.props() }, <FlowauditAccountWorkspace {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität AccountWorkspace nach Interaktion', () => {
  it('Eintrag auswählen', async () => {
    const port = createAccountMemoryPort(accountItems)
    const rendered = await renderBoth(AccountWorkspace, { port }, <FlowauditAccountWorkspace port={port} />)
    await both(rendered, (root) => root.querySelectorAll('button')[1], { kind: 'click' })
    expect(rendered.react.querySelectorAll('[aria-pressed="true"]')).toHaveLength(1)
  })
})

it('bearbeitet dasselbe Profilformular und schützt ungespeicherte Angaben', async () => {
  const document = { id: 'profile', title: 'Profil', description: '', kind: 'profile' as const, revision: 1,
    fields: [{ id: 'display_name', label: 'Anzeigename' }], values: { display_name: 'Alex' }, editable: true }
  const make = () => createAccountMemoryPort([{ id: 'profile', label: 'Profil' }], [document])
  const rendered = await renderBoth(AccountWorkspace, { port: make() }, <FlowauditAccountWorkspace port={make()} />)
  await both(rendered, (root) => root.querySelector('nav button'), { kind: 'click' })
  await both(rendered, (root) => root.querySelector('input'), { kind: 'input', value: 'Alex Neu' })
  expectParity(rendered, { texts: ['Ungespeicherte Änderungen. Bitte speichern oder verwerfen, bevor Sie den Bereich wechseln.'] })
  await both(rendered, (root) => root.querySelector('form'), { kind: 'submit' })
  expectParity(rendered, { texts: ['Änderungen gespeichert.'] })
})
