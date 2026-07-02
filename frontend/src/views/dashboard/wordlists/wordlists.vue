<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'

interface WordlistEntry {
  password?: string
  username?: string
  count: number
}

interface ComboEntry {
  username: string
  password: string
  count: number
}

interface WordlistStats {
  passwords: {
    count: number
    total_attempts: number
    top: WordlistEntry[]
  }
  usernames: {
    count: number
    total_attempts: number
    top: WordlistEntry[]
  }
  combinations: {
    count: number
    total_attempts: number
    top: ComboEntry[]
  }
}

export default defineComponent({
  name: "WordlistsView",
  setup() {
    const stats = ref<WordlistStats | null>(null)
    const loading = ref(true)
    const error = ref<string | null>(null)
    const activeTab = ref<'passwords' | 'usernames' | 'combinations'>('passwords')

    const loadStats = async () => {
      loading.value = true
      error.value = null
      try {
        const response = await fetch('/api/agent/user/wordlists', {
          credentials: 'include'
        })
        const data = await response.json()
        if (response.ok) {
          stats.value = data
        } else {
          error.value = data.error || 'Erreur lors du chargement'
        }
      } catch (e) {
        error.value = 'Erreur de connexion au serveur'
      } finally {
        loading.value = false
      }
    }

    const downloadWordlist = (type: string) => {
      window.location.href = `/api/agent/user/wordlists/download/${type}`
    }

    const formatNumber = (n: number) => {
      return n.toLocaleString('fr-FR')
    }

    onMounted(() => {
      loadStats()
    })

    return {
      stats,
      loading,
      error,
      activeTab,
      loadStats,
      downloadWordlist,
      formatNumber
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <h1 class="page-title">Wordlists</h1>
    <p class="page-subtitle">Telechargez les listes de mots de passe, noms d'utilisateur et combinaisons collectes par vos honeypots.</p>

    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Chargement des statistiques...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-container">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadStats">Reessayer</button>
    </div>

    <!-- Content -->
    <div v-else-if="stats">
      <!-- Stats Cards -->
      <div class="wordlist-cards">
        <!-- Passwords Card -->
        <div class="card wordlist-card">
          <div class="wl-card-icon passwords-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
          </div>
          <div class="wl-card-content">
            <div class="wl-card-title">Mots de passe</div>
            <div class="wl-card-stat">{{ formatNumber(stats.passwords.count) }} <span class="stat-unit">uniques</span></div>
            <div class="wl-card-meta">{{ formatNumber(stats.passwords.total_attempts) }} tentatives totales</div>
          </div>
          <div class="wl-card-actions">
            <button class="btn btn-primary btn-sm" @click="downloadWordlist('passwords')">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              .txt
            </button>
            <button class="btn btn-secondary btn-sm" @click="downloadWordlist('passwords-ranked')">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              .csv (avec compteur)
            </button>
          </div>
        </div>

        <!-- Usernames Card -->
        <div class="card wordlist-card">
          <div class="wl-card-icon usernames-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </div>
          <div class="wl-card-content">
            <div class="wl-card-title">Noms d'utilisateur</div>
            <div class="wl-card-stat">{{ formatNumber(stats.usernames.count) }} <span class="stat-unit">uniques</span></div>
            <div class="wl-card-meta">{{ formatNumber(stats.usernames.total_attempts) }} tentatives totales</div>
          </div>
          <div class="wl-card-actions">
            <button class="btn btn-primary btn-sm" @click="downloadWordlist('usernames')">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              .txt
            </button>
            <button class="btn btn-secondary btn-sm" @click="downloadWordlist('usernames-ranked')">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              .csv (avec compteur)
            </button>
          </div>
        </div>

        <!-- Combinations Card -->
        <div class="card wordlist-card">
          <div class="wl-card-icon combos-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="16 18 22 12 16 6"></polyline>
              <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
          </div>
          <div class="wl-card-content">
            <div class="wl-card-title">Combinaisons user:pass</div>
            <div class="wl-card-stat">{{ formatNumber(stats.combinations.count) }} <span class="stat-unit">paires</span></div>
            <div class="wl-card-meta">{{ formatNumber(stats.combinations.total_attempts) }} tentatives totales</div>
          </div>
          <div class="wl-card-actions">
            <button class="btn btn-primary btn-sm" @click="downloadWordlist('combinations')">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              .txt (user:pass)
            </button>
          </div>
        </div>
      </div>

      <!-- Tabs for preview -->
      <div class="tabs-container">
        <button class="tab-btn" :class="{ active: activeTab === 'passwords' }" @click="activeTab = 'passwords'">
          Top Mots de passe
        </button>
        <button class="tab-btn" :class="{ active: activeTab === 'usernames' }" @click="activeTab = 'usernames'">
          Top Utilisateurs
        </button>
        <button class="tab-btn" :class="{ active: activeTab === 'combinations' }" @click="activeTab = 'combinations'">
          Top Combinaisons
        </button>
      </div>

      <!-- Passwords Tab -->
      <div v-if="activeTab === 'passwords'" class="card">
        <div class="card-header">
          <h3 class="card-title">Top 10 mots de passe</h3>
        </div>
        <div v-if="stats.passwords.top.length === 0" class="empty-state">
          Aucun mot de passe collecte
        </div>
        <div v-else class="table-container">
          <table class="wl-table">
            <thead>
              <tr>
                <th style="width: 60px">#</th>
                <th>Mot de passe</th>
                <th style="width: 150px">Tentatives</th>
                <th style="width: 200px">Frequence</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, index) in stats.passwords.top" :key="index">
                <td class="rank-cell">{{ index + 1 }}</td>
                <td><code class="password-value">{{ entry.password }}</code></td>
                <td class="count-cell">{{ formatNumber(entry.count) }}</td>
                <td>
                  <div class="freq-bar">
                    <div class="freq-fill" :style="{ width: (stats.passwords.top[0]?.count ? entry.count / stats.passwords.top[0].count * 100 : 0) + '%' }"></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Usernames Tab -->
      <div v-if="activeTab === 'usernames'" class="card">
        <div class="card-header">
          <h3 class="card-title">Top 10 noms d'utilisateur</h3>
        </div>
        <div v-if="stats.usernames.top.length === 0" class="empty-state">
          Aucun nom d'utilisateur collecte
        </div>
        <div v-else class="table-container">
          <table class="wl-table">
            <thead>
              <tr>
                <th style="width: 60px">#</th>
                <th>Nom d'utilisateur</th>
                <th style="width: 150px">Tentatives</th>
                <th style="width: 200px">Frequence</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, index) in stats.usernames.top" :key="index">
                <td class="rank-cell">{{ index + 1 }}</td>
                <td><code class="password-value">{{ entry.username }}</code></td>
                <td class="count-cell">{{ formatNumber(entry.count) }}</td>
                <td>
                  <div class="freq-bar">
                    <div class="freq-fill username-fill" :style="{ width: (stats.usernames.top[0]?.count ? entry.count / stats.usernames.top[0].count * 100 : 0) + '%' }"></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Combinations Tab -->
      <div v-if="activeTab === 'combinations'" class="card">
        <div class="card-header">
          <h3 class="card-title">Top combinaisons identifiants</h3>
        </div>
        <div v-if="stats.combinations.top.length === 0" class="empty-state">
          Aucune combinaison collectee
        </div>
        <div v-else class="table-container">
          <table class="wl-table">
            <thead>
              <tr>
                <th style="width: 60px">#</th>
                <th>Utilisateur</th>
                <th>Mot de passe</th>
                <th style="width: 150px">Tentatives</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, index) in stats.combinations.top" :key="index">
                <td class="rank-cell">{{ index + 1 }}</td>
                <td><code class="password-value">{{ entry.username }}</code></td>
                <td><code class="password-value">{{ entry.password }}</code></td>
                <td class="count-cell">{{ formatNumber(entry.count) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-subtitle {
  color: var(--text-color-muted);
  font-size: 15px;
  margin-bottom: 32px;
  margin-top: -8px;
}

/* Loading / Error */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
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

.error-container {
  text-align: center;
  padding: 40px;
  color: var(--text-color-muted);
}

/* Wordlist Cards */
.wordlist-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.wordlist-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.wl-card-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.passwords-icon {
  background: rgba(255, 58, 94, 0.15);
  color: #ff3a5e;
}

.usernames-icon {
  background: rgba(30, 84, 229, 0.15);
  color: #42a5f5;
}

.combos-icon {
  background: rgba(156, 77, 255, 0.15);
  color: var(--accent-color);
}

.wl-card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.wl-card-stat {
  font-size: 32px;
  font-weight: 700;
  color: var(--white);
  line-height: 1;
}

.stat-unit {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-color-muted);
}

.wl-card-meta {
  font-size: 13px;
  color: var(--text-color-muted);
}

.wl-card-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-sm {
  padding: 8px 14px;
  font-size: 13px;
  gap: 6px;
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

/* Table */
.table-container {
  overflow-x: auto;
}

.wl-table {
  width: 100%;
  border-collapse: collapse;
}

.wl-table th {
  background: var(--table-header-bg);
  padding: 14px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  color: var(--text-color-muted);
  border-bottom: 1px solid var(--container-border-color);
}

.wl-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--container-border-color);
  font-size: 14px;
  color: var(--white);
}

.wl-table tr:hover {
  background: var(--table-row-hover);
}

.rank-cell {
  color: var(--text-color-muted);
  font-weight: 700;
  font-size: 13px;
}

.count-cell {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.password-value {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  font-size: 13px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: var(--text-color);
}

/* Frequency bar */
.freq-bar {
  height: 8px;
  background: var(--container-background-lighter);
  border-radius: 4px;
  overflow: hidden;
}

.freq-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff3a5e, #ff6b88);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.username-fill {
  background: linear-gradient(90deg, #1e54e5, #42a5f5);
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-color-muted);
  font-style: italic;
}

/* Info Section */
.info-section {
  margin-top: 32px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.info-item h4 {
  margin: 0 0 8px 0;
  color: var(--white);
  font-size: 15px;
  font-weight: 600;
}

.info-item p {
  margin: 0;
  color: var(--text-color-muted);
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .wordlist-cards {
    grid-template-columns: 1fr;
  }

  .wl-card-actions {
    flex-direction: column;
  }
}
</style>
