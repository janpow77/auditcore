/** Entry of the standalone app (`dist-standalone/index.html`). */

import { createApp } from 'vue'
import StandaloneApp from '../src/standalone/StandaloneApp.vue'
import { readConfig } from '@auditcore/bpmn-flowaudit/ui'
import '@auditcore/bpmn-flowaudit/ui.css'

createApp(StandaloneApp, { config: readConfig() }).mount('#app')
