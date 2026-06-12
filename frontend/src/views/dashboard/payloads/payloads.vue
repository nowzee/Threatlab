<script lang="ts">
import { defineComponent, ref, onMounted, computed } from 'vue'

interface Payload {
  file_hash: string
  file_name: string
  file_size: number
  source_ip: string
  username: string
  password: string
  service_type: string
  upload_count: number
  first_seen: string
  last_seen: string
}

interface Command {
  id: number
  created_at: string
  source_ip: string
  country_code: string
  username_attempt: string
  payload: string
  attack_type: string
  service_type: string
}

export default defineComponent({
  name: 'PayloadsView',
  setup() {
    const activeTab = ref<'payloads' | 'commands'>('payloads')
    const payloads = ref<Payload[]>([])
    const commands = ref<Command[]>([])
    const cmdFilter = ref<'all' | 'success' | 'failed'>('all')
    const loading = ref(false)

    const loadPayloads = async () => {
      loading.value = true
      try {
        const r = await fetch('/api/agent/user/payloads', { credentials: 'include' })
        payloads.value = r.ok ? await r.json() : []
      } catch { payloads.value = [] }
      finally { loading.value = false }
    }

    const loadCommands = async () => {
      loading.value = true
      try {
        const r = await fetch(`/api/agent/user/commands?status=${cmdFilter.value}`, { credentials: 'include' })
        commands.value = r.ok ? await r.json() : []
      } catch { commands.value = [] }
      finally { loading.value = false }
    }

    const setTab = (t: 'payloads' | 'commands') => {
      activeTab.value = t
      if (t === 'payloads') loadPayloads()
      else loadCommands()
    }

    const setFilter = (f: 'all' | 'success' | 'failed') => {
      cmdFilter.value = f
      loadCommands()
    }

    const downloadPayload = (hash: string) => {
      window.location.href = `/api/agent/user/payloads/download/${hash}`
    }

    const formatBytes = (n: number) => {
      if (!n) return '0 B'
      const u = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(n) / Math.log(1024))
      return (n / Math.pow(1024, i)).toFixed(i ? 1 : 0) + ' ' + u[i]
    }
    const formatDate = (s: string) => s ? new Date(s).toLocaleString('fr-FR') : '-'
    const shortHash = (h: string) => h ? h.slice(0, 12) + '…' : ''

    const failedCount = computed(() =>
      commands.value.filter(c => c.attack_type === 'shell_command_failed').length)

    onMounted(loadPayloads)

    return {
      activeTab, payloads, commands, cmdFilter, loading, failedCount,
      setTab, setFilter, downloadPayload, formatBytes, formatDate, shortHash
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <h1 class="page-title">Payloads &amp; Commandes</h1>

    <div class="tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'payloads' }" @click="setTab('payloads')">
        Fichiers capturés
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'commands' }" @click="setTab('commands')">
        Commandes shell
      </button>
    </div>

    <!-- PAYLOADS -->
    <div v-if="activeTab === 'payloads'" class="card">
      <div v-if="loading" class="empty-state">Chargement…</div>
      <div v-else-if="payloads.length === 0" class="empty-state">Aucun fichier capturé pour le moment.</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Nom</th><th>Hash (SHA-256)</th><th>Taille</th><th>Service</th>
            <th>IP source</th><th>Identifiants</th><th>Occur.</th><th>Dernier vu</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in payloads" :key="p.file_hash">
            <td class="mono">{{ p.file_name }}</td>
            <td class="mono dim" :title="p.file_hash">{{ shortHash(p.file_hash) }}</td>
            <td>{{ formatBytes(p.file_size) }}</td>
            <td><span class="pill">{{ p.service_type }}</span></td>
            <td class="mono">{{ p.source_ip }}</td>
            <td class="mono dim">{{ p.username }}<span v-if="p.password">:{{ p.password }}</span></td>
            <td>{{ p.upload_count }}</td>
            <td class="dim">{{ formatDate(p.last_seen) }}</td>
            <td><button class="btn-dl" @click="downloadPayload(p.file_hash)">Télécharger</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- COMMANDS -->
    <div v-if="activeTab === 'commands'">
      <div class="filter-bar">
        <button class="filter-btn" :class="{ active: cmdFilter === 'all' }" @click="setFilter('all')">Toutes</button>
        <button class="filter-btn" :class="{ active: cmdFilter === 'success' }" @click="setFilter('success')">Réussies</button>
        <button class="filter-btn fail" :class="{ active: cmdFilter === 'failed' }" @click="setFilter('failed')">Échouées</button>
      </div>
      <div class="card">
        <div v-if="loading" class="empty-state">Chargement…</div>
        <div v-else-if="commands.length === 0" class="empty-state">Aucune commande pour ce filtre.</div>
        <table v-else class="data-table">
          <thead>
            <tr><th>Heure</th><th>IP source</th><th>Pays</th><th>Utilisateur</th><th>Commande</th><th>Statut</th></tr>
          </thead>
          <tbody>
            <tr v-for="c in commands" :key="c.id">
              <td class="dim">{{ formatDate(c.created_at) }}</td>
              <td class="mono">{{ c.source_ip }}</td>
              <td>{{ c.country_code || '-' }}</td>
              <td class="mono dim">{{ c.username_attempt || '-' }}</td>
              <td class="mono cmd">{{ c.payload }}</td>
              <td>
                <span class="badge" :class="c.attack_type === 'shell_command_failed' ? 'bad' : 'ok'">
                  {{ c.attack_type === 'shell_command_failed' ? 'échouée' : 'réussie' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-title { color: var(--white); margin-bottom: 24px; }
.tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid var(--container-border-color); }
.tab-btn {
  background: transparent; border: none; color: var(--text-color-muted);
  padding: 10px 18px; font-size: 14px; font-weight: 600; cursor: pointer;
  border-bottom: 2px solid transparent;
}
.tab-btn.active { color: var(--white); border-bottom-color: var(--accent-color); }

.card { background: var(--container-background); border: 1px solid var(--container-border-color); border-radius: 10px; overflow: hidden; }
.empty-state { padding: 40px; text-align: center; color: var(--text-color-muted); }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th {
  text-align: left; padding: 12px 14px; background: #1c1c1c;
  color: var(--text-color-muted); font-size: 11px; text-transform: uppercase; letter-spacing: .5px;
  border-bottom: 1px solid var(--container-border-color);
}
.data-table td { padding: 11px 14px; border-bottom: 1px solid var(--container-border-color); color: var(--text-color); }
.data-table tbody tr:hover { background: #1a1a1a; }
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; }
.dim { color: var(--text-color-muted); }
.cmd { max-width: 520px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #cfd3dc; }

.pill { font-size: 11px; padding: 2px 8px; border-radius: 4px; background: rgba(156,77,255,.15); color: var(--accent-color); text-transform: uppercase; }
.badge { font-size: 11px; padding: 2px 9px; border-radius: 4px; font-weight: 600; }
.badge.ok { background: rgba(0,230,118,.15); color: #00e676; }
.badge.bad { background: rgba(255,82,82,.18); color: #ff6b6b; }

.btn-dl {
  background: rgba(156,77,255,.12); border: 1px solid rgba(156,77,255,.25);
  color: var(--accent-color); padding: 5px 12px; border-radius: 6px;
  font-size: 12px; font-weight: 600; cursor: pointer;
}
.btn-dl:hover { background: rgba(156,77,255,.22); }

.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; }
.filter-btn {
  background: var(--container-background); border: 1px solid var(--container-border-color);
  color: var(--text-color-muted); padding: 7px 16px; border-radius: 6px;
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.filter-btn.active { background: var(--accent-color); color: #fff; border-color: var(--accent-color); }
.filter-btn.fail.active { background: var(--danger-color); border-color: var(--danger-color); }
</style>
