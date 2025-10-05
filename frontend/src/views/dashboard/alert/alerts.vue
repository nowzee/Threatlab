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
  source: string
  severity: 'high' | 'medium' | 'low'
  type: string
  message: string
  ip: string
  honeypot: string
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

    // Données factices pour les alertes
    const alerts = ref<LogAlert[]>([
      {
        id: 1,
        timestamp: '2024-03-15 14:32:45',
        source: 'SSH Honeypot',
        severity: 'high',
        type: 'Tentative de connexion',
        message: 'Tentative de brute force détectée',
        ip: '192.168.1.100',
        honeypot: 'ssh-honeypot-01'
      },
      {
        id: 2,
        timestamp: '2024-03-15 14:28:12',
        source: 'Web Honeypot',
        severity: 'medium',
        type: 'Scan de vulnérabilités',
        message: 'Scan SQL injection détecté',
        ip: '203.0.113.45',
        honeypot: 'web-honeypot-02'
      },
      {
        id: 3,
        timestamp: '2024-03-15 14:15:33',
        source: 'FTP Honeypot',
        severity: 'low',
        type: 'Connexion anonyme',
        message: 'Tentative de connexion FTP anonyme',
        ip: '198.51.100.78',
        honeypot: 'ftp-honeypot-03'
      },
      {
        id: 4,
        timestamp: '2024-03-15 14:10:21',
        source: 'SSH Honeypot',
        severity: 'high',
        type: 'Commande malicieuse',
        message: 'Exécution de commandes système suspectes',
        ip: '192.168.1.100',
        honeypot: 'ssh-honeypot-01'
      },
      {
        id: 5,
        timestamp: '2024-03-15 14:05:07',
        source: 'Web Honeypot',
        severity: 'medium',
        type: 'Upload de fichier',
        message: 'Tentative d\'upload de shell malveillant',
        ip: '203.0.113.45',
        honeypot: 'web-honeypot-02'
      }
    ])

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
    })

    return {
      alerts,
      attackWaves,
      chartData,
      chartOptions,
      viewDetails,
      selectedTimeline,
      setTimeline
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
          <div class="table-actions">
            <button class="btn btn-secondary">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
              </svg>
              Filtres
            </button>
          </div>
        </div>

        <div class="table-container">
          <table class="table">
            <thead>
              <tr>
                <th>Date/Heure</th>
                <th>Source</th>
                <th>Type</th>
                <th>IP Source</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="alert in alerts" :key="alert.id" class="alert-row">
                <td class="timestamp">{{ alert.timestamp }}</td>
                <td>{{ alert.source }}</td>
                <td>{{ alert.type }}</td>
                <td>{{ alert.ip }}</td>
                <td class="actions-cell">
                  <button class="btn btn-sm btn-secondary" @click="viewDetails(alert.id)">
                    Détails
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
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

@media (max-width: 768px) {

  .chart-wrapper {
    height: 300px;
    padding: 16px;
  }
}
</style>