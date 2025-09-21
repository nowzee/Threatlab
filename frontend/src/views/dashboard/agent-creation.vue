<script lang="ts">
import { defineComponent, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

interface AgentConfig {
  name: string
  description: string
  honeypotType: string
  integrations: {
    elk: boolean
    opencti: boolean
    siem: boolean
    webhook: boolean
    [key: string]: boolean
  }
  settings: {
    telemetryInterval: number
    maxConnections: number
    enableLogging: boolean
    autoUpdates: boolean
  }
  networkConfig: {
    host: string
    port: number
    interface: string
  }
}

export default defineComponent({
  name: "AgentCreation",
  setup() {
    const router = useRouter()
    
    const agentConfig = reactive<AgentConfig>({
      name: '',
      description: '',
      honeypotType: 'SSH',
      integrations: {
        elk: false,
        opencti: false,
        siem: false,
        webhook: false
      },
      settings: {
        telemetryInterval: 30,
        maxConnections: 3,
        enableLogging: true,
        autoUpdates: true
      },
      networkConfig: {
        host: '0.0.0.0',
        port: 22,
        interface: 'eth0'
      }
    })

    const isSubmitting = ref(false)
    const showAdvanced = ref(false)

    const integrationOptions = [
      {
        key: 'elk',
        name: 'ELK Stack',
        description: 'Intégration avec Elasticsearch, Logstash et Kibana',
        icon: 'database',
      },
      {
        key: 'opencti',
        name: 'OpenCTI',
        description: 'Plateforme de threat intelligence open source',
        icon: 'shield',
      },
      {
        key: 'siem',
        name: 'SIEM Générique',
        description: 'Intégration avec des solutions SIEM tierces',
        icon: 'monitor',
      },
      {
        key: 'webhook',
        name: 'Webhook',
        description: 'Notifications via webhook personnalisé',
        icon: 'link',
      }
    ]

    const validateForm = (): boolean => {
      if (!agentConfig.name.trim()) {
        alert('Le nom de l\'agent est obligatoire')
        return false
      }
      if (!agentConfig.description.trim()) {
        alert('La description de l\'agent est obligatoire')
        return false
      }
      if (agentConfig.networkConfig.port < 1 || agentConfig.networkConfig.port > 65535) {
        alert('Le port doit être compris entre 1 et 65535')
        return false
      }
      return true
    }

    const createAgent = async () => {
      if (!validateForm()) return
      
      isSubmitting.value = true
      
      try {
        // Simulation de la création d'agent
        console.log('Configuration de l\'agent:', agentConfig)
        
        // Ici, vous ajouterez l'appel API réel
        // const response = await fetch('/api/agents', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify(agentConfig)
        // })
        
        // Simulation d'un délai
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        alert('Agent créé avec succès!')
        router.push({ name: 'home' })
        
      } catch (error) {
        console.error('Erreur lors de la création de l\'agent:', error)
        alert('Erreur lors de la création de l\'agent')
      } finally {
        isSubmitting.value = false
      }
    }

    const goBack = () => {
      router.push({ name: 'deploy' })
    }

    return {
      agentConfig,
      isSubmitting,
      integrationOptions,
      showAdvanced,
      createAgent,
      goBack
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <div class="page-header">
      <h1 class="page-title">
        Créer un Agent SSH
      </h1>
    </div>

    <form @submit.prevent="createAgent" class="agent-form">
      <!-- Main Layout Container -->
      <div class="form-layout">
        <!-- Left Column - Main Content -->
        <div class="main-content">
          <!-- Configuration de base -->
          <div class="section-card">
            <div class="card-header">
              <h3 class="card-title">Configuration de base</h3>
            </div>
            <div class="card-body">
              <div class="form-grid">
                <div class="form-group">
                  <label for="agent-name">Nom de l'agent *</label>
                  <input
                    id="agent-name"
                    v-model="agentConfig.name"
                    type="text"
                    class="form-input"
                    placeholder="Ex: SSH-Prod-01"
                    required
                  />
                </div>
                
                <div class="form-group full-width">
                  <label for="agent-description">Description *</label>
                  <textarea
                    id="agent-description"
                    v-model="agentConfig.description"
                    class="form-input"
                    rows="3"
                    placeholder="Description de l'agent et de son rôle"
                    required
                  ></textarea>
                </div>
              </div>
            </div>
          </div>

          <!-- Intégrations -->
          <div class="section-card">
            <div class="card-header">
              <h3 class="card-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                  <polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline>
                  <polyline points="7.5 19.79 7.5 14.6 3 12"></polyline>
                  <polyline points="21 12 16.5 14.6 16.5 19.79"></polyline>
                </svg>
                Intégrations
              </h3>
            </div>
            <div class="card-body">
              <div class="integrations-grid">
                <div
                  v-for="integration in integrationOptions"
                  :key="integration.key"
                  class="integration-card"
                  :class="{ 'selected': agentConfig.integrations[integration.key] }"
                >
                  <div class="integration-header">
                    <div class="integration-icon">
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="3" width="20" height="14" rx="2" ry="2" v-if="integration.icon === 'monitor'"></rect>
                        <line x1="8" y1="21" x2="16" y2="21" v-if="integration.icon === 'monitor'"></line>
                        <line x1="12" y1="17" x2="12" y2="21" v-if="integration.icon === 'monitor'"></line>
                        
                        <circle cx="12" cy="12" r="3" v-if="integration.icon === 'database'"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" v-if="integration.icon === 'database'"></path>
                        
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" v-if="integration.icon === 'shield'"></path>
                        
                        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" v-if="integration.icon === 'link'"></path>
                        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" v-if="integration.icon === 'link'"></path>
                      </svg>
                    </div>
                    <div class="integration-info">
                      <h4 class="integration-name">
                        {{ integration.name }}
                      </h4>
                      <p class="integration-description">{{ integration.description }}</p>
                    </div>
                  </div>
                  <div class="integration-toggle">
                    <input
                      :id="`integration-${integration.key}`"
                      v-model="agentConfig.integrations[integration.key]"
                      type="checkbox"
                      class="form-checkbox"
                    />
                    <label :for="`integration-${integration.key}`" class="checkbox-label">
                      {{ agentConfig.integrations[integration.key] ? 'Activé' : 'Désactivé' }}
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Paramètres avancés -->
          <div class="section-card">
            <div class="card-header">
              <h3 class="card-title">
                <button
                  type="button"
                  class="toggle-advanced-btn"
                  @click="showAdvanced = !showAdvanced"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="{ 'rotated': showAdvanced }">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                  Paramètres avancés
                </button>
              </h3>
            </div>
            <div v-if="showAdvanced" class="card-body">
              <div class="form-grid">
                <div class="form-group">
                  <label for="telemetry-interval">Intervalle de télémétrie (sec)</label>
                  <input
                    id="telemetry-interval"
                    v-model.number="agentConfig.settings.telemetryInterval"
                    type="number"
                    class="form-input"
                    min="1"
                    placeholder="30"
                  />
                </div>
                
                <div class="form-group">
                  <label for="max-connections">Connexions max</label>
                  <input
                    id="max-connections"
                    v-model.number="agentConfig.settings.maxConnections"
                    type="number"
                    class="form-input"
                    min="1"
                    placeholder="3"
                  />
                </div>

                <div class="form-group checkbox-group">
                  <input
                    id="enable-logging"
                    v-model="agentConfig.settings.enableLogging"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <label for="enable-logging">Logs détaillés</label>
                </div>

                <div class="form-group checkbox-group">
                  <input
                    id="auto-updates"
                    v-model="agentConfig.settings.autoUpdates"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <label for="auto-updates">Mises à jour auto</label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Sidebar - Network Configuration -->
        <div class="sidebar-content">
          <div class="section-card sticky-card">
            <div class="card-header">
              <h3 class="card-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                  <path d="M8 21l4-4 4 4"></path>
                  <path d="M12 17v4"></path>
                </svg>
                Configuration réseau
              </h3>
            </div>
            <div class="card-body">
              <div class="sidebar-form-grid">
                <div class="form-group">
                  <label for="network-host">Adresse d'écoute</label>
                  <input
                    id="network-host"
                    v-model="agentConfig.networkConfig.host"
                    type="text"
                    class="form-input"
                    placeholder="0.0.0.0"
                  />
                </div>
                
                <div class="form-group">
                  <label for="network-port">Port</label>
                  <input
                    id="network-port"
                    v-model.number="agentConfig.networkConfig.port"
                    type="number"
                    class="form-input"
                    min="1"
                    max="65535"
                    placeholder="22"
                  />
                </div>

                <div class="form-group">
                  <label for="network-interface">Interface réseau</label>
                  <input
                    id="network-interface"
                    v-model="agentConfig.networkConfig.interface"
                    type="text"
                    class="form-input"
                    placeholder="eth0"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Actions - Fixed in sidebar -->
          <div class="sidebar-actions">
            <button type="submit" class="btn btn-primary btn-block" :disabled="isSubmitting">
              <svg v-if="isSubmitting" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="spinner">
                <line x1="12" y1="2" x2="12" y2="6"></line>
                <line x1="12" y1="18" x2="12" y2="22"></line>
                <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
                <line x1="2" y1="12" x2="6" y2="12"></line>
                <line x1="18" y1="12" x2="22" y2="12"></line>
                <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
                <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
              </svg>
              {{ isSubmitting ? 'Création...' : 'Créer l\'agent' }}
            </button>
            <button type="button" class="btn btn-secondary btn-block" @click="goBack">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 12H5M12 19l-7-7 7-7"/>
              </svg>
              Annuler
            </button>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

/* Layout */
.agent-form {
  display: flex;
  flex-direction: column;
  max-width: 1400px;
  width: 100%;
}

.form-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 32px;
  align-items: start;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sidebar-content {
  position: sticky;
  top: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sticky-card {
  position: sticky;
  top: 0;
}

/* Form Elements */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.sidebar-form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-weight: 600;
  color: #ffffff;
  font-size: 14px;
}

.form-input {
  padding: 12px;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  background-color: #1a1a1a;
  color: #ffffff;
  font-size: 14px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(156, 77, 255, 0.1);
}

/* Integrations */
.integrations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.integration-card {
  border: 2px solid #2a2a2a;
  border-radius: 8px;
  padding: 18px;
  background-color: #1a1a1a;
  transition: all 0.2s ease;
  cursor: pointer;
}

.integration-card:hover {
  background-color: rgba(156, 77, 255, 0.05);
}

.integration-card.selected {
  border-color: var(--accent-color);
  background-color: rgba(142, 63, 255, 0.08);
}

.integration-header {
  display: flex;
  gap: 14px;
  margin-bottom: 14px;
}

.integration-icon {
  width: 40px;
  height: 40px;
  background-color: rgba(0, 200, 255, 0.1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.integration-info {
  flex: 1;
}

.integration-name {
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.integration-description {
  font-size: 13px;
  color: #888888;
  margin: 0;
  line-height: 1.4;
}

.integration-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Form Controls */
.form-checkbox {
  width: 18px;
  height: 18px;
  accent-color: var(--accent-color);
}

.checkbox-label {
  font-size: 13px;
  color: #ffffff;
  cursor: pointer;
}

.checkbox-group {
  flex-direction: row;
  align-items: center;
  gap: 12px;
}

.checkbox-group label {
  margin: 0;
  cursor: pointer;
}

.toggle-advanced-btn {
  background: none;
  border: none;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 0;
  transition: color 0.3s ease;
}

.toggle-advanced-btn:hover {
  color: var(--accent-color);
}

.toggle-advanced-btn svg {
  transition: transform 0.3s ease;
}

.toggle-advanced-btn svg.rotated {
  transform: rotate(180deg);
}

/* Sidebar Actions */
.sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  background-color: #1a1a1a;
  border-radius: 12px;
  border: 1px solid #2a2a2a;
  position: sticky;
  bottom: 24px;
}

.btn-block {
  width: 100%;
  justify-content: center;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Responsive Design */
@media (max-width: 1200px) {
  .form-layout {
    grid-template-columns: 1fr 300px;
    gap: 24px;
  }
}

@media (max-width: 968px) {
  .form-layout {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .sidebar-content {
    position: static;
    order: -1;
  }
  
  .sidebar-actions {
    position: static;
    order: 1;
    margin-top: 24px;
  }
  
  .integrations-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .integrations-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>