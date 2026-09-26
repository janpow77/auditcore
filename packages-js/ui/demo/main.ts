import { createApp } from 'vue'
import { createFlowauditUi } from '@auditcore/ui'
import { defineFlowauditElements } from '@auditcore/ui/elements'
import App from './App.vue'
import { demoLocale } from './locale'
import './demo.css'

defineFlowauditElements()
createApp(App).use(createFlowauditUi({ locale: demoLocale })).mount('#app')
