<script setup lang="ts">
/**
 * Standalone app: collection and editor against the REST contract
 * (`docs/bpmn/rest-api.md`). Delivered as static files (`dist-standalone/`).
 */
import { computed, onMounted, shallowRef } from 'vue'
import { DEFAULT_PROFILE, type ProfileData, type ProfileSummary } from '@flowaudit/bpmn-flowaudit'
import { bundledProfiles } from '@flowaudit/bpmn-flowaudit/profiles'
import FlowauditWorkbench from '../components/FlowauditWorkbench.vue'
import FaIcon from '../components/base/FaIcon.vue'
import { createI18n, provideI18n } from '../i18n/useI18n'
import { restPorts } from '../rest/restPorts'
import type { StandaloneConfig } from './config'

const props = defineProps<{ config: StandaloneConfig }>()
const { t } = provideI18n(createI18n(props.config.locale))
const rest = restPorts({ baseUrl: props.config.apiBase })
const ports = { legalSearch: rest.legalSearch, catalogue: rest.catalogue, validation: rest.validation, esi: rest.esi }
const profiles = shallowRef<ProfileSummary[]>([])
const profile = shallowRef<ProfileData | null>(null)
const message = shallowRef('')
const title = computed(() => props.config.title || t('app.title'))

async function loadProfile(): Promise<void> {
  try {
    profiles.value = await rest.profiles.profiles()
    const wanted = props.config.profile ?? profiles.value.find((entry) => entry.id === DEFAULT_PROFILE)?.id ?? profiles.value[0]?.id
    profile.value = wanted ? await rest.profiles.loadProfile(wanted) : null
  } catch {
    // Server without profile endpoints: bundled profiles of auditcore_bpmn.
    profile.value = bundledProfiles().find((entry) => entry.id === (props.config.profile ?? DEFAULT_PROFILE)) ?? null
  }
}

onMounted(loadProfile)
</script>

<template>
  <div class="fa-root fa-standalone" data-fa-theme="auto" :lang="config.locale">
    <header class="fa-standalone__bar">
      <FaIcon name="diagram" />
      <h1>{{ title }}</h1>
      <span v-if="profile" class="fa-badge fa-badge--info">{{ profile.id }}@{{ profile.version }}</span>
      <p v-if="message" class="fa-badge fa-badge--danger" role="alert">{{ message }}</p>
    </header>
    <FlowauditWorkbench
      class="fa-standalone__main"
      :storage="rest.storage"
      :ports="ports"
      :profile="profile"
      :profiles="profiles"
      :locale="config.locale"
      :author="config.author"
      @error="message = $event"
    />
  </div>
</template>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
}

.fa-standalone {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--fa-bg);
}

.fa-standalone__bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  border-bottom: 1px solid var(--fa-border);
  background: var(--fa-surface);
  color: var(--fa-primary);
}

.fa-standalone__bar h1 {
  margin: 0;
  font-size: 16px;
  color: var(--fa-text);
}

.fa-standalone__main {
  flex: 1;
  min-height: 0;
}
</style>
