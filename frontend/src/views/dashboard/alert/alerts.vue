<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface LogAlert {
  id: number
  timestamp: string
  agent_id: number
  source_ip: string
  target_port: number
  service_type: string
  country_name: string
}

interface AttackWave {
  time: string
  label: string
  count: number
}

export default defineComponent({
  name: "AlertsView",
  components: {
    Line
  },
  setup() {
    const router = useRouter()

    // Données réelles des alertes
    const alerts = ref<LogAlert[]>([])

    // Variables de pagination
    const currentPage = ref(1)
    const itemsPerPage = ref(10)

    // Computed: Nombre total de pages
    const totalPages = computed(() => {
      return Math.ceil(alerts.value.length / itemsPerPage.value)
    })

    // Computed: Alertes paginées (seulement celles de la page actuelle)
    const paginatedAlerts = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage.value
      const end = start + itemsPerPage.value
      return alerts.value.slice(start, end)
    })

    // Computed: Numéros de pages à afficher
    const pageNumbers = computed(() => {
      const pages: (number | string)[] = []
      const total = totalPages.value
      const current = currentPage.value

      if (total <= 7) {
        // Afficher toutes les pages si <= 7
        for (let i = 1; i <= total; i++) {
          pages.push(i)
        }
      } else {
        // Logique intelligente pour beaucoup de pages
        pages.push(1)

        if (current > 3) {
          pages.push('...')
        }

        const start = Math.max(2, current - 1)
        const end = Math.min(total - 1, current + 1)

        for (let i = start; i <= end; i++) {
          if (!pages.includes(i)) {
            pages.push(i)
          }
        }

        if (current < total - 2) {
          pages.push('...')
        }

        if (total > 1) {
          pages.push(total)
        }
      }

      return pages
    })

    // Méthodes de navigation
    const goToPage = (page: number) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page
      }
    }

    const nextPage = () => {
      if (currentPage.value < totalPages.value) {
        currentPage.value++
      }
    }

    const prevPage = () => {
      if (currentPage.value > 1) {
        currentPage.value--
      }
    }

    // Récupérer la liste des alertes depuis l'API
    const fetchAlerts = async () => {
      try {
        const response = await fetch('/log-analyse/alerts', {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          },
          credentials: 'include'
        })

        if (response.ok) {
          const data = await response.json()
          alerts.value = data
          console.log('Alerts loaded:', data)
        } else {
          console.error('Error fetching alerts:', response.statusText)
        }
      } catch (error) {
        console.error('Error fetching alerts:', error)
      }
    }

    // Générer des données temporelles pour le graphique
    const attackWaves = ref<AttackWave[]>([])
    const selectedTimeline = ref('24h')
