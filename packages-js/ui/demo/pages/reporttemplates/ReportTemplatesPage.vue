<script setup lang="ts">
import { ref } from 'vue'
import { ReportTemplates, createReportTemplatesRestPort } from '@auditcore/ui'

const port = createReportTemplatesRestPort({ baseUrl: '/api/reporting' })
const last = ref('')
</script>

<template>
  <h1>Berichtsvorlagen</h1>
  <p>
    <code>&lt;ReportTemplates&gt;</code> bzw. <code>&lt;flowaudit-report-templates&gt;</code> mit dem REST-Port auf
    <code>auditcore_reporting.web</code> (Vertrag <code>reporting_ui/1</code>, Vorlagen-Endpunkte). Die neutralen
    Vorlagen „Vermerk“ und „Prüfbericht“ laufen mit ihren synthetischen Beispieldaten.
  </p>
  <ReportTemplates :port="port" filename="Prüfbericht" @report-rendered="(file) => (last = `Ereignis report-rendered: ${file.filename}`)" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
