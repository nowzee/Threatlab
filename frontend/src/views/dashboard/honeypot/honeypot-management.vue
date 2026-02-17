<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'

interface Honeypot {
  id: number
  name: string
  type: 'SSH' | 'HTTP' | 'FTP' | 'SMTP' | 'Telnet'
  ip: string
  group: string
  created_at: string
  last_activity: string
  alerts_count: number
}

interface HoneypotGroup {
  name: string
}

export default defineComponent({
  name: "HoneypotManagementView",
  setup() {

    // États réactifs
    const honeypots = ref<Honeypot[]>([])
    const groups = ref<HoneypotGroup[]>([])
    const selectedHoneypots = ref<number[]>([])
    const showCreateModal = ref(false)
    const showGroupModal = ref(false)
    const showDeleteConfirm = ref(false)
    const showIntegrationModal = ref(false)
    const currentHoneypot = ref<Honeypot | null>(null)
    const filterGroup = ref<string>('all')
    const filterStatus = ref<string>('all')
    const searchQuery = ref('')

    const groupForm = ref({
      name: '',
      description: '',
    })

    const integrationForm = ref({
      elk_enabled: false,
      elk_url: '',
      opencti_enabled: false,
      opencti_url: ''
    })

    const loadHoneypots = async () => {
      try {
        const response = await fetch('/api/agent/manage/list', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        })
        if (!response.ok) {
          throw new Error("Erreur API")
        }
        const data = await response.json()

        honeypots.value = data.map((item: any) => ({
          id: item.id,
          name: item.agent_name,
          type: (item.service_type || 'SSH') as 'SSH' | 'HTTP' | 'FTP' | 'SMTP' | 'Telnet',
          status: item.is_active ? 'active' : 'inactive',
          ip: item.ip_address,
          group: item.groupe || 'default',
          created_at: item.created_at || '',
          last_activity: item.updated_at || '',
          alerts_count: item.alert_generated || 0
        }))
        const names = new Set<string>()

        data.forEach((item: any) => {
        names.add(item.groupe || "default")
        })

        groups.value = []
        names.forEach((name: string) => {
          groups.value.push({name})
        })

      } catch (error) {
        console.error("Erreur lors du chargement des honeypots:", error)
      }
    }

    // Honeypots filtrés
    const filteredHoneypots = computed(() => {
      let filtered = honeypots.value
      if (filterGroup.value !== 'all') {
        filtered = filtered.filter(h => h.group === filterGroup.value)
      }
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(h =>
          h.name.toLowerCase().includes(query) ||
          h.type.toLowerCase().includes(query) ||
          h.ip.includes(query)
        )
      }
      return filtered
    })

    // Fonctions utilitaires
    const getStatusClass = (status: string) => {
      switch (status) {
        case 'active': return 'status-active'
        case 'inactive': return 'status-inactive'
        case 'error': return 'status-error'
        default: return 'status-inactive'
      }
    }

    const getStatusText = (status: string) => {
      switch (status) {
        case 'active': return 'Actif'
        case 'inactive': return 'Inactif'
        case 'error': return 'Erreur'
        default: return 'Inconnu'
      }
    }

    const getTypeIcon = (type: string) => {
      switch (type) {
        case 'SSH': return 'M2 3h20v18H2z'
        case 'HTTP': return 'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z'
        case 'FTP': return 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'
        case 'SMTP': return 'M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z'
        case 'Telnet': return 'M2 3h20v18H2z'
        default: return 'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z'
      }
    }

    const openGroupModal = () => {
      groupForm.value = { name: '', description: ''}
      showGroupModal.value = true
    }

    const createGroup = async () => {
      const newGroup: HoneypotGroup = {
        name: groupForm.value.name,
      }
      const response = await fetch('api/agent/manage/create_group', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({group_name: groupForm.value.name})
      })

      const result = await response.json()
      if (result.success) {

        groups.value.push(newGroup)
        showGroupModal.value = false
      }
    }

    const uniqueGroupsCount = computed(() => {
    const groupsSet = new Set(honeypots.value.map(h => h.group))
        return groupsSet.size
    })

    const deleteSelected = async () => {
    try {
    for (const id of selectedHoneypots.value) {
      const response = await fetch('/api/agent/manage/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ agent_id: id })
      })

      if (!response.ok) {
        console.error(`Erreur lors de la suppression de l'agent ${id}`)
      } else {
        const result = await response.json()
        if (!result.success) {
          console.error(`Suppression échouée pour l'agent ${id}`)
        }
      }
    }

    // Mise à jour locale de la liste
    honeypots.value = honeypots.value.filter(h => !selectedHoneypots.value.includes(h.id))
    selectedHoneypots.value = []
    showDeleteConfirm.value = false

  } catch (error) {
    console.error("Erreur lors de la suppression :", error)
  }
}


    const selectAll = () => {
      if (selectedHoneypots.value.length === filteredHoneypots.value.length) {
        selectedHoneypots.value = []
      } else {
        selectedHoneypots.value = filteredHoneypots.value.map(h => h.id)
      }
    }

    const closeModals = () => {
      showCreateModal.value = false
      showGroupModal.value = false
      showDeleteConfirm.value = false
      showIntegrationModal.value = false
    }

    onMounted(() => {
      loadHoneypots()
    })

    return {
      uniqueGroupsCount,
      honeypots,
      groups,
      selectedHoneypots,
      filteredHoneypots,
      showCreateModal,
      showGroupModal,
      showDeleteConfirm,
      showIntegrationModal,
      currentHoneypot,
      filterGroup,
      filterStatus,
      searchQuery,
      groupForm,
      integrationForm,
      getStatusClass,
      getStatusText,
      getTypeIcon,
      openGroupModal,
      createGroup,
      deleteSelected,
      selectAll,
      closeModals
    }
  }
})
</script>


<template>
  <div class="content-wrapper">
    <!-- En-tête -->
    <h1 class="page-title">
        Gestion des Honeypots
    </h1>

    <!-- Statistiques rapides -->
      <div class="stats-grid">

      <div class="card active card-body stat-card total">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 11V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"></path>
            <path d="M12 16H7"></path>
            <path d="M12 12H7"></path>
            <path d="M12 8H7"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ honeypots.length }}</div>
          <div class="stat-label">Total Honeypots</div>
        </div>
      </div>

      <div class="card active card-body stat-card groups">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ uniqueGroupsCount }}</div>
          <div class="stat-label">Groupes</div>
        </div>
      </div>

      <div class="card active card-body stat-card alerts">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ honeypots.reduce((sum, h) => sum + h.alerts_count, 0) }}</div>
          <div class="stat-label">Alertes Générées</div>
        </div>
      </div>
    </div>

    <!-- Contrôles et filtres -->
    <div class="controls-section">
      <div class="controls-left">

        <button class="btn btn-secondary" @click="openGroupModal">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          Nouveau Groupe
        </button>

        <button
          class="btn btn-danger"
          @click="showDeleteConfirm = true"
          :disabled="selectedHoneypots.length === 0">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          Supprimer
        </button>
      </div>

      <div class="controls-right">
        <div class="search-container">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="M21 21l-4.35-4.35"></path>
          </svg>
          <input
            type="text"
            placeholder="Rechercher un honeypot..."
            v-model="searchQuery"
            class="search-input">
        </div>

        <select v-model="filterGroup" class="filter-select">
          <option value="all">Tous les groupes</option>
          <option v-for="group in groups" :value="group.name">
            {{ group.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Liste des honeypots -->
    <div class="content-section">
      <div class="table-container">
        <div class="table-header">
          <h2 class="table-title">Honeypots</h2>
        </div>

        <div class="modern-table">
          <table class="honeypots-table">
            <thead>
              <tr>
                <th width="40">
                  <input
                    type="checkbox"
                    @change="selectAll"
                    :checked="selectedHoneypots.length === filteredHoneypots.length && filteredHoneypots.length > 0">
                </th>
                <th>Nom</th>
                <th>Type</th>
                <th>Adresse IP</th>
                <th>Groupe</th>
                <th>Alertes</th>
                <th>Dernière Activité</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="honeypot in filteredHoneypots"
                  :key="honeypot.id"
                  class="honeypot-row">
                <td>
                  <input
                    type="checkbox"
                    :value="honeypot.id"
                    v-model="selectedHoneypots">
                </td>
                <td class="name-cell">
                  <div class="honeypot-name">
                    <div class="name-info">
                      <div class="name-primary">{{ honeypot.name }}</div>
                      <div class="name-secondary">ID: {{ honeypot.id }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="type-badge" :class="'type-' + honeypot.type.toLowerCase()">
                    {{ honeypot.type }}
                  </span>
                </td>
                <td>
                  <code class="ip-address">{{ honeypot.ip }}</code>
                </td>
                <td>
                  <span class="group-badge">{{ honeypot.group }}</span>
                </td>
                <td class="alerts-cell">
                  <div class="alerts-count">{{ honeypot.alerts_count }}</div>
                </td>
                <td class="activity-cell">
                  <time class="last-activity">{{ honeypot.last_activity }}</time>
                </td>
                <td class="actions-cell">
                  <div class="action-buttons">
                    <router-link
                      :to="{ name: 'honeypot-detail', params: { id: honeypot.id } }"
                      class="action-btn view"
                      title="Voir les détails">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    </router-link>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal Création Groupe -->
    <div v-if="showGroupModal" class="modal-overlay" @click="closeModals">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h3>Créer un Nouveau Groupe</h3>
          <button class="modal-close-btn" @click="closeModals">×</button>
        </div>
        <div class="modal-content">
          <div class="form-group">
            <label>Nom du groupe</label>
            <input type="text" v-model="groupForm.name" placeholder="Ex: Production">
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModals">Annuler</button>
          <button class="btn btn-primary" @click="createGroup">Créer</button>
        </div>
      </div>
    </div>

    <!-- Modal Confirmation Suppression -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="closeModals">
      <div class="modal-container danger" @click.stop>
        <div class="modal-header">
          <h3>Confirmer la Suppression</h3>
          <button class="modal-close-btn" @click="closeModals">×</button>
        </div>
        <div class="modal-content">
          <p>Êtes-vous sûr de vouloir supprimer {{ selectedHoneypots.length }} honeypot(s) ?</p>
          <p class="warning-text">Cette action est irréversible.</p>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModals">Annuler</button>
          <button class="btn btn-danger" @click="deleteSelected">Supprimer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

.status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.active .stat-icon {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
}

.total .stat-icon {
  background: rgba(30, 84, 229, 0.2);
  color: #1e54e5;
}

.groups .stat-icon {
  background: rgba(255, 183, 77, 0.2);
  color: #ffb74d;
}

.alerts .stat-icon {
  background: rgba(255, 58, 94, 0.2);
  color: #ff3a5e;
}

/* Contrôles */
.controls-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  gap: 24px;
}

.controls-left {
  display: flex;
  gap: 12px;
}

.controls-right {
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
  z-index: 1;
}

.search-input {
  padding: 10px 16px 10px 40px;
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 8px;
  color: var(--white);
  font-size: 14px;
  width: 300px;
}

.search-input::placeholder {
  color: var(--text-color-muted);
}

.filter-select {
  padding: 10px 16px;
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 8px;
  color: var(--white);
  font-size: 14px;
  min-width: 150px;
}

/* Table */
.content-section {
  margin-bottom: 32px;
}

.table-container {
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 16px;
  overflow: hidden;
}

.table-header {
  padding: 24px 32px;
  border-bottom: 1px solid var(--container-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--white);
  margin: 0;
}

.modern-table {
  overflow-x: auto;
}

.honeypots-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.honeypots-table thead th {
  background: var(--table-header-bg);
  color: var(--text-color-muted);
  font-weight: 500;
  font-size: 14px;
  letter-spacing: 0.5px;
  padding: 16px 24px;
  text-align: left;
  border-bottom: 1px solid var(--container-border-color);
}

.honeypot-row {
  border-bottom: 1px solid var(--table-border);
  transition: all 0.1s ease;
}

.honeypot-row:hover {
  background: var(--table-row-hover);
}

.honeypots-table td {
  padding: 20px 24px;
  vertical-align: middle;
}

.name-cell {
  min-width: 200px;
}

.honeypot-name {
  display: flex;
  align-items: center;
  gap: 12px;
}

.name-primary {
  font-weight: 600;
  color: var(--white);
  font-size: 14px;
}

.name-secondary {
  font-size: 12px;
  color: var(--text-color-muted);
  font-family: 'Courier New', monospace;
}

.type-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.ip-address {
  padding: 6px 10px;
  font-family: 'Courier New', monospace;
  font-weight: 600;
  font-size: 13px;
}

.group-badge {
  background: rgba(255, 255, 255, 0.1);
  color: var(--white);
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.alerts-count {
  font-size: 18px;
  font-weight: 400;
  color: #ff3a5e;
  text-align: center;
}

.last-activity {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: var(--text-color-muted);
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.toggle {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
}

.action-btn.toggle:hover {
  background: rgba(0, 230, 118, 0.3);
}

.action-btn.view {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
  text-decoration: none;
}

.action-btn.view:hover {
  background: rgba(0, 230, 118, 0.3);
}

.action-btn.integration {
  background: rgba(30, 84, 229, 0.2);
  color: #1e54e5;
}

.action-btn.integration:hover {
  background: rgba(30, 84, 229, 0.3);
}

.modal-content {
  padding: 32px;
}

.modal-actions {
  padding: 24px 32px;
  border-top: 1px solid var(--container-border-color);
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.form-group label {
  display: block;
  color: var(--white);
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 14px;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 80%;
  padding: 12px 16px;
  background: var(--container-background);
  border: 1px solid var(--container-border-color);
  border-radius: 8px;
  color: var(--white);
  font-size: 14px;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}
input:checked + .slider {
  background-color: var(--accent-color);
}

input:checked + .slider:before {
  transform: translateX(26px);
}
</style>
