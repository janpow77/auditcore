<script setup lang="ts">
import { axisValueLabel, type GateView, type StatusAxes } from '@auditcore/ui-core'
import { useI18n } from '../../i18n'
import { dataprotectionMessages, prefixedLabel } from '../core'

defineProps<{ axes: StatusAxes; gates: GateView[] }>()
const { t } = useI18n(dataprotectionMessages)
</script>

<template>
  <section class="fa-dataprotection__panel" data-testid="assistant-status" aria-labelledby="fa-assistant-axes">
    <h3 id="fa-assistant-axes">{{ t('axesTitle') }}</h3>
    <p class="fa-dataprotection__muted">{{ t('axesNotice') }}</p>
    <dl class="fa-assistant__axes">
      <template v-for="(value, key) in axes" :key="key">
        <dt>{{ prefixedLabel(t, 'axis', String(key)) }}</dt>
        <dd>{{ axisValueLabel(value) }}</dd>
      </template>
    </dl>
    <h3>{{ t('gatesTitle') }}</h3>
    <p v-if="!gates.length">{{ t('noGates') }}</p>
    <ul v-else>
      <li v-for="gate in gates" :key="gate.id" :data-gate="gate.id">
        <strong>{{ gate.id }}</strong> – {{ gate.reason }}
        <br /><span class="fa-dataprotection__muted">{{ t('gateRole', { role: gate.role }) }} · {{ t('gateNext', { step: gate.next_step }) }}</span>
      </li>
    </ul>
  </section>
</template>
