<script lang="ts">
import { defineComponent, ref, computed } from 'vue'

interface SearchResult {
  type: 'ip' | 'hash' | 'key'
  value: string
  confidence: 'high' | 'medium' | 'low'
  classification: string
  location: string
  country: string
  firstSeen: string
  lastSeen: string
  knownFor: string[]
  attackCount: number
  blocklists: string[]
  asn: string
  reverseDns: string
  ipRange: string
  activity: {
    last24h: string
    lastWeek: string
    lastMonth: string
    last3Months: string
  }
  targetedCountries: Array<{code: string, name: string, percentage: number}>
}

export default defineComponent({
  name: "ThreatIntelligence",
  setup() {
    const searchQuery = ref('')
    const isLoading = ref(false)
    const searchResult = ref<SearchResult | null>(null)

    const searchPlaceholder = computed(() => {
      return "Rechercher une adresse IP, hash, cve..."
    })

    const performSearch = async () => {
      if (!searchQuery.value.trim()) return

      isLoading.value = true

      try {
        // Simulation d'une recherche - ici vous pouvez appeler votre API
        await new Promise(resolve => setTimeout(resolve, 1000))

        // Données d'exemple basées sur votre format CrowdSec
        searchResult.value = {
          type: 'ip',
          value: searchQuery.value.trim(),
          confidence: 'high',
          classification: 'Malicious IP',
          location: 'Seattle, USA',
          country: 'USA',
          firstSeen: 'il y a plus de 2 ans',
          lastSeen: 'il y a 2 jours',
          knownFor: [
            'HTTP Exploit',
            'HTTP Scan', 
            'Database Bruteforce',
            'HTTP Bruteforce',
            'TCP Scan',
            'HTTP Crawl'
          ],
          attackCount: 847,
          blocklists: [
            'High Background Noise',
            'HTTP Exploit Attackers'
          ],
          asn: 'Datacamp Limited',
          reverseDns: `unn-${searchQuery.value.trim().replace(/\./g, '-')}.datapacket.com`,
          ipRange: '138.199.42.0/23',
          activity: {
            last24h: 'Très agressive',
            lastWeek: 'Très agressive', 
            lastMonth: 'Très agressive',
            last3Months: 'Très agressive'
          },
          targetedCountries: [
            {code: 'HU', name: 'Hongrie', percentage: 28},
            {code: 'DE', name: 'Allemagne', percentage: 21},
            {code: 'US', name: 'États-Unis', percentage: 14},
            {code: 'NL', name: 'Pays-Bas', percentage: 12},
            {code: 'PL', name: 'Pologne', percentage: 8},
            {code: 'AT', name: 'Autriche', percentage: 7},
            {code: 'AU', name: 'Australie', percentage: 5},
            {code: 'BR', name: 'Brésil', percentage: 3},
            {code: 'FI', name: 'Finlande', percentage: 1},
            {code: 'FR', name: 'France', percentage: 1}
          ]
        }

      } catch (error) {
        console.error('Erreur lors de la recherche:', error)
      } finally {
        isLoading.value = false
      }
    }

    const clearSearch = () => {
      searchQuery.value = ''
      searchResult.value = null
    }

    const getConfidenceColor = (confidence: string) => {
      switch (confidence) {
        case 'high': return '#dc3545'
        case 'medium': return '#fd7e14' 
        case 'low': return '#ffc107'
        default: return '#6c757d'
      }
    }

    const getActivityColor = (activity: string) => {
      switch (activity.toLowerCase()) {
        case 'très agressive': return '#dc3545'
        case 'agressive': return '#fd7e14'
        case 'modérée': return '#ffc107'
        case 'faible': return '#28a745'
        default: return '#6c757d'
      }
    }

    return {
      searchQuery,
      searchPlaceholder,
      isLoading,
      searchResult,
      performSearch,
      clearSearch,
      getConfidenceColor,
      getActivityColor
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <div class="page-header">
      <h1 class="page-title">
        Threat Intelligence
      </h1>
    </div>

    <!-- Barre de recherche principale -->
    <div class="section-card search-section">
      <div class="search-container">
        <div class="search-input-wrapper">
          <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            v-model="searchQuery"
            :placeholder="searchPlaceholder"
            class="search-input form-control"
            @keyup.enter="performSearch"
          />
          <button 
            v-if="searchQuery"
            @click="clearSearch"
            class="clear-btn"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <button 
          @click="performSearch" 
          :disabled="!searchQuery.trim() || isLoading"
          class="btn btn-primary search-btn"
        >
          <svg v-if="!isLoading" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <div v-else class="spinner-small"></div>
          <span v-if="isLoading">Recherche...</span>
          <span v-else>Analyser</span>
        </button>
      </div>
    </div>

    <!-- Résultats de recherche -->
    <div v-if="searchResult" class="results-section">
      <!-- Grille des informations -->
      <div class="grid-container">
        <!-- Informations principales -->
        <div class="section-card">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
            Informations générales
          </h3>
          <div class="info-grid">
            <div class="info-row">
              <label>Localisation:</label>
              <div class="location-info">
                <span>{{ searchResult.location }}</span>
                <span class="country-flag badge badge-primary">{{ searchResult.country }}</span>
              </div>
            </div>
            <div class="info-row">
              <label>Première détection:</label>
              <span class="info-value">{{ searchResult.firstSeen }}</span>
            </div>
            <div class="info-row">
              <label>Dernière détection:</label>
              <span class="info-value">{{ searchResult.lastSeen }}</span>
            </div>
            <div class="info-row">
              <label>Activités connues:</label>
              <div class="activity-tags">
                <span v-for="activity in searchResult.knownFor" :key="activity" class="badge badge-danger activity-tag">
                  {{ activity }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Plage d'adresses IP -->
        <div class="section-card">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="8" y1="21" x2="16" y2="21"></line>
              <line x1="12" y1="17" x2="12" y2="21"></line>
            </svg>
            Infrastructure réseau
          </h3>
          <div class="info-grid">
            <div class="info-row">
              <label>Plage IP:</label>
              <span class="info-value">{{ searchResult.ipRange }}</span>
            </div>
            <div class="info-row">
              <label>AS:</label>
              <span class="info-value">{{ searchResult.asn }}</span>
            </div>
            <div class="info-row">
              <label>DNS Inverse:</label>
              <span class="info-value code">{{ searchResult.reverseDns }}</span>
            </div>
          </div>
        </div>

        <!-- Activité temporelle -->
        <div class="section-card">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="6"></line>
            </svg>
            Activité récente
          </h3>
          <div class="activity-chart">
            <div class="activity-timeline">
              <span>Jun</span>
              <span>Jul</span>
              <span>Août</span>
              <span>Sep</span>
            </div>
            <div class="activity-progression">
              <div class="progress">
                <div class="progress-bar progress-bar-danger" style="width: 85%"></div>
              </div>
              <span class="activity-trend">Faible → Très agressive</span>
            </div>
          </div>
          <div class="activity-periods">
            <div class="activity-period">
              <label>Dernières 24h:</label>
              <span class="badge badge-danger activity-status">{{ searchResult.activity.last24h }}</span>
            </div>
            <div class="activity-period">
              <label>7 derniers jours:</label>
              <span class="badge badge-danger activity-status">{{ searchResult.activity.lastWeek }}</span>
            </div>
            <div class="activity-period">
              <label>30 derniers jours:</label>
              <span class="badge badge-danger activity-status">{{ searchResult.activity.lastMonth }}</span>
            </div>
            <div class="activity-period">
              <label>3 derniers mois:</label>
              <span class="badge badge-danger activity-status">{{ searchResult.activity.last3Months }}</span>
            </div>
          </div>
        </div>

        <!-- Listes de blocage -->
        <div class="section-card blocklists-card">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="9" y1="9" x2="15" y2="15"></line>
              <line x1="15" y1="9" x2="9" y2="15"></line>
            </svg>
            Listes de blocage
          </h3>
          <div class="blocklist-container">
            <div class="blocklist-item">
              <div class="blocklist-header">
                <div class="blocklist-info">
                  <h4>High Background Noise</h4>
                  <span class="badge badge-warning tier-badge">Platinum</span>
                </div>
                <div class="blocklist-stats">
                  <span class="stat">29.2k IPs</span>
                  <span class="stat change-negative">-28%</span>
                </div>
              </div>
              <p class="blocklist-description">
                Contient les IPs considérées comme bruit de fond internet, identifiées comme malveillantes.
              </p>
              <div class="blocklist-meta">
                <span>Mise à jour: il y a 5h</span>
              </div>
            </div>

            <div class="blocklist-item">
              <div class="blocklist-header">
                <div class="blocklist-info">
                  <h4>HTTP Exploit Attackers</h4>
                  <span class="badge badge-warning tier-badge">Platinum</span>
                </div>
                <div class="blocklist-stats">
                  <span class="stat">18.2k IPs</span>
                  <span class="stat change-negative">-1%</span>
                </div>
              </div>
              <p class="blocklist-description">
                IPs signalées pour des tentatives d'exploitation HTTP.
              </p>
              <div class="blocklist-meta">
                <span>Mise à jour: il y a 5h</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Classifications -->
        <div class="section-card">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 11H5a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h4"></path>
              <path d="M20 16V7a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v9"></path>
              <path d="M3 16h6m8 0h3"></path>
            </svg>
            Classifications
          </h3>
          <div class="classification-list">
            <div class="classification-item">
              <div class="classification-header">
                <span class="status-indicator status-danger">
                  <span class="status-dot"></span>
                  IP de Centre de Données
                </span>
              </div>
              <p>Cette adresse IP appartient à un centre de données et présente un comportement malveillant.</p>
            </div>
          </div>
        </div>

        <!-- Pays ciblés -->
        <div class="section-card countries-card">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M2 12h20"></path>
            </svg>
            Pays les plus ciblés
          </h3>
          <div class="countries-list">
            <div 
              v-for="country in searchResult.targetedCountries.slice(0, 6)" 
              :key="country.code"
              class="country-row"
            >
              <div class="country-info">
                <span class="country-flag">{{ country.code }}</span>
                <span class="country-name">{{ country.name }}</span>
              </div>
              <div class="country-stats">
                <div class="progress country-progress">
                  <div class="progress-bar" :style="{width: country.percentage + '%'}"></div>
                </div>
                <span class="country-percentage">{{ country.percentage }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- État vide -->
    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-content">
        <svg class="empty-icon" xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <h3>Analyse de menaces</h3>
        <p>Recherchez une adresse IP, un hash ou une CVE pour obtenir des informations détaillées depuis notre base de donnée.</p>
        <div class="search-examples">
          <span class="example-tag">192.168.1.1</span>
          <span class="example-tag">5d41402abc4b2a76b9719d911017c592</span>
          <span class="example-tag">CVE-2025-31201</span>
        </div>
      </div>
    </div>

    <!-- État de chargement -->
    <div v-if="isLoading" class="loading-state">
      <div class="loading-content">
        <div class="spinner-large"></div>
        <h3>Analyse en cours...</h3>
        <p>Recherche d'informations sur "{{ searchQuery }}"</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Header section */
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  color: var(--white);
  font-size: 28px;
  font-weight: 700;
}

.page-title svg {
  color: var(--accent-color);
}

/* Search section */
.search-section {
  margin-bottom: 24px !important;
}

.search-container {
  display: flex;
  gap: 16px;
  align-items: center;
}

.search-input-wrapper {
  position: relative;
  flex: 1;
  max-width: 600px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-color-muted);
  z-index: 1;
}

.search-input {
  padding-left: 44px !important;
  padding-right: 40px !important;
  font-size: 16px;
}

.clear-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-color-muted);
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.clear-btn:hover {
  background-color: var(--container-background-lighter);
  color: var(--text-color);
}

.search-btn {
  white-space: nowrap;
  min-width: 120px;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Results section */
.results-section {
  animation: slideIn 0.4s ease;
}

@keyframes slideIn {
  from { 
    opacity: 0; 
    transform: translateY(20px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

/* Info grids */
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-row label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  color: var(--text-color);
  font-size: 14px;
  font-weight: 500;
}

.code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  background-color: var(--container-background);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--container-border-color);
}

.location-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.activity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Activity section */
.activity-chart {
  background-color: var(--container-background);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  border: 1px solid var(--container-border-color);
}

.activity-timeline {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-color-muted);
}

.activity-progression {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.activity-trend {
  font-size: 12px;
  color: var(--text-color-muted);
  text-align: center;
}

.activity-periods {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-period {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-period label {
  font-size: 13px;
  color: var(--text-color-muted);
  font-weight: 500;
}

/* Blocklists */
.blocklists-card {
  grid-column: span 2;
}

@media (max-width: 768px) {
  .blocklists-card {
    grid-column: span 1;
  }
}

.blocklist-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.blocklist-item {
  background-color: var(--container-background);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--container-border-color);
}

.blocklist-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.blocklist-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.blocklist-info h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--white);
}

.blocklist-stats {
  display: flex;
  gap: 12px;
  align-items: center;
}

.stat {
  font-size: 13px;
  color: var(--text-color-muted);
  font-weight: 500;
}

.change-negative {
  color: var(--success-color);
}

.blocklist-description {
  color: var(--text-color);
  font-size: 14px;
  line-height: 1.5;
  margin: 8px 0;
}

.blocklist-meta {
  font-size: 12px;
  color: var(--text-color-muted);
}

.tier-badge {
  font-size: 11px !important;
  padding: 2px 8px !important;
}

/* Classifications */
.classification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.classification-item {
  background-color: var(--container-background);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--container-border-color);
}

.classification-header {
  margin-bottom: 8px;
}

.classification-item p {
  color: var(--text-color);
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

/* Countries */
.countries-card {
  grid-column: span 2;
}

@media (max-width: 768px) {
  .countries-card {
    grid-column: span 1;
  }
}

.countries-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.country-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.country-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 140px;
}

.country-flag {
  font-size: 11px !important;
  padding: 2px 6px !important;
  font-weight: 600;
}

.country-name {
  color: var(--text-color);
  font-size: 14px;
  font-weight: 500;
}

.country-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.country-progress {
  flex: 1;
  max-width: 120px;
}

.country-percentage {
  font-size: 13px;
  color: var(--text-color-muted);
  font-weight: 500;
  min-width: 35px;
  text-align: right;
}

/* Empty state */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px;
}

.empty-content {
  text-align: center;
  max-width: 500px;
}

.empty-icon {
  color: var(--text-color-muted);
  margin-bottom: 24px;
  opacity: 0.7;
}

.empty-content h3 {
  color: var(--white);
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 600;
}

.empty-content p {
  color: var(--text-color-muted);
  margin: 0 0 20px 0;
  line-height: 1.6;
}

.search-examples {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.example-tag {
  background-color: var(--container-background-lighter);
  color: var(--text-color-muted);
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  border: 1px solid var(--container-border-color);
}

/* Loading state */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px;
}

.loading-content {
  text-align: center;
}

.spinner-large {
  width: 48px;
  height: 48px;
  border: 3px solid var(--container-border-color);
  border-top: 3px solid var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 24px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-content h3 {
  color: var(--white);
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.loading-content p {
  color: var(--text-color-muted);
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .search-container {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input-wrapper {
    max-width: none;
  }
}
</style>