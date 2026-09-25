<template>
  <ul>
    <li v-for="item in props.items" :key="item.created">
      {{ formatDatum(item.created) }} {{ new Date(item.created).toLocaleString('de-DE') }}
    </li>
  </ul>
</template>

<script setup lang="ts">
const props = defineProps<{ items: Array<{ created: string }> }>()

function formatDatum(value: string): string {
  return new Date(value).toLocaleDateString('de-DE')
}
</script>
