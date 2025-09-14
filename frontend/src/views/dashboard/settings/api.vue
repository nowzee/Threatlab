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
                                    <th>Ajouté le</th>
                                    <th>Intégration</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Clé de production</td>
                                    <td>10/06/2023</td>
                                    <td>Elastic Search</td>
                                    <td>
                                        <button class="btn btn-secondary btn-sm">Modifier</button>
                                        <button class="btn btn-danger btn-sm">Supprimer</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Clé de test</td>
                                    <td>05/07/2023</td>
                                    <td>Opencti</td>
                                    <td>
                                        <button class="btn btn-secondary btn-sm">Modifier</button>
                                        <button class="btn btn-danger btn-sm">Supprimer</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="form-group">
                    <button class="btn btn-primary">Ajouter une nouvelle clé API</button>
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