<script setup lang="ts">
/**
 * Generic tab for FlowAudit lists (controls, risks, evidence, deadlines,
 * findings, audit steps, sources, references) – from the descriptors.
 */
import { computed } from 'vue'
import type { Extensions, ListExtensionKey } from '@flowaudit/bpmn-flowaudit'
import { useI18n } from '../../i18n/useI18n'
import { useEditorContext } from '../../stores/context'
import ListEditor from '../ListEditor.vue'
import { isDescribedList, LISTS } from '@flowaudit/bpmn-flowaudit/ui'
import { useOptions } from '../useOptions'

const props = defineProps<{ lists: ListExtensionKey[] }>()
const { selection, profile, ports, readonly } = useEditorContext()
const { locale } = useI18n()
const { optionsFor } = useOptions({ profile, catalogue: ports.catalogue, locale })

const descriptors = computed(() => props.lists.filter(isDescribedList).map((key) => LISTS[key]))

function items(key: ListExtensionKey): Record<string, unknown>[] {
  return selection.extensions.value[key] as unknown as Record<string, unknown>[]
}

function update(key: ListExtensionKey, value: Record<string, unknown>[]): void {
  selection.write({ [key]: value } as Partial<Extensions>)
}
</script>

<template>
  <div class="fa-tab-lists">
    <ListEditor
      v-for="descriptor in descriptors"
      :key="descriptor.key"
      :descriptor="descriptor"
      :items="items(descriptor.key)"
      :options-for="optionsFor"
      :disabled="readonly()"
      @update="update(descriptor.key, $event)"
    />
  </div>
</template>
