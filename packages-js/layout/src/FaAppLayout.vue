<script setup lang="ts">
import FaThemeSwitch from './FaThemeSwitch.vue'

withDefaults(defineProps<{
  brand?: string
  logo?: string
  logoAlt?: string
  accountName?: string
  accountImage?: string
  accountHref?: string
}>(), { brand: 'FlowAudit', logo: '', logoAlt: 'Logo', accountName: '', accountImage: '', accountHref: '' })
</script>

<template>
  <div class="fa-app-layout">
    <header class="fa-app-header">
      <a class="fa-app-brand" href="/" aria-label="Startseite">
        <img v-if="logo" class="fa-app-brand__logo" :src="logo" :alt="logoAlt">
        <span v-else class="fa-app-brand__mark" aria-hidden="true">F</span>
        <span class="fa-app-brand__name">{{ brand }}</span>
      </a>
      <nav class="fa-app-header__nav" aria-label="Hauptnavigation"><slot name="navigation" /></nav>
      <details class="fa-app-mobile-nav">
        <summary aria-label="Navigation öffnen" title="Navigation öffnen">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
        </summary>
        <nav aria-label="Mobile Hauptnavigation"><slot name="navigation" /></nav>
      </details>
      <div class="fa-app-header__actions"><slot name="actions" /><FaThemeSwitch /></div>
      <a v-if="accountName || accountImage" class="fa-app-account" :href="accountHref || undefined" :aria-label="accountName || 'Benutzerkonto'">
        <span class="fa-app-account__name">{{ accountName }}</span>
        <img v-if="accountImage" class="fa-app-account__image" :src="accountImage" alt="">
        <span v-else class="fa-app-account__avatar" aria-hidden="true">{{ accountName.slice(0, 1).toUpperCase() || '?' }}</span>
      </a>
      <slot name="account" />
    </header>
    <main class="fa-app-main"><slot /></main>
  </div>
</template>
