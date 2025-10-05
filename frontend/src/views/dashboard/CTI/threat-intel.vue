<script lang="ts">
import { defineComponent, ref, computed } from 'vue'

interface RelatedItem {
  count: number
}

interface RelatedPassword extends RelatedItem {
  password: string
}

interface RelatedUsername extends RelatedItem {
  username: string
}

interface RelatedIp extends RelatedItem {
  ip: string
  country: string
}

interface Service extends RelatedItem {
  service: string
}

interface Country {
  country: string
  count: number
  percentage: number
}

interface Activity {
  last24h: number
  last7d: number
  last30d: number
}

interface SearchResult {
  type: 'ip' | 'password' | 'username'
  value: string
  total_count: number
  first_seen: string
  last_seen: string
  activity: Activity

  // Pour IP
  country?: string
  country_code?: string
  classification?: string
  related_passwords?: RelatedPassword[]
  related_usernames?: RelatedUsername[]
  targeted_services?: Service[]

  // Pour Password/Username
  related_ips?: RelatedIp[]
  origin_countries?: Country[]
}

export default defineComponent({
  name: "ThreatIntelligence",
  setup() {
    const searchQuery = ref('')
    const searchType = ref<'auto' | 'ip' | 'password' | 'username'>('auto')
    const isLoading = ref(false)
    const searchResult = ref<SearchResult | null>(null)
    const error = ref<string | null>(null)

    const searchPlaceholder = computed(() => {
      switch (searchType.value) {
        case 'ip': return 'Entrez une adresse IP (ex: 192.168.1.1)'
        case 'password': return 'Entrez un mot de passe'
        case 'username': return 'Entrez un nom d\'utilisateur'
        default: return 'Rechercher une IP, mot de passe ou nom d\'utilisateur...'
      }
    })

    const performSearch = async () => {
      if (!searchQuery.value.trim()) return

      isLoading.value = true
      error.value = null
      searchResult.value = null

      try {
        const response = await fetch('/api/threat-intel/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({
            query: searchQuery.value.trim(),
            type: searchType.value
          })
        })

        if (response.ok) {
          const data = await response.json()
          searchResult.value = data
        } else if (response.status === 404) {
          error.value = `Aucun résultat trouvé pour "${searchQuery.value}"`
        } else {
          error.value = 'Erreur lors de la recherche'
        }
      } catch (e: any) {
        console.error('Erreur lors de la recherche:', e)
        error.value = 'Erreur de connexion au serveur'
      } finally {
        isLoading.value = false
      }
    }

    const clearSearch = () => {
      searchQuery.value = ''
      searchResult.value = null
      error.value = null
    }

    const getTypeLabel = (type: string) => {
      switch (type) {
        case 'ip': return 'Adresse IP'
        case 'password': return 'Mot de passe'
        case 'username': return 'Nom d\'utilisateur'
        default: return 'Recherche'
      }
    }

    const formatNumber = (num: number) => {
      return num.toLocaleString('fr-FR')
    }

    return {
      searchQuery,
      searchType,
      searchPlaceholder,
      isLoading,
      searchResult,
      error,
      performSearch,
      clearSearch,
      getTypeLabel,
      formatNumber
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <h1 class="page-title">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="M12 16v-4"></path>
        <path d="M12 8h.01"></path>
      </svg>
      Threat Intelligence
    </h1>

    <!-- Barre de recherche -->
    <div class="section-card search-section">
      <!-- Type de recherche -->
      <div class="search-type-selector">
        <label class="type-label">Type de recherche :</label>
        <div class="type-options">
          <label class="type-option">
            <input type="radio" name="searchType" value="ip" v-model="searchType" />
            <span class="type-option-text">
              Adresse ip
            </span>
          </label>
          <label class="type-option">
            <input type="radio" name="searchType" value="password" v-model="searchType" />
            <span class="type-option-text">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
              Mot de passe
            </span>
          </label>
          <label class="type-option">
            <input type="radio" name="searchType" value="username" v-model="searchType" />
            <span class="type-option-text">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              Nom d'utilisateur
            </span>
          </label>
        </div>
      </div>

      <!-- Barre de recherche -->
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
          <span>{{ isLoading ? 'Recherche...' : 'Rechercher' }}</span>
        </button>
      </div>
    </div>

    <!-- Résultats -->
    <div v-if="searchResult" class="results-section">
      <!-- En-tête du résultat -->
      <div class="section-card result-header">
        <div class="result-type">
          <span class="badge badge-primary">{{ getTypeLabel(searchResult.type) }}</span>
        </div>
        <h2 class="result-value">{{ searchResult.value }}</h2>
        <div class="result-stats">
          <div class="stat-item">
            <span class="stat-label">Total</span>
            <span class="stat-value">{{ formatNumber(searchResult.total_count) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Première vue</span>
            <span class="stat-value">{{ searchResult.first_seen }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Dernière vue</span>
            <span class="stat-value">{{ searchResult.last_seen }}</span>
          </div>
        </div>
      </div>

      <!-- Timeline d'activité -->
      <div class="section-card">
        <h3 class="card-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          Activité récente
        </h3>
        <div class="activity-grid">
          <div class="activity-item">
            <span class="activity-label">24 heures</span>
            <span class="activity-count">{{ formatNumber(searchResult.activity.last24h) }}</span>
          </div>
          <div class="activity-item">
            <span class="activity-label">7 jours</span>
            <span class="activity-count">{{ formatNumber(searchResult.activity.last7d) }}</span>
          </div>
          <div class="activity-item">
            <span class="activity-label">30 jours</span>
            <span class="activity-count">{{ formatNumber(searchResult.activity.last30d) }}</span>
          </div>
        </div>
      </div>

      <!-- Résultats pour IP -->
      <template v-if="searchResult.type === 'ip'">
        <!-- Pays -->
        <div class="section-card" v-if="searchResult.country">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
            Localisation
          </h3>
          <div class="card-body">
            <p><strong>Pays :</strong> {{ searchResult.country }}</p>
            <p v-if="searchResult.classification"><strong>Classification :</strong> {{ searchResult.classification }}</p>
          </div>
        </div>

        <!-- Mots de passe utilisés -->
        <div class="section-card" v-if="searchResult.related_passwords && searchResult.related_passwords.length > 0">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            Mots de passe utilisés ({{ searchResult.related_passwords.length }})
          </h3>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th>Mot de passe</th>
                  <th>Utilisations</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in searchResult.related_passwords.slice(0, 10)" :key="index">
                  <td><code>{{ item.password }}</code></td>
                  <td>{{ formatNumber(item.count) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Noms d'utilisateur utilisés -->
        <div class="section-card" v-if="searchResult.related_usernames && searchResult.related_usernames.length > 0">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            Noms d'utilisateur utilisés ({{ searchResult.related_usernames.length }})
          </h3>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th>Nom d'utilisateur</th>
                  <th>Utilisations</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in searchResult.related_usernames.slice(0, 10)" :key="index">
                  <td><code>{{ item.username }}</code></td>
                  <td>{{ formatNumber(item.count) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Services ciblés -->
        <div class="section-card" v-if="searchResult.targeted_services && searchResult.targeted_services.length > 0">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="8" y1="21" x2="16" y2="21"></line>
              <line x1="12" y1="17" x2="12" y2="21"></line>
            </svg>
            Services ciblés
          </h3>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Attaques</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in searchResult.targeted_services" :key="index">
                  <td>{{ item.service }}</td>
                  <td>{{ formatNumber(item.count) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Résultats pour Password -->
      <template v-if="searchResult.type === 'password'">
        <!-- IPs qui ont utilisé ce password -->
        <div class="section-card" v-if="searchResult.related_ips && searchResult.related_ips.length > 0">
          <h3 class="card-title">
            Adresses IP ayant utilisé ce mot de passe ({{ searchResult.related_ips.length }})
          </h3>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th>IP</th>
                  <th>Pays</th>
                  <th>Utilisations</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in searchResult.related_ips.slice(0, 15)" :key="index">
                  <td><code>{{ item.ip }}</code></td>
                  <td>{{ item.country }}</td>
                  <td>{{ formatNumber(item.count) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Usernames associés -->
        <div class="section-card" v-if="searchResult.related_usernames && searchResult.related_usernames.length > 0">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            Noms d'utilisateur associés ({{ searchResult.related_usernames.length }})
          </h3>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th>Nom d'utilisateur</th>
                  <th>Utilisations</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in searchResult.related_usernames.slice(0, 10)" :key="index">
                  <td><code>{{ item.username }}</code></td>
                  <td>{{ formatNumber(item.count) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Pays d'origine -->
        <div class="section-card" v-if="searchResult.origin_countries && searchResult.origin_countries.length > 0">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M2 12h20"></path>
            </svg>
            Pays d'origine
          </h3>
          <div class="countries-list">
            <div v-for="(item, index) in searchResult.origin_countries" :key="index" class="country-row">
              <span class="country-name">{{ item.country }}</span>
              <span class="country-stats">{{ formatNumber(item.count) }} ({{ item.percentage }}%)</span>
            </div>
          </div>
        </div>

        <!-- Services -->
        <div class="section-card" v-if="searchResult.targeted_services && searchResult.targeted_services.length > 0">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="8" y1="21" x2="16" y2="21"></line>
              <line x1="12" y1="17" x2="12" y2="21"></line>
            </svg>
            Services ciblés
          </h3>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Tentatives</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in searchResult.targeted_services" :key="index">
                  <td>{{ item.service }}</td>
                  <td>{{ formatNumber(item.count) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Résultats pour Username -->
      <template v-if="searchResult.type === 'username'">
        <!-- IPs qui ont utilisé ce username -->
        <div class="section-card" v-if="searchResult.related_ips && searchResult.related_ips.length > 0">
          <h3 class="card-title">
            Adresses IP ayant utilisé ce nom d'utilisateur ({{ searchResult.related_ips.length }})
          </h3>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th>IP</th>
                  <th>Pays</th>
                  <th>Utilisations</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in searchResult.related_ips.slice(0, 15)" :key="index">
                  <td><code>{{ item.ip }}</code></td>
                  <td>{{ item.country }}</td>
                  <td>{{ formatNumber(item.count) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Passwords associés -->
        <div class="section-card" v-if="searchResult.related_passwords && searchResult.related_passwords.length > 0">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            Mots de passe associés ({{ searchResult.related_passwords.length }})
          </h3>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th>Mot de passe</th>
                  <th>Utilisations</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in searchResult.related_passwords.slice(0, 10)" :key="index">
                  <td><code>{{ item.password }}</code></td>
                  <td>{{ formatNumber(item.count) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Pays d'origine -->
        <div class="section-card" v-if="searchResult.origin_countries && searchResult.origin_countries.length > 0">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M2 12h20"></path>
            </svg>
            Pays d'origine
          </h3>
          <div class="countries-list">
            <div v-for="(item, index) in searchResult.origin_countries" :key="index" class="country-row">
              <span class="country-name">{{ item.country }}</span>
              <span class="country-stats">{{ formatNumber(item.count) }} ({{ item.percentage }}%)</span>
            </div>
          </div>
        </div>

        <!-- Services -->
        <div class="section-card" v-if="searchResult.targeted_services && searchResult.targeted_services.length > 0">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="8" y1="21" x2="16" y2="21"></line>
              <line x1="12" y1="17" x2="12" y2="21"></line>
            </svg>
            Services ciblés
          </h3>
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Tentatives</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in searchResult.targeted_services" :key="index">
                  <td>{{ item.service }}</td>
                  <td>{{ formatNumber(item.count) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>

    <!-- Message d'erreur -->
    <div v-else-if="error" class=" error-card">
      <div class="error-content">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <p>{{ error }}</p>
      </div>
    </div>

    <!-- État vide -->
    <div v-else-if="!isLoading" class=" empty-state">
      <div class="empty-content">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <h3>Recherche de menaces</h3>
        <p>Entrez une adresse IP, un mot de passe ou un nom d'utilisateur pour obtenir des informations détaillées depuis notre base de données.</p>
        <div class="example-tags">
          <code>192.168.1.1</code>
          <code>admin</code>
          <code>password123</code>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="section-card loading-state">
      <div class="loading-content">
        <div class="spinner-large"></div>
        <p>Recherche en cours...</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Search section */
.search-section {
  margin-bottom: 24px;
}

/* Type selector */
.search-type-selector {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--container-border-color);
}

.type-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-color-muted);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.type-options {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.type-option {
  position: relative;
  cursor: pointer;
}

.type-option input[type="radio"] {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.type-option-text {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--container-border-color);
  border-radius: 6px;
  color: var(--text-color);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.type-option-text svg {
  width: 16px;
  height: 16px;
  opacity: 0.7;
}

.type-option:hover .type-option-text {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--accent-color);
}

.type-option input[type="radio"]:checked + .type-option-text {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: var(--white);
}

.type-option input[type="radio"]:checked + .type-option-text svg {
  opacity: 1;
}

.search-container {
  display: flex;
  gap: 12px;
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
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-color);
}

.search-btn {
  white-space: nowrap;
  min-width: 140px;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Results */
.results-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.result-header {
  text-align: center;
}

.result-type {
  margin-bottom: 12px;
}

.result-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--white);
  margin: 0 0 20px 0;
  word-break: break-all;
  font-family: 'Courier New', monospace;
}

.result-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-color-muted);
  text-transform: uppercase;
  font-weight: 600;
}

.stat-value {
  font-size: 18px;
  color: var(--white);
  font-weight: 700;
}

/* Activity */
.activity-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.activity-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border: 1px solid var(--container-border-color);
}

.activity-label {
  font-size: 12px;
  color: var(--text-color-muted);
  margin-bottom: 8px;
  font-weight: 600;
}

.activity-count {
  font-size: 24px;
  color: var(--accent-color);
  font-weight: 700;
}

/* Countries */
.countries-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.country-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 6px;
  border: 1px solid var(--container-border-color);
}

.country-name {
  font-size: 14px;
  color: var(--text-color);
  font-weight: 500;
}

.country-stats {
  font-size: 14px;
  color: var(--text-color-muted);
  font-weight: 600;
}

/* Empty & Error states */
.empty-state,
.error-card,
.loading-state {
  padding: 60px 20px;
  text-align: center;
}

.empty-content,
.error-content,
.loading-content {
  max-width: 500px;
  margin: 0 auto;
}

.empty-content svg,
.error-content svg {
  color: var(--text-color-muted);
  margin-bottom: 20px;
  opacity: 0.6;
}

.empty-content h3 {
  color: var(--white);
  font-size: 20px;
  margin: 0 0 12px 0;
}

.empty-content p,
.error-content p {
  color: var(--text-color-muted);
  margin: 0 0 20px 0;
  line-height: 1.6;
}

.example-tags {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.example-tags code {
  background: rgba(255, 255, 255, 0.05);
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  border: 1px solid var(--container-border-color);
}

.spinner-large {
  width: 48px;
  height: 48px;
  border: 3px solid var(--container-border-color);
  border-top: 3px solid var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .type-options {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }

  .search-container {
    flex-direction: column;
  }

  .search-input-wrapper {
    max-width: none;
    width: 100%;
  }

  .activity-grid {
    grid-template-columns: 1fr;
  }

  .result-value {
    font-size: 24px;
  }

  .result-stats {
    gap: 20px;
  }
}

@media (max-width: 480px) {
  .type-options {
    grid-template-columns: 1fr;
  }
}
</style>
