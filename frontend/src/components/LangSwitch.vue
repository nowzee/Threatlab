<script lang="ts" setup>
import { useI18n } from 'vue-i18n'
import { setLocale, SUPPORTED_LOCALES, type Locale } from '@/i18n'

const { locale } = useI18n()

const choose = (l: Locale) => setLocale(l)
</script>

<template>
  <div class="lang-switch mono">
    <button
      v-for="l in SUPPORTED_LOCALES"
      :key="l"
      type="button"
      class="lang-opt"
      :class="{ active: locale === l }"
      @click="choose(l)"
    >{{ l.toUpperCase() }}</button>
  </div>
</template>

<style scoped>
.lang-switch {
  position: absolute;
  top: 24px; right: 24px;
  display: flex;
  border: 1px solid var(--container-border-color);
  z-index: 2;
}
.lang-opt {
  padding: 6px 12px;
  font-size: 11px; letter-spacing: 1px;
  background: transparent;
  color: var(--text-color-muted);
  border: none; cursor: pointer;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  transition: all 0.15s ease;
}
.lang-opt + .lang-opt { border-left: 1px solid var(--container-border-color); }
.lang-opt:hover { color: var(--white); }
.lang-opt.active { background: var(--accent-color); color: var(--white); font-weight: 600; }
</style>
