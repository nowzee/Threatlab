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

    <div v-else-if="data">
      <!-- Metadata: compact strip that wraps at any width -->
      <div class="card pd-meta">
        <div class="pd-mi"><span class="pd-l">Taille</span><span class="pd-v">{{ formatBytes(data.meta.file_size) }}</span></div>
        <div class="pd-mi"><span class="pd-l">Service</span><span class="pd-v">{{ data.meta.service_type || '-' }}</span></div>
        <div class="pd-mi"><span class="pd-l">IP source</span><span class="pd-v mono">{{ data.meta.source_ip || '-' }}</span></div>
        <div class="pd-mi"><span class="pd-l">Identifiants</span><span class="pd-v mono">{{ (data.meta.username || data.meta.password) ? (data.meta.username + (data.meta.password ? ':' + data.meta.password : '')) : '-' }}</span></div>
        <div class="pd-mi"><span class="pd-l">Occurrences</span><span class="pd-v">{{ data.meta.upload_count }}</span></div>
        <div class="pd-mi"><span class="pd-l">Agent</span><span class="pd-v">{{ data.meta.agent_id ?? '-' }}</span></div>
        <div class="pd-mi"><span class="pd-l">Première capture</span><span class="pd-v">{{ formatDate(data.meta.first_seen) }}</span></div>
        <div class="pd-mi"><span class="pd-l">Dernière capture</span><span class="pd-v">{{ formatDate(data.meta.last_seen) }}</span></div>
        <div class="pd-mi pd-mi-wide"><span class="pd-l">SHA-256</span><span class="pd-v mono pd-hash">{{ data.meta.file_hash }}</span></div>
      </div>

      <!-- Raw content: full width, height-capped, scrollable -->
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
    </div>
    </div>
  </div>
</template>

<style scoped>
/* Uses admin-paper primitives (.card/.card-head/.code/.pill/.btn) and the
   --ap-* palette. Single-column, full-width layout — robust at any width/zoom. */

/* Back button row — sits above the header, outside the paper scope */
.pd-back { margin-bottom: 20px; }

/* Metadata strip: a wrapping row of label/value pairs (no fragile grid) */
.pd-meta { display: flex; flex-wrap: wrap; gap: 14px 28px; padding: 16px 20px; margin-bottom: 16px; }
.pd-mi { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.pd-mi-wide { flex-basis: 100%; }
.pd-l { font-family: var(--ap-mono); font-size: 9.5px; text-transform: uppercase; letter-spacing: 1px; color: var(--ap-gray); }
.pd-v { font-size: 13px; color: var(--ap-ink); }
.pd-hash { word-break: break-all; }

/* Content card header */
.pd-head { padding: 14px 20px; margin-bottom: 0; }
.pd-head-right { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

.pd-notice {
  padding: 10px 20px; font-size: 12px; color: var(--ap-ink);
  background: var(--ap-warn-bg); border-bottom: 1px solid var(--ap-line);
}

/* Scrollable raw content pane. min-width:0 stops long lines from blowing out
   the layout; the .code block already carries the ink surface + colours.
   `pre.` prefix raises specificity so these beat the shared .code rule. */
pre.pd-pre {
  margin: 0; min-width: 0; max-width: 100%;
  max-height: 65vh; overflow: auto;
  border-left: none; border-radius: 0;
  font-size: 13px; line-height: 1.55;
  white-space: pre-wrap; word-break: break-word;
}
/* Hex dump: keep the columns aligned (scroll sideways rather than wrap) */
pre.pd-nowrap { white-space: pre; word-break: normal; }
</style>
