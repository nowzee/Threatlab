<script lang="ts">
import {defineComponent} from 'vue'

export default defineComponent({
  name: "advanced"
})
</script>

<template>
  <div class="settings-pane">
                <div class="alert alert-warning">
                    <div class="alert-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                            <line x1="12" y1="9" x2="12" y2="13"></line>
                            <line x1="12" y1="17" x2="12.01" y2="17"></line>
                        </svg>
                    </div>
                    <div class="alert-content">
                        <div class="alert-title">Attention</div>
                        <div class="alert-message">La modification de ces paramètres peut affecter le fonctionnement de la plateforme. Procédez avec prudence.</div>
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label">Stockage des journaux</label>
                    <select class="form-control">
                        <option value="30" selected>30 jours</option>
                        <option value="60">60 jours</option>
                        <option value="90">90 jours</option>
                        <option value="180">180 jours</option>
                        <option value="365">1 an</option>
                    </select>
                </div>

                <div class="form-group">
                    <label class="form-label">Chemin de sauvegarde des données</label>
                    <input type="text" class="form-control" value="/var/lib/honeypot/data">
                </div>

                <div class="form-group">
                    <label class="form-label">Réinitialisation de la plateforme</label>
                    <button class="btn btn-danger">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
                            <path d="M3 6h18"></path>
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                        </svg>
                        Réinitialiser toutes les données
                    </button>
                    <div class="form-help text-danger">Cette action est irréversible et supprimera toutes les données.</div>
                </div>

                <div class="settings-actions">
                    <button class="btn btn-primary">Enregistrer les modifications</button>
                </div>
            </div>
</template>

<style scoped>
.settings-pane {
    display: block;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
</style>