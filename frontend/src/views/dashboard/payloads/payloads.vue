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
    const itemsPerPage = 10
    const activeTab = ref<'payloads' | 'commands'>('payloads')
    const payloads = ref<Payload[]>([])
    const commands = ref<Command[]>([])
    const payloadTotal = ref(0)
    const cmdTotal = ref(0)
    const payloadPage = ref(1)
    const cmdPage = ref(1)
    const payloadQuery = ref('')
    const cmdQuery = ref('')
    const cmdFilter = ref<'all' | 'success' | 'failed'>('all')
    const loading = ref(false)
    const selectedCmd = ref<Command | null>(null)
    const copied = ref(false)

    const loadPayloads = async () => {
      loading.value = true
      try {
        const u = `/api/agent/user/payloads?page=${payloadPage.value}&limit=${itemsPerPage}&q=${encodeURIComponent(payloadQuery.value)}`
        const r = await fetch(u, { credentials: 'include' })
        const d = r.ok ? await r.json() : { items: [], total: 0 }
        payloads.value = d.items || []
        payloadTotal.value = d.total || 0
      } catch { payloads.value = []; payloadTotal.value = 0 }
      finally { loading.value = false }
    }

    const loadCommands = async () => {
      loading.value = true
      try {
        const u = `/api/agent/user/commands?status=${cmdFilter.value}&page=${cmdPage.value}&limit=${itemsPerPage}&q=${encodeURIComponent(cmdQuery.value)}`
        const r = await fetch(u, { credentials: 'include' })
        const d = r.ok ? await r.json() : { items: [], total: 0 }
        commands.value = d.items || []
        cmdTotal.value = d.total || 0
      } catch { commands.value = []; cmdTotal.value = 0 }
      finally { loading.value = false }
    }

    const setTab = (t: 'payloads' | 'commands') => {
      activeTab.value = t
      if (t === 'payloads') loadPayloads()
      else loadCommands()
    }

    const setFilter = (f: 'all' | 'success' | 'failed') => {
      cmdFilter.value = f
      cmdPage.value = 1
      loadCommands()
    }

    // Debounced search
    let pTimer = 0, cTimer = 0
    const onPayloadSearch = () => {
      clearTimeout(pTimer)
      pTimer = window.setTimeout(() => { payloadPage.value = 1; loadPayloads() }, 350)
    }
    const onCmdSearch = () => {
      clearTimeout(cTimer)
      cTimer = window.setTimeout(() => { cmdPage.value = 1; loadCommands() }, 350)
    }

    // --- Pagination (10 par page, façon vue alertes) ---
    const buildPages = (current: number, total: number): (number | string)[] => {
      const pages: (number | string)[] = []
      if (total <= 7) { for (let i = 1; i <= total; i++) pages.push(i); return pages }
      pages.push(1)
      if (current > 3) pages.push('...')
      for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i)
      if (current < total - 2) pages.push('...')
      pages.push(total)
      return pages
    }

    const payloadTotalPages = computed(() => Math.max(1, Math.ceil(payloadTotal.value / itemsPerPage)))
    const payloadPages = computed(() => buildPages(payloadPage.value, payloadTotalPages.value))
    const goPayloadPage = (p: number) => { if (p >= 1 && p <= payloadTotalPages.value) { payloadPage.value = p; loadPayloads() } }

    const cmdTotalPages = computed(() => Math.max(1, Math.ceil(cmdTotal.value / itemsPerPage)))
    const cmdPages = computed(() => buildPages(cmdPage.value, cmdTotalPages.value))
    const goCmdPage = (p: number) => { if (p >= 1 && p <= cmdTotalPages.value) { cmdPage.value = p; loadCommands() } }

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

    const copyCmd = async () => {
      if (!selectedCmd.value) return
      try { await navigator.clipboard.writeText(selectedCmd.value.payload) } catch { /* ignore */ }
      copied.value = true
      setTimeout(() => { copied.value = false }, 1500)
    }

    onMounted(loadPayloads)

    return {
      activeTab, payloads, commands, cmdFilter, loading,
      selectedCmd, copied, copyCmd, itemsPerPage,
      payloadTotal, cmdTotal, payloadQuery, cmdQuery, onPayloadSearch, onCmdSearch,
      payloadPage, payloadTotalPages, payloadPages, goPayloadPage,
      cmdPage, cmdTotalPages, cmdPages, goCmdPage,
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
    <div v-if="activeTab === 'payloads'">
      <div class="search-bar">
        <input v-model="payloadQuery" @input="onPayloadSearch" class="search-input"
               placeholder="Rechercher dans le contenu, le nom, l'IP, le hash… (ex: une IP, un domaine, un mot)" />
      </div>
      <div class="card">
      <div v-if="loading" class="empty-state">Chargement…</div>
      <div v-else-if="payloads.length === 0" class="empty-state">
        {{ payloadQuery ? 'Aucun fichier ne contient « ' + payloadQuery + ' ».' : 'Aucun fichier capturé pour le moment.' }}
      </div>
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

      <div class="pagination-wrapper" v-if="payloadTotalPages > 1">
        <div class="pagination-info">
          {{ (payloadPage - 1) * itemsPerPage + 1 }}-{{ Math.min(payloadPage * itemsPerPage, payloadTotal) }} sur {{ payloadTotal }}
        </div>
        <div class="pagination">
          <button class="page-btn" @click="goPayloadPage(payloadPage - 1)" :disabled="payloadPage === 1">‹</button>
          <template v-for="(pg, i) in payloadPages" :key="i">
            <button v-if="typeof pg === 'number'" class="page-number" :class="{ active: pg === payloadPage }" @click="goPayloadPage(pg)">{{ pg }}</button>
            <span v-else class="page-ellipsis">…</span>
          </template>
          <button class="page-btn" @click="goPayloadPage(payloadPage + 1)" :disabled="payloadPage === payloadTotalPages">›</button>
        </div>
      </div>
      </div>
    </div>

    <!-- COMMANDS -->
    <div v-if="activeTab === 'commands'">
      <div class="filter-bar">
        <button class="filter-btn" :class="{ active: cmdFilter === 'all' }" @click="setFilter('all')">Toutes</button>
        <button class="filter-btn" :class="{ active: cmdFilter === 'success' }" @click="setFilter('success')">Réussies</button>
        <button class="filter-btn fail" :class="{ active: cmdFilter === 'failed' }" @click="setFilter('failed')">Échouées</button>
        <input v-model="cmdQuery" @input="onCmdSearch" class="search-input cmd-search"
               placeholder="Rechercher une commande (ip, mot, URL…)" />
      </div>
      <div class="card">
        <div v-if="loading" class="empty-state">Chargement…</div>
        <div v-else-if="commands.length === 0" class="empty-state">
          {{ cmdQuery ? 'Aucune commande ne contient « ' + cmdQuery + ' ».' : 'Aucune commande pour ce filtre.' }}
        </div>
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
              <td class="mono cmd" :title="'Cliquer pour voir en entier'" @click="selectedCmd = c">{{ c.payload }}</td>
              <td>
                <span class="badge" :class="c.attack_type === 'shell_command_failed' ? 'bad' : 'ok'">
                  {{ c.attack_type === 'shell_command_failed' ? 'échouée' : 'réussie' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="pagination-wrapper" v-if="cmdTotalPages > 1">
          <div class="pagination-info">
            {{ (cmdPage - 1) * itemsPerPage + 1 }}-{{ Math.min(cmdPage * itemsPerPage, cmdTotal) }} sur {{ cmdTotal }}
          </div>
          <div class="pagination">
            <button class="page-btn" @click="goCmdPage(cmdPage - 1)" :disabled="cmdPage === 1">‹</button>
            <template v-for="(pg, i) in cmdPages" :key="i">
              <button v-if="typeof pg === 'number'" class="page-number" :class="{ active: pg === cmdPage }" @click="goCmdPage(pg)">{{ pg }}</button>
              <span v-else class="page-ellipsis">…</span>
            </template>
            <button class="page-btn" @click="goCmdPage(cmdPage + 1)" :disabled="cmdPage === cmdTotalPages">›</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Command detail modal -->
    <div v-if="selectedCmd" class="modal-overlay" @click.self="selectedCmd = null">
      <div class="modal">
        <div class="modal-head">
          <span>Commande complète</span>
          <button class="modal-close" @click="selectedCmd = null">✕</button>
        </div>
        <div class="modal-meta">
          <span>{{ formatDate(selectedCmd.created_at) }}</span>
          <span class="mono">{{ selectedCmd.source_ip }}</span>
          <span class="mono dim">{{ selectedCmd.username_attempt }}</span>
          <span class="badge" :class="selectedCmd.attack_type === 'shell_command_failed' ? 'bad' : 'ok'">
            {{ selectedCmd.attack_type === 'shell_command_failed' ? 'échouée' : 'réussie' }}
          </span>
        </div>
        <pre class="modal-cmd">{{ selectedCmd.payload }}</pre>
        <div class="modal-actions">
          <button class="btn-dl" @click="copyCmd">{{ copied ? 'Copié !' : 'Copier' }}</button>
        </div>
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
.cmd { max-width: 520px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #cfd3dc; cursor: pointer; }
.cmd:hover { color: var(--accent-color); }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  display: flex; align-items: center; justify-content: center; z-index: 100; padding: 24px;
}
.modal {
  background: var(--container-background); border: 1px solid var(--container-border-color);
  border-radius: 10px; width: 100%; max-width: 760px; max-height: 80vh; display: flex; flex-direction: column;
}
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 18px; border-bottom: 1px solid var(--container-border-color);
  color: var(--white); font-weight: 600;
}
.modal-close { background: none; border: none; color: var(--text-color-muted); font-size: 16px; cursor: pointer; }
.modal-close:hover { color: var(--white); }
.modal-meta { display: flex; gap: 14px; align-items: center; padding: 12px 18px; font-size: 12px; color: var(--text-color-muted); flex-wrap: wrap; }
.modal-cmd {
  margin: 0; padding: 16px 18px; overflow: auto; flex: 1;
  font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 12.5px;
  color: #cfd3dc; white-space: pre-wrap; word-break: break-all; line-height: 1.6;
  background: #0d0d0d; border-top: 1px solid var(--container-border-color);
  border-bottom: 1px solid var(--container-border-color);
}
.modal-actions { padding: 12px 18px; display: flex; justify-content: flex-end; }

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

.search-bar { margin-bottom: 16px; }
.search-input {
  width: 100%; box-sizing: border-box;
  padding: 11px 14px; background: var(--container-background);
  border: 1px solid var(--container-border-color); border-radius: 8px;
  color: var(--white); font-size: 14px;
}
.search-input:focus { outline: none; border-color: var(--accent-color); box-shadow: 0 0 0 2px rgba(156,77,255,.15); }
.search-input::placeholder { color: var(--text-color-muted); }
.cmd-search { flex: 1; min-width: 180px; padding: 7px 12px; font-size: 13px; }

.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; align-items: center; }
.filter-btn {
  background: var(--container-background); border: 1px solid var(--container-border-color);
  color: var(--text-color-muted); padding: 7px 16px; border-radius: 6px;
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.filter-btn.active { background: var(--accent-color); color: #fff; border-color: var(--accent-color); }
.filter-btn.fail.active { background: var(--danger-color); border-color: var(--danger-color); }

/* Pagination (style vue alertes) */
.pagination-wrapper {
  padding: 16px 20px; border-top: 1px solid var(--container-border-color);
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;
}
.pagination-info { font-size: 13px; color: var(--text-color-muted); }
.pagination { display: flex; gap: 6px; align-items: center; }
.page-btn, .page-number {
  min-width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;
  background: transparent; border: 1px solid var(--container-border-color); border-radius: 6px;
  color: var(--text-color); font-size: 14px; cursor: pointer; transition: all .2s ease; padding: 0 6px;
}
.page-btn:hover:not(:disabled), .page-number:hover { background: rgba(255,255,255,.05); border-color: var(--accent-color); }
.page-number.active { background: var(--accent-color); border-color: var(--accent-color); color: #fff; }
.page-btn:disabled { opacity: .4; cursor: not-allowed; }
.page-ellipsis { min-width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; color: var(--text-color-muted); }
</style>
