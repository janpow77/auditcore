<script setup lang="ts">
/**
 * XML view (legacy XML mode). A plain text area with „apply“; an
 * application can place its own XML editor into the `editor` slot.
 */
import { ref, watch } from 'vue'
import BaseDialog from '../base/BaseDialog.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ open: boolean; xml: string; readonly?: boolean }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void; (e: 'apply', xml: string): void }>()
const { t } = useI18n()
const draft = ref(props.xml)

watch(
  () => [props.open, props.xml] as const,
  ([open, xml]) => {
    if (open) draft.value = xml
  },
)
</script>

<template>
  <BaseDialog :open="open" :title="t('xml.title')" :subtitle="t('xml.help')" width="900px" @update:open="emit('update:open', $event)">
    <slot name="editor" :xml="draft" :update="(value: string) => (draft = value)">
      <textarea v-model="draft" class="fa-textarea fa-xml" spellcheck="false" :readonly="readonly" :aria-label="t('xml.title')" />
    </slot>
    <template #footer>
      <button type="button" class="fa-btn" @click="emit('update:open', false)">{{ t('common.cancel') }}</button>
      <button type="button" class="fa-btn fa-btn--primary" :disabled="readonly || draft === xml" @click="(emit('apply', draft), emit('update:open', false))">{{ t('common.apply') }}</button>
    </template>
  </BaseDialog>
</template>

<style>
.fa-xml {
  min-height: 60vh;
  font-family: var(--fa-mono);
  font-size: 12px;
  white-space: pre;
}
</style>
