<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import '@/assets/css/admin-paper.css'

interface Honeypot {
  id: number
  name: string
  type: string
  ip: string
  owner: string
  created_at: string
  last_activity: string
  alerts_count: number
}

const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const honeypots = ref<Honeypot[]>([])
const selectedHoneypots = ref<number[]>([])
const showDeleteConfirm = ref(false)
const searchQuery = ref('')
const deleting = ref(false)
const toast = ref('')
const loading = ref(true)

const distinctTypes = computed(() => new Set(honeypots.value.map(h => h.type)).size)

const filteredHoneypots = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return honeypots.value
  return honeypots.value.filter(h =>
    h.name.toLowerCase().includes(query) ||
    h.type.toLowerCase().includes(query) ||
    h.ip.includes(query) ||
    h.owner.toLowerCase().includes(query)
  )
})

const allSelected = computed(() =>
  filteredHoneypots.value.length > 0 &&
  selectedHoneypots.value.length === filteredHoneypots.value.length
)

async function loadHoneypots() {
  loading.value = true
  try {
    const response = await fetch('/api/agent/manage/list', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) throw new Error('Erreur API')

    const data = await response.json()
    honeypots.value = data.map((item: any) => ({
      id: item.id,
      name: item.agent_name,
      type: (item.service_type || 'ssh').toUpperCase(),
      ip: item.ip_address,
      owner: item.owner_username || '—',
      created_at: item.created_at || '',
      last_activity: item.last_activity || '',
      alerts_count: item.alert_generated || 0
    }))
  } catch (error) {
    console.error('Erreur lors du chargement des honeypots:', error)
  } finally {
    loading.value = false
  }
}

function selectAll() {
  selectedHoneypots.value = allSelected.value ? [] : filteredHoneypots.value.map(h => h.id)
}

async function deleteSelected() {
  deleting.value = true
  const deleted: number[] = []
  let hadError = false
  try {
    for (const id of selectedHoneypots.value) {
      try {
        const response = await fetch('/api/agent/manage/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ agent_id: id })
        })
        const data = await response.json().catch(() => ({}))
        // Ne retirer de la liste que si le backend confirme la suppression.
        if (response.ok && data.success) {
          deleted.push(id)
        } else {
          hadError = true
          console.error(`Erreur suppression agent ${id}`)
        }
      } catch (e) {
        hadError = true
        console.error(`Erreur suppression agent ${id}:`, e)
      }
    }
  } finally {
    honeypots.value = honeypots.value.filter(h => !deleted.includes(h.id))
    selectedHoneypots.value = []
    showDeleteConfirm.value = false
    deleting.value = false
    // En cas d'échec partiel, resynchroniser avec l'état réel du serveur.
    if (hadError) {
      await loadHoneypots()
      flash('Certaines suppressions ont échoué.')
    } else {
      flash(`${deleted.length} honeypot(s) supprimé(s).`)
    }
  }
}

function fmt(d: string): string {
  return d || '—'
}

// Format compact : 2000 -> "2k", 2340 -> "2.3k", 1500000 -> "1.5M".
function compact(n: number): string {
  if (n < 1000) return String(n)
  if (n < 1_000_000) {
    const v = n / 1000
    return (v < 10 ? v.toFixed(1).replace(/\.0$/, '') : Math.round(v).toString()) + 'k'
  }
  const v = n / 1_000_000
  return (v < 10 ? v.toFixed(1).replace(/\.0$/, '') : Math.round(v).toString()) + 'M'
}

let toastTimer: ReturnType<typeof setTimeout>
function flash(m: string) {
  toast.value = m
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 2600)
}

onMounted(loadHoneypots)
</script>

