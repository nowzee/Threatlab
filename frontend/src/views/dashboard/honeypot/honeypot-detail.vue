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
    const serverUrl = window.location.origin

    const honeypot = ref<HoneypotDetail | null>(null)
    const activeTab = ref<'overview' | 'attacks' | 'settings'>('overview')
    const loading = ref(true)
    const error = ref<string | null>(null)
    const deployOS = ref<'linux' | 'windows'>('linux')
    const copied = ref(false)

    const loadHoneypotData = async () => {
      loading.value = true
      error.value = null
      try {
        const response = await fetch(`/api/agent/about/${agentId}`, { credentials: 'include' })
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

    const formatDate = (dateString: string) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString('fr-FR', {
        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      })
    }

    const getInstallCommand = () => {
      if (deployOS.value === 'windows') {
        const url = `${serverUrl}/api/agent/install/${agentId}?os=windows`
        return `& ([scriptblock]::Create((curl.exe -ksSL "${url}" | Out-String)))`
      }
      return `curl -ksSL ${serverUrl}/api/agent/install/${agentId} | sudo bash`
    }

    const copyCommand = async () => {
      const cmd = getInstallCommand()
      try {
        await navigator.clipboard.writeText(cmd)
      } catch {
        const ta = document.createElement('textarea')
        ta.value = cmd
        document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta)
      }
      copied.value = true
      setTimeout(() => { copied.value = false }, 2000)
    }

    const goBack = () => { router.push('/dashboard/honeypot-management') }

    onMounted(loadHoneypotData)

    return {
      honeypot, activeTab, loading, error, deployOS, copied,
      formatDate, getInstallCommand, copyCommand, goBack, loadHoneypotData
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Chargement des donnees du honeypot...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-container">
      <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>
      </svg>
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
            <line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          Retour
        </button>
        <div class="header-info">
          <h1 class="page-title">{{ honeypot.name }}</h1>
          <span class="mono-badge">{{ honeypot.type.toUpperCase() }}</span>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="stats-grid">
        <div class="card stat-card">
          <div class="stat-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          </div>
          <div class="stat-content"><div class="stat-value">{{ honeypot.stats.total_attacks }}</div><div class="stat-label">Attaques Totales</div></div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>
          </div>
          <div class="stat-content"><div class="stat-value">{{ honeypot.stats.unique_ips }}</div><div class="stat-label">IPs Uniques</div></div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          </div>
          <div class="stat-content"><div class="stat-value">{{ honeypot.stats.attacks_today }}</div><div class="stat-label">Aujourd'hui</div></div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
          </div>
          <div class="stat-content"><div class="stat-value">{{ honeypot.alert_generated }}</div><div class="stat-label">Alertes</div></div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs-container">
        <button class="tab-btn" :class="{ active: activeTab === 'overview' }" @click="activeTab = 'overview'">Vue d'ensemble</button>
        <button class="tab-btn" :class="{ active: activeTab === 'attacks' }" @click="activeTab = 'attacks'">Attaques Recentes</button>
        <button class="tab-btn" :class="{ active: activeTab === 'settings' }" @click="activeTab = 'settings'">Parametres</button>
      </div>

      <div class="tab-content">
        <!-- Overview -->
        <div v-if="activeTab === 'overview'" class="tab-pane">
          <div class="overview-grid">
            <div class="card info-card">
              <div class="card-header"><h3 class="card-title">Informations Generales</h3></div>
              <div class="card-body">
                <div class="info-row"><span class="info-label">Adresse IP</span><code class="info-value">{{ honeypot.ip }}</code></div>
                <div class="info-row"><span class="info-label">Type</span><span class="info-value">{{ honeypot.type.toUpperCase() }}</span></div>
                <div class="info-row"><span class="info-label">Pays</span><span class="info-value">{{ honeypot.country || 'Non defini' }}</span></div>
                <div class="info-row"><span class="info-label">Banniere</span><code class="info-value banner-value">{{ honeypot.banner || 'N/A' }}</code></div>
                <div class="info-row"><span class="info-label">Cree le</span><span class="info-value">{{ formatDate(honeypot.created_at) }}</span></div>
                <div class="info-row"><span class="info-label">Derniere activite</span><span class="info-value">{{ formatDate(honeypot.updated_at) }}</span></div>
              </div>
            </div>

            <div class="card trends-card">
              <div class="card-header"><h3 class="card-title">Tendances des Attaques</h3></div>
              <div class="card-body">
                <div class="trend-item">
                  <div class="trend-head"><span class="trend-label">Aujourd'hui</span><span class="trend-value">{{ honeypot.stats.attacks_today }}</span></div>
                  <div class="trend-bar"><div class="trend-progress" :style="{ width: (honeypot.stats.attacks_week > 0 ? honeypot.stats.attacks_today / honeypot.stats.attacks_week * 100 : 0) + '%' }"></div></div>
                </div>
                <div class="trend-item">
                  <div class="trend-head"><span class="trend-label">Cette Semaine</span><span class="trend-value">{{ honeypot.stats.attacks_week }}</span></div>
                  <div class="trend-bar"><div class="trend-progress" :style="{ width: (honeypot.stats.attacks_month > 0 ? honeypot.stats.attacks_week / honeypot.stats.attacks_month * 100 : 0) + '%' }"></div></div>
                </div>
                <div class="trend-item">
                  <div class="trend-head"><span class="trend-label">Ce Mois</span><span class="trend-value">{{ honeypot.stats.attacks_month }}</span></div>
                  <div class="trend-bar"><div class="trend-progress" style="width: 100%"></div></div>
                </div>
              </div>
            </div>

            <div class="card countries-card">
              <div class="card-header"><h3 class="card-title">Top Pays Sources</h3></div>
              <div class="card-body">
                <div v-if="honeypot.top_countries.length === 0" class="empty-state">Aucune donnee de pays disponible</div>
                <div v-for="country in honeypot.top_countries" :key="country.country" class="country-item">
                  <div class="country-info"><span class="country-name">{{ country.country }}</span><span class="country-count">{{ country.count }} attaques</span></div>
                  <div class="country-bar"><div class="country-progress" :style="{ width: country.percentage + '%' }"></div></div>
                  <span class="country-percentage">{{ country.percentage.toFixed(1) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Attacks -->
        <div v-if="activeTab === 'attacks'" class="tab-pane">
          <div class="card no-pad">
            <div v-if="honeypot.recent_attacks.length === 0" class="empty-state" style="padding: 40px;">Aucune attaque enregistree pour cet agent</div>
            <div v-else class="attacks-table-container">
              <table class="attacks-table">
                <thead><tr><th>Date/Heure</th><th>IP Source</th><th>Pays</th><th>Type</th><th>Service</th><th>Identifiants</th></tr></thead>
                <tbody>
                  <tr v-for="attack in honeypot.recent_attacks" :key="attack.id">
                    <td>{{ formatDate(attack.timestamp) }}</td>
                    <td><code>{{ attack.source_ip }}</code></td>
                    <td><span class="cell-tag">{{ attack.country }}</span></td>
                    <td>{{ attack.type }}</td>
                    <td><span class="cell-tag">{{ attack.service_type }}</span></td>
                    <td>
                      <code v-if="attack.username || attack.password">{{ attack.username || '?' }}:{{ attack.password || '?' }}</code>
                      <span v-else class="text-muted">-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Settings -->
        <div v-if="activeTab === 'settings'" class="tab-pane">
          <div class="card">
            <div class="card-header"><h3 class="card-title">Redeploiement</h3></div>
            <div class="card-body">
              <p class="settings-hint">Relancez cet agent sur une cible (en root / administrateur). La commande telecharge, configure et demarre l'agent, et l'active au demarrage.</p>
              <div class="os-toggle">
                <button class="os-btn" :class="{ active: deployOS === 'linux' }" @click="deployOS = 'linux'">Linux</button>
                <button class="os-btn" :class="{ active: deployOS === 'windows' }" @click="deployOS = 'windows'">Windows</button>
              </div>
              <div class="cmd-row">
                <code class="cmd">{{ getInstallCommand() }}</code>
                <button class="btn btn-secondary btn-sm cmd-copy" @click="copyCommand">{{ copied ? 'Copie !' : 'Copier' }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Everything monochrome: only ink/gray/borders — no accent, no colored badges. */

/* Loading */
.loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 400px; gap: 20px; }
.spinner { width: 44px; height: 44px; border: 3px solid var(--container-border-color); border-top-color: var(--text-color); border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Error */
.error-container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 400px; gap: 14px; text-align: center; color: var(--text-color); }
.error-container h2 { margin: 0; color: var(--white); }
.error-container p { color: var(--text-color-muted); }
.error-actions { display: flex; gap: 12px; margin-top: 8px; }

/* Header */
.detail-header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
.btn-back { flex-shrink: 0; }
.header-info { display: flex; align-items: center; gap: 12px; flex: 1; flex-wrap: wrap; }
.header-info .page-title { margin: 0; }

.mono-badge {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 5px 12px; border: 1px solid var(--container-border-color);
  border-radius: 4px; font-size: 12px; font-weight: 600; letter-spacing: .4px;
  color: var(--text-color); background: transparent;
}
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-color); }
.status-dot.off { background: var(--text-color-muted); opacity: .5; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 20px; margin-bottom: 28px; }
.stat-card { display: flex; align-items: center; gap: 16px; padding: 20px; }
.stat-icon {
  width: 48px; height: 48px; border-radius: 8px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--container-background-lighter); color: var(--text-color);
  border: 1px solid var(--container-border-color);
}
.stat-value { font-size: 26px; font-weight: 700; color: var(--white); }
.stat-label { font-size: 13px; color: var(--text-color-muted); }

