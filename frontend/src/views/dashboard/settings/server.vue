<script setup lang="ts">
import { ref, onMounted } from 'vue'

const timezones = ref<string[]>([])
const selected = ref<string>('Europe/Paris')
const offset = ref<string>('')
const saving = ref(false)
const loading = ref(true)
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null)

async function loadCurrent() {
  loading.value = true
  try {
    const [sRes, tzRes] = await Promise.all([
      fetch('/api/admin/settings', { credentials: 'include', headers: { Accept: 'application/json' } }),
      fetch('/api/config/timezones', { credentials: 'include', headers: { Accept: 'application/json' } }),
    ])
    const sData = await sRes.json()
    const tzData = await tzRes.json()
    timezones.value = Array.isArray(tzData?.timezones) ? tzData.timezones : []
    if (sData?.settings?.timezone) selected.value = sData.settings.timezone
    if (sData?.settings?.offset) offset.value = sData.settings.offset
  } catch {
    message.value = { type: 'error', text: 'Impossible de charger la configuration.' }
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  message.value = null
  try {
    const res = await fetch('/api/admin/settings', {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ timezone: selected.value }),
    })
    const data = await res.json()
    if (res.ok && data.success) {
      if (data?.settings?.offset) offset.value = data.settings.offset
      message.value = { type: 'success', text: 'Fuseau horaire enregistré. Les dates affichées utilisent désormais ce fuseau.' }
    } else {
      message.value = { type: 'error', text: data.error || "Échec de l'enregistrement." }
    }
  } catch {
    message.value = { type: 'error', text: 'Erreur de connexion au serveur.' }
  } finally {
    saving.value = false
  }
}

onMounted(loadCurrent)
</script>

<template>
  <div class="server-settings">
    <h3 class="server-title">Fuseau horaire du serveur</h3>
    <p class="server-hint">
      Appliqué à toute la plateforme. Les données sont stockées en UTC ; ce réglage détermine l'heure
      affichée à tous les utilisateurs, quel que soit le fuseau de leur navigateur.
    </p>

    <div v-if="loading" class="server-loading">Chargement…</div>

    <div v-else class="tz-body">
      <label class="tz-label" for="tz-select">Fuseau horaire</label>
      <select id="tz-select" v-model="selected" class="tz-select">
        <option v-for="tz in timezones" :key="tz" :value="tz">{{ tz }}</option>
      </select>

      <div v-if="offset" class="tz-preview">
        <span class="tz-preview-label">Décalage UTC actuel&nbsp;:</span>
        <span class="tz-preview-value">{{ offset }}</span>
      </div>

      <div class="tz-actions">
        <button class="btn btn-primary" :disabled="saving" @click="save">
          {{ saving ? 'Enregistrement…' : 'Enregistrer' }}
        </button>
        <span v-if="message" class="tz-msg" :class="message.type">{{ message.text }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.server-title { font-size: 16px; font-weight: 600; color: var(--white); margin: 0 0 6px; }
.server-hint { color: var(--text-color-muted); font-size: 14px; margin: 0 0 20px; line-height: 1.5; }
.server-loading { color: var(--text-color-muted); }
.tz-body { display: flex; flex-direction: column; gap: 14px; max-width: 520px; }
.tz-label { font-size: 13px; color: var(--text-color-muted); font-weight: 600; }
.tz-select {
  width: 100%; padding: 10px 12px; border-radius: 8px;
  border: 1px solid var(--container-border-color);
  background: var(--input-background); color: var(--text-color); font-size: 14px;
}
.tz-preview {
  display: flex; gap: 8px; flex-wrap: wrap; align-items: baseline;
  padding: 12px 14px; border: 1px solid var(--container-border-color); border-radius: 8px;
}
.tz-preview-label { color: var(--text-color-muted); font-size: 13px; }
.tz-preview-value { color: var(--white); font-weight: 600; font-size: 14px; }
.tz-actions { display: flex; align-items: center; gap: 14px; margin-top: 4px; flex-wrap: wrap; }
.tz-msg { font-size: 13px; font-weight: 600; }
.tz-msg.success { color: #2e9e5b; }
.tz-msg.error { color: rgba(207, 15, 31, 0.92); }
</style>
