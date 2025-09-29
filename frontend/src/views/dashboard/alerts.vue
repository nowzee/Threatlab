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
  severity_high: number
  severity_medium: number
  severity_low: number
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

    const generateTimelineData = () => {
      const data: AttackWave[] = []
      const now = new Date()

      // Générer des données pour les dernières 24 heures
      for (let i = 23; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000)
        const baseCount = Math.floor(Math.random() * 15) + 5
        const highCount = Math.floor(Math.random() * 5)
        const mediumCount = Math.floor(Math.random() * 8)
        const lowCount = baseCount - highCount - mediumCount

        data.push({
          time: time.toISOString(),
          label: time.getHours().toString().padStart(2, '0') + ':00',
          count: baseCount,
          severity_high: Math.max(0, highCount),
          severity_medium: Math.max(0, mediumCount),
          severity_low: Math.max(0, lowCount)
        })
      }
      attackWaves.value = data
    }

    // Configuration du graphique
    const chartData = computed(() => {
      const labels = attackWaves.value.map(wave => wave.label)

      return {
        labels,
        datasets: [
          {
            label: 'Alertes Moyennes',
            data: attackWaves.value.map(wave => wave.severity_medium),
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
          position: 'top' as const,
          labels: {
            color: '#ffffff',
            usePointStyle: true,
            padding: 20,
            font: {
              size: 14
            }
          }
        },
        title: {
          display: true,
          text: 'Analyse des attaques',
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

    const getSeverityClass = (severity: string) => {
      switch (severity) {
        case 'high': return 'badge-danger'
        case 'medium': return 'badge-warning'
        case 'low': return 'badge-info'
        default: return 'badge-primary'
      }
    }

    const getSeverityText = (severity: string) => {
      switch (severity) {
        case 'high': return 'Élevée'
        case 'medium': return 'Moyenne'
        case 'low': return 'Faible'
        default: return 'Inconnue'
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
      getSeverityClass,
      getSeverityText,
      viewDetails
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
            <button class="btn btn-secondary btn-sm active">24h</button>
            <button class="btn btn-secondary btn-sm">7j</button>
            <button class="btn btn-secondary btn-sm">30j</button>
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
            <button class="btn btn-secondary">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              Exporter
            </button>
          </div>
        </div>

        <div class="modern-table">
          <table class="alerts-table">
            <thead>
              <tr>
                <th>Date/Heure</th>
                <th>Source</th>
                <th>Gravité</th>
                <th>Type</th>
                <th>IP Source</th>
                <th>Description</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="alert in alerts" :key="alert.id" class="alert-row" :class="'severity-' + alert.severity">
                <td class="timestamp-cell">
                  <time class="timestamp">{{ alert.timestamp }}</time>
                </td>
                <td class="source-cell">
                  <div class="source-info">
                    <div class="source-name">{{ alert.source }}</div>
                    <div class="honeypot-name">{{ alert.honeypot }}</div>
                  </div>
                </td>
                <td class="severity-cell">
                  <span class="severity-badge" :class="getSeverityClass(alert.severity)">
                    <span class="severity-dot"></span>
                    {{ getSeverityText(alert.severity) }}
                  </span>
                </td>
                <td class="type-cell">{{ alert.type }}</td>
                <td class="ip-cell">
                  <code class="ip-address">{{ alert.ip }}</code>
                </td>
                <td class="message-cell">
                  <span class="alert-message">{{ alert.message }}</span>
                </td>
                <td class="actions-cell">
                  <button class="action-btn primary" @click="viewDetails(alert.id)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
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

/* Conteneur de graphique modernisé */
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

.modern-table {
  overflow-x: auto;
}

.alerts-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.alerts-table thead th {
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

.alerts-table thead th:first-child {
  border-top-left-radius: 0;
}

.alerts-table thead th:last-child {
  border-top-right-radius: 0;
}

.alert-row {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.2s ease;
}

.alert-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.alert-row.severity-high {
  border-left: 4px solid #ff3a5e;
}

.alert-row.severity-medium {
  border-left: 4px solid #ffb74d;
}

.alert-row.severity-low {
  border-left: 4px solid #29b6f6;
}

.alerts-table td {
  padding: 20px 24px;
  vertical-align: middle;
}

.timestamp {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--text-color-muted);
  display: block;
}

.source-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.source-name {
  font-weight: 600;
  color: var(--white);
  font-size: 14px;
}

.honeypot-name {
  font-size: 12px;
  color: var(--text-color-muted);
  font-family: 'Courier New', monospace;
}

.severity-badge {
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

.severity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.badge-danger {
  background: rgba(255, 58, 94, 0.2);
  color: #ff3a5e;
  border: 1px solid rgba(255, 58, 94, 0.3);
}

.badge-danger .severity-dot {
  background: #ff3a5e;
}

.badge-warning {
  background: rgba(255, 183, 77, 0.2);
  color: #ffb74d;
  border: 1px solid rgba(255, 183, 77, 0.3);
}

.badge-warning .severity-dot {
  background: #ffb74d;
}

.badge-info {
  background: rgba(41, 182, 246, 0.2);
  color: #29b6f6;
  border: 1px solid rgba(41, 182, 246, 0.3);
}

.badge-info .severity-dot {
  background: #29b6f6;
}

.type-cell {
  color: var(--white);
  font-weight: 500;
}

.ip-address {
  background: rgba(255, 255, 255, 0.1);
  padding: 6px 10px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--accent-color);
  font-weight: 600;
}

.alert-message {
  color: var(--white);
  line-height: 1.4;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.primary {
  background: var(--accent-color);
  color: var(--white);
}

.action-btn.primary:hover {
  background: #3f7cff;
  transform: translateY(-1px);
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .alerts-page {
    padding: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .chart-wrapper {
    height: 300px;
    padding: 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>