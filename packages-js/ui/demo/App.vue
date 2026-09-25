<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch, type Component } from 'vue'
import { FaButton, useTheme } from '@flowaudit/ui'
import { DEMO_PAGES, findPage } from './pages'
import { demoLocale } from './locale'

const current = ref(readHash())
const view = shallowRef<Component | null>(null)
const theme = useTheme()
const groups = computed(() => [...new Set(DEMO_PAGES.map((page) => page.group))])

function readHash(): string {
  return window.location.hash.replace(/^#\/?/, '') || (DEMO_PAGES[0]?.id ?? '')
}

function onHashChange(): void {
  current.value = readHash()
}

watch(current, async (id) => {
  view.value = (await findPage(id).load()).default
}, { immediate: true })

onMounted(() => window.addEventListener('hashchange', onHashChange))
onBeforeUnmount(() => window.removeEventListener('hashchange', onHashChange))

function toggleLocale(): void {
  demoLocale.value = demoLocale.value === 'de' ? 'en' : 'de'
  document.documentElement.lang = demoLocale.value
}
</script>

<template>
  <div class="demo">
    <nav class="demo__nav" aria-label="Komponenten">
      <div class="demo__brand">FlowAudit UI<small>Komponenten-Demo</small></div>
      <div v-for="group in groups" :key="group">
        <p class="demo__group">{{ group }}</p>
        <ul class="demo__links">
          <li v-for="page in DEMO_PAGES.filter((entry) => entry.group === group)" :key="page.id">
            <a :href="`#/${page.id}`" :aria-current="page.id === current ? 'page' : undefined">{{ page.title }}</a>
          </li>
        </ul>
      </div>
      <div class="demo__tools">
        <FaButton size="sm" :icon="theme.mode.value === 'dark' ? 'sun' : 'moon'" data-testid="theme-toggle" @click="theme.toggle()">
          {{ theme.mode.value === 'dark' ? 'Hell' : 'Dunkel' }}
        </FaButton>
        <FaButton size="sm" data-testid="locale-toggle" @click="toggleLocale">{{ demoLocale === 'de' ? 'English' : 'Deutsch' }}</FaButton>
      </div>
    </nav>
    <main class="demo__main">
      <component :is="view" v-if="view" />
    </main>
  </div>
</template>
