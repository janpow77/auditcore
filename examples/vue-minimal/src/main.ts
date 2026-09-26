import { createApp } from 'vue'
import { createFlowauditUi } from '@flowaudit/ui'
// Einmal je Anwendung: Designtoken (--fa-*), Hell-/Dunkelmodus und Komponentenstile.
import '@flowaudit/ui/style.css'
import App from './App.vue'
import { locale } from './locale'

createApp(App).use(createFlowauditUi({ locale })).mount('#app')
