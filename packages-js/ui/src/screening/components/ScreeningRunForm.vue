<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import { useI18n } from '../../i18n'
import { screeningMessages } from '../core'
import type { RunRequest, ScreeningKind, SettingsView, SourceView } from '../core'
import { SCREENING_KINDS as kinds, buildRunRequest, kindProfiles, kindSources, runFormDefaults, selectedProfile, type ViewMessage } from '../core'

const props = defineProps<{ settings: SettingsView; sources: SourceView[]; busy: boolean }>()
const emit = defineEmits<{ submit: [request: RunRequest] }>()
const { t } = useI18n(screeningMessages)

const kind = ref<ScreeningKind>('sanctions')
const profileKey = ref('')
const lists = ref<string[]>([])
const subjectsText = ref('')
const minScore = ref<number | null>(null)
const caseReference = ref('')
const errors = ref<ViewMessage[]>([])

const profiles = computed(() => kindProfiles(props.settings, kind.value))
const profile = computed(() => selectedProfile(props.settings, { kind: kind.value, profileKey: profileKey.value }))
const sourcesOfKind = computed(() => kindSources(props.sources, kind.value))
const errorTexts = computed(() => errors.value.map((error) => t(error.key, error.params)))

watch([kind, () => props.settings, () => props.sources], () => {
  const defaults = runFormDefaults(props.settings, props.sources, kind.value)
  profileKey.value = defaults.profileKey
  lists.value = defaults.lists
  minScore.value = defaults.minScore
}, { immediate: true })

function submit(): void {
  const form = { kind: kind.value, profileKey: profileKey.value, lists: lists.value, subjectsText: subjectsText.value, minScore: minScore.value, caseReference: caseReference.value }
  const result = buildRunRequest(props.settings, form)
  errors.value = result.errors
  if (result.request) emit('submit', result.request)
}
</script>

<template>
  <section class="fa-screening__panel" aria-labelledby="fa-screening-run-form-title">
    <h3 id="fa-screening-run-form-title">{{ t('newRun') }}</h3>
    <form novalidate @submit.prevent="submit">
      <fieldset class="fa-screening__field">
        <legend>{{ t('kind') }}</legend>
        <label v-for="key in kinds" :key="key" class="fa-screening__check">
          <input v-model="kind" type="radio" name="fa-screening-kind" :value="key" />{{ t(`kind_${key}`) }}
        </label>
      </fieldset>
      <label class="fa-screening__field">
        <span>{{ t('profile') }}</span>
        <select v-model="profileKey">
          <option v-for="p in profiles" :key="`${p.id}@${p.version}`" :value="`${p.id}@${p.version}`">
            {{ p.id }} {{ p.version }}{{ p.recommended ? ` ${t('recommended')}` : '' }}
          </option>
        </select>
      </label>
      <fieldset class="fa-screening__field">
        <legend>{{ t('lists') }}</legend>
        <label v-for="s in sourcesOfKind" :key="s.list.key" class="fa-screening__check">
          <input v-model="lists" type="checkbox" :value="s.list.key" />
          <span>
            {{ s.list.name }}
            <FaBadge v-if="!s.searchable" tone="danger">{{ t('noStockRun') }}</FaBadge>
          </span>
        </label>
      </fieldset>
      <label class="fa-screening__field">
        <span>{{ t('subjects') }}</span>
        <textarea v-model="subjectsText" data-testid="screening-subjects" :placeholder="t('subjectsPlaceholder')" />
      </label>
      <label class="fa-screening__field">
        <span>{{ t('minScore', { min: profile?.scale.min ?? 0, max: profile?.scale.max ?? 100 }) }}</span>
        <input
          v-model.number="minScore"
          type="number"
          :min="profile?.scale.min"
          :max="profile?.scale.max"
          :step="profile && profile.scale.max <= 1 ? 0.01 : 1"
        />
      </label>
      <label class="fa-screening__field">
        <span>{{ t('caseReference') }}</span>
        <input v-model="caseReference" type="text" maxlength="500" data-testid="screening-case" />
      </label>
      <ul v-if="errorTexts.length" class="fa-screening__errors" role="alert">
        <li v-for="e in errorTexts" :key="e">{{ e }}</li>
      </ul>
      <button class="fa-screening__btn fa-screening__btn--primary" type="submit" :disabled="busy" data-testid="screening-start">{{ t('startRun') }}</button>
    </form>
  </section>
</template>
