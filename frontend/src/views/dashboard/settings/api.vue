<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'

interface ApiKey {
  id: number
  name: string
  key: string
  integration: string
}

export default defineComponent({
  name: "api",
  setup() {
    const apiKeys = ref<ApiKey[]>([])
    const isLoading = ref(false)
    const showAddModal = ref(false)
    const showEditModal = ref(false)
    const error = ref<string | null>(null)
    const success = ref<string | null>(null)

    // Formulaire pour ajouter/modifier
    const formData = ref({
      name: '',
      api_key: '',
      integration: ''
    })

    const editingKey = ref<ApiKey | null>(null)

    // Charger la liste des clés API
    const loadApiKeys = async () => {
      isLoading.value = true
      error.value = null

      try {
        const response = await fetch('/api_key/list', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          throw new Error('Erreur lors du chargement des clés API')
        } else {
          // Le backend retourne directement un array, pas un objet avec data
          const data = await response.json()
          // Transformer les données pour correspondre à l'interface
          apiKeys.value = Array.isArray(data) ? data.map(item => ({
            id: item[0], // id
            key: item[1], // key
            name: item[2], // name
            integration: item[3] // integration
          })) : []
        }
      } catch (err) {
        error.value = 'Erreur lors du chargement des clés API'
        console.error(err)
      } finally {
        isLoading.value = false
      }
    }

    // Ajouter une clé API
    const addApiKey = async () => {
      if (!formData.value.name || !formData.value.api_key || !formData.value.integration) {
        error.value = 'Tous les champs sont requis'
        return
      }

      isLoading.value = true
      error.value = null

      try {
        const response = await fetch('/api_key/add', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(formData.value)
        })

        const data = await response.json()

        if (data.success) {
          success.value = 'Clé API ajoutée avec succès'
          showAddModal.value = false
          resetForm()
          await loadApiKeys()
        } else {
          error.value = data.error || 'Erreur lors de l\'ajout'
        }
      } catch (err) {
        error.value = 'Erreur lors de l\'ajout de la clé API'
        console.error(err)
      } finally {
        isLoading.value = false
      }
    }

    // Modifier une clé API
    const updateApiKey = async () => {
      if (!formData.value.name || !formData.value.api_key || !formData.value.integration) {
        error.value = 'Tous les champs sont requis'
        return
      }

      isLoading.value = true
      error.value = null

      try {
        const response = await fetch('/api_key/update', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(formData.value)
        })

        const data = await response.json()

        if (data.success) {
          success.value = 'Clé API mise à jour avec succès'
          showEditModal.value = false
          resetForm()
          await loadApiKeys()
        } else {
          error.value = data.error || 'Erreur lors de la mise à jour'
        }
      } catch (err) {
        error.value = 'Erreur lors de la mise à jour de la clé API'
        console.error(err)
      } finally {
        isLoading.value = false
      }
    }

    // Supprimer une clé API
    const deleteApiKey = async (apiKey: string) => {
      if (!confirm('Êtes-vous sûr de vouloir supprimer cette clé API ?')) {
        return
      }

      isLoading.value = true
      error.value = null

      try {
        const response = await fetch('/api_key/delete', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ api_key: apiKey })
        })

        const data = await response.json()

        if (data.success) {
          success.value = 'Clé API supprimée avec succès'
          await loadApiKeys()
        } else {
          error.value = data.error || 'Erreur lors de la suppression'
        }
      } catch (err) {
        error.value = 'Erreur lors de la suppression de la clé API'
        console.error(err)
      } finally {
        isLoading.value = false
      }
    }

    // Ouvrir le modal d'édition
    const openEditModal = (apiKey: ApiKey) => {
      editingKey.value = apiKey
      formData.value = {
        name: apiKey.name,
        api_key: apiKey.key,
        integration: apiKey.integration
      }
      showEditModal.value = true
    }

    // Réinitialiser le formulaire
    const resetForm = () => {
      formData.value = {
        name: '',
        api_key: '',
        integration: ''
      }
      editingKey.value = null
    }

    // Fermer les modals
    const closeModals = () => {
      showAddModal.value = false
      showEditModal.value = false
      resetForm()
    }

    // Effacer les messages
    const clearMessages = () => {
      error.value = null
      success.value = null
    }

    onMounted(() => {
      loadApiKeys()
    })

    return {
      apiKeys,
      isLoading,
      showAddModal,
      showEditModal,
      error,
      success,
      formData,
      editingKey,
      addApiKey,
      updateApiKey,
      deleteApiKey,
      openEditModal,
      closeModals,
      clearMessages
    }
  }
})
</script>

