<script setup lang="ts">
import { useGeoContext } from './context'
import { displayName } from '@flowaudit/ui-core'

defineProps<{ testid: string }>()
const { state, t } = useGeoContext()
</script>

<template>
  <label class="fa-geo__field fa-geo__grow">
    <span class="fa-geo__label">{{ t('area') }}</span>
    <select v-model="state.areaId.value" class="fa-geo__input" :data-testid="testid">
      <option :value="null">{{ t('choose') }}</option>
      <option v-for="area in state.areas.value" :key="area.id" :value="area.id">{{ displayName(area) }}</option>
    </select>
  </label>
</template>