const generateTimelineData = async (timeline: string = '24h') => {
  try {
    const response = await fetch(`/log-analyse/get_data_chart`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ time: timeline })
    })

    if (response.ok) {
      const data = await response.json()
      attackWaves.value = data
      console.log('Timeline data loaded:', data)
    } else {
      console.error('Error fetching timeline data:', response.statusText)
    }
  } catch (error) {
    console.error('Error fetching timeline data:', error)
  }
}

    const setTimeline = (timeline: string) => {
      selectedTimeline.value = timeline
      generateTimelineData(timeline)
    }

    // Configuration du graphique
    const chartData = computed(() => {
      const labels = attackWaves.value.map(wave => wave.label)

      return {
        labels,
        datasets: [
          {
            label: 'TimeLIne',
            data: attackWaves.value.map(wave => wave.count),
            borderColor: '#ffb74d',
            backgroundColor: 'rgba(255, 183, 77, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6
          }
        ]
      }
    })

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
        display: false
      },
        title: {
          display: true,
          color: '#ffffff',
          font: {
            size: 16,
            weight: 'bold' as const
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#ffffff',
          bodyColor: '#ffffff',
          borderColor: 'rgba(255, 255, 255, 0.2)',
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: '#cccccc',
            font: {
              size: 12
            }
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: '#cccccc',
            font: {
              size: 12
            }
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index' as const
      }
    }

    const viewDetails = (alertId: number) => {
      router.push({ name: 'alert-details', params: { id: alertId.toString() } })
    }

    onMounted(() => {
      generateTimelineData()
      fetchAlerts()
    })

    return {
      alerts,
      paginatedAlerts,
      attackWaves,
      chartData,
      chartOptions,
      viewDetails,
      selectedTimeline,
      setTimeline,
      currentPage,
      totalPages,
      pageNumbers,
      goToPage,
      nextPage,
      prevPage,
      itemsPerPage
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <h1 class="page-title">
          Alertes de Sécurité
    </h1>

    <!-- Graphique temporel -->
    <div class="content-section">
      <div class="chart-container">
        <div class="chart-header">
          <h2 class="chart-title">Timeline des Attaques</h2>
          <div class="chart-controls">
            <button
              class="btn btn-secondary btn-sm"
              :class="{ active: selectedTimeline === '24h' }"
              @click="setTimeline('24h')"
            >
              24h
            </button>
            <button
              class="btn btn-secondary btn-sm"
              :class="{ active: selectedTimeline === '7d' }"
              @click="setTimeline('7d')"
            >
              7j
            </button>
            <button
              class="btn btn-secondary btn-sm"
              :class="{ active: selectedTimeline === '30d' }"
              @click="setTimeline('30d')"
            >
              30j
            </button>
          </div>
        </div>
        <div class="chart-wrapper">
          <Line :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </div>

    <!-- Tableau modernisé -->
    <div class="content-section">
      <div class="table-container">
        <div class="table-header">
          <h2 class="table-title">Dernières Alertes</h2>
        </div>

        <div class="table-container">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Date/Heure</th>
                <th>IP Source</th>
                <th>Service</th>
                <th>Port</th>
                <th>Pays</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="alert in paginatedAlerts" :key="alert.id" class="alert-row">
                <td>{{ alert.id }}</td>
                <td class="timestamp">{{ alert.timestamp }}</td>
                <td>{{ alert.source_ip }}</td>
                <td>{{ alert.service_type }}</td>
                <td>{{ alert.target_port }}</td>
                <td>{{ alert.country_name }}</td>
                <td class="actions-cell">
                  <button class="btn btn-sm btn-secondary" @click="viewDetails(alert.id)">
                    Détails
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="pagination-wrapper" v-if="totalPages > 1">
          <div class="pagination-info">
            Affichage {{ (currentPage - 1) * itemsPerPage + 1 }}-{{ Math.min(currentPage * itemsPerPage, alerts.length) }} sur {{ alerts.length }} alertes
          </div>
          <div class="pagination-container">
            <div class="pagination">
              <!-- Bouton Précédent -->
              <button
                class="page-btn page-prev"
                @click="prevPage"
                :disabled="currentPage === 1"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
              </button>

              <!-- Numéros de pages -->
              <template v-for="(page, index) in pageNumbers" :key="index">
                <button
                  v-if="typeof page === 'number'"
                  class="page-number"
                  :class="{ active: page === currentPage }"
                  @click="goToPage(page)"
                >
                  {{ page }}
                </button>
                <span v-else class="page-ellipsis">...</span>
              </template>

              <!-- Bouton Suivant -->
              <button
                class="page-btn page-next"
                @click="nextPage"
                :disabled="currentPage === totalPages"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

/* Sections de contenu */
.content-section {
  margin-bottom: 32px;
}

/* Conteneur de graphique */
.chart-container {
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 16px;
  overflow: hidden;
}

.chart-header {
  padding: 24px 32px;
  border-bottom: 1px solid var(--container-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--white);
  margin: 0;
}

.chart-controls {
  display: flex;
  gap: 8px;
}

.chart-controls .btn.active {
  background: var(--accent-color);
  color: var(--white);
}

.chart-wrapper {
  height: 400px;
  padding: 32px;
}

/* Conteneur de tableau modernisé */
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

.table-actions {
  display: flex;
  gap: 12px;
}

.timestamp {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--text-color-muted);
}

/* Pagination */
.pagination-wrapper {
  padding: 20px 32px;
  border-top: 1px solid var(--container-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.pagination-info {
  font-size: 14px;
  color: var(--text-color-muted);
}

.pagination-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.pagination {
  display: flex;
  gap: 8px;
  align-items: center;
}

.page-btn,
.page-number {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--container-border-color);
  border-radius: 6px;
  color: var(--text-color);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled),
.page-number:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--accent-color);
}

.page-number.active {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: var(--white);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-ellipsis {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-color-muted);
  font-size: 14px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .chart-wrapper {
    height: 300px;
    padding: 16px;
  }

  .pagination-wrapper {
    padding: 16px;
    flex-direction: column;
    text-align: center;
  }

  .pagination {
    gap: 6px;
  }

  .page-btn,
  .page-number {
    width: 32px;
    height: 32px;
    font-size: 13px;
  }
}
</style>