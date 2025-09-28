<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

interface Honeypot {
  id: number
  name: string
  type: 'SSH' | 'HTTP' | 'FTP' | 'SMTP' | 'Telnet'
  status: 'active' | 'inactive' | 'error'
  ip: string
  port: number
  group: string
  created_at: string
  last_activity: string
  alerts_count: number
  integrations: {
    elk_enabled: boolean
    elk_url: string
    opencti_enabled: boolean
    opencti_url: string
  }
}

interface HoneypotGroup {
  id: number
  name: string
  description: string
  honeypots_count: number
  color: string
}

export default defineComponent({
  name: "HoneypotManagementView",
  setup() {
    const router = useRouter()

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

    // Formulaires
    const honeypotForm = ref({
      name: '',
      type: 'SSH',
      ip: '',
      port: 22,
      group: 'default'
    })

    const groupForm = ref({
      name: '',
      description: '',
      color: '#1e54e5'
    })

    const integrationForm = ref({
      elk_enabled: false,
      elk_url: '',
      opencti_enabled: false,
      opencti_url: ''
    })

    // Données factices
    const loadMockData = () => {
      groups.value = [
        { id: 1, name: 'Production', description: 'Honeypots de production', honeypots_count: 5, color: '#ff3a5e' },
        { id: 2, name: 'Test', description: 'Honeypots de test', honeypots_count: 3, color: '#ffb74d' },
        { id: 3, name: 'DMZ', description: 'Honeypots en zone démilitarisée', honeypots_count: 2, color: '#29b6f6' }
      ]

      honeypots.value = [
        {
          id: 1,
          name: 'SSH-Honeypot-01',
          type: 'SSH',
          status: 'active',
          ip: '10.0.1.100',
          port: 22,
          group: 'Production',
          created_at: '2024-03-15 10:30:00',
          last_activity: '2024-03-15 14:25:12',
          alerts_count: 127,
          integrations: {
            elk_enabled: true,
            elk_url: 'https://elk.company.com:9200',
            opencti_enabled: false,
            opencti_url: ''
          }
        },
        {
          id: 2,
          name: 'Web-Honeypot-01',
          type: 'HTTP',
          status: 'active',
          ip: '10.0.1.101',
          port: 80,
          group: 'Production',
          created_at: '2024-03-15 09:15:00',
          last_activity: '2024-03-15 14:20:45',
          alerts_count: 89,
          integrations: {
            elk_enabled: true,
            elk_url: 'https://elk.company.com:9200',
            opencti_enabled: true,
            opencti_url: 'https://opencti.company.com'
          }
        },
        {
          id: 3,
          name: 'FTP-Test-01',
          type: 'FTP',
          status: 'inactive',
          ip: '10.0.2.100',
          port: 21,
          group: 'Test',
          created_at: '2024-03-14 16:45:00',
          last_activity: '2024-03-14 18:30:22',
          alerts_count: 23,
          integrations: {
            elk_enabled: false,
            elk_url: '',
            opencti_enabled: false,
            opencti_url: ''
          }
        },
        {
          id: 4,
          name: 'SMTP-DMZ-01',
          type: 'SMTP',
          status: 'error',
          ip: '172.16.1.100',
          port: 25,
          group: 'DMZ',
          created_at: '2024-03-13 11:20:00',
          last_activity: '2024-03-13 15:10:33',
          alerts_count: 45,
          integrations: {
            elk_enabled: true,
            elk_url: 'https://elk.company.com:9200',
            opencti_enabled: false,
            opencti_url: ''
          }
        }
      ]
    }

    // Honeypots filtrés
    const filteredHoneypots = computed(() => {
      let filtered = honeypots.value

      if (filterGroup.value !== 'all') {
        filtered = filtered.filter(h => h.group === filterGroup.value)
      }

      if (filterStatus.value !== 'all') {
        filtered = filtered.filter(h => h.status === filterStatus.value)
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

    // Actions
    const openCreateModal = () => {
      honeypotForm.value = {
        name: '',
        type: 'SSH',
        ip: '',
        port: 22,
        group: groups.value[0]?.name || 'default'
      }
      showCreateModal.value = true
    }

    const openIntegrationModal = (honeypot: Honeypot) => {
      currentHoneypot.value = honeypot
      integrationForm.value = {
        elk_enabled: honeypot.integrations.elk_enabled,
        elk_url: honeypot.integrations.elk_url,
        opencti_enabled: honeypot.integrations.opencti_enabled,
        opencti_url: honeypot.integrations.opencti_url
      }
      showIntegrationModal.value = true
    }

    const openGroupModal = () => {
      groupForm.value = { name: '', description: '', color: '#1e54e5' }
      showGroupModal.value = true
    }

    const createHoneypot = () => {
      const newHoneypot: Honeypot = {
        id: Date.now(),
        name: honeypotForm.value.name,
        type: honeypotForm.value.type as 'SSH' | 'HTTP' | 'FTP' | 'SMTP' | 'Telnet',
        status: 'inactive',
        ip: honeypotForm.value.ip,
        port: honeypotForm.value.port,
        group: honeypotForm.value.group,
        created_at: new Date().toLocaleString(),
        last_activity: 'Jamais',
        alerts_count: 0,
        integrations: {
          elk_enabled: false,
          elk_url: '',
          opencti_enabled: false,
          opencti_url: ''
        }
      }
      honeypots.value.push(newHoneypot)
      showCreateModal.value = false
    }

    const createGroup = () => {
      const newGroup: HoneypotGroup = {
        id: Date.now(),
        name: groupForm.value.name,
        description: groupForm.value.description,
        honeypots_count: 0,
        color: groupForm.value.color
      }
      groups.value.push(newGroup)
      showGroupModal.value = false
    }

    const saveIntegrations = () => {
      if (currentHoneypot.value) {
        const index = honeypots.value.findIndex(h => h.id === currentHoneypot.value!.id)
        if (index !== -1 && honeypots.value[index]) {
          honeypots.value[index].integrations = {
            elk_enabled: integrationForm.value.elk_enabled,
            elk_url: integrationForm.value.elk_url,
            opencti_enabled: integrationForm.value.opencti_enabled,
            opencti_url: integrationForm.value.opencti_url
          }
        }
      }
      showIntegrationModal.value = false
    }

    const toggleHoneypot = (honeypot: Honeypot) => {
      const index = honeypots.value.findIndex(h => h.id === honeypot.id)
      if (index !== -1 && honeypots.value[index]) {
        honeypots.value[index].status = honeypot.status === 'active' ? 'inactive' : 'active'
      }
    }

    const deleteSelected = () => {
      honeypots.value = honeypots.value.filter(h => !selectedHoneypots.value.includes(h.id))
      selectedHoneypots.value = []
      showDeleteConfirm.value = false
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
      loadMockData()
    })

    return {
      // Données
      honeypots,
      groups,
      selectedHoneypots,
      filteredHoneypots,

      // États des modales
      showCreateModal,
      showGroupModal,
      showDeleteConfirm,
      showIntegrationModal,
      currentHoneypot,

      // Filtres
      filterGroup,
      filterStatus,
      searchQuery,

      // Formulaires
      honeypotForm,
      groupForm,
      integrationForm,

      // Méthodes
      getStatusClass,
      getStatusText,
      getTypeIcon,
      openCreateModal,
      openIntegrationModal,
      openGroupModal,
      createHoneypot,
      createGroup,
      saveIntegrations,
      toggleHoneypot,
      deleteSelected,
      selectAll,
      closeModals
    }
  }
})
</script>

<template>
  <div class="honeypot-management-page">
    <!-- En-tête -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 11V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"></path>
            <path d="M12 16H7"></path>
            <path d="M12 12H7"></path>
            <path d="M12 8H7"></path>
            <path d="M16 16v6"></path>
            <path d="M19 19l-3-3-3 3"></path>
          </svg>
          Gestion des Honeypots
        </h1>
        <div class="status-indicator">
          <span class="status-dot status-active"></span>
          <span class="status-text">{{ filteredHoneypots.length }} honeypot(s) trouvé(s)</span>
        </div>
      </div>
    </div>

    <!-- Statistiques rapides -->
    <div class="stats-grid">
      <div class="stat-card active">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="8 12 12 16 16 12"></polyline>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ honeypots.filter(h => h.status === 'active').length }}</div>
          <div class="stat-label">Honeypots Actifs</div>
        </div>
      </div>

      <div class="stat-card total">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 11V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"></path>
            <path d="M12 16H7"></path>
            <path d="M12 12H7"></path>
            <path d="M12 8H7"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ honeypots.length }}</div>
          <div class="stat-label">Total Honeypots</div>
        </div>
      </div>

      <div class="stat-card groups">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ groups.length }}</div>
          <div class="stat-label">Groupes</div>
        </div>
      </div>

      <div class="stat-card alerts">
        <div class="stat-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ honeypots.reduce((sum, h) => sum + h.alerts_count, 0) }}</div>
          <div class="stat-label">Alertes Générées</div>
        </div>
      </div>
    </div>

    <!-- Contrôles et filtres -->
    <div class="controls-section">
      <div class="controls-left">
        <button class="btn btn-primary" @click="openCreateModal">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Nouveau Honeypot
        </button>

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
          Supprimer ({{ selectedHoneypots.length }})
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
          <option v-for="group in groups" :key="group.id" :value="group.name">
            {{ group.name }}
          </option>
        </select>

        <select v-model="filterStatus" class="filter-select">
          <option value="all">Tous les statuts</option>
          <option value="active">Actif</option>
          <option value="inactive">Inactif</option>
          <option value="error">Erreur</option>
        </select>
      </div>
    </div>

    <!-- Liste des honeypots -->
    <div class="content-section">
      <div class="table-container">
        <div class="table-header">
          <h2 class="table-title">Honeypots</h2>
          <button class="btn btn-secondary btn-sm" @click="selectAll">
            {{ selectedHoneypots.length === filteredHoneypots.length ? 'Désélectionner tout' : 'Sélectionner tout' }}
          </button>
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
                <th>Statut</th>
                <th>Adresse IP</th>
                <th>Port</th>
                <th>Groupe</th>
                <th>Alertes</th>
                <th>Dernière Activité</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="honeypot in filteredHoneypots" 
                  :key="honeypot.id" 
                  class="honeypot-row"
                  :class="'status-' + honeypot.status">
                <td>
                  <input 
                    type="checkbox" 
                    :value="honeypot.id"
                    v-model="selectedHoneypots">
                </td>
                <td class="name-cell">
                  <div class="honeypot-name">
                    <div class="type-icon">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path :d="getTypeIcon(honeypot.type)"></path>
                      </svg>
                    </div>
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
                  <div class="status-cell">
                    <span class="status-indicator" :class="getStatusClass(honeypot.status)">
                      <span class="status-dot"></span>
                      {{ getStatusText(honeypot.status) }}
                    </span>
                  </div>
                </td>
                <td>
                  <code class="ip-address">{{ honeypot.ip }}</code>
                </td>
                <td>
                  <code class="port-number">{{ honeypot.port }}</code>
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
                    <button 
                      class="action-btn toggle" 
                      @click="toggleHoneypot(honeypot)"
                      :title="honeypot.status === 'active' ? 'Désactiver' : 'Activer'">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                        <circle cx="12" cy="16" r="1"></circle>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                      </svg>
                    </button>

                    <button 
                      class="action-btn integration" 
                      @click="openIntegrationModal(honeypot)"
                      title="Configurer les intégrations">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                        <polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline>
                        <polyline points="7.5 19.79 7.5 14.6 3 12"></polyline>
                        <polyline points="21 12 16.5 14.6 16.5 19.79"></polyline>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal Création Honeypot -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeModals">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h3>Créer un Nouveau Honeypot</h3>
          <button class="modal-close" @click="closeModals">×</button>
        </div>
        <div class="modal-content">
          <div class="form-group">
            <label>Nom du honeypot</label>
            <input type="text" v-model="honeypotForm.name" placeholder="Ex: SSH-Prod-01">
          </div>
          <div class="form-group">
            <label>Type</label>
            <select v-model="honeypotForm.type">
              <option value="SSH">SSH</option>
              <option value="HTTP">HTTP</option>
              <option value="FTP">FTP</option>
              <option value="SMTP">SMTP</option>
              <option value="Telnet">Telnet</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Adresse IP</label>
              <input type="text" v-model="honeypotForm.ip" placeholder="192.168.1.100">
            </div>
            <div class="form-group">
              <label>Port</label>
              <input type="number" v-model="honeypotForm.port">
            </div>
          </div>
          <div class="form-group">
            <label>Groupe</label>
            <select v-model="honeypotForm.group">
              <option v-for="group in groups" :key="group.id" :value="group.name">
                {{ group.name }}
              </option>
            </select>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModals">Annuler</button>
          <button class="btn btn-primary" @click="createHoneypot">Créer</button>
        </div>
      </div>
    </div>

    <!-- Modal Création Groupe -->
    <div v-if="showGroupModal" class="modal-overlay" @click="closeModals">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h3>Créer un Nouveau Groupe</h3>
          <button class="modal-close" @click="closeModals">×</button>
        </div>
        <div class="modal-content">
          <div class="form-group">
            <label>Nom du groupe</label>
            <input type="text" v-model="groupForm.name" placeholder="Ex: Production">
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="groupForm.description" placeholder="Description du groupe"></textarea>
          </div>
          <div class="form-group">
            <label>Couleur</label>
            <input type="color" v-model="groupForm.color">
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModals">Annuler</button>
          <button class="btn btn-primary" @click="createGroup">Créer</button>
        </div>
      </div>
    </div>

    <!-- Modal Intégrations -->
    <div v-if="showIntegrationModal" class="modal-overlay" @click="closeModals">
      <div class="modal-container large" @click.stop>
        <div class="modal-header">
          <h3>Configurer les Intégrations - {{ currentHoneypot?.name }}</h3>
          <button class="modal-close" @click="closeModals">×</button>
        </div>
        <div class="modal-content">
          <div class="integration-section">
            <div class="integration-header">
              <div class="integration-icon elk">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"></path>
                  <path d="M13 13l6 6"></path>
                </svg>
              </div>
              <div class="integration-info">
                <h4>Elastic Stack (ELK)</h4>
                <p>Redirection des logs vers Elasticsearch</p>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="integrationForm.elk_enabled">
                <span class="slider"></span>
              </label>
            </div>
            <div v-if="integrationForm.elk_enabled" class="integration-config">
              <div class="form-group">
                <label>URL Elasticsearch</label>
                <input type="url" v-model="integrationForm.elk_url" placeholder="https://elastic.company.com:9200">
              </div>
            </div>
          </div>

          <div class="integration-section">
            <div class="integration-header">
              <div class="integration-icon opencti">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                </svg>
              </div>
              <div class="integration-info">
                <h4>OpenCTI</h4>
                <p>Enrichissement avec la Threat Intelligence</p>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="integrationForm.opencti_enabled">
                <span class="slider"></span>
              </label>
            </div>
            <div v-if="integrationForm.opencti_enabled" class="integration-config">
              <div class="form-group">
                <label>URL OpenCTI</label>
                <input type="url" v-model="integrationForm.opencti_url" placeholder="https://opencti.company.com">
              </div>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModals">Annuler</button>
          <button class="btn btn-primary" @click="saveIntegrations">Enregistrer</button>
        </div>
      </div>
    </div>

    <!-- Modal Confirmation Suppression -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="closeModals">
      <div class="modal-container danger" @click.stop>
        <div class="modal-header">
          <h3>Confirmer la Suppression</h3>
          <button class="modal-close" @click="closeModals">×</button>
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
.honeypot-management-page {
  padding: 24px 32px;
  background: var(--container-background);
  min-height: 100vh;
}

