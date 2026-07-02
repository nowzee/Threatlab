<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

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

export default defineComponent({
  name: "HoneypotManagementView",
  setup() {
    const auth = useAuthStore()
    const isAdmin = computed(() => auth.user?.role === 'admin')
    const honeypots = ref<Honeypot[]>([])
    const selectedHoneypots = ref<number[]>([])
    const showDeleteConfirm = ref(false)
    const searchQuery = ref('')

    const loadHoneypots = async () => {
      try {
        const response = await fetch('/api/agent/manage/list', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        })
        if (!response.ok) throw new Error("Erreur API")

        const data = await response.json()
        honeypots.value = data.map((item: any) => ({
          id: item.id,
          name: item.agent_name,
          type: (item.service_type || 'ssh').toUpperCase(),
          ip: item.ip_address,
          owner: item.owner_username || '—',
          created_at: item.created_at || '',
          last_activity: item.updated_at || '',
          alerts_count: item.alert_generated || 0
        }))
      } catch (error) {
        console.error("Erreur lors du chargement des honeypots:", error)
      }
    }

    const filteredHoneypots = computed(() => {
      if (!searchQuery.value.trim()) return honeypots.value
      const query = searchQuery.value.toLowerCase()
      return honeypots.value.filter(h =>
        h.name.toLowerCase().includes(query) ||
        h.type.toLowerCase().includes(query) ||
        h.ip.includes(query)
      )
    })

    const deleteSelected = async () => {
      const deleted: typeof selectedHoneypots.value = []
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
        // En cas d'échec partiel, resynchroniser avec l'état réel du serveur.
        if (hadError) await loadHoneypots()
      }
    }

    const selectAll = () => {
      if (selectedHoneypots.value.length === filteredHoneypots.value.length) {
        selectedHoneypots.value = []
      } else {
        selectedHoneypots.value = filteredHoneypots.value.map(h => h.id)
      }
    }

    onMounted(() => { loadHoneypots() })

    return {
      honeypots,
      isAdmin,
      selectedHoneypots,
      filteredHoneypots,
      showDeleteConfirm,
      searchQuery,
      deleteSelected,
      selectAll
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <h1 class="page-title">Gestion des Honeypots</h1>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="card card-body stat-card">
        <div class="stat-icon icon-total">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 11V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"></path>
            <path d="M12 12H7"></path><path d="M12 8H7"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ honeypots.length }}</div>
          <div class="stat-label">Total Honeypots</div>
        </div>
      </div>

      <div class="card card-body stat-card">
        <div class="stat-icon icon-alerts">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ honeypots.reduce((sum, h) => sum + h.alerts_count, 0) }}</div>
          <div class="stat-label">Alertes Generees</div>
        </div>
      </div>
    </div>

    <!-- Controls -->
    <div class="controls-section">
      <div class="controls-left">
        <button class="btn btn-danger" @click="showDeleteConfirm = true" :disabled="selectedHoneypots.length === 0">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          Supprimer ({{ selectedHoneypots.length }})
        </button>
      </div>
      <div class="controls-right">
        <div class="search-container">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><path d="M21 21l-4.35-4.35"></path></svg>
          <input type="text" placeholder="Rechercher..." v-model="searchQuery" class="search-input">
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="table-wrap">
      <table class="honeypots-table">
        <thead>
          <tr>
            <th width="40">
              <input type="checkbox" @change="selectAll" :checked="selectedHoneypots.length === filteredHoneypots.length && filteredHoneypots.length > 0">
            </th>
            <th>Nom</th>
            <th>Type</th>
            <th v-if="isAdmin">Proprietaire</th>
            <th>Adresse IP</th>
            <th>Alertes</th>
            <th>Derniere Activite</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="honeypot in filteredHoneypots" :key="honeypot.id">
            <td><input type="checkbox" :value="honeypot.id" v-model="selectedHoneypots"></td>
            <td>
              <div class="name-primary">{{ honeypot.name }}</div>
              <div class="name-secondary">ID: {{ honeypot.id }}</div>
            </td>
            <td><span class="type-badge">{{ honeypot.type }}</span></td>
            <td v-if="isAdmin">{{ honeypot.owner }}</td>
            <td><code class="ip-address">{{ honeypot.ip }}</code></td>
            <td class="alerts-cell">{{ honeypot.alerts_count }}</td>
            <td class="activity-cell">{{ honeypot.last_activity }}</td>
            <td>
              <router-link :to="{ name: 'honeypot-detail', params: { id: honeypot.id } }" class="action-btn" title="Details">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
              </router-link>
            </td>
          </tr>
          <tr v-if="filteredHoneypots.length === 0">
            <td :colspan="isAdmin ? 8 : 7" class="empty-state">Aucun honeypot trouve</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Delete Confirm Modal -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="showDeleteConfirm = false">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h3>Confirmer la Suppression</h3>
          <button class="modal-close-btn" @click="showDeleteConfirm = false">x</button>
        </div>
        <div class="modal-body">
          <p>Supprimer {{ selectedHoneypots.length }} honeypot(s) ? Cette action est irreversible.</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDeleteConfirm = false">Annuler</button>
          <button class="btn btn-danger" @click="deleteSelected">Supprimer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.icon-total { background: rgba(30, 84, 229, 0.2); color: #1e54e5; }
.icon-alerts { background: rgba(255, 58, 94, 0.2); color: #ff3a5e; }

.controls-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
}

.controls-left, .controls-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-container {
  position: relative;
  display: flex;
  align-items: center;
}

.search-container svg {
  position: absolute;
  left: 12px;
  color: var(--text-color-muted);
}

.search-input {
  padding: 10px 16px 10px 40px;
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 8px;
  color: var(--white);
  font-size: 14px;
  width: 280px;
}

.search-input::placeholder { color: var(--text-color-muted); }

.table-wrap {
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 12px;
  overflow: hidden;
}

.honeypots-table {
  width: 100%;
  border-collapse: collapse;
}

.honeypots-table th {
  background: var(--table-header-bg);
  color: var(--text-color-muted);
  font-weight: 600;
  font-size: 13px;
  padding: 14px 20px;
  text-align: left;
  border-bottom: 1px solid var(--container-border-color);
}

.honeypots-table td {
  padding: 16px 20px;
  border-bottom: 1px solid var(--container-border-color);
  font-size: 14px;
  color: var(--white);
}

.honeypots-table tr:hover { background: var(--table-row-hover); }

.name-primary { font-weight: 600; font-size: 14px; }
.name-secondary { font-size: 12px; color: var(--text-color-muted); font-family: monospace; }

.type-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  background: rgba(30, 84, 229, 0.2);
  color: #42a5f5;
}

.ip-address {
  padding: 4px 8px;
  font-family: monospace;
  font-size: 13px;
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
}

.alerts-cell { color: #ff3a5e; font-weight: 600; }
.activity-cell { font-size: 12px; color: var(--text-color-muted); font-family: monospace; }

.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(0, 230, 118, 0.15);
  color: #00e676;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  transition: background 0.2s;
}

.action-btn:hover { background: rgba(0, 230, 118, 0.25); }

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-color-muted);
  font-style: italic;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--container-border-color);
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .controls-section { flex-direction: column; }
  .search-input { width: 100%; }
}
</style>
