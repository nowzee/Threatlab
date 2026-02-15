<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface Service {
  id: number
  name: string
  port: number
  protocol: string
  status: 'active' | 'inactive'
  connections: number
  attacks: number
}

interface Attack {
  id: number
  timestamp: string
  source_ip: string
  country: string
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  blocked: boolean
}

interface Integration {
  id: string
  name: string
  type: 'discord' | 'elk' | 'opencti' | 'slack' | 'webhook'
  enabled: boolean
  config: any
}

interface HoneypotDetail {
  id: number
  name: string
  type: string
  status: 'active' | 'inactive' | 'error'
  ip: string
  location: {
    country: string
    city: string
    coordinates: { lat: number; lng: number }
  }
  group: string
  created_at: string
  last_activity: string
  uptime: number
  services: Service[]
  stats: {
    total_attacks: number
    blocked_attacks: number
    unique_ips: number
    total_connections: number
    attacks_today: number
    attacks_week: number
    attacks_month: number
  }
  top_countries: Array<{ country: string; count: number; percentage: number }>
  recent_attacks: Attack[]
  integrations: Integration[]
}

export default defineComponent({
  name: "HoneypotDetailView",
  setup() {
    const route = useRoute()
    const router = useRouter()
    const honeypotId = parseInt(route.params.id as string)

    const honeypot = ref<HoneypotDetail | null>(null)
    const activeTab = ref<'overview' | 'services' | 'attacks' | 'integrations'>('overview')
    const showAddServiceModal = ref(false)
    const showAddIntegrationModal = ref(false)
    const loading = ref(true)

    // Simulated data
    const loadHoneypotData = async () => {
      loading.value = true
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800))

      honeypot.value = {
        id: honeypotId,
        name: `Honeypot-${honeypotId}`,
        type: 'SSH',
        status: 'active',
        ip: '192.168.1.100',
        location: {
          country: 'France',
          city: 'Paris',
          coordinates: { lat: 48.8566, lng: 2.3522 }
        },
        group: 'Production',
        created_at: '2024-01-15T10:30:00Z',
        last_activity: '2024-03-20T15:45:00Z',
        uptime: 99.8,
        services: [
          { id: 1, name: 'SSH', port: 22, protocol: 'TCP', status: 'active', connections: 1523, attacks: 342 },
          { id: 2, name: 'FTP', port: 21, protocol: 'TCP', status: 'active', connections: 892, attacks: 156 },
          { id: 3, name: 'HTTP', port: 80, protocol: 'TCP', status: 'active', connections: 2341, attacks: 523 },
          { id: 4, name: 'Telnet', port: 23, protocol: 'TCP', status: 'inactive', connections: 0, attacks: 0 }
        ],
        stats: {
          total_attacks: 1021,
          blocked_attacks: 987,
          unique_ips: 234,
          total_connections: 4756,
          attacks_today: 45,
          attacks_week: 312,
          attacks_month: 1021
        },
        top_countries: [
          { country: 'China', count: 342, percentage: 33.5 },
          { country: 'Russia', count: 256, percentage: 25.1 },
          { country: 'USA', count: 189, percentage: 18.5 },
          { country: 'India', count: 123, percentage: 12.0 },
          { country: 'Brazil', count: 111, percentage: 10.9 }
        ],
        recent_attacks: [
          { id: 1, timestamp: '2024-03-20T15:45:23Z', source_ip: '45.142.120.10', country: 'CN', type: 'Brute Force', severity: 'high', blocked: true },
          { id: 2, timestamp: '2024-03-20T15:42:15Z', source_ip: '185.220.101.45', country: 'RU', type: 'Port Scan', severity: 'medium', blocked: true },
          { id: 3, timestamp: '2024-03-20T15:38:50Z', source_ip: '103.85.24.157', country: 'IN', type: 'SSH Login Attempt', severity: 'high', blocked: true },
          { id: 4, timestamp: '2024-03-20T15:35:12Z', source_ip: '159.65.142.33', country: 'US', type: 'SQL Injection', severity: 'critical', blocked: true },
          { id: 5, timestamp: '2024-03-20T15:30:45Z', source_ip: '177.54.144.66', country: 'BR', type: 'Directory Traversal', severity: 'medium', blocked: true }
        ],
        integrations: [
          { id: '1', name: 'Discord Security Channel', type: 'discord', enabled: true, config: { webhook_url: 'https://discord.com/api/webhooks/...' } },
          { id: '2', name: 'ELK Stack', type: 'elk', enabled: true, config: { url: 'https://elastic.company.com:9200' } },
          { id: '3', name: 'OpenCTI Threat Intel', type: 'opencti', enabled: false, config: { url: '' } }
        ]
      }

      loading.value = false
    }

    const newService = ref({
      name: '',
      port: 0,
      protocol: 'TCP'
    })

    const newIntegration = ref({
      type: 'discord',
      name: '',
      config: {}
    })

    const getStatusClass = (status: string) => {
      switch (status) {
        case 'active': return 'status-active'
        case 'inactive': return 'status-inactive'
        case 'error': return 'status-error'
        default: return 'status-inactive'
      }
    }

    const getSeverityClass = (severity: string) => {
      switch (severity) {
        case 'critical': return 'severity-critical'
        case 'high': return 'severity-high'
        case 'medium': return 'severity-medium'
        case 'low': return 'severity-low'
        default: return 'severity-low'
      }
    }

    const formatDate = (dateString: string) => {
      const date = new Date(dateString)
      return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const formatUptime = (uptime: number) => {
      return `${uptime.toFixed(2)}%`
    }

    const addService = () => {
      if (honeypot.value && newService.value.name && newService.value.port > 0) {
        honeypot.value.services.push({
          id: honeypot.value.services.length + 1,
          name: newService.value.name,
          port: newService.value.port,
          protocol: newService.value.protocol,
          status: 'active',
          connections: 0,
          attacks: 0
        })
        showAddServiceModal.value = false
        newService.value = { name: '', port: 0, protocol: 'TCP' }
      }
    }

    const toggleService = (service: Service) => {
      service.status = service.status === 'active' ? 'inactive' : 'active'
    }

    const removeService = (serviceId: number) => {
      if (honeypot.value) {
        honeypot.value.services = honeypot.value.services.filter(s => s.id !== serviceId)
      }
    }

    const addIntegration = () => {
      if (honeypot.value && newIntegration.value.name) {
        honeypot.value.integrations.push({
          id: String(honeypot.value.integrations.length + 1),
          name: newIntegration.value.name,
          type: newIntegration.value.type as any,
          enabled: true,
          config: newIntegration.value.config
        })
        showAddIntegrationModal.value = false
        newIntegration.value = { type: 'discord', name: '', config: {} }
      }
    }

    const toggleIntegration = (integration: Integration) => {
      integration.enabled = !integration.enabled
    }

    const removeIntegration = (integrationId: string) => {
      if (honeypot.value) {
        honeypot.value.integrations = honeypot.value.integrations.filter(i => i.id !== integrationId)
      }
    }

    const goBack = () => {
      router.push('/dashboard/honeypot-management')
    }

    onMounted(() => {
      loadHoneypotData()
    })

    return {
      honeypot,
      activeTab,
      loading,
      showAddServiceModal,
      showAddIntegrationModal,
      newService,
      newIntegration,
      getStatusClass,
      getSeverityClass,
      formatDate,
      formatUptime,
      addService,
      toggleService,
      removeService,
      addIntegration,
      toggleIntegration,
      removeIntegration,
      goBack
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Chargement des données du honeypot...</p>
    </div>

    <!-- Content -->
    <div v-else-if="honeypot">
      <!-- Header -->
      <div class="detail-header">
        <button class="btn btn-secondary btn-back" @click="goBack">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          Retour
        </button>
        <div class="header-info">
          <h1 class="page-title">{{ honeypot.name }}</h1>
          <span class="status-badge" :class="getStatusClass(honeypot.status)">
            <span class="status-dot"></span>
            {{ honeypot.status === 'active' ? 'Actif' : 'Inactif' }}
          </span>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="stats-grid">
        <div class="card stat-card">
          <div class="stat-icon attacks">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ honeypot.stats.total_attacks }}</div>
            <div class="stat-label">Attaques Totales</div>
          </div>
        </div>

        <div class="card stat-card">
          <div class="stat-icon blocked">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ honeypot.stats.blocked_attacks }}</div>
            <div class="stat-label">Attaques Bloquées</div>
          </div>
        </div>

        <div class="card stat-card">
          <div class="stat-icon ips">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ honeypot.stats.unique_ips }}</div>
            <div class="stat-label">IPs Uniques</div>
          </div>
        </div>

        <div class="card stat-card">
          <div class="stat-icon uptime">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatUptime(honeypot.uptime) }}</div>
            <div class="stat-label">Disponibilité</div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs-container">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'overview' }"
          @click="activeTab = 'overview'">
          Vue d'ensemble
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'services' }"
          @click="activeTab = 'services'">
          Services ({{ honeypot.services.length }})
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'attacks' }"
          @click="activeTab = 'attacks'">
          Attaques Récentes
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'integrations' }"
          @click="activeTab = 'integrations'">
          Intégrations ({{ honeypot.integrations.length }})
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'" class="tab-pane">
          <div class="overview-grid">
            <!-- Info Card -->
            <div class="card info-card">
              <div class="card-header">
                <h3 class="card-title">Informations Générales</h3>
              </div>
              <div class="card-body">
                <div class="info-row">
                  <span class="info-label">Adresse IP</span>
                  <code class="info-value">{{ honeypot.ip }}</code>
                </div>
                <div class="info-row">
                  <span class="info-label">Type</span>
                  <span class="info-value">{{ honeypot.type }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">Groupe</span>
                  <span class="info-value">{{ honeypot.group }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">Localisation</span>
                  <span class="info-value">{{ honeypot.location.city }}, {{ honeypot.location.country }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">Créé le</span>
                  <span class="info-value">{{ formatDate(honeypot.created_at) }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">Dernière activité</span>
                  <span class="info-value">{{ formatDate(honeypot.last_activity) }}</span>
                </div>
              </div>
            </div>

            <!-- Attack Trends -->
            <div class="card trends-card">
              <div class="card-header">
                <h3 class="card-title">Tendances des Attaques</h3>
              </div>
              <div class="card-body">
                <div class="trend-item">
                  <div class="trend-label">Aujourd'hui</div>
                  <div class="trend-value">{{ honeypot.stats.attacks_today }}</div>
                  <div class="trend-bar">
                    <div class="trend-progress" :style="{ width: (honeypot.stats.attacks_today / honeypot.stats.attacks_week * 100) + '%' }"></div>
                  </div>
                </div>
                <div class="trend-item">
                  <div class="trend-label">Cette Semaine</div>
                  <div class="trend-value">{{ honeypot.stats.attacks_week }}</div>
                  <div class="trend-bar">
                    <div class="trend-progress" :style="{ width: (honeypot.stats.attacks_week / honeypot.stats.attacks_month * 100) + '%' }"></div>
                  </div>
                </div>
                <div class="trend-item">
                  <div class="trend-label">Ce Mois</div>
                  <div class="trend-value">{{ honeypot.stats.attacks_month }}</div>
                  <div class="trend-bar">
                    <div class="trend-progress" style="width: 100%"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Top Countries -->
            <div class="card countries-card">
              <div class="card-header">
                <h3 class="card-title">Top Pays Sources</h3>
              </div>
              <div class="card-body">
                <div v-for="country in honeypot.top_countries" :key="country.country" class="country-item">
                  <div class="country-info">
                    <span class="country-name">{{ country.country }}</span>
                    <span class="country-count">{{ country.count }} attaques</span>
                  </div>
                  <div class="country-bar">
                    <div class="country-progress" :style="{ width: country.percentage + '%' }"></div>
                  </div>
                  <span class="country-percentage">{{ country.percentage.toFixed(1) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Services Tab -->
        <div v-if="activeTab === 'services'" class="tab-pane">
          <div class="services-header">
            <h2>Services Configurés</h2>
            <button class="btn btn-primary" @click="showAddServiceModal = true">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              Ajouter un Service
            </button>
          </div>

          <div class="services-grid">
            <div v-for="service in honeypot.services" :key="service.id" class="card service-card">
              <div class="service-header">
                <div class="service-info">
                  <h3 class="service-name">{{ service.name }}</h3>
                  <span class="service-port">Port {{ service.port }}/{{ service.protocol }}</span>
                </div>
                <span class="status-badge" :class="getStatusClass(service.status)">
                  <span class="status-dot"></span>
                  {{ service.status === 'active' ? 'Actif' : 'Inactif' }}
                </span>
              </div>
              <div class="service-stats">
                <div class="service-stat">
                  <div class="service-stat-value">{{ service.connections }}</div>
                  <div class="service-stat-label">Connexions</div>
                </div>
                <div class="service-stat">
                  <div class="service-stat-value">{{ service.attacks }}</div>
                  <div class="service-stat-label">Attaques</div>
                </div>
              </div>
              <div class="service-actions">
                <button class="btn btn-sm btn-secondary" @click="toggleService(service)">
                  {{ service.status === 'active' ? 'Désactiver' : 'Activer' }}
                </button>
                <button class="btn btn-sm btn-danger" @click="removeService(service.id)">
                  Supprimer
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Attacks Tab -->
        <div v-if="activeTab === 'attacks'" class="tab-pane">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Attaques Récentes</h3>
            </div>
            <div class="attacks-table-container">
              <table class="attacks-table">
                <thead>
                  <tr>
                    <th>Date/Heure</th>
                    <th>IP Source</th>
                    <th>Pays</th>
                    <th>Type d'Attaque</th>
                    <th>Sévérité</th>
                    <th>Statut</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="attack in honeypot.recent_attacks" :key="attack.id">
                    <td>{{ formatDate(attack.timestamp) }}</td>
                    <td><code>{{ attack.source_ip }}</code></td>
                    <td>
                      <span class="country-code">{{ attack.country }}</span>
                    </td>
                    <td>{{ attack.type }}</td>
                    <td>
                      <span class="severity-badge" :class="getSeverityClass(attack.severity)">
                        {{ attack.severity }}
                      </span>
                    </td>
                    <td>
                      <span v-if="attack.blocked" class="badge badge-success">Bloquée</span>
                      <span v-else class="badge badge-danger">Non Bloquée</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Integrations Tab -->
        <div v-if="activeTab === 'integrations'" class="tab-pane">
          <div class="integrations-header">
            <h2>Intégrations Configurées</h2>
            <button class="btn btn-primary" @click="showAddIntegrationModal = true">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              Ajouter une Intégration
            </button>
          </div>

          <div class="integrations-grid">
            <div v-for="integration in honeypot.integrations" :key="integration.id" class="card integration-card">
              <div class="integration-header">
                <div class="integration-icon" :class="'icon-' + integration.type">
                  <svg v-if="integration.type === 'discord'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.865-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z"/>
                  </svg>
                  <svg v-else-if="integration.type === 'elk'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"></path>
                  </svg>
                  <svg v-else-if="integration.type === 'opencti'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                  </svg>
                </div>
                <div class="integration-info">
                  <h3 class="integration-name">{{ integration.name }}</h3>
                  <span class="integration-type">{{ integration.type.toUpperCase() }}</span>
                </div>
                <label class="switch">
                  <input type="checkbox" :checked="integration.enabled" @change="toggleIntegration(integration)">
                  <span class="slider"></span>
                </label>
              </div>
              <div class="integration-actions">
                <button class="btn btn-sm btn-secondary">Configurer</button>
                <button class="btn btn-sm btn-danger" @click="removeIntegration(integration.id)">Supprimer</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Service Modal -->
    <div v-if="showAddServiceModal" class="modal-overlay" @click="showAddServiceModal = false">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h3>Ajouter un Service</h3>
          <button class="modal-close-btn" @click="showAddServiceModal = false">×</button>
        </div>
        <div class="modal-content">
          <div class="form-group">
            <label>Nom du Service</label>
            <input type="text" v-model="newService.name" placeholder="Ex: SMTP" class="form-control">
          </div>
          <div class="form-group">
            <label>Port</label>
            <input type="number" v-model="newService.port" placeholder="Ex: 25" class="form-control">
          </div>
          <div class="form-group">
            <label>Protocole</label>
            <select v-model="newService.protocol" class="form-control">
              <option value="TCP">TCP</option>
              <option value="UDP">UDP</option>
            </select>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showAddServiceModal = false">Annuler</button>
          <button class="btn btn-primary" @click="addService">Ajouter</button>
        </div>
      </div>
    </div>

    <!-- Add Integration Modal -->
    <div v-if="showAddIntegrationModal" class="modal-overlay" @click="showAddIntegrationModal = false">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h3>Ajouter une Intégration</h3>
          <button class="modal-close-btn" @click="showAddIntegrationModal = false">×</button>
        </div>
        <div class="modal-content">
          <div class="form-group">
            <label>Type d'Intégration</label>
            <select v-model="newIntegration.type" class="form-control">
              <option value="discord">Discord</option>
              <option value="elk">ELK Stack</option>
              <option value="opencti">OpenCTI</option>
              <option value="slack">Slack</option>
              <option value="webhook">Webhook Personnalisé</option>
            </select>
          </div>
          <div class="form-group">
            <label>Nom</label>
            <input type="text" v-model="newIntegration.name" placeholder="Ex: Canal de Sécurité Discord" class="form-control">
          </div>
          <div class="form-group">
            <label>URL de Configuration</label>
            <input type="url" placeholder="https://..." class="form-control">
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showAddIntegrationModal = false">Annuler</button>
          <button class="btn btn-primary" @click="addIntegration">Ajouter</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Loading */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid var(--container-border-color);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Header */
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.btn-back {
  flex-shrink: 0;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.status-badge.status-active {
  background: rgba(0, 230, 118, 0.15);
  color: var(--success-color);
}

.status-badge.status-inactive {
  background: rgba(158, 158, 158, 0.15);
  color: var(--text-color-muted);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.attacks {
  background: rgba(255, 58, 94, 0.2);
  color: #ff3a5e;
}

.stat-icon.blocked {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
}

.stat-icon.ips {
  background: rgba(30, 84, 229, 0.2);
  color: #1e54e5;
}

.stat-icon.uptime {
  background: rgba(255, 183, 77, 0.2);
  color: #ffb74d;
}

/* Tabs */
.tabs-container {
  display: flex;
  gap: 8px;
  border-bottom: 2px solid var(--container-border-color);
  margin-bottom: 24px;
}

.tab-btn {
  padding: 12px 24px;
  background: transparent;
  border: none;
  color: var(--text-color-muted);
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: var(--white);
}

.tab-btn.active {
  color: var(--accent-color);
  border-bottom-color: var(--accent-color);
}

/* Overview Grid */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--container-border-color);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-weight: 500;
  color: var(--text-color-muted);
}

.info-value {
  color: var(--white);
  font-weight: 600;
}

/* Trends */
.trend-item {
  margin-bottom: 20px;
}

.trend-item:last-child {
  margin-bottom: 0;
}

.trend-label {
  font-size: 14px;
  color: var(--text-color-muted);
  margin-bottom: 8px;
}

.trend-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--white);
  margin-bottom: 8px;
}

.trend-bar {
  height: 8px;
  background: var(--container-background-lighter);
  border-radius: 4px;
  overflow: hidden;
}

.trend-progress {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-color), #00e676);
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* Countries */
.country-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.country-item:last-child {
  margin-bottom: 0;
}

.country-info {
  display: flex;
  flex-direction: column;
  min-width: 120px;
}

.country-name {
  font-weight: 600;
  color: var(--white);
  font-size: 14px;
}

.country-count {
  font-size: 12px;
  color: var(--text-color-muted);
}

.country-bar {
  flex: 1;
  height: 8px;
  background: var(--container-background-lighter);
  border-radius: 4px;
  overflow: hidden;
}

.country-progress {
  height: 100%;
  background: var(--accent-color);
  border-radius: 4px;
}

.country-percentage {
  font-size: 14px;
  font-weight: 600;
  color: var(--white);
  min-width: 50px;
  text-align: right;
}

/* Services */
.services-header,
.integrations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.services-grid,
.integrations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.service-card,
.integration-card {
  padding: 24px;
}

.service-header,
.integration-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.service-name,
.integration-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--white);
  margin: 0 0 4px 0;
}

.service-port,
.integration-type {
  font-size: 13px;
  color: var(--text-color-muted);
}

.service-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--container-background);
  border-radius: 8px;
}

