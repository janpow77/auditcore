<script setup lang="ts">
import { computed } from 'vue'
import {
  extractionAccept,
  extractionProfileText,
  extractionSizeText,
  extractionValidationText,
  type ExtractionController,
  type ExtractionData,
  type ExtractionTranslate,
  type Locale,
} from '@flowaudit/ui-core'
import FaButton from '../base/FaButton.vue'

const props = defineProps<{
  id: string
  controller: ExtractionController
  state: ExtractionData
  t: ExtractionTranslate
  locale: Locale
}>()

const catalogue = computed(() => props.state.catalogue)
const profile = computed(() => catalogue.value?.profiles.find((entry) => entry.id === props.state.profileId) ?? null)
const problem = computed(() => (props.state.validation ? extractionValidationText(props.state.validation, catalogue.value, props.t, props.locale) : ''))

function onFile(event: Event): void {
  props.controller.selectFile((event.target as HTMLInputElement).files?.[0] ?? null)
}

function onProfile(event: Event): void {
  props.controller.setProfile((event.target as HTMLSelectElement).value || null)
}
</script>

<template>
  <form v-if="catalogue" class="fa-extraction__card" novalidate :aria-labelledby="`${id}-upload`" @submit.prevent="controller.extract">
    <h3 :id="`${id}-upload`" class="fa-extraction__heading">{{ t('upload') }}</h3>
    <div class="fa-extraction__form">
      <label class="fa-extraction__field">
        <span class="fa-extraction__label">{{ t('file') }}</span>
        <input class="fa-extraction__file" type="file" :accept="extractionAccept(catalogue)" data-testid="extraction-file" @change="onFile" />
      </label>
      <label class="fa-extraction__field">
        <span class="fa-extraction__label">{{ t('profile') }}</span>
        <select class="fa-extraction__input" :value="state.profileId ?? ''" data-testid="extraction-profile" @change="onProfile">
          <option v-for="entry in catalogue.profiles" :key="entry.id" :value="entry.id" :disabled="!entry.available">{{ extractionProfileText(entry, t) }}</option>
        </select>
      </label>
    </div>
    <p class="fa-extraction__muted">{{ t('fileHelp', { size: extractionSizeText(catalogue.limits.max_upload_bytes, locale) }) }}</p>
    <p v-if="profile?.status === 'EXPERIMENTAL'" class="fa-extraction__muted" data-testid="extraction-experimental">{{ t('experimental') }}</p>
    <p class="fa-extraction__muted">{{ t('retention') }}</p>
    <p v-if="problem" class="fa-extraction__error" role="alert">{{ problem }}</p>
    <div>
      <FaButton variant="primary" type="submit" :loading="state.busy === 'run'" data-testid="extraction-run">{{ t('run') }}</FaButton>
    </div>
  </form>
</template>
