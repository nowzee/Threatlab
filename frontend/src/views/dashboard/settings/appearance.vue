<script setup lang="ts">
import { ref } from 'vue'
import { getThemePref, setThemePref, type ThemePref } from '@/utils/theme'

const pref = ref<ThemePref>(getThemePref())

const options: { value: ThemePref; label: string; desc: string }[] = [
  { value: 'system', label: 'Système', desc: 'Suit le thème de votre appareil.' },
  { value: 'light', label: 'Clair', desc: 'Thème papier clair.' },
  { value: 'dark', label: 'Sombre', desc: 'Thème sombre (par défaut).' },
]

function choose(v: ThemePref) {
  pref.value = v
  setThemePref(v)
}
</script>

<template>
  <div class="appearance">
    <h3 class="appearance-title">Thème de l'interface</h3>
    <p class="appearance-hint">Le mode « Système » suit automatiquement les préférences claires/sombres de votre appareil.</p>
    <div class="theme-options">
      <button
        v-for="o in options"
        :key="o.value"
        type="button"
        class="theme-option"
        :class="{ active: pref === o.value }"
        @click="choose(o.value)">
        <span class="theme-option-label">{{ o.label }}</span>
        <span class="theme-option-desc">{{ o.desc }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.appearance-title { font-size: 16px; font-weight: 600; color: var(--white); margin: 0 0 6px; }
.appearance-hint { color: var(--text-color-muted); font-size: 14px; margin: 0 0 20px; }
.theme-options { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 12px; }
.theme-option {
  text-align: left; display: flex; flex-direction: column; gap: 4px;
  padding: 16px; border: 1px solid var(--container-border-color);
  background: var(--input-background); border-radius: 8px; cursor: pointer;
  transition: border-color .15s, box-shadow .15s;
}
.theme-option:hover { border-color: var(--accent-color); }
.theme-option.active { border-color: var(--accent-color); box-shadow: 0 0 0 2px var(--button-hover-background); }
.theme-option-label { font-weight: 600; color: var(--text-color); font-size: 14px; }
.theme-option-desc { color: var(--text-color-muted); font-size: 12px; }
</style>