<template>
  <div class="admin-paper content-wrapper hp-page">
    <!-- Header -->
    <div class="head">
      <div>
        <h1>Gestion des Honeypots</h1>
        <p class="muted">Supervisez vos agents honeypot et les alertes qu'ils génèrent.</p>
      </div>
      <div class="actions">
        <input v-model="searchQuery" class="input search" placeholder="Rechercher…" />
        <button class="btn btn-danger" :disabled="selectedHoneypots.length === 0" @click="showDeleteConfirm = true">
          Supprimer
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div class="hp-stats">
      <div class="hp-stat">
        <div class="n"><span v-if="loading" class="sk-bar sk-num"></span><template v-else>{{ honeypots.length }}</template></div>
        <div class="l">Honeypots</div>
      </div>
      <div class="hp-stat">
        <div class="n"><span v-if="loading" class="sk-bar sk-num"></span><template v-else>{{ distinctTypes }}</template></div>
        <div class="l">Types de services</div>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="hp-toolbar" v-if="filteredHoneypots.length">
      <label class="hp-selectall">
        <input type="checkbox" class="hp-check" :checked="allSelected" @change="selectAll" />
        <span>Tout sélectionner</span>
      </label>
      <span class="hp-selcount" v-if="selectedHoneypots.length">{{ selectedHoneypots.length }} sélectionné(s)</span>
    </div>

    <!-- Skeleton de chargement (pas de spinner : cartes fantômes avec reflet qui glisse) -->
    <div class="hp-grid" v-if="loading">
      <article class="hp-card sk-card" v-for="n in 6" :key="'sk' + n" aria-hidden="true">
        <div class="hp-card-top">
          <div class="sk-head">
            <span class="sk-bar" style="width:62%;height:15px"></span>
            <span class="sk-bar" style="width:34%;height:11px;margin-top:8px"></span>
          </div>
          <span class="sk-bar sk-box"></span>
        </div>
        <span class="sk-bar" style="width:64px;height:20px"></span>
        <div class="hp-meta">
          <span class="sk-bar" style="width:100%;height:12px"></span>
          <span class="sk-bar" style="width:100%;height:12px"></span>
          <span class="sk-bar" style="width:100%;height:12px"></span>
        </div>
        <div class="hp-foot">
          <span class="sk-bar" style="width:52px;height:22px"></span>
          <span class="sk-bar" style="width:62px;height:26px"></span>
        </div>
      </article>
    </div>

    <!-- Grid -->
    <div class="hp-grid" v-else-if="filteredHoneypots.length">
      <article
        v-for="h in filteredHoneypots"
        :key="h.id"
        class="hp-card"
        :class="{ sel: selectedHoneypots.includes(h.id) }"
      >
        <div class="hp-card-top">
          <div class="hp-head">
            <div class="hp-name">{{ h.name }}</div>
            <div class="hp-id">ID {{ h.id }}</div>
          </div>
          <input type="checkbox" class="hp-check" :value="h.id" v-model="selectedHoneypots" />
        </div>

        <div class="hp-tags">
          <span class="pill"><span class="d"></span>{{ h.type }}</span>
        </div>

        <div class="hp-meta">
          <div class="hp-row">
            <span class="k">Adresse IP</span>
            <span class="v mono">{{ h.ip }}</span>
          </div>
          <div class="hp-row" v-if="isAdmin">
            <span class="k">Propriétaire</span>
            <span class="v">{{ h.owner }}</span>
          </div>
          <div class="hp-row">
            <span class="k">Activité</span>
            <span class="v mono">{{ fmt(h.last_activity) }}</span>
          </div>
        </div>

        <div class="hp-foot">
          <div class="hp-alerts" :title="`${h.alerts_count} alerte(s) sur les dernières 24 h`">
            <span class="num">{{ compact(h.alerts_count) }}</span>
            <span class="lbl">alertes · 24 h</span>
          </div>
          <router-link :to="{ name: 'honeypot-detail', params: { id: h.id } }" class="btn btn-ghost btn-sm">Détails</router-link>
        </div>
      </article>
    </div>

    <!-- Empty -->
    <div class="hp-empty card" v-else>
      {{ searchQuery ? 'Aucun honeypot ne correspond à votre recherche.' : 'Aucun honeypot pour le moment.' }}
    </div>

    <!-- Delete confirm modal -->
    <div v-if="showDeleteConfirm" class="modal-mask" @click.self="showDeleteConfirm = false">
      <div class="modal">
        <h2>Supprimer {{ selectedHoneypots.length }} honeypot(s)</h2>
        <p class="sub">Cette action est irréversible. Les agents sélectionnés seront définitivement supprimés.</p>
        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" @click="showDeleteConfirm = false">Annuler</button>
          <button type="button" class="btn btn-danger" :disabled="deleting" @click="deleteSelected">
            {{ deleting ? 'Suppression…' : 'Supprimer' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<style scoped>
/* Header — search input and button share the exact same height */
.hp-page .head .actions { display: flex; gap: 10px; align-items: center; }
.hp-page .head .actions .search { flex: 1 1 220px; width: auto; min-width: 0; max-width: 320px; height: 40px; }
.hp-page .head .actions .btn { height: 40px; padding: 0 18px; }

/* Stat tiles — no colour, just a structural ink rule on the left */
.hp-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
}
.hp-stat {
  flex: 1 1 180px;
  max-width: 260px;
  background: var(--ap-panel);
  border: 1px solid var(--ap-line);
  padding: 20px 22px;
}
.hp-stat .n { font-size: 30px; font-weight: 600; letter-spacing: -1px; line-height: 1; color: var(--ap-ink); }
.hp-stat .l { margin-top: 8px; font-family: var(--ap-mono); font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--ap-gray); }

