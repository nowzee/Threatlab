<script lang="ts">
import { defineComponent, ref, onMounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

interface MetricData {
  ip_count: number
  Sample_downloaded: number
  tentative_access: number
  active_honeypot: number
}

interface LogData {
  agent_id: number
  agent_name: string
  country_name: string
  source_ip: string
  target_port: number
  service_type: string
  created_at: string
}

interface CountryData {
  country_name: string
  attack_count: number
}

export default defineComponent({
  name: "home",
  setup() {
    const metrics = ref<MetricData>({
      ip_count: 0,
      Sample_downloaded: 0,
      tentative_access: 0,
      active_honeypot: 0
    })

    const logs = ref<LogData[]>([])
    const countryRanking = ref<CountryData[]>([])
    const isLoading = ref(true)
    const error = ref<string | null>(null)
    let chartInstance: Chart | null = null

    const fetchMetrics = async () => {
      try {
        isLoading.value = true
        error.value = null

        const response = await fetch('/api/agent/user/metric_dashboard', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error('Erreur lors du chargement des données')
        }

        metrics.value = await response.json()

      } catch (e: any) {
        error.value = e?.message || 'Erreur inconnue'
        console.error('Error fetching metrics:', e)
      } finally {
        isLoading.value = false
      }
    }

    const fetchLog = async () => {
      try {
        const response = await fetch('/api/agent/user/new_logs', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error('Erreur lors du chargement des logs')
        }

        logs.value = await response.json()
      } catch (e: any) {
        console.error('Error fetching log:', e)
      }
    }

    const fetchCountryRanking = async () => {
      try {
        const response = await fetch('/api/agent/user/country_ranking', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error('Erreur lors du chargement du classement des pays')
        }

        countryRanking.value = await response.json()
        await nextTick()
        createChart()
      } catch (e: any) {
        console.error('Error fetching country ranking:', e)
      }
    }

    const createChart = () => {
      const canvas = document.getElementById('countryChart') as HTMLCanvasElement
      if (!canvas) return

      // Destroy existing chart if it exists
      if (chartInstance) {
        chartInstance.destroy()
      }

      const ctx = canvas.getContext('2d')
      if (!ctx) return

      const countries = countryRanking.value.map(c => c.country_name)
      const counts = countryRanking.value.map(c => c.attack_count)

      chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: countries,
          datasets: [{
            label: 'Nombre d\'attaques',
            data: counts,
            backgroundColor: '#9c4dff',
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(26, 29, 41, 0.95)',
              titleColor: '#ffffff',
              bodyColor: '#8b92a7',
              borderColor: 'rgba(62, 69, 88, 1)',
              borderWidth: 1,
              padding: 12,
              displayColors: false
            }
          },
          scales: {
            x: {
              beginAtZero: true,
              ticks: {
                color: '#8b92a7',
                font: {
                  size: 12
                }
              },
              grid: {
                color: 'rgba(62, 69, 88, 0.5)'
              }
            },
            y: {
              ticks: {
                color: '#ffffff',
                font: {
                  size: 13
                }
              },
              grid: {
                display: false
              }
            }
          }
        }
      })
    }

    onMounted(() => {
      fetchMetrics()
      fetchLog()
      fetchCountryRanking()
    })

    return {
      metrics,
      logs,
      countryRanking,
      isLoading,
      error
    }
  }
})
</script>

<template>
<div class="content-wrapper">
    <h1 class="page-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
        </svg>
        Tableau de bord
    </h1>

    <!-- Résumé statistique -->
    <div class="grid-container">
        <div class="card">
            <div class="card-body">
                <div class="stat-card">
                    <div class="stat-icon" style="color: var(--accent-color);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                            <line x1="12" y1="19" x2="12" y2="22"></line>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">{{ isLoading ? '‎' : metrics.active_honeypot }}</div>
                        <div class="stat-label">Honeypots actifs</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-body">
                <div class="stat-card">
                    <div class="stat-icon" style="color: var(--warning-color);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">{{ isLoading ? '‎' : metrics.tentative_access }}</div>
                        <div class="stat-label">Tentatives d'accès</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-body">
                <div class="stat-card">
                    <div class="stat-icon" style="color: var(--success-color);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 7h-9"></path>
                            <path d="M14 17H5"></path>
                            <circle cx="17" cy="17" r="3"></circle>
                            <circle cx="7" cy="7" r="3"></circle>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">{{ isLoading ? '‎' : metrics.ip_count }}</div>
                        <div class="stat-label">IP collectées</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-body">
                <div class="stat-card">
                    <div class="stat-icon" style="color: var(--danger-color);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 7h-9"></path>
                            <path d="M14 17H5"></path>
                            <circle cx="17" cy="17" r="3"></circle>
                            <circle cx="7" cy="7" r="3"></circle>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">{{ isLoading ? '‎' : metrics.Sample_downloaded }}</div>
                        <div class="stat-label">Samples téléchargés</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Classement des pays -->
    <div class="section-card">
        <div class="card-header" style="padding: 0 0 16px 0; margin-bottom: 16px;">
            <h3 class="card-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 3v18h18"></path>
                    <path d="M18 17V9"></path>
                    <path d="M13 17V5"></path>
                    <path d="M8 17v-3"></path>
                </svg>
                Classement des pays
            </h3>
        </div>
        <div class="chart-container">
            <canvas id="countryChart"></canvas>
        </div>
    </div>

    <!-- Alertes récentes -->
    <div class="section-card">
        <div class="card-header" style="padding: 0 0 16px 0; margin-bottom: 16px;">
            <h3 class="card-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                Alertes récentes
            </h3>
            <a href="#" class="view-all-link">Voir tout</a>
        </div>

      <div class="table-container">
        <table class="table">
          <thead>
          <tr>
            <th>Date</th>
            <th>Agent ID</th>
            <th>Nom de l'agent</th>
            <th>IP Source</th>
            <th>Port cible</th>
            <th>Service</th>
            <th>Pays</th>
            <th>Action</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="log in logs" :key="log.agent_id">
            <td>{{log.created_at}}</td>
            <td>{{ log.agent_id }}</td>
            <td>{{ log.agent_name }}</td>
            <td>{{ log.source_ip }}</td>
            <td>{{ log.target_port }}</td>
            <td>{{ log.service_type }}</td>
            <td>{{ log.country_name }}</td>
            <td><button class="btn btn-sm btn-secondary">Détails</button></td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
</div>

<!-- Conteneur pour les notifications -->
<div id="notification-container"></div>
</template>

<style src="@/assets/css/dashboard/notifications.css"></style>
<style scoped>

    .view-all-link {
        color: var(--accent-color);
        font-size: 14px;
        text-decoration: none;
        font-weight: 500;
    }

    .view-all-link:hover {
        text-decoration: underline;
    }

    .chart-container {
        position: relative;
        height: 30vh;
        width: 100%;
    }
</style>