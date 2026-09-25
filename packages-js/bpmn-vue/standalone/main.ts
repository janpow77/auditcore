/** Entry of the standalone app (`dist-standalone/index.html`). */

import { createApp } from 'vue'
import StandaloneApp from '../src/standalone/StandaloneApp.vue'
import { readConfig } from '../src/standalone/config'
import '../src/styles/theme.css'

createApp(StandaloneApp, { config: readConfig() }).mount('#app')
