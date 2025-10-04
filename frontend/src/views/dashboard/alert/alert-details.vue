<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface AlertDetail {
  id: number
  timestamp: string
  source: string
  severity: 'high' | 'medium' | 'low'
  type: string
  message: string
  ip: string
  honeypot: string
  user_agent: string
  country: string
  port: number
  protocol: string
  payload: string
  geolocation: {
    latitude: number
    longitude: number
    city: string
    country: string
    isp: string
  }
  session_details: {
    duration: string
    commands: string[]
    files_accessed: string[]
  }
  threat_intelligence: {
    reputation: 'malicious' | 'suspicious' | 'clean'
    blacklisted: boolean
    known_campaigns: string[]
  }
}

export default defineComponent({
  name: "AlertDetailsView",
  setup() {
    const route = useRoute()
    const router = useRouter()

    // Simuler les détails étendus de l'alerte basé sur l'ID
    const alertDetails = computed(() => {
      const alertId = parseInt(route.params.id as string)

      // Données factices étendues basées sur l'ID
      const details: { [key: number]: AlertDetail } = {
        1: {
          id: 1,
          timestamp: '2024-03-15 14:32:45',
          source: 'SSH Honeypot',
          severity: 'high',
          type: 'Tentative de connexion',
          message: 'Tentative de brute force détectée',
          ip: '192.168.1.100',
          honeypot: 'ssh-honeypot-01',
          user_agent: 'SSH-2.0-OpenSSH_7.4',
          country: 'Russie',
          port: 22,
          protocol: 'SSH',
          payload: 'root:admin, root:123456, root:password, admin:admin',
          geolocation: {
            latitude: 55.7558,
            longitude: 37.6176,
            city: 'Moscou',
            country: 'Russie',
            isp: 'Rostelecom'
          },
          session_details: {
            duration: '00:05:23',
            commands: ['whoami', 'ls -la', 'cat /etc/passwd', 'wget malware.sh'],
            files_accessed: ['/etc/passwd', '/root/.ssh/']
          },
          threat_intelligence: {
            reputation: 'malicious',
            blacklisted: true,
            known_campaigns: ['Mirai Botnet', 'SSH Brute Force Campaign 2024']
          }
        },
        2: {
          id: 2,
          timestamp: '2024-03-15 14:28:12',
          source: 'Web Honeypot',
          severity: 'medium',
          type: 'Scan de vulnérabilités',
          message: 'Scan SQL injection détecté',
          ip: '203.0.113.45',
          honeypot: 'web-honeypot-02',
          user_agent: 'Mozilla/5.0 (compatible; SQLMap/1.3.11)',
          country: 'États-Unis',
          port: 80,
          protocol: 'HTTP',
          payload: "' OR 1=1 --",
          geolocation: {
            latitude: 40.7128,
            longitude: -74.0060,
            city: 'New York',
            country: 'États-Unis',
            isp: 'DigitalOcean'
          },
          session_details: {
            duration: '00:02:15',
            commands: [],
            files_accessed: ['/login.php', '/admin.php', '/database.php']
          },
          threat_intelligence: {
            reputation: 'suspicious',
            blacklisted: false,
            known_campaigns: ['Automated SQLi Scanner']
          }
        }
      }

      return details[alertId] || null
    })

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

    const getReputationClass = (reputation: string) => {
      switch (reputation) {
        case 'malicious': return 'badge-danger'
        case 'suspicious': return 'badge-warning'
        case 'clean': return 'badge-success'
        default: return 'badge-primary'
      }
    }

    const getReputationText = (reputation: string) => {
      switch (reputation) {
        case 'malicious': return 'Malveillant'
        case 'suspicious': return 'Suspect'
        case 'clean': return 'Propre'
        default: return 'Inconnu'
      }
    }

    const goBack = () => {
      router.push({ name: 'alerts' })
    }

    return {
      alertDetails,
      getSeverityClass,
      getSeverityText,
      getReputationClass,
      getReputationText,
      goBack
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <!-- En-tête -->
    <div class="page-header">
      <div class="header-navigation">
        <button @click="goBack" class="back-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5"></path>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          <span>Retour aux alertes</span>
        </button>
      </div>

      <div class="header-content" v-if="alertDetails">
        <div class="header-main">
          <h1 class="page-title">
            Alerte #{{ alertDetails.id }}
          </h1>
          <p class="page-subtitle">{{ alertDetails.message }}</p>
        </div>

        <div class="header-badges">
          <div class="timestamp-badge">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            {{ alertDetails.timestamp }}
          </div>
        </div>
      </div>
    </div>

    <!-- Alerte non trouvée -->
    <div v-if="!alertDetails" class="error-container">
      <div class="error-card">
        <div class="error-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <h2 class="error-title">Alerte introuvable</h2>
        <p class="error-message">L'alerte demandée n'existe pas ou n'est plus disponible.</p>
        <button @click="goBack" class="error-action">Retour aux alertes</button>
      </div>
    </div>

    <!-- Contenu principal -->
    <div v-else class="page-content">
      <!-- Vue d'ensemble -->
      <div class="overview-section">
        <div class="overview-grid">
          <!-- Informations générales -->
          <div class="info-card">
            <div class="card-header">
              <div class="card-icon general">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
              </div>
              <h3 class="card-title">Informations Générales</h3>
            </div>
            <div class="card-content">
              <div class="info-item">
                <span class="info-label">Source</span>
                <span class="info-value source-value">{{ alertDetails.source }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Honeypot</span>
                <span class="info-value honeypot-value">{{ alertDetails.honeypot }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Type d'attaque</span>
                <span class="info-value">{{ alertDetails.type }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Protocole</span>
                <span class="info-value protocol-value">{{ alertDetails.protocol }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Port</span>
                <span class="info-value port-value">{{ alertDetails.port }}</span>
              </div>
            </div>
          </div>

          <!-- Informations attaquant -->
          <div class="info-card">
            <div class="card-header">
              <div class="card-icon attacker">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </div>
              <h3 class="card-title">Informations Attaquant</h3>
            </div>
            <div class="card-content">
              <div class="info-item prominent">
                <span class="info-label">Adresse IP</span>
                <code class="ip-address">{{ alertDetails.ip }}</code>
              </div>
              <div class="info-item">
                <span class="info-label">Localisation</span>
                <span class="info-value location-value">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                  </svg>
                  {{ alertDetails.geolocation.city }}, {{ alertDetails.geolocation.country }}
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">Fournisseur</span>
                <span class="info-value">{{ alertDetails.geolocation.isp }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Durée de session</span>
                <span class="info-value duration-value">{{ alertDetails.session_details.duration }}</span>
              </div>
            </div>
          </div>

          <!-- Analyse de menace -->
          <div class="threat-card">
            <div class="card-header">
              <div class="card-icon threat">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                </svg>
              </div>
              <h3 class="card-title">Analyse de Menace</h3>
            </div>
            <div class="card-content">
              <div class="threat-metrics">
                <div class="threat-metric">
                  <div class="metric-label">Réputation</div>
                  <span class="reputation-badge" :class="'reputation-' + alertDetails.threat_intelligence.reputation">
                    {{ getReputationText(alertDetails.threat_intelligence.reputation) }}
                  </span>
                </div>
                <div class="threat-metric">
                  <div class="metric-label">Liste noire</div>
                  <span class="blacklist-badge" :class="alertDetails.threat_intelligence.blacklisted ? 'blacklisted' : 'clean'">
                    {{ alertDetails.threat_intelligence.blacklisted ? 'Blacklisté' : 'Propre' }}
                  </span>
                </div>
              </div>
              <div v-if="alertDetails.threat_intelligence.known_campaigns.length > 0" class="campaigns-section">
                <div class="campaigns-label">Campagnes connues</div>
                <div class="campaigns-list">
                  <span v-for="campaign in alertDetails.threat_intelligence.known_campaigns" 
                        :key="campaign" 
                        class="campaign-tag">
                    {{ campaign }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Détails techniques -->
      <div class="technical-section">
        <div class="section-grid">
          <!-- User Agent -->
          <div class="tech-card">
            <div class="card-header">
              <h3 class="card-title">User Agent</h3>
            </div>
            <div class="card-content">
              <code class="user-agent-code">{{ alertDetails.user_agent }}</code>
            </div>
          </div>

          <!-- Payload -->
          <div class="tech-card">
            <div class="card-header">
              <h3 class="card-title">Charge Utile (Payload)</h3>
            </div>
            <div class="card-content">
              <div class="payload-container">
                <pre class="payload-code">{{ alertDetails.payload }}</pre>
              </div>
            </div>
          </div>

          <!-- Fichiers accédés -->
          <div class="tech-card" v-if="alertDetails.session_details.files_accessed.length > 0">
            <div class="card-header">
              <h3 class="card-title">Fichiers Accédés</h3>
            </div>
            <div class="card-content">
              <div class="files-list">
                <div v-for="file in alertDetails.session_details.files_accessed" 
                     :key="file" 
                     class="file-item">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                  <code class="file-path">{{ file }}</code>
                </div>
              </div>
            </div>
          </div>

          <!-- Commandes exécutées -->
          <div class="tech-card" v-if="alertDetails.session_details.commands.length > 0">
            <div class="card-header">
              <h3 class="card-title">Commandes Exécutées</h3>
            </div>
            <div class="card-content">
              <div class="terminal-container">
                <div v-for="(command, index) in alertDetails.session_details.commands" 
                     :key="index" 
                     class="terminal-line">
                  <span class="terminal-prompt">$</span>
                  <code class="terminal-command">{{ command }}</code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.alert-details-page {
  padding: 24px 32px;
  background: var(--container-background);
  min-height: 100vh;
}

/* En-tête professionnel */
.page-header {
  margin-bottom: 32px;
}

.header-navigation {
  margin-bottom: 20px;
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--text-color-muted);
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
}

.back-button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--white);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
}

.header-main {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 32px;
  font-weight: 800;
  color: var(--white);
  margin: 0 0 8px 0;
}

.page-title svg {
  color: #ff3a5e;
}

.page-subtitle {
  font-size: 18px;
  color: var(--text-color-muted);
  margin: 0;
  line-height: 1.4;
}

.header-badges {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-end;
}

.severity-high .severity-dot {
  background: #ff3a5e;
}

.severity-medium .severity-dot {
  background: #ffb74d;
}

.severity-low .severity-dot {
  background: #29b6f6;
}

.timestamp-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--text-color-muted);
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

/* Erreur */
.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.error-card {
  text-align: center;
  padding: 48px 32px;
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 16px;
  max-width: 400px;
}

.error-icon {
  color: #ffb74d;
  margin-bottom: 24px;
}

.error-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--white);
  margin: 0 0 12px 0;
}

.error-message {
  color: var(--text-color-muted);
  margin: 0 0 32px 0;
  line-height: 1.5;
}

.error-action {
  padding: 12px 24px;
  background: var(--accent-color);
  color: var(--white);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.error-action:hover {
  background: #3f7cff;
}

/* Contenu principal */
.page-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Vue d'ensemble */
.overview-section {
  margin-bottom: 24px;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 24px;
}

/* Cartes d'information */
.info-card, .threat-card {
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.info-card:hover, .threat-card:hover {
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
}

.card-header {
  padding: 20px 24px 16px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-icon.general {
  background: rgba(30, 84, 229, 0.2);
  color: #1e54e5;
}

.card-icon.attacker {
  background: rgba(255, 58, 94, 0.2);
  color: #ff3a5e;
}

.card-icon.threat {
  background: rgba(255, 183, 77, 0.2);
  color: #ffb74d;
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--white);
  margin: 0;
}

.card-content {
  padding: 20px 24px 24px 24px;
}

/* Éléments d'information */
.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.info-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.info-item.prominent {
  background: rgba(255, 255, 255, 0.02);
  padding: 16px;
  border-radius: 8px;
  border: none;
  margin-bottom: 12px;
}

.info-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color-muted);
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--white);
  text-align: right;
}

.source-value {
  color: #29b6f6;
}

.honeypot-value {
  font-family: 'Courier New', monospace;
  background: rgba(255, 255, 255, 0.05);
  padding: 4px 8px;
  border-radius: 4px;
}

.protocol-value {
  color: #ffb74d;
  font-weight: 700;
}

.port-value {
  color: #ff3a5e;
  font-family: 'Courier New', monospace;
}

.ip-address {
  background: rgba(30, 84, 229, 0.15);
  color: #1e54e5;
  padding: 8px 12px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 14px;
}

.location-value {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #00e676;
}

.duration-value {
  font-family: 'Courier New', monospace;
  color: #ffb74d;
}

/* Analyse de menace */
.threat-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.threat-metric {
  text-align: center;
}

.metric-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.reputation-badge, .blacklist-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.reputation-malicious {
  background: rgba(255, 58, 94, 0.2);
  color: #ff3a5e;
  border: 1px solid rgba(255, 58, 94, 0.3);
}

.reputation-suspicious {
  background: rgba(255, 183, 77, 0.2);
  color: #ffb74d;
  border: 1px solid rgba(255, 183, 77, 0.3);
}

.reputation-clean {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
  border: 1px solid rgba(0, 230, 118, 0.3);
}

.blacklisted {
  background: rgba(255, 58, 94, 0.2);
  color: #ff3a5e;
  border: 1px solid rgba(255, 58, 94, 0.3);
}

.clean {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
  border: 1px solid rgba(0, 230, 118, 0.3);
}

.campaigns-section {
  margin-top: 16px;
}

.campaigns-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.campaigns-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.campaign-tag {
  padding: 4px 8px;
  background: rgba(255, 183, 77, 0.15);
  color: #ffb74d;
  border: 1px solid rgba(255, 183, 77, 0.2);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}

/* Section technique */
.technical-section {
  margin-top: 32px;
}

.section-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

.tech-card {
  background: var(--container-background-lighter);
  border: 1px solid var(--container-border-color);
  border-radius: 16px;
  overflow: hidden;
}

.user-agent-code {
  display: block;
  background: rgba(0, 0, 0, 0.3);
  padding: 16px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #29b6f6;
  word-break: break-all;
  line-height: 1.4;
}

.payload-container {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 20px;
}

.payload-code {
  color: #ff3a5e;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  line-height: 1.5;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.file-item:hover {
  background: rgba(0, 0, 0, 0.3);
}

.file-item svg {
  color: #29b6f6;
  flex-shrink: 0;
}

.file-path {
  color: #00e676;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.terminal-container {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 20px;
}

.terminal-line {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  line-height: 1.4;
}

.terminal-line:last-child {
  margin-bottom: 0;
}

.terminal-prompt {
  color: #00e676;
  font-weight: bold;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.terminal-command {
  color: var(--white);
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

/* Responsive */
@media (max-width: 1200px) {
  .overview-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .alert-details-page {
    padding: 16px;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-badges {
    align-items: flex-start;
  }

  .page-title {
    font-size: 24px;
  }
}
</style>