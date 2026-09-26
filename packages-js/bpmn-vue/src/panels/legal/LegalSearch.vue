<script setup lang="ts">
/**
 * Search field for legal bases: parses the typed citation and asks the
 * legal search port (if present) for suggestions. Emits the chosen entry.
 */
import { computed, ref, watch } from 'vue'
import { shortCitation, type LegalBasis, type LegalSearchHit, type LegalSearchPort } from '@flowaudit/bpmn-flowaudit'
import { hitHint, typedCitation, withoutDisplayFields } from '@flowaudit/bpmn-flowaudit/ui'
import FaIcon from '../../components/base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ port?: LegalSearchPort; profileId?: string; disabled?: boolean }>()
const emit = defineEmits<{ (e: 'choose', value: LegalBasis): void }>()
const { t, locale } = useI18n()

const query = ref('')
const hits = ref<LegalSearchHit[]>([])
const busy = ref(false)
const listId = `fa-legal-${Math.random().toString(36).slice(2, 8)}`
let controller: AbortController | null = null
let timer: ReturnType<typeof setTimeout> | undefined

const typed = computed<LegalBasis | null>(() => typedCitation(query.value))

async function search(text: string): Promise<void> {
  controller?.abort()
  if (!props.port || text.trim().length < 2) {
    hits.value = []
    return
  }
  controller = new AbortController()
  busy.value = true
  try {
    hits.value = await props.port.search(text, { locale: locale.value, limit: 12, profile: props.profileId, signal: controller.signal })
  } catch {
    hits.value = []
  } finally {
    busy.value = false
  }
}

watch(query, (text) => {
  clearTimeout(timer)
  timer = setTimeout(() => search(text), 250)
})

function choose(value: LegalBasis): void {
  emit('choose', withoutDisplayFields(value))
  query.value = ''
  hits.value = []
}
</script>

<template>
  <div class="fa-legal-search">
    <label class="fa-field">
      <span class="fa-label">{{ t('legal.search') }}</span>
      <span class="fa-legal-search__input">
        <FaIcon name="search" :size="16" />
        <input v-model="query" class="fa-input" type="search" :disabled="disabled" :aria-controls="query.trim() ? listId : undefined" @keydown.enter.prevent="typed && choose(typed)" />
      </span>
    </label>
    <div v-if="query.trim()" :id="listId" class="fa-legal-search__results" role="listbox" :aria-busy="busy">
      <button v-if="typed" type="button" role="option" class="fa-menu-item" @click="choose(typed)">
        <FaIcon name="plus" :size="16" />
        <span>
          {{ t('legal.takeTyped') }}: <strong>{{ shortCitation(typed) || typed.text }}</strong>
        </span>
      </button>
      <button v-for="(hit, index) in hits" :key="index" type="button" role="option" class="fa-menu-item" @click="choose(hit)">
        <FaIcon name="marker-rechtsgrundlage" :size="16" />
        <span>
          <strong>{{ shortCitation(hit) || hit.text }}</strong>
          <span class="fa-menu-hint">{{ hitHint(hit) }}</span>
          <span v-if="hit.excerpt" class="fa-menu-hint">{{ hit.excerpt }}</span>
        </span>
      </button>
      <p v-if="!busy && !hits.length && port" class="fa-help">{{ t('legal.noResults') }}</p>
    </div>
  </div>
</template>
