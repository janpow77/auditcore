<script setup lang="ts">
import { computed, ref } from 'vue'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useGeoContext } from './context'

const props = defineProps<{ upload: boolean; sources: boolean }>()
const { state, t } = useGeoContext()
const id = useId('fa-geo-gpkg')
const source = ref('')
const names = computed(() => (props.sources ? state.catalogue.value?.gpkg_quellen ?? [] : []))
const result = computed(() => state.gpkgResult.value)

async function onFile(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) await state.loadFile(file)
  input.value = ''
}
</script>

<template>
  <section class="fa-geo__card" :aria-labelledby="`${id}-h`">
    <h3 :id="`${id}-h`" class="fa-geo__heading">{{ t('gpkg') }}</h3>
    <label v-if="upload" class="fa-geo__field">
      <span class="fa-geo__label">{{ t('gpkgFile') }}</span>
      <input class="fa-geo__file" type="file" accept=".gpkg,application/geopackage+sqlite3" data-testid="geo-gpkg-file" @change="onFile" />
    </label>
    <form v-if="names.length" class="fa-geo__row" novalidate @submit.prevent="source && state.loadSource(source)">
      <label class="fa-geo__field fa-geo__grow">
        <span class="fa-geo__label">{{ t('gpkgSource') }}</span>
        <select v-model="source" class="fa-geo__input" data-testid="geo-gpkg-source">
          <option value="">{{ t('choose') }}</option>
          <option v-for="name in names" :key="name" :value="name">{{ name }}</option>
        </select>
      </label>
      <FaButton type="submit" :disabled="!source" :loading="state.busy.value === 'gpkg'" data-testid="geo-gpkg-load">{{ t('gpkgLoad') }}</FaButton>
    </form>
    <div v-if="result" class="fa-geo__stack" aria-live="polite" data-testid="geo-gpkg-result">
      <p class="fa-geo__summary">
        {{ t('gpkgResult', { count: result.flaechen.length, table: result.tabelle, srs: result.srs_id }) }}
        <span v-if="result.umgerechnet" class="fa-geo__muted">({{ t('gpkgConverted') }})</span>
      </p>
      <p v-if="result.abgeschnitten" class="fa-geo__notice">{{ t('gpkgTruncated') }}</p>
      <details v-if="result.fehler.length" class="fa-geo__details">
        <summary>{{ t('gpkgErrors', { count: result.fehler.length }) }}</summary>
        <ul class="fa-geo__list">
          <li v-for="entry in result.fehler" :key="entry.id">{{ entry.id }}: {{ entry.meldung }}</li>
        </ul>
      </details>
    </div>
  </section>
</template>
