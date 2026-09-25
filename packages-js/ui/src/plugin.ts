import { ref, type App, type Plugin, type Ref } from 'vue'
import { DEFAULT_LOCALE, LOCALE_KEY, type Locale } from './i18n'

export interface FlowauditUiOptions {
  locale?: Locale | Ref<Locale>
}

/** Vue-Plugin: stellt die Sprache app-weit bereit. */
export function createFlowauditUi(options: FlowauditUiOptions = {}): Plugin {
  return {
    install(app: App): void {
      const locale = typeof options.locale === 'object' ? options.locale : ref<Locale>(options.locale ?? DEFAULT_LOCALE)
      app.provide(LOCALE_KEY, locale)
    },
  }
}
