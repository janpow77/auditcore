<script setup lang="ts">
import { onBeforeUnmount } from 'vue'
import { AccountWorkspace } from '@auditcore/ui'
import { createAccountMemoryPort, type AccountDocument } from '@auditcore/ui-core'
import fixture from '../../../../ui-core/test/fixtures/account/workspace.json'
const urls = new Map<string, string>()
const port = createAccountMemoryPort(fixture.items, fixture.documents as unknown as AccountDocument[])
port.imageUrl = (id) => urls.get(id) ?? ''
port.upload = async (_document, _field, file) => {
  const id = crypto.randomUUID()
  const url = URL.createObjectURL(file)
  urls.set(id, url)
  return { id, url }
}
onBeforeUnmount(() => { for (const url of urls.values()) URL.revokeObjectURL(url) })
</script>
<template>
  <h1>Konto, Mandant und Administration</h1>
  <p>Synthetische Beispieldaten. Änderungen bleiben nur bis zum Neuladen dieser Demo erhalten.</p>
  <AccountWorkspace :port="port" />
</template>