<template>
  <div class="settings-pane">
    <!-- Messages d'erreur et de succès -->
    <div v-if="error" class="alert alert-danger">
      <div class="alert-icon">⚠</div>
      <div class="alert-content">
        <div class="alert-message">{{ error }}</div>
      </div>
      <button @click="clearMessages" class="alert-close">&times;</button>
    </div>

    <div v-if="success" class="alert alert-success">
      <div class="alert-icon">✓</div>
      <div class="alert-content">
        <div class="alert-message">{{ success }}</div>
      </div>
      <button @click="clearMessages" class="alert-close">&times;</button>
    </div>

    <div class="form-group">
      <label class="form-label">Clés API</label>

      <!-- Indicateur de chargement -->
      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner"></div>
        <span>Chargement des clés API...</span>
      </div>

      <div v-else class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Clé API</th>
              <th>Intégration</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="apiKey in apiKeys" :key="apiKey.id">
              <td>{{ apiKey.name }}</td>
              <td>
                <code class="api-key-display">{{ apiKey.key }}</code>
              </td>
              <td>
                <span class="badge badge-primary">{{ apiKey.integration }}</span>
              </td>
              <td>
                <div class="action-buttons">
                  <button 
                    @click="openEditModal(apiKey)" 
                    class="btn btn-secondary btn-sm"
                    :disabled="isLoading"
                  >
                    Modifier
                  </button>
                  <button 
                    @click="deleteApiKey(apiKey.key)" 
                    class="btn btn-danger btn-sm"
                    :disabled="isLoading"
                  >
                    Supprimer
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="apiKeys.length === 0 && !isLoading">
              <td colspan="4" class="no-data">
                <div class="no-data-content">
                  <div class="no-data-text">
                    <h4>Aucune clé API configurée</h4>
                    <p>Ajoutez votre première clé API pour commencer</p>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="form-group">
      <button 
        @click="showAddModal = true" 
        class="btn btn-primary"
        :disabled="isLoading"
      >
        Ajouter une nouvelle clé API
      </button>
    </div>

    <!-- Modal d'ajout -->
    <div v-if="showAddModal" class="modal-overlay" @click="closeModals">
      <div class="modal-container" @click.stop>
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Ajouter une clé API</h3>
            <button @click="closeModals" class="btn-close">&times;</button>
          </div>
          <div class="card-body">
            <div class="form-group">
              <label class="form-label">Nom :</label>
              <input 
                v-model="formData.name" 
                type="text" 
                class="form-control"
                placeholder="Ex: Production API Key"
              />
            </div>
            <div class="form-group">
              <label class="form-label">Clé API :</label>
              <input 
                v-model="formData.api_key" 
                type="text" 
                class="form-control"
                placeholder="sk-..."
              />
            </div>
            <div class="form-group">
              <label class="form-label">Intégration :</label>
              <select v-model="formData.integration" class="form-control">
                <option value="">Sélectionner une intégration</option>
                <option value="Elastic Search">Elastic Search</option>
                <option value="OpenCTI">OpenCTI</option>
                <option value="MISP">MISP</option>
                <option value="TheHive">TheHive</option>
                <option value="Cortex">Cortex</option>
                <option value="Autre">Autre</option>
              </select>
            </div>
          </div>
          <div class="card-footer">
            <button @click="closeModals" class="btn btn-secondary">Annuler</button>
            <button @click="addApiKey" class="btn btn-primary" :disabled="isLoading">
              {{ isLoading ? 'Ajout en cours...' : 'Ajouter' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de modification -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeModals">
      <div class="modal-container" @click.stop>
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Modifier la clé API</h3>
            <button @click="closeModals" class="btn-close">&times;</button>
          </div>
          <div class="card-body">
            <div class="form-group">
              <label class="form-label">Nom :</label>
              <input 
                v-model="formData.name" 
                type="text" 
                class="form-control"
              />
            </div>
            <div class="form-group">
              <label class="form-label">Clé API :</label>
              <input 
                v-model="formData.api_key" 
                type="text" 
                class="form-control"
              />
            </div>
            <div class="form-group">
              <label class="form-label">Intégration :</label>
              <select v-model="formData.integration" class="form-control">
                <option value="">Sélectionner une intégration</option>
                <option value="Elastic Search">Elastic Search</option>
                <option value="OpenCTI">OpenCTI</option>
                <option value="MISP">MISP</option>
                <option value="TheHive">TheHive</option>
                <option value="Cortex">Cortex</option>
                <option value="Autre">Autre</option>
              </select>
            </div>
          </div>
          <div class="card-footer">
            <button @click="closeModals" class="btn btn-secondary">Annuler</button>
            <button @click="updateApiKey" class="btn btn-primary" :disabled="isLoading">
              {{ isLoading ? 'Mise à jour...' : 'Mettre à jour' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-pane {
  display: block;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Styles spécifiques pour ce composant */
.api-key-display {
  background: var(--input-background);
  color: var(--warning-color);
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  border: 1px solid var(--input-border);
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  color: var(--text-color-muted);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--container-border-color);
  border-top: 2px solid var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.no-data {
  text-align: center;
  padding: 60px 20px;
}

.no-data-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.no-data-icon {
  font-size: 48px;
  opacity: 0.5;
}

.no-data-text h4 {
  margin: 0;
  color: var(--text-color);
  font-size: 16px;
}

.no-data-text p {
  margin: 4px 0 0 0;
  color: var(--text-color-muted);
  font-size: 14px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-container {
  min-width: 500px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-color-muted);
  transition: color 0.2s;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: var(--danger-color);
}

/* Personnalisation des alerts */
.alert {
  position: relative;
}

.alert-close {
  position: absolute;
  top: 12px;
  right: 16px;
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
  transition: opacity 0.2s;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.alert-close:hover {
  opacity: 1;
}
</style>