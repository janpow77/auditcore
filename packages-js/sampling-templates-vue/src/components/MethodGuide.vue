<script setup lang="ts">
import type { GuideView, Translate } from '@auditcore/sampling-templates-core'
import { FaBadge, useId } from '@auditcore/ui'

/** Wegweiser: Hinweise der Vorlage aus der angepassten Grundgesamtheit; keine Empfehlung eines Verfahrens. */
defineProps<{ guide: GuideView; t: Translate }>()

const id = useId('fa-st-guide')
</script>

<template>
  <aside class="fa-st__card fa-st__guide" :aria-labelledby="id" data-guide>
    <h3 :id="id" class="fa-st__caption">{{ t('guide') }}</h3>
    <p class="fa-st__muted">{{ guide.lead }}</p>
    <ul class="fa-st__hint-list">
      <li v-for="item in guide.items" :key="item.id" :data-guide-item="item.id">
        <FaBadge class="fa-st__pill" :tone="item.tone" :label="item.text" />
      </li>
    </ul>
  </aside>
</template>
