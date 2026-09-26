import { ref } from 'vue'
import type { Locale } from '@auditcore/ui'

/** Sprache der Anwendung; als Ref an das Plugin übergeben, damit sie umschaltbar bleibt. */
export const locale = ref<Locale>('de')
