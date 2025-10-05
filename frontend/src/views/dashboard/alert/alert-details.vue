<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface AlertDetail {
  id: number
  timestamp: string
  agent_id: number
  agent_name: string
  source_ip: string
  source_port: number | null
  target_port: number
  service_type: string
  username_attempt: string | null
  password_attempt: string | null
  payload: string | null
  command: string | null
  country_code: string | null
  country_name: string
  attack_type: string | null
}

export default defineComponent({
  name: "AlertDetailsView",
  setup() {
    const route = useRoute()
    const router = useRouter()

    const alertDetails = ref<AlertDetail | null>(null)
    const isLoading = ref(true)
    const error = ref<string | null>(null)

    const fetchAlertDetails = async () => {
      const alertId = route.params.id as string

      try {
        isLoading.value = true
        error.value = null

        const response = await fetch(`/log-analyse/alert/${alertId}`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          },
          credentials: 'include'
        })

        if (response.ok) {
          const data = await response.json()
          alertDetails.value = data
        } else if (response.status === 404) {
          error.value = 'Alerte introuvable'
        } else {
          error.value = 'Erreur lors du chargement des détails'
        }
      } catch (e: any) {
        error.value = e?.message || 'Erreur inconnue'
        console.error('Error fetching alert details:', e)
      } finally {
        isLoading.value = false
      }
    }

    const goBack = () => {
      router.push({ name: 'alerts' })
    }

    onMounted(() => {
      fetchAlertDetails()
    })

    return {
      alertDetails,
      isLoading,
      error,
      goBack
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <!-- Bouton retour -->
    <div style="margin-bottom: 24px;">
      <button @click="goBack" class="btn btn-secondary">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5"></path>
          <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
        Retour aux alertes
      </button>
    </div>

    <!-- En-tête -->
    <h1 class="page-title" v-if="alertDetails">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
        <line x1="12" y1="9" x2="12" y2="13"></line>
        <line x1="12" y1="17" x2="12.01" y2="17"></line>
      </svg>
      Détails de l'alerte #{{ alertDetails.id }}
    </h1>

    <!-- Loading -->
    <div v-if="isLoading" class="section-card">
      <div class="card-body" style="text-align: center; padding: 40px;">
        Chargement des détails...
      </div>
    </div>

    <!-- Erreur -->
    <div v-else-if="error" class="section-card">
      <div class="card-body" style="text-align: center; padding: 40px;">
        <p style="color: var(--danger-color); margin-bottom: 20px;">{{ error }}</p>
        <button @click="goBack" class="btn btn-primary">Retour aux alertes</button>
      </div>
    </div>

    <!-- Contenu -->
    <div v-else-if="alertDetails">
      <!-- Informations générales -->
      <div class="section-card">
        <div class="card-header">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            Informations Générales
          </h3>
        </div>
        <div class="card-body">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Date et heure</span>
              <span class="info-value">{{ alertDetails.timestamp }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Agent</span>
              <span class="info-value">{{ alertDetails.agent_name }} (ID: {{ alertDetails.agent_id }})</span>
            </div>
            <div class="info-item">
              <span class="info-label">IP Source</span>
              <code class="info-value">{{ alertDetails.source_ip }}</code>
            </div>
            <div class="info-item">
              <span class="info-label">Port Source</span>
              <span class="info-value">{{ alertDetails.source_port || 'N/A' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Port Cible</span>
              <span class="info-value">{{ alertDetails.target_port }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Service</span>
              <span class="info-value">{{ alertDetails.service_type }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Pays</span>
              <span class="info-value">{{ alertDetails.country_name }}</span>
            </div>
            <div class="info-item" v-if="alertDetails.attack_type">
              <span class="info-label">Type d'attaque</span>
              <span class="info-value">{{ alertDetails.attack_type }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Identifiants utilisés -->
      <div class="section-card" v-if="alertDetails.username_attempt || alertDetails.password_attempt">
        <div class="card-header">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            Identifiants utilisés
          </h3>
        </div>
        <div class="card-body">
          <div class="info-grid">
            <div class="info-item" v-if="alertDetails.username_attempt">
              <span class="info-label">Nom d'utilisateur</span>
              <code class="info-value">{{ alertDetails.username_attempt }}</code>
            </div>
            <div class="info-item" v-if="alertDetails.password_attempt">
              <span class="info-label">Mot de passe</span>
              <code class="info-value">{{ alertDetails.password_attempt }}</code>
            </div>
          </div>
        </div>
      </div>

      <!-- Payload -->
      <div class="section-card" v-if="alertDetails.payload || alertDetails.command">
        <div class="card-header">
          <h3 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="16 18 22 12 16 6"></polyline>
              <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
            Payload / Commande
          </h3>
        </div>
        <div class="card-body">
          <pre class="code-block">{{ alertDetails.payload || alertDetails.command }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border: 1px solid var(--container-border-color);
}

.info-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color-muted);
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--white);
}

.code-block {
  background: rgba(0, 0, 0, 0.3);
  padding: 16px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--text-color);
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  border: 1px solid var(--container-border-color);
}

code {
  background: rgba(255, 255, 255, 0.05);
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
