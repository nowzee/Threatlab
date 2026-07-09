<script lang="ts">
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import '@/assets/css/admin-paper.css'

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
    const router = useRouter()
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

    let pTimer = 0, cTimer = 0
    const onPayloadSearch = () => {
      clearTimeout(pTimer)
      pTimer = window.setTimeout(() => { payloadPage.value = 1; loadPayloads() }, 350)
    }
    const onCmdSearch = () => {
      clearTimeout(cTimer)
      cTimer = window.setTimeout(() => { cmdPage.value = 1; loadCommands() }, 350)
    }

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

    const viewPayload = (hash: string) => {
      router.push({ name: 'payload-detail', params: { hash } })
    }

    const formatBytes = (n: number) => {
      if (!n) return '0 B'
      const u = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(n) / Math.log(1024))
      return (n / Math.pow(1024, i)).toFixed(i ? 1 : 0) + ' ' + u[i]
    }
    const formatDate = (s: string) => s || '-'
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
      setTab, setFilter, downloadPayload, viewPayload, formatBytes, formatDate, shortHash
    }
  }
})
</script>

<template>
  <div class="admin-paper content-wrapper">
    <div class="head">
      <div>
        <h1>Payloads &amp; Commandes</h1>
        <p class="muted">Fichiers capturés par les honeypots et commandes shell observées.</p>
      </div>
    </div>

    <div class="pp-tabs">
      <button class="pp-tab" :class="{ active: activeTab === 'payloads' }" @click="setTab('payloads')">Fichiers capturés</button>
      <button class="pp-tab" :class="{ active: activeTab === 'commands' }" @click="setTab('commands')">Commandes shell</button>
    </div>

    <!-- PAYLOADS -->
    <div v-if="activeTab === 'payloads'">
      <div class="toolbar">
        <input v-model="payloadQuery" @input="onPayloadSearch" class="input"
               placeholder="Rechercher dans le contenu, le nom, l'IP, le hash…" />
      </div>
      <div class="card no-pad">
        <div v-if="loading" class="empty">Chargement…</div>
        <div v-else-if="payloads.length === 0" class="empty">
          {{ payloadQuery ? 'Aucun fichier ne contient « ' + payloadQuery + ' ».' : 'Aucun fichier capturé pour le moment.' }}
        </div>
        <table v-else class="t">
          <thead>
            <tr><th>Nom</th><th>Hash (SHA-256)</th><th>Taille</th><th>Service</th><th>IP source</th><th>Identifiants</th><th>Occur.</th><th>Dernier vu</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="p in payloads" :key="p.file_hash">
              <td class="mono">{{ p.file_name }}</td>
              <td class="mono small" :title="p.file_hash">{{ shortHash(p.file_hash) }}</td>
              <td>{{ formatBytes(p.file_size) }}</td>
              <td><span class="pill svc"><span class="d"></span>{{ p.service_type }}</span></td>
              <td class="mono">{{ p.source_ip }}</td>
              <td class="mono small">{{ p.username }}<span v-if="p.password">:{{ p.password }}</span></td>
              <td>{{ p.upload_count }}</td>
              <td class="small">{{ formatDate(p.last_seen) }}</td>
              <td>
                <div class="pp-actions">
                  <button class="btn btn-sm dl" @click="viewPayload(p.file_hash)">Voir</button>
                  <button class="btn btn-sm dl" @click="downloadPayload(p.file_hash)">Télécharger</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="pp-pager" v-if="payloadTotalPages > 1">
          <span class="pp-pager-info">{{ (payloadPage - 1) * itemsPerPage + 1 }}-{{ Math.min(payloadPage * itemsPerPage, payloadTotal) }} sur {{ payloadTotal }}</span>
          <div class="pp-pages">
            <button class="pp-page" @click="goPayloadPage(payloadPage - 1)" :disabled="payloadPage === 1">‹</button>
            <template v-for="(pg, i) in payloadPages" :key="i">
              <button v-if="typeof pg === 'number'" class="pp-page" :class="{ active: pg === payloadPage }" @click="goPayloadPage(pg)">{{ pg }}</button>
              <span v-else class="pp-ellipsis">…</span>
            </template>
            <button class="pp-page" @click="goPayloadPage(payloadPage + 1)" :disabled="payloadPage === payloadTotalPages">›</button>
          </div>
        </div>
      </div>
    </div>

    <!-- COMMANDS -->
    <div v-if="activeTab === 'commands'">
      <div class="toolbar">
        <div class="seg">
          <button class="seg-btn" :class="{ active: cmdFilter === 'all' }" @click="setFilter('all')">Toutes</button>
          <button class="seg-btn" :class="{ active: cmdFilter === 'success' }" @click="setFilter('success')">Réussies</button>
          <button class="seg-btn" :class="{ active: cmdFilter === 'failed' }" @click="setFilter('failed')">Échouées</button>
        </div>
        <input v-model="cmdQuery" @input="onCmdSearch" class="input pp-grow" placeholder="Rechercher une commande (ip, mot, URL…)" />
      </div>
      <div class="card no-pad">
        <div v-if="loading" class="empty">Chargement…</div>
        <div v-else-if="commands.length === 0" class="empty">
          {{ cmdQuery ? 'Aucune commande ne contient « ' + cmdQuery + ' ».' : 'Aucune commande pour ce filtre.' }}
        </div>
        <table v-else class="t">
          <thead>
            <tr><th>Heure</th><th>IP source</th><th>Pays</th><th>Utilisateur</th><th>Commande</th><th>Statut</th></tr>
          </thead>
          <tbody>
            <tr v-for="c in commands" :key="c.id">
              <td class="small">{{ formatDate(c.created_at) }}</td>
              <td class="mono">{{ c.source_ip }}</td>
              <td>{{ c.country_code || '-' }}</td>
              <td class="mono small">{{ c.username_attempt || '-' }}</td>
              <td class="mono cmd" title="Cliquer pour voir en entier" @click="selectedCmd = c">{{ c.payload }}</td>
              <td>
                <span class="pill" :class="c.attack_type === 'shell_command_failed' ? 'pill-bad' : 'pill-ok'">
                  <span class="d"></span>{{ c.attack_type === 'shell_command_failed' ? 'échouée' : 'réussie' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="pp-pager" v-if="cmdTotalPages > 1">
          <span class="pp-pager-info">{{ (cmdPage - 1) * itemsPerPage + 1 }}-{{ Math.min(cmdPage * itemsPerPage, cmdTotal) }} sur {{ cmdTotal }}</span>
          <div class="pp-pages">
            <button class="pp-page" @click="goCmdPage(cmdPage - 1)" :disabled="cmdPage === 1">‹</button>
            <template v-for="(pg, i) in cmdPages" :key="i">
              <button v-if="typeof pg === 'number'" class="pp-page" :class="{ active: pg === cmdPage }" @click="goCmdPage(pg)">{{ pg }}</button>
              <span v-else class="pp-ellipsis">…</span>
            </template>
            <button class="pp-page" @click="goCmdPage(cmdPage + 1)" :disabled="cmdPage === cmdTotalPages">›</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Command detail modal -->
    <div v-if="selectedCmd" class="modal-mask" @click.self="selectedCmd = null">
      <div class="pp-modal">
        <div class="pp-modal-head">
          <span>Commande complète</span>
          <button class="pp-x" @click="selectedCmd = null">✕</button>
        </div>
        <div class="pp-modal-meta">
          <span>{{ formatDate(selectedCmd.created_at) }}</span>
          <span class="mono">{{ selectedCmd.source_ip }}</span>
          <span class="mono">{{ selectedCmd.username_attempt }}</span>
          <span class="pill" :class="selectedCmd.attack_type === 'shell_command_failed' ? 'pill-bad' : 'pill-ok'">
            <span class="d"></span>{{ selectedCmd.attack_type === 'shell_command_failed' ? 'échouée' : 'réussie' }}
          </span>
        </div>
        <pre class="pp-cmd">{{ selectedCmd.payload }}</pre>
        <div class="pp-foot">
          <button class="btn btn-primary btn-sm" @click="copyCmd">{{ copied ? 'Copié !' : 'Copier' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Paper design — reuses admin-paper classes (.head/.card/.t/.pill/.btn/.input/.modal-mask)
   and the --ap-* palette variables (paper in light, dark-remapped in dark). */

.toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.pp-grow { flex: 1; min-width: 200px; }

/* Tabs (ink underline) */
.pp-tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--ap-line); margin-bottom: 20px; }
.pp-tab { background: transparent; border: none; padding: 10px 18px; font-size: 13px; font-weight: 600; color: var(--ap-gray); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; }
.pp-tab:hover { color: var(--ap-ink); }
.pp-tab.active { color: var(--ap-ink); border-bottom-color: var(--ap-ink); }

/* Segmented filter */
.seg { display: inline-flex; border: 1px solid var(--ap-line-strong); }
.seg-btn { padding: 8px 15px; font-size: 12px; font-weight: 600; background: transparent; color: var(--ap-gray); border: none; border-right: 1px solid var(--ap-line-strong); cursor: pointer; }
.seg-btn:last-child { border-right: none; }
.seg-btn:hover { color: var(--ap-ink); }
.seg-btn.active { background: var(--ap-ink); color: var(--ap-paper); }

/* Service tag: outlined so it stays visible on the light paper surface */
.svc { border: 1px solid var(--ap-line-strong); }

/* Row actions: keep View + Download side by side, no wrap */
.pp-actions { display: flex; gap: 8px; white-space: nowrap; }

/* Action buttons: outlined, fill on hover (clear affordance vs a text-only hover) */
.dl { border: 1px solid var(--ap-line-strong); background: transparent; color: var(--ap-ink); opacity: 1; }
.dl:hover { background: var(--ap-ink); color: var(--ap-paper); border-color: var(--ap-ink); }

/* Command cell */
.cmd { max-width: 520px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }
.cmd:hover { text-decoration: underline; }

/* Pagination */
.pp-pager { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-top: 1px solid var(--ap-line); flex-wrap: wrap; gap: 12px; }
.pp-pager-info { font-size: 12px; color: var(--ap-gray); }
.pp-pages { display: flex; gap: 6px; align-items: center; }
.pp-page { min-width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center; padding: 0 6px; border: 1px solid var(--ap-line-strong); background: transparent; color: var(--ap-ink); font-size: 13px; cursor: pointer; }
.pp-page:hover:not(:disabled):not(.active) { background: var(--ap-sand); }
.pp-page.active { background: var(--ap-ink); color: var(--ap-paper); border-color: var(--ap-ink); }
.pp-page:disabled { opacity: .4; cursor: not-allowed; }
.pp-ellipsis { min-width: 20px; text-align: center; color: var(--ap-gray); }

/* Command modal (paper) */
.pp-modal { background: var(--ap-paper); border: 1px solid var(--ap-line); width: 100%; max-width: 760px; max-height: 80vh; display: flex; flex-direction: column; }
.pp-modal-head { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--ap-line); font-weight: 600; font-size: 15px; color: var(--ap-ink); }
.pp-x { background: none; border: none; color: var(--ap-gray); font-size: 16px; cursor: pointer; }
.pp-x:hover { color: var(--ap-ink); }
.pp-modal-meta { display: flex; gap: 14px; align-items: center; padding: 12px 20px; font-size: 12px; color: var(--ap-gray); flex-wrap: wrap; border-bottom: 1px solid var(--ap-line); }
.pp-cmd { margin: 0; padding: 16px 20px; overflow: auto; flex: 1; font-family: var(--ap-mono); font-size: 12.5px; color: var(--ap-ink); white-space: pre-wrap; word-break: break-all; line-height: 1.6; background: var(--ap-sand); }
.pp-foot { padding: 14px 20px; display: flex; justify-content: flex-end; border-top: 1px solid var(--ap-line); }
</style>