/* Toolbar */
.hp-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 2px 14px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--ap-line);
}
.hp-selectall { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; color: var(--ap-ink); cursor: pointer; user-select: none; }
.hp-selcount { font-family: var(--ap-mono); font-size: 11px; text-transform: uppercase; letter-spacing: .8px; color: var(--ap-gray); }

/* Checkbox */
.hp-check { width: 16px; height: 16px; cursor: pointer; accent-color: var(--ap-accent); flex-shrink: 0; }

/* Card grid */
.hp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.hp-card {
  display: flex; flex-direction: column; gap: 14px;
  background: var(--ap-panel);
  border: 1px solid var(--ap-line);
  padding: 18px;
  transition: border-color .15s;
}
.hp-card:hover { border-color: var(--ap-line-strong); }
.hp-card.sel { border-color: var(--ap-accent); box-shadow: inset 0 0 0 1px var(--ap-accent); }

.hp-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.hp-head { min-width: 0; }
.hp-name { font-size: 15px; font-weight: 600; color: var(--ap-ink); line-height: 1.3; word-break: break-word; }
.hp-id { margin-top: 3px; font-family: var(--ap-mono); font-size: 11px; color: var(--ap-gray); }

.hp-tags { display: flex; flex-wrap: wrap; gap: 6px; }

.hp-meta { display: flex; flex-direction: column; gap: 9px; }
.hp-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.hp-row .k { font-family: var(--ap-mono); font-size: 10px; text-transform: uppercase; letter-spacing: .8px; color: var(--ap-gray); white-space: nowrap; }
.hp-row .v { font-size: 13px; color: var(--ap-ink); text-align: right; word-break: break-all; }

.hp-foot { display: flex; align-items: center; justify-content: space-between; margin-top: auto; padding-top: 14px; border-top: 1px solid var(--ap-line); }
.hp-foot .btn { text-decoration: none; }
.hp-alerts { display: flex; align-items: baseline; gap: 6px; }
.hp-alerts .num { font-size: 22px; font-weight: 600; color: var(--ap-ink); line-height: 1; }
.hp-alerts .lbl { font-family: var(--ap-mono); font-size: 10px; text-transform: uppercase; letter-spacing: .8px; color: var(--ap-gray); }

.hp-empty { text-align: center; color: var(--ap-gray); font-size: 14px; padding: 48px 24px; }

/* En dark, le survol ghost par défaut (--ap-sand) est trop proche du fond des cartes : on le renforce. */
[data-theme="dark"] .hp-page .btn-ghost:hover { background: var(--ap-line-strong); opacity: 1; }

/* Skeleton de chargement — barres fantômes avec reflet qui glisse (aucun spinner). */
.hp-page { --sk-base: #e9e6df; --sk-shine: rgba(255, 255, 255, 0.6); }
[data-theme="dark"] .hp-page { --sk-base: #262626; --sk-shine: rgba(255, 255, 255, 0.06); }
.sk-bar {
  position: relative;
  display: block;
  overflow: hidden;
  background: var(--sk-base);
  border-radius: 3px;
}
.sk-bar::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, var(--sk-shine), transparent);
  animation: sk-slide 1.4s ease-in-out infinite;
}
@keyframes sk-slide { to { transform: translateX(100%); } }
.sk-head { flex: 1; min-width: 0; }
.sk-box { width: 16px; height: 16px; flex-shrink: 0; }
.sk-num { display: inline-block; width: 44px; height: 26px; }
@media (prefers-reduced-motion: reduce) { .sk-bar::after { animation: none; } }

@media (max-width: 640px) {
  .hp-page .head { flex-direction: column; align-items: stretch; }
  .hp-page .head .actions { flex-direction: column; align-items: stretch; }
  .hp-page .head .actions .search { max-width: none; }
}
</style>
