/**
 * Lokaler Entwurf im Web Storage dieses Browsers: eine Bequemlichkeit, keine
 * Speicherung. In der Bibliothek abgeschaltet, die Anwendung schaltet ihn bewusst ein;
 * ein von der Anwendung vorgegebener Arbeitsstand hat Vorrang; der Entwurf wird wie eine Datei geprüft, bevor er
 * übernommen wird, und lässt sich über das Menü löschen.
 */
import { debounce } from '@auditcore/common'
import { safeStorage } from '@auditcore/common/browser'
import { cleanInputs, openWorkspace, saveWorkspace, type SheetModule, type Translate } from '@auditcore/sampling-templates-core'
import { onBeforeUnmount, onMounted, watch } from 'vue'
import type { SamplingSession } from './useSamplingSession'

export interface LocalDraftOptions {
  enabled: () => boolean
  /** Schlüssel im Web Storage; je Anwendung verschieden wählen. */
  key: () => string
  /** Die Anwendung hat einen Arbeitsstand vorgegeben; er hat Vorrang vor einem alten Entwurf. */
  hasInitialState: () => boolean
  sheets: () => readonly SheetModule[]
  t: Translate
}

const STORAGE_PREFIX = 'auditcore-sampling-templates'
const WRITE_DELAY_MS = 600

export function useLocalDraft(session: SamplingSession, options: LocalDraftOptions): { clear: () => void } {
  const storage = safeStorage({ prefix: STORAGE_PREFIX, version: 1 })

  async function write(): Promise<void> {
    if (!options.enabled()) return
    const state = session.workspace.value
    const empty = Object.keys(cleanInputs(state.sheets)).length === 0
    if (empty || !session.meta.value.dirty) return storage.remove(options.key())
    storage.set(options.key(), (await saveWorkspace(state, { sheets: options.sheets() })).text)
  }

  async function restore(): Promise<void> {
    const text = options.enabled() && !options.hasInitialState() ? storage.get<string | null>(options.key(), null) : null
    if (typeof text !== 'string') return
    const result = await openWorkspace(text, { sheets: options.sheets() })
    if (!result.ok || Object.keys(result.state.sheets).length === 0) return storage.remove(options.key())
    session.replace(result.state, { fileName: null, dirty: true, sample: false }, [{ tone: 'info', text: options.t('draftRestored') }])
  }

  const schedule = debounce(() => void write(), WRITE_DELAY_MS)
  onMounted(() => void restore())
  watch([session.workspace, session.meta], () => schedule())
  onBeforeUnmount(() => schedule.flush())

  return {
    clear() {
      schedule.cancel()
      storage.remove(options.key())
      session.say(options.t('draftCleared'))
    },
  }
}
