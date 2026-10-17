/**
 * Zwischenstand im Web Storage dieses Browsers: eine Bequemlichkeit, keine
 * Speicherung. Drei Stufen: `off` (nichts wird abgelegt), `session` (nur für
 * diese Sitzung: `sessionStorage`, endet mit dem Schließen des Tabs) und
 * `device` (auf diesem Gerät behalten: `localStorage`). In der Bibliothek ist
 * er abgeschaltet; die Anwendung wählt die Stufe. Ein von der Anwendung
 * vorgegebener Arbeitsstand hat Vorrang; der Zwischenstand wird wie eine Datei
 * geprüft, bevor er übernommen wird. Beim Wechsel der Stufe zieht er um, bei
 * `off` und beim Zurücksetzen werden beide Ablagen geleert.
 */
import { debounce } from '@auditcore/common'
import { safeStorage, type SafeStorage } from '@auditcore/common/browser'
import { cleanInputs, openWorkspace, saveWorkspace, type SheetModule, type Translate } from '@auditcore/sampling-templates-core'
import { onBeforeUnmount, onMounted, ref, watch, type Ref } from 'vue'
import type { DraftMode } from '../types'
import type { SamplingSession } from './useSamplingSession'

export interface LocalDraftOptions {
  /** Stufe des Zwischenstands. */
  mode: () => DraftMode
  /** Schlüssel im Web Storage; je Anwendung verschieden wählen. */
  key: () => string
  /** Die Anwendung hat einen Arbeitsstand vorgegeben; er hat Vorrang vor einem alten Zwischenstand. */
  hasInitialState: () => boolean
  sheets: () => readonly SheetModule[]
  t: Translate
  /** Meldet, ob gerade ein Zwischenstand abgelegt ist (für einen Umschalter der Anwendung). */
  onStored?: (stored: boolean) => void
}

export interface LocalDraft {
  /** Zwischenstand in beiden Ablagen löschen. */
  clear: (announce?: boolean) => void
  /** Es liegt ein Zwischenstand in der Ablage der gewählten Stufe. */
  stored: Ref<boolean>
}

const STORAGE_PREFIX = 'auditcore-sampling-templates'
const WRITE_DELAY_MS = 600

export function useLocalDraft(session: SamplingSession, options: LocalDraftOptions): LocalDraft {
  const stores: Readonly<Record<Exclude<DraftMode, 'off'>, SafeStorage>> = {
    session: safeStorage({ prefix: STORAGE_PREFIX, version: 1, storage: 'session' }),
    device: safeStorage({ prefix: STORAGE_PREFIX, version: 1, storage: 'local' }),
  }
  const stored = ref(false)
  const current = (): SafeStorage | null => (options.mode() === 'off' ? null : stores[options.mode() as 'session' | 'device'])

  function mark(value: boolean): void {
    if (stored.value === value) return
    stored.value = value
    options.onStored?.(value)
  }

  function removeAll(): void {
    stores.session.remove(options.key())
    stores.device.remove(options.key())
    mark(false)
  }

  async function write(): Promise<void> {
    const storage = current()
    if (!storage) return
    const state = session.workspace.value
    const empty = Object.keys(cleanInputs(state.sheets)).length === 0
    if (empty || !session.meta.value.dirty) return removeAll()
    const text = (await saveWorkspace(state, { sheets: options.sheets() })).text
    // Inzwischen kann die Stufe gewechselt haben; geschrieben wird nur in die noch gewählte Ablage.
    if (current() !== storage) return
    storage.set(options.key(), text)
    // Der Zwischenstand liegt immer nur in einer Ablage.
    for (const other of Object.values(stores)) if (other !== storage) other.remove(options.key())
    mark(true)
  }

  async function restore(): Promise<void> {
    const text = options.hasInitialState() ? null : (current()?.get<string | null>(options.key(), null) ?? null)
    if (typeof text !== 'string') return
    const result = await openWorkspace(text, { sheets: options.sheets() })
    if (!result.ok || Object.keys(result.state.sheets).length === 0) return removeAll()
    session.replace(result.state, { fileName: null, dirty: true, sample: false }, [{ tone: 'info', text: options.t('draftRestored') }])
    mark(true)
  }

  const schedule = debounce(() => void write(), WRITE_DELAY_MS)
  onMounted(() => void restore())
  watch([session.workspace, session.meta], () => schedule())
  // Stufenwechsel: abschalten leert beide Ablagen, sonst zieht der Zwischenstand in die neue Ablage um.
  watch(options.mode, (mode) => {
    schedule.cancel()
    if (mode === 'off') removeAll()
    else void write()
  })
  onBeforeUnmount(() => schedule.flush())

  return {
    stored,
    clear(announce = true) {
      schedule.cancel()
      removeAll()
      if (announce) session.say(options.t('draftCleared'))
    },
  }
}
