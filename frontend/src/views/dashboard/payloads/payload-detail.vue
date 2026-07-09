<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import '@/assets/css/admin-paper.css'

interface PayloadMeta {
  file_hash: string
  file_name: string
  file_size: number
  source_ip: string
  username: string
  password: string
  service_type: string
  agent_id: number | null
  upload_count: number
  first_seen: string
  last_seen: string
}

interface PayloadView {
  meta: PayloadMeta
  is_binary: boolean
  truncated: boolean
  shown_bytes: number
  content: string | null
  hexdump: string | null
}

export default defineComponent({
  name: 'PayloadDetailView',
  setup() {
    const route = useRoute()
    const router = useRouter()

    const hash = computed(() => route.params.hash as string)
    const data = ref<PayloadView | null>(null)
    const loading = ref(true)
    const error = ref<string | null>(null)
    const copied = ref(false)

    const fetchView = async () => {
      loading.value = true
      error.value = null
      try {
        const r = await fetch(`/api/agent/user/payloads/view/${hash.value}`, { credentials: 'include' })
        if (r.ok) {
          data.value = await r.json()
        } else if (r.status === 404) {
          error.value = 'Fichier introuvable ou supprimé du disque.'
        } else {
          error.value = 'Erreur lors du chargement du contenu.'
        }
      } catch (e: any) {
        error.value = e?.message || 'Erreur inconnue.'
      } finally {
        loading.value = false
      }
    }

    // Raw content to render: hex dump for binaries, decoded text otherwise.
    const body = computed(() => {
      if (!data.value) return ''
      return (data.value.is_binary ? data.value.hexdump : data.value.content) || ''
    })

    const goBack = () => router.push({ name: 'payloads' })
    const download = () => { window.location.href = `/api/agent/user/payloads/download/${hash.value}` }

    const copyContent = async () => {
      try { await navigator.clipboard.writeText(body.value) } catch { /* ignore */ }
      copied.value = true
      setTimeout(() => { copied.value = false }, 1500)
    }

    const formatBytes = (n: number) => {
      if (!n) return '0 B'
      const u = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(n) / Math.log(1024))
      return (n / Math.pow(1024, i)).toFixed(i ? 1 : 0) + ' ' + u[i]
    }
    const formatDate = (s: string) => s || '-'

    onMounted(fetchView)

    return {
      hash, data, loading, error, copied, body,
      goBack, download, copyContent, formatBytes, formatDate
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <!-- Back button: standard app style (global .btn), same arrow as the other
         detail pages. Kept outside .admin-paper so it isn't restyled as paper. -->
    <div class="pd-back">
      <button class="btn btn-secondary" @click="goBack">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5"></path>
          <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
        Retour
      </button>
    </div>

    <div class="admin-paper">
    <!-- Header -->
    <div class="page-head">
      <div>
        <h1>{{ data ? (data.meta.file_name || 'Fichier capturé') : 'Fichier capturé' }}</h1>
        <p class="muted mono">{{ hash }}</p>
      </div>
      <div class="head-actions">
        <button class="btn btn-primary btn-sm" @click="download">Télécharger</button>
      </div>
    </div>

    <div v-if="loading" class="loading">Chargement du contenu…</div>

    <div v-else-if="error" class="card">
      <p class="muted" style="margin:0">{{ error }}</p>
    </div>

    <div v-else-if="data" class="split">
      <!-- Raw content -->
      <div class="card no-pad">
        <div class="card-head pd-head">
          <h3>Contenu brut</h3>
          <div class="pd-head-right">
            <span class="pill" :class="data.is_binary ? 'pill-warn' : 'pill-ok'">
              <span class="d"></span>{{ data.is_binary ? 'binaire · hex' : 'texte' }}
            </span>
            <span class="small">{{ formatBytes(data.shown_bytes) }}</span>
            <button class="btn btn-ghost btn-sm" @click="copyContent">{{ copied ? 'Copié !' : 'Copier' }}</button>
          </div>
        </div>
        <div v-if="data.truncated" class="pd-notice">
          Aperçu tronqué — seul le début du fichier est affiché. Utilisez « Télécharger » pour le fichier complet.
        </div>
        <pre v-if="body" class="code pd-pre" :class="{ 'pd-nowrap': data.is_binary }">{{ body }}</pre>
        <div v-else class="empty">Fichier vide.</div>
      </div>

      <!-- Metadata -->
      <div class="card">
        <div class="card-head"><h3>Métadonnées</h3></div>
        <table class="kv">
          <tbody>
            <tr><td>Nom</td><td class="mono">{{ data.meta.file_name || '-' }}</td></tr>
            <tr><td>SHA-256</td><td class="mono" style="word-break:break-all">{{ data.meta.file_hash }}</td></tr>
            <tr><td>Taille</td><td>{{ formatBytes(data.meta.file_size) }}</td></tr>
            <tr><td>Service</td><td><span class="pill"><span class="d"></span>{{ data.meta.service_type || '-' }}</span></td></tr>
            <tr><td>IP source</td><td class="mono">{{ data.meta.source_ip || '-' }}</td></tr>
            <tr>
              <td>Identifiants</td>
              <td class="mono">
                <template v-if="data.meta.username || data.meta.password">
                  {{ data.meta.username }}<span v-if="data.meta.password">:{{ data.meta.password }}</span>
                </template>
                <template v-else>-</template>
              </td>
            </tr>
            <tr><td>Occurrences</td><td>{{ data.meta.upload_count }}</td></tr>
            <tr><td>Agent</td><td>{{ data.meta.agent_id ?? '-' }}</td></tr>
            <tr><td>Première capture</td><td class="small">{{ formatDate(data.meta.first_seen) }}</td></tr>
            <tr><td>Dernière capture</td><td class="small">{{ formatDate(data.meta.last_seen) }}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
    </div>
  </div>
</template>

<style scoped>
/* Uses admin-paper primitives (.split/.card/.card-head/.kv/.code/.pill/.btn)
   and the --ap-* palette. Only view-specific tweaks live here. */

/* Back button row — sits above the header, outside the paper scope */
.pd-back { margin-bottom: 20px; }

.pd-head { padding: 16px 20px; margin-bottom: 0; }
.pd-head-right { display: flex; align-items: center; gap: 12px; }

.pd-notice {
  padding: 10px 20px; font-size: 12px; color: var(--ap-ink);
  background: var(--ap-warn-bg); border-bottom: 1px solid var(--ap-line);
}

/* Scrollable raw content pane — the .code block already carries the ink surface */
.pd-pre {
  margin: 0; max-height: 70vh; overflow: auto; border-left: none;
  border-radius: 0; font-size: 12.5px; line-height: 1.6;
}
/* Hex dump: keep the columns aligned (scroll sideways rather than wrap) */
.pd-nowrap { white-space: pre; word-break: normal; }
</style>
