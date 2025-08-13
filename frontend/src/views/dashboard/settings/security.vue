<script lang="ts">
import { defineComponent, onMounted, onUnmounted } from 'vue'
import { SettingsManager } from '@/utils/settings'

export default defineComponent({
  name: "security",
  setup() {
    let settingsManager: SettingsManager | null = null

    onMounted(() => {
      // Initialiser le gestionnaire quand le composant est monté
      settingsManager = new SettingsManager()
    })

    onUnmounted(() => {
      // Nettoyage optionnel quand le composant est détruit
      settingsManager = null
    })

    return {}
  }
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

<style src="@/assets/css/settings.css"></style>
<style scoped>
.settings-pane {
    display: block;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* A2F specific styles extracted from settings.css */
.settings-actions {
    margin-top: 32px;
    padding-top: 16px;
    border-top: 1px solid var(--container-border-color);
    display: flex;
    justify-content: flex-end;
}

.two-factor-status {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background-color: var(--card-background);
    border-radius: 8px;
    border: 1px solid var(--container-border-color);
}

.text-danger {
    color: var(--danger-color) !important;
}

.password-strength-meter {
    display: flex;
    gap: 5px;
    margin: 10px 0;
}

.strength-bar {
    height: 6px;
    flex: 1;
    background-color: var(--container-border-color);
    border-radius: 2px;
    transition: background-color 0.3s ease;
}

.strength-bar.active {
    background-color: var(--danger-color);
}

.password-strength-meter.weak .strength-bar.active {
    background-color: var(--danger-color);
}

.password-strength-meter.medium .strength-bar.active {
    background-color: var(--warning-color);
}

.password-strength-meter.strong .strength-bar.active {
    background-color: var(--success-color);
}

/* Modal styles */
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    animation: fadeIn 0.3s ease;
}

.modal-content {
    position: relative;
    background-color: var(--card-background);
    margin: 10% auto;
    max-width: 500px;
    border-radius: 8px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    animation: slideIn 0.3s ease;
}

.modal-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--container-border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-header h3 {
    margin: 0;
    font-weight: 500;
    color: var(--text-color);
}

.modal-body {
    padding: 20px;
}

.form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 20px;
}

/* QR code styles */
.qrcode-container {
    display: flex;
    justify-content: center;
    margin: 20px 0;
    padding: 16px;
    background-color: white;
    border-radius: 8px;
    width: fit-content;
    margin-left: auto;
    margin-right: auto;
}

.secret-key-container {
    margin: 16px 0;
    text-align: center;
}

.secret-key {
    font-family: monospace;
    background-color: var(--container-border-color);
    padding: 8px 12px;
    border-radius: 4px;
    word-break: break-all;
    margin-top: 8px;
    cursor: text;
    user-select: text;
}

.verification-code-input {
    width: 100%;
    margin: 8px 0;
}

/* Status indicators */
.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: var(--danger-color);
}

.status-online .status-dot {
    background-color: var(--success-color);
}

.status-offline .status-dot {
    background-color: var(--danger-color);
}

@keyframes slideIn {
    from { transform: translateY(-20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

/* Close button */
.modal-close-btn {
    color: var(--text-color-muted);
    float: right;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
    line-height: 1;
}

.modal-close-btn:hover,
.modal-close-btn:focus {
    color: var(--text-color);
}

@media (max-width: 768px) {
    .modal-content {
        width: 90%;
        margin: 20% auto;
    }
}
</style>