.service-stat {
  text-align: center;
}

.service-stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--white);
}

.service-stat-label {
  font-size: 12px;
  color: var(--text-color-muted);
}

.service-actions,
.integration-actions {
  display: flex;
  gap: 8px;
}

/* Integration Icon */
.integration-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.integration-icon.icon-discord {
  background: rgba(88, 101, 242, 0.2);
  color: #5865f2;
}

.integration-icon.icon-elk {
  background: rgba(255, 183, 77, 0.2);
  color: #ffb74d;
}

.integration-icon.icon-opencti {
  background: rgba(30, 84, 229, 0.2);
  color: #1e54e5;
}

.integration-icon.icon-slack {
  background: rgba(74, 21, 75, 0.2);
  color: #e01e5a;
}

.integration-icon.icon-webhook {
  background: rgba(158, 158, 158, 0.2);
  color: var(--text-color-muted);
}

/* Attacks Table */
.attacks-table-container {
  overflow-x: auto;
}

.attacks-table {
  width: 100%;
  border-collapse: collapse;
}

.attacks-table th {
  background: var(--table-header-bg);
  padding: 16px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  color: var(--text-color-muted);
  border-bottom: 1px solid var(--container-border-color);
}

.attacks-table td {
  padding: 16px;
  border-bottom: 1px solid var(--container-border-color);
  font-size: 14px;
  color: var(--white);
}

.attacks-table tr:hover {
  background: var(--table-row-hover);
}

.severity-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.severity-critical {
  background: rgba(211, 47, 47, 0.2);
  color: #d32f2f;
}

.severity-high {
  background: rgba(255, 58, 94, 0.2);
  color: #ff3a5e;
}

.severity-medium {
  background: rgba(255, 183, 77, 0.2);
  color: #ffb74d;
}

.severity-low {
  background: rgba(66, 165, 245, 0.2);
  color: #42a5f5;
}

.country-code {
  display: inline-block;
  padding: 4px 8px;
  background: var(--container-background);
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
}

/* Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 28px;
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
  border-radius: 28px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
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
  transform: translateX(22px);
}
</style>
