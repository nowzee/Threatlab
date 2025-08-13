<script lang="ts">
import {defineComponent} from 'vue'

export default defineComponent({
  name: "api"
})
</script>

<template>
  <div class="settings-pane">
                <div class="form-group">
                    <label class="form-label">Clés API</label>
                    <div class="table-container">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Créée le</th>
                                    <th>Dernière utilisation</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Clé de production</td>
                                    <td>10/06/2023</td>
                                    <td>Il y a 2 heures</td>
                                    <td>
                                        <button class="btn btn-secondary btn-sm">Régénérer</button>
                                        <button class="btn btn-danger btn-sm">Supprimer</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Clé de test</td>
                                    <td>05/07/2023</td>
                                    <td>Jamais utilisée</td>
                                    <td>
                                        <button class="btn btn-secondary btn-sm">Régénérer</button>
                                        <button class="btn btn-danger btn-sm">Supprimer</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="form-group">
                    <button class="btn btn-primary">Créer une nouvelle clé API</button>
                </div>

                <div class="form-group">
                    <label class="form-label">Limites d'utilisation de l'API</label>
                    <select class="form-control">
                        <option value="unlimited">Illimité</option>
                        <option value="1000" selected>1000 requêtes/heure</option>
                        <option value="5000">5000 requêtes/heure</option>
                        <option value="10000">10000 requêtes/heure</option>
                    </select>
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