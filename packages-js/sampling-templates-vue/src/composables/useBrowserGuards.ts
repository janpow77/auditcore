/** Browser-Schutz und Ablegen von Dateien: Warnung beim Verlassen, Ziehen-und-Ablegen, gedrosselte Ansage. */
import { throttle } from '@auditcore/common'
import { onBeforeUnmount, onMounted, ref, watch, type Ref } from 'vue'

/** Browser-Warnung beim Verlassen der Seite, solange `active()` gilt. */
export function useUnloadGuard(active: () => boolean): void {
  const handler = (event: BeforeUnloadEvent): void => {
    if (!active()) return
    event.preventDefault()
    event.returnValue = ''
  }
  onMounted(() => window.addEventListener('beforeunload', handler))
  onBeforeUnmount(() => window.removeEventListener('beforeunload', handler))
}

export interface FileDrop {
  dragging: Ref<boolean>
  onDragEnter: (event: DragEvent) => void
  onDragOver: (event: DragEvent) => void
  onDragLeave: (event: DragEvent) => void
  onDrop: (event: DragEvent) => void
}

const hasFiles = (event: DragEvent): boolean => [...(event.dataTransfer?.types ?? [])].includes('Files')

/** Ziehen und Ablegen einer Datei auf die Komponente. */
export function useFileDrop(onFile: (file: File) => void): FileDrop {
  const dragging = ref(false)
  let depth = 0
  return {
    dragging,
    onDragEnter(event) {
      if (!hasFiles(event)) return
      depth += 1
      dragging.value = true
    },
    onDragOver(event) {
      if (hasFiles(event)) event.preventDefault()
    },
    onDragLeave(event) {
      if (!hasFiles(event)) return
      depth = Math.max(0, depth - 1)
      dragging.value = depth > 0
    },
    onDrop(event) {
      if (!hasFiles(event)) return
      // Auch ohne lesbare Datei verhindern, dass der Browser die Seite verlässt.
      event.preventDefault()
      const file = event.dataTransfer?.files[0]
      depth = 0
      dragging.value = false
      if (file) onFile(file)
    },
  }
}

/** Text für einen `aria-live`-Bereich, höchstens alle `ms` aktualisiert. */
export function useAnnouncer(source: () => string, ms = 1500): Ref<string> {
  const announced = ref('')
  const update = throttle((text: string) => {
    announced.value = text
  }, ms)
  let first = true
  watch(source, (text) => {
    // Der Anfangsstand wird nicht angesagt, nur Änderungen.
    if (first) first = false
    else update(text)
  }, { immediate: true })
  onBeforeUnmount(() => update.cancel())
  return announced
}