/* Tabs */
.tabs-container { display: flex; gap: 4px; border-bottom: 1px solid var(--container-border-color); margin-bottom: 24px; }
.tab-btn { padding: 12px 20px; background: transparent; border: none; color: var(--text-color-muted); font-weight: 500; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: color .15s, border-color .15s; }
.tab-btn:hover { color: var(--white); }
.tab-btn.active { color: var(--white); border-bottom-color: var(--text-color); }

/* Overview */
.overview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 20px; }
.info-row { display: flex; justify-content: space-between; gap: 12px; padding: 11px 0; border-bottom: 1px solid var(--container-border-color); }
.info-row:last-child { border-bottom: none; }
.info-label { color: var(--text-color-muted); }
.info-value { color: var(--white); font-weight: 600; text-align: right; }
.banner-value { font-size: 12px; max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Trends (mono bars) */
.trend-item { margin-bottom: 18px; }
.trend-item:last-child { margin-bottom: 0; }
.trend-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
.trend-label { font-size: 13px; color: var(--text-color-muted); }
.trend-value { font-size: 18px; font-weight: 700; color: var(--white); }
.trend-bar { height: 6px; background: var(--container-border-color); border-radius: 3px; overflow: hidden; }
.trend-progress { height: 100%; background: var(--text-color); border-radius: 3px; transition: width .3s ease; }

/* Countries (mono bars) */
.country-item { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.country-item:last-child { margin-bottom: 0; }
.country-info { display: flex; flex-direction: column; min-width: 120px; }
.country-name { font-weight: 600; color: var(--white); font-size: 14px; }
.country-count { font-size: 12px; color: var(--text-color-muted); }
.country-bar { flex: 1; height: 6px; background: var(--container-border-color); border-radius: 3px; overflow: hidden; }
.country-progress { height: 100%; background: var(--text-color); border-radius: 3px; }
.country-percentage { font-size: 13px; font-weight: 600; color: var(--white); min-width: 46px; text-align: right; }

/* Attacks table */
.no-pad { padding: 0; overflow: hidden; }
.attacks-table-container { overflow-x: auto; }
.attacks-table { width: 100%; border-collapse: collapse; }
.attacks-table th { background: var(--table-header-bg); padding: 14px 16px; text-align: left; font-weight: 600; font-size: 13px; color: var(--text-color-muted); border-bottom: 1px solid var(--container-border-color); }
.attacks-table td { padding: 14px 16px; border-bottom: 1px solid var(--container-border-color); font-size: 14px; color: var(--white); }
.attacks-table tr:hover { background: var(--table-row-hover); }
.cell-tag { display: inline-block; padding: 3px 8px; border: 1px solid var(--container-border-color); border-radius: 4px; font-size: 11px; font-weight: 600; color: var(--text-color); text-transform: uppercase; letter-spacing: .3px; }
.text-muted { color: var(--text-color-muted); }

/* Settings / redeploy */
.settings-hint { color: var(--text-color-muted); font-size: 14px; margin: 0 0 16px; line-height: 1.5; }
.os-toggle { display: flex; gap: 8px; margin-bottom: 14px; }
.os-btn { padding: 7px 18px; border: 1px solid var(--container-border-color); background: transparent; color: var(--text-color); font-weight: 600; font-size: 13px; cursor: pointer; border-radius: 4px; transition: border-color .15s, background .15s; }
.os-btn:hover { border-color: var(--text-color); }
.os-btn.active { border-color: var(--text-color); background: var(--container-background-lighter); }
.cmd-row { display: flex; gap: 10px; align-items: stretch; }
.cmd { flex: 1; min-width: 0; padding: 12px 14px; background: var(--container-background); border: 1px solid var(--container-border-color); border-radius: 6px; font-family: monospace; font-size: 12.5px; color: var(--text-color); white-space: pre-wrap; word-break: break-all; line-height: 1.5; }
.cmd-copy { flex-shrink: 0; }

.empty-state { text-align: center; padding: 24px; color: var(--text-color-muted); font-style: italic; }
</style>
