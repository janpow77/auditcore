<script setup lang="ts">
/** Demo of @flowaudit/bpmn-vue: workbench with in-memory storage and synthetic data. */
import { onMounted, shallowRef } from 'vue'
import { InMemoryStorage, localized, ProfileCataloguePort, ProfileLegalSearch, StaticProfilePort, type ProfileData } from '@flowaudit/bpmn-flowaudit'
import { bundledProfiles, defaultProfile } from '@flowaudit/bpmn-flowaudit/profiles'
import { FlowauditWorkbench } from '../src'
import { demoStorage } from './demoData'

const params = new URLSearchParams(window.location.search)
const locale = params.get('locale') === 'en' ? 'en' : 'de'
const storage = shallowRef<InMemoryStorage | null>(null)
const profile: ProfileData | null = defaultProfile() ?? null
const profilePort = new StaticProfilePort(bundledProfiles())
const ports = { legalSearch: new ProfileLegalSearch(profile), catalogue: new ProfileCataloguePort(profilePort) }
const profiles = bundledProfiles().map((entry) => ({ id: entry.id, version: entry.version, title: localized(entry.title, locale) }))

onMounted(async () => {
  storage.value = await demoStorage()
})
</script>

<template>
  <FlowauditWorkbench v-if="storage" :storage="storage" :profile="profile" :profiles="profiles" :ports="ports" :locale="locale" author="Demo" />
</template>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
}
</style>
