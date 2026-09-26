<script setup lang="ts">
import { onMounted, ref } from 'vue'

const host = ref<HTMLElement | null>(null)
const last = ref('')

onMounted(() => {
  const element = host.value?.querySelector('flowaudit-table') as (HTMLElement & Record<string, unknown>) | null
  if (!element) return
  element.columns = [{ key: 'name', label: 'Name', sortable: true }, { key: 'status', label: 'Status' }]
  element.rows = [{ id: 1, name: 'Systemprüfung S03', status: 'Entwurf' }, { id: 2, name: 'Vorhabenprüfung VP-19', status: 'Abschluss' }]
  element.clickable = true
  element.addEventListener('row-click', (event) => {
    const [row] = (event as CustomEvent<[Record<string, unknown>]>).detail
    last.value = String(row.name)
  })
})
</script>

<template>
  <h1>Web Components</h1>
  <p>Jede Komponente ist auch als <code>&lt;flowaudit-…&gt;</code> nutzbar – ohne Vue in der Host-Anwendung.</p>
  <pre><code>import { defineFlowauditElements } from '@auditcore/ui/elements'
import '@auditcore/ui/style.css'
defineFlowauditElements()</code></pre>
  <div ref="host"><flowaudit-table /></div>
  <p aria-live="polite">{{ last ? `Ereignis row-click: ${last}` : '' }}</p>
</template>
