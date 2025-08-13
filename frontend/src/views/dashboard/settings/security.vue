<script lang="ts">
import {defineComponent} from 'vue'

export default defineComponent({
  name: "security"
})
</script>

<template>
  <div class="settings-pane">
                <form id="password-change-form">
                    <div class="form-group">
                        <label class="form-label">Changer le mot de passe</label>
                        <input type="password" class="form-control" name="old_password" placeholder="Mot de passe actuel">
                    </div>

                    <div class="form-group">
                        <input type="password" class="form-control" name="new_password" placeholder="Nouveau mot de passe">
                    </div>

                    <div class="form-group">
                        <input type="password" class="form-control" name="confirm_password" placeholder="Confirmer le nouveau mot de passe">
                        <div class="form-help">Utilisez un mot de passe fort avec au moins 12 caractères, minuscule, majuscule, chiffre, caractère spécial </div>
                    </div>

                    <div id="password-status" class="form-status"></div>

                    <div class="settings-actions">
                        <button type="submit" class="btn btn-primary">Changer le mot de passe</button>
                    </div>
                </form>

                <div class="form-group">
                    <label class="form-label">Authentification à deux facteurs</label>
                    <div class="two-factor-status" id="a2f-status-display">
                        <div class="status-indicator" id="a2f-status-indicator">
                            <span class="status-dot"></span>
                            <span id="a2f-status-text">Chargement...</span>
                        </div>
                        <button class="btn btn-secondary btn-sm" id="a2f-toggle-btn">Chargement...</button>
                    </div>

                    <!-- Modal pour activer l'A2F -->
                    <div id="a2f-activate-modal" class="modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h3>Activer l'authentification à deux facteurs</h3>
                                <span class="modal-close-btn">&times;</span>
                            </div>
                            <div class="modal-body">
                                <div class="form-group">
                                    <label>Veuillez entrer votre mot de passe pour continuer :</label>
                                    <input type="password" id="a2f-activate-password" class="form-control">
                                </div>
                                <div class="form-actions">
                                    <button id="a2f-activate-submit" class="btn btn-primary">Continuer</button>
                                    <button class="btn btn-secondary close-btn">Annuler</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Modal pour afficher le QR code -->
                    <div id="a2f-qrcode-modal" class="modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h3>Scanner ce QR code</h3>
                                <span class="modal-close-btn">&times;</span>
                            </div>
                            <div class="modal-body">
                                <p>Scannez ce QR code avec votre application d'authentification (Google Authenticator, Authy, etc.)</p>
                                <div id="qrcode-container" class="qrcode-container"></div>
                                <div class="secret-key-container">
                                    <p>Ou entrez cette clé manuellement :</p>
                                    <div class="secret-key" id="a2f-secret-key"></div>
                                </div>
                                <div class="form-group" id="a2f-verification-container">
                                    <label>Veuillez entrer le code généré par votre application :</label>
                                    <div class="verification-code-input">
                                        <input type="text" id="a2f-verification-code" class="form-control" maxlength="6" inputmode="numeric" pattern="[0-9]*" placeholder="123456">
                                    </div>
                                    <div id="a2f-verification-status" class="form-status"></div>
                                </div>
                                <div class="form-actions">
                                    <button class="btn btn-primary" id="a2f-verification-submit">Valider le code</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Modal pour désactiver l'A2F -->
                    <div id="a2f-deactivate-modal" class="modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h3>Désactiver l'authentification à deux facteurs</h3>
                                <span class="modal-close-btn">&times;</span>
                            </div>
                            <div class="modal-body">
                                <div class="form-group">
                                    <label>Entrez votre mot de passe :</label>
                                    <input type="password" id="a2f-deactivate-password" class="form-control">
                                </div>
                                <div class="form-group">
                                    <label>Entrez le code de vérification de votre application :</label>
                                    <div class="verification-code-input">
                                        <input type="text" id="a2f-deactivate-code" class="form-control" maxlength="6" inputmode="numeric" pattern="[0-9]*">
                                    </div>
                                </div>
                                <div class="form-actions">
                                    <button id="a2f-deactivate-submit" class="btn btn-danger">Désactiver l'A2F</button>
                                    <button class="btn btn-secondary close-btn">Annuler</button>
                                </div>
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
    from { opacity: 0; }
    to { opacity: 1; }
}
</style>
<style scoped>
/* S'assurer que les modales sont cachées par défaut */
.modal {
    display: none !important;
}

/* Quand la modal est active, elle s'affiche */
.modal.active,
.modal.show {
    display: block !important;
}
</style>