/* Réutilisation du CSS global d'alerts.vue */
.page-header {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--container-border-color);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 32px;
  font-weight: 700;
  color: var(--white);
  margin: 0;
}

.page-title svg {
  color: var(--accent-color);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(30, 84, 229, 0.15);
  border: 1px solid rgba(30, 84, 229, 0.3);
  border-radius: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-active {
  background-color: #00e676;
  box-shadow: 0 0 8px rgba(0, 230, 118, 0.4);
}

.status-text {
  color: var(--white);
  font-weight: 500;
  font-size: 14px;
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 16px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
}

.stat-card.active::before {
  background: linear-gradient(90deg, #00e676, #64ffda);
}

.stat-card.total::before {
  background: linear-gradient(90deg, #1e54e5, #3f7cff);
}

.stat-card.groups::before {
  background: linear-gradient(90deg, #ffb74d, #ffd54f);
}

.stat-card.alerts::before {
  background: linear-gradient(90deg, #ff3a5e, #ff6b8a);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
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

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 36px;
  font-weight: 800;
  color: var(--white);
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 16px;
  color: var(--text-color-muted);
  font-weight: 500;
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
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-color-muted);
  font-weight: 600;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 16px 24px;
  text-align: left;
  border-bottom: 1px solid var(--container-border-color);
}

.honeypot-row {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.2s ease;
}

.honeypot-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.honeypot-row.status-active {
  border-left: 4px solid #00e676;
}

.honeypot-row.status-inactive {
  border-left: 4px solid #666;
}

.honeypot-row.status-error {
  border-left: 4px solid #ff3a5e;
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

.type-icon {
  width: 32px;
  height: 32px;
  background: rgba(30, 84, 229, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-color);
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

.type-ssh {
  background: rgba(255, 58, 94, 0.2);
  color: #ff3a5e;
}

.type-http {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
}

.type-ftp {
  background: rgba(255, 183, 77, 0.2);
  color: #ffb74d;
}

.type-smtp {
  background: rgba(41, 182, 246, 0.2);
  color: #29b6f6;
}

.type-telnet {
  background: rgba(156, 39, 176, 0.2);
  color: #9c27b0;
}

.status-cell .status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-indicator.status-active {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
  border: 1px solid rgba(0, 230, 118, 0.3);
}

.status-indicator.status-inactive {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-color-muted);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.status-indicator.status-error {
  background: rgba(255, 58, 94, 0.2);
  color: #ff3a5e;
  border: 1px solid rgba(255, 58, 94, 0.3);
}

.status-indicator .status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-active .status-dot {
  background: #00e676;
}

.status-inactive .status-dot {
  background: #666;
}

.status-error .status-dot {
  background: #ff3a5e;
}

.ip-address {
  background: rgba(30, 84, 229, 0.15);
  color: #1e54e5;
  padding: 6px 10px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-weight: 600;
  font-size: 13px;
}

.port-number {
  background: rgba(255, 183, 77, 0.15);
  color: #ffb74d;
  padding: 6px 10px;
  border-radius: 6px;
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
  font-weight: 700;
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

.action-btn.integration {
  background: rgba(30, 84, 229, 0.2);
  color: #1e54e5;
}

.action-btn.integration:hover {
  background: rgba(30, 84, 229, 0.3);
}

/* Modales */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 16px;
  width: 500px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-container.large {
  width: 700px;
}

.modal-container.danger {
  border-color: rgba(255, 58, 94, 0.3);
}

.modal-header {
  padding: 24px 32px;
  border-bottom: 1px solid var(--container-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--white);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-color-muted);
  font-size: 24px;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--white);
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

/* Formulaires */
.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 120px;
  gap: 16px;
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
  width: 100%;
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

.warning-text {
  color: #ff3a5e;
  font-weight: 600;
}

/* Intégrations */
.integration-section {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.integration-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.integration-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.integration-icon.elk {
  background: rgba(255, 183, 77, 0.2);
  color: #ffb74d;
}

.integration-icon.opencti {
  background: rgba(30, 84, 229, 0.2);
  color: #1e54e5;
}

.integration-info {
  flex: 1;
}

.integration-info h4 {
  font-size: 16px;
  font-weight: 700;
  color: var(--white);
  margin: 0 0 4px 0;
}

.integration-info p {
  font-size: 14px;
  color: var(--text-color-muted);
  margin: 0;
}

.integration-config {
  padding-left: 56px;
}

/* Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 34px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #333;
  transition: .4s;
  border-radius: 34px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--accent-color);
}

input:checked + .slider:before {
  transform: translateX(26px);
}

/* Responsive */
@media (max-width: 768px) {
  .honeypot-management-page {
    padding: 16px;
  }

  .controls-section {
    flex-direction: column;
    align-items: stretch;
  }

  .controls-left,
  .controls-right {
    flex-wrap: wrap;
  }

  .search-input {
    width: 100%;
  }

  .modal-container {
    width: 95vw;
    margin: 16px;
  }
}
</style>
