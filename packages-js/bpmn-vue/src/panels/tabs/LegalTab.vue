<script setup lang="ts">
/** Legal bases of the selected element. */
import type { LegalBasis } from '@flowaudit/bpmn-flowaudit'
import { useEditorContext } from '../../stores/context'
import LegalBasisEditor from '../legal/LegalBasisEditor.vue'

const { selection, ports, profile, readonly } = useEditorContext()

function update(items: LegalBasis[]): void {
  selection.write({ legalBases: items })
}
</script>

<template>
  <LegalBasisEditor :items="selection.extensions.value.legalBases" :port="ports.legalSearch" :profile-id="profile()?.id" :disabled="readonly()" @update="update" />
</template>
