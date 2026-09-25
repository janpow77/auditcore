<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import { samplingMessages } from './messages'
import type { MethodProfile, SamplingCatalogue } from './types'

const props = withDefaults(defineProps<{
  catalogue: SamplingCatalogue
  profile: MethodProfile | null
  locale?: Locale
}>(), { locale: undefined })

const methodId = defineModel<string>({ required: true })
const { t } = useI18n(samplingMessages, () => props.locale)
const id = useId('fa-sampling-method')
const groups = computed(() => [
  { kind: 'mus', label: 'MUS', methods: props.catalogue.methods.filter((m) => m.kind === 'mus') },
  { kind: 'srs', label: 'SRS', methods: props.catalogue.methods.filter((m) => m.kind === 'srs') },
])
const tone = computed(() => {
  const status = props.profile?.status
  return status === 'RECOMMENDED' ? 'success' : status === 'SUPERSEDED' ? 'warning' : 'neutral'
})
</script>

<template>
  <section class="fa-sampling__card" :aria-labelledby="`${id}-title`">
    <h3 :id="`${id}-title`" class="fa-sampling__heading">{{ t('method') }}</h3>
    <label class="fa-sampling__field">
      <span class="fa-sampling__label">{{ t('method') }}</span>
      <select v-model="methodId" class="fa-sampling__select" data-testid="sampling-method" :aria-describedby="`${id}-hint`">
        <optgroup v-for="group in groups" :key="group.kind" :label="group.label">
          <option v-for="method in group.methods" :key="method.id" :value="method.id">{{ method.label }}</option>
        </optgroup>
      </select>
    </label>
    <p :id="`${id}-hint`" class="fa-sampling__hint">{{ t('methodHint') }}</p>
    <div v-if="profile" class="fa-sampling__profile">
      <p><FaBadge :tone="tone">{{ t(`status${profile.status}`) }}</FaBadge> <code class="fa-sampling__id">{{ profile.id }}</code></p>
      <p><span class="fa-sampling__label">{{ t('formula') }}</span><br /><span class="fa-sampling__formula">{{ profile.formula }}</span></p>
      <p class="fa-sampling__note">{{ profile.note }}</p>
      <details class="fa-sampling__source">
        <summary>{{ t('source') }}</summary>
        <code>{{ profile.source }}</code>
      </details>
    </div>
  </section>
</template>
