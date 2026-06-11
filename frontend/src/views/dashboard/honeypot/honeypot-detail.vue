<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface Attack {
  id: number
  timestamp: string
  source_ip: string
  country: string
  type: string
  service_type: string
  source_port: number
  target_port: number
  username: string
  password: string
}

interface HoneypotDetail {
  id: number
  name: string
  type: string
  status: string
  ip: string
  country: string
  banner: string
  alert_generated: number
  created_at: string
  updated_at: string
  stats: {
    total_attacks: number
    unique_ips: number
    attacks_today: number
    attacks_week: number
    attacks_month: number
  }
  top_countries: Array<{ country: string; count: number; percentage: number }>
  recent_attacks: Attack[]
}

export default defineComponent({
  name: "HoneypotDetailView",
  setup() {
    const route = useRoute()
    const router = useRouter()
    const agentId = route.params.id as string

    const honeypot = ref<HoneypotDetail | null>(null)
    const activeTab = ref<'overview' | 'attacks'>('overview')
    const loading = ref(true)
    const error = ref<string | null>(null)

    const loadHoneypotData = async () => {
      loading.value = true
      error.value = null

      try {
        const response = await fetch(`/api/agent/about/${agentId}`, {
          credentials: 'include'
        })

        const data = await response.json()

        if (response.ok && data.success) {
          honeypot.value = data.agent
        } else {
          error.value = data.error || 'Impossible de charger les données'
        }
      } catch (e) {
        console.error('Error loading honeypot data:', e)
        error.value = 'Erreur de connexion au serveur'
      } finally {
        loading.value = false
      }
    }

    const getStatusClass = (status: string) => {
      switch (status) {
        case 'active': return 'status-active'
        case 'inactive': return 'status-inactive'
        case 'error': return 'status-error'
        default: return 'status-inactive'
      }
    }

    const formatDate = (dateString: string) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
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
      error,
      getStatusClass,
      formatDate,
      goBack,
      loadHoneypotData
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Chargement des donnees du honeypot...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
      </div>
      <h2>Erreur</h2>
      <p>{{ error }}</p>
      <div class="error-actions">
        <button class="btn btn-primary" @click="loadHoneypotData">Reessayer</button>
        <button class="btn btn-secondary" @click="goBack">Retour</button>
      </div>
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
          <span class="type-badge">{{ honeypot.type.toUpperCase() }}</span>
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
          <div class="stat-icon today">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ honeypot.stats.attacks_today }}</div>
            <div class="stat-label">Aujourd'hui</div>
          </div>
        </div>

        <div class="card stat-card">
          <div class="stat-icon alerts">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ honeypot.alert_generated }}</div>
            <div class="stat-label">Alertes</div>
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
          :class="{ active: activeTab === 'attacks' }"
          @click="activeTab = 'attacks'">
          Attaques Recentes ({{ honeypot.recent_attacks.length }})
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
                <h3 class="card-title">Informations Generales</h3>
              </div>
              <div class="card-body">
                <div class="info-row">
                  <span class="info-label">Adresse IP</span>
                  <code class="info-value">{{ honeypot.ip }}</code>
                </div>
                <div class="info-row">
                  <span class="info-label">Type</span>
                  <span class="info-value">{{ honeypot.type.toUpperCase() }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">Pays</span>
                  <span class="info-value">{{ honeypot.country || 'Non defini' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">Banniere</span>
                  <code class="info-value banner-value">{{ honeypot.banner || 'N/A' }}</code>
                </div>
                <div class="info-row">
                  <span class="info-label">Cree le</span>
                  <span class="info-value">{{ formatDate(honeypot.created_at) }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">Derniere activite</span>
                  <span class="info-value">{{ formatDate(honeypot.updated_at) }}</span>
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
                    <div class="trend-progress" :style="{ width: (honeypot.stats.attacks_week > 0 ? honeypot.stats.attacks_today / honeypot.stats.attacks_week * 100 : 0) + '%' }"></div>
                  </div>
                </div>
                <div class="trend-item">
                  <div class="trend-label">Cette Semaine</div>
                  <div class="trend-value">{{ honeypot.stats.attacks_week }}</div>
                  <div class="trend-bar">
                    <div class="trend-progress" :style="{ width: (honeypot.stats.attacks_month > 0 ? honeypot.stats.attacks_week / honeypot.stats.attacks_month * 100 : 0) + '%' }"></div>
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
                <div v-if="honeypot.top_countries.length === 0" class="empty-state">
                  Aucune donnee de pays disponible
                </div>
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

        <!-- Attacks Tab -->
        <div v-if="activeTab === 'attacks'" class="tab-pane">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Attaques Recentes</h3>
            </div>
            <div v-if="honeypot.recent_attacks.length === 0" class="empty-state" style="padding: 40px;">
              Aucune attaque enregistree pour cet agent
            </div>
            <div v-else class="attacks-table-container">
              <table class="attacks-table">
                <thead>
                  <tr>
                    <th>Date/Heure</th>
                    <th>IP Source</th>
                    <th>Pays</th>
                    <th>Type</th>
                    <th>Service</th>
                    <th>Identifiants</th>
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
                      <span class="service-badge">{{ attack.service_type }}</span>
                    </td>
                    <td>
                      <span v-if="attack.username || attack.password" class="credential-info">
                        <code>{{ attack.username || '?' }}:{{ attack.password || '?' }}</code>
                      </span>
                      <span v-else class="text-muted">-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
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

/* Error */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
  text-align: center;
}

.error-icon {
  color: #ff3a5e;
}

.error-container h2 {
  margin: 0;
  color: var(--white);
}

.error-container p {
  color: var(--text-color-muted);
}

.error-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
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

.type-badge {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  background: rgba(30, 84, 229, 0.2);
  color: #42a5f5;
  letter-spacing: 0.5px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
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

.stat-icon.ips {
  background: rgba(30, 84, 229, 0.2);
  color: #1e54e5;
}

.stat-icon.today {
  background: rgba(255, 183, 77, 0.2);
  color: #ffb74d;
}

.stat-icon.alerts {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
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

.banner-value {
  font-size: 12px;
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.country-code {
  display: inline-block;
  padding: 4px 8px;
  background: var(--container-background);
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
}

.service-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  background: rgba(30, 84, 229, 0.2);
  color: #42a5f5;
}

.credential-info code {
  font-size: 12px;
  padding: 2px 6px;
  background: var(--container-background);
  border-radius: 4px;
}

.text-muted {
  color: var(--text-color-muted);
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 24px;
  color: var(--text-color-muted);
  font-style: italic;
}
</style>
