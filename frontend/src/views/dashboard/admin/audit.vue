<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import '@/assets/css/admin-paper.css'

type AuditEntry = {
  id: number
  created_at: string | null
  actor_username: string | null
  action: string
  target_type: string | null
  target_id: string | null
  detail: string | null
  ip_address: string | null
}

const items = ref<AuditEntry[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(25)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit.value)))

async function load() {
  try {
    const res = await fetch(`/api/admin/audit?page=${page.value}&limit=${limit.value}`, {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
    const data = await res.json()
    items.value = data.items || []
    total.value = data.total || 0
  } catch (e) { /* noop */ }
}
onMounted(load)

function prev() { if (page.value > 1) { page.value--; load() } }
function next() { if (page.value < totalPages.value) { page.value++; load() } }

function fmt(d: string | null): string {
  return d || '—'
}

function target(a: AuditEntry): string {
  if (a.target_type && a.target_id) return `${a.target_type}#${a.target_id}`
  return a.target_type || '—'
}
</script>

<template>
  <div class="admin-paper content-wrapper">
    <div class="head">
      <div>
        <h1>Journaux d'audit</h1>
        <p class="muted">Actions sensibles enregistrées ({{ total }}) — création/suppression de comptes et de honeypots.</p>
      </div>
    </div>

    <div class="card no-pad">
      <table class="t">
        <thead>
          <tr>
            <th style="width:170px">Date</th>
            <th style="width:140px">Utilisateur</th>
            <th style="width:130px">Action</th>
            <th>Cible</th>
            <th style="width:130px">IP</th>
            <th>Détail</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in items" :key="a.id">
            <td class="mono small">{{ fmt(a.created_at) }}</td>
            <td>{{ a.actor_username || '—' }}</td>
            <td><span class="pill"><span class="d"></span>{{ a.action }}</span></td>
            <td class="mono small">{{ target(a) }}</td>
            <td class="mono small">{{ a.ip_address || '—' }}</td>
            <td class="small">{{ a.detail || '—' }}</td>
          </tr>
          <tr v-if="!items.length"><td colspan="6" class="empty">Aucune action enregistrée</td></tr>
        </tbody>
      </table>
    </div>

    <div class="pager" v-if="totalPages > 1">
      <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="prev">← Précédent</button>
      <span class="mono">page {{ page }} / {{ totalPages }}</span>
      <button class="btn btn-ghost btn-sm" :disabled="page >= totalPages" @click="next">Suivant →</button>
    </div>
  </div>
</template>
