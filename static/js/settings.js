/**
 * Fichier JavaScript pour gérer les fonctionnalités de la page de paramètres
 * Inclut la gestion du changement de mot de passe et de l'authentification à deux facteurs
 */

// Variables globales pour éviter les duplications
let handlersInitialized = false;

// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', function() {
    // Éviter l'initialisation multiple
    if (handlersInitialized) return;
    handlersInitialized = true;

    // Initialiser les gestionnaires pour l'authentification à deux facteurs
    initA2FHandlers();

    // Gestion des onglets de paramètres
    const tabs = document.querySelectorAll('.settings-tab');
    const panes = document.querySelectorAll('.settings-pane');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Retirer la classe active de tous les onglets et panneaux
            tabs.forEach(t => t.classList.remove('active'));
            panes.forEach(p => p.classList.remove('active'));

            // Ajouter la classe active à l'onglet cliqué
            tab.classList.add('active');

            // Afficher le panneau correspondant
            const tabName = tab.getAttribute('data-tab');
            document.getElementById(`${tabName}-pane`).classList.add('active');
        });
    });

    // Gestion du formulaire de changement de mot de passe
    const securityPane = document.getElementById('security-pane');

    // Gestion des modales - CONSOLIDÉE
    initModalHandlers();

    if (securityPane) {
        const passwordForm = securityPane.querySelector('form') ||
                          createPasswordForm(securityPane);

        // Ajouter les barres de robustesse du mot de passe si elles n'existent pas déjà
        const newPasswordInput = passwordForm.querySelector('input[name="new_password"]');
        if (newPasswordInput && !document.getElementById('password-strength')) {
            // Créer le conteneur pour les barres de robustesse
            const strengthContainer = document.createElement('div');
            strengthContainer.id = 'password-strength';
            strengthContainer.className = 'password-strength-meter';

            // Créer les trois barres
            for (let i = 0; i < 3; i++) {
                const bar = document.createElement('div');
                bar.className = 'strength-bar';
                bar.dataset.level = i + 1;
                strengthContainer.appendChild(bar);
            }

            // Ajouter le conteneur après l'input du nouveau mot de passe
            newPasswordInput.parentNode.insertBefore(strengthContainer, newPasswordInput.nextSibling);

            // Ajouter l'événement pour évaluer la robustesse en temps réel
            newPasswordInput.addEventListener('input', evaluatePasswordStrength);
        }

        passwordForm.addEventListener('submit', handlePasswordChange);
    }

    /**
     * Initialise les gestionnaires pour les modales de manière consolidée
     */
    function initModalHandlers() {
        const modals = document.querySelectorAll('.modal');
        const closeButtons = document.querySelectorAll('.modal-close-btn, .close-btn');

        // Gestionnaire unique pour fermer toutes les modales
        closeButtons.forEach(button => {
            // Retirer les anciens événements potentiels
            button.removeEventListener('click', closeModalHandler);
            // Ajouter le nouveau gestionnaire
            button.addEventListener('click', closeModalHandler);
        });

        // Fermer les modales en cliquant sur l'arrière-plan
        modals.forEach(modal => {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }

    /**
     * Gestionnaire unique pour fermer les modales
     */
    function closeModalHandler(e) {
        e.preventDefault();
        e.stopPropagation();

        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
    }

    /**
     * Crée un formulaire de changement de mot de passe si non existant
     * @param {HTMLElement} container - L'élément conteneur pour le formulaire
     * @return {HTMLElement} Le formulaire créé
     */
    function createPasswordForm(container) {
        const formGroups = container.querySelectorAll('.form-group');
        const actionsDiv = container.querySelector('.settings-actions');

        // Créer le formulaire
        const form = document.createElement('form');
        form.id = 'password-change-form';

        // Ajouter les champs existants au formulaire
        formGroups.forEach((group, index) => {
            if (index <= 2) { // Les trois premiers groupes sont pour le mot de passe
                const clone = group.cloneNode(true);
                form.appendChild(clone);
                container.removeChild(group);
            }
        });

        // Ajouter un message d'état
        const statusDiv = document.createElement('div');
        statusDiv.id = 'password-status';
        statusDiv.classList.add('form-status');
        form.appendChild(statusDiv);

        // Ajouter le bouton de soumission
        const submitBtn = document.createElement('button');
        submitBtn.type = 'submit';
        submitBtn.classList.add('btn', 'btn-primary');
        submitBtn.textContent = 'Changer le mot de passe';

        const formActions = document.createElement('div');
        formActions.classList.add('settings-actions');
        formActions.appendChild(submitBtn);
        form.appendChild(formActions);

        // Insérer le formulaire avant les actions existantes
        container.insertBefore(form, actionsDiv);

        return form;
    }

    /**
     * Gère la soumission du formulaire de changement de mot de passe
     * @param {Event} event - L'événement de soumission
     */
    function handlePasswordChange(event) {
        event.preventDefault();

        const form = event.target;
        const statusDiv = document.getElementById('password-status');
        const passwordInputs = form.querySelectorAll('input[type="password"]');

        // Vérifier que les nouveaux mots de passe correspondent
        const newPassword = passwordInputs[1].value;
        const confirmPassword = passwordInputs[2].value;

        if (newPassword !== confirmPassword) {
            showStatus(statusDiv, 'Les nouveaux mots de passe ne correspondent pas', 'error');
            return;
        }

        // Vérifier la longueur minimale du mot de passe
        if (newPassword.length < 12) {
            showStatus(statusDiv, 'Le mot de passe doit contenir au moins 12 caractères', 'error');
            return;
        }

        // Collecter les données du formulaire
        const formData = new FormData();
        formData.append('old_password', passwordInputs[0].value);
        formData.append('new_password', newPassword);
        formData.append('confirm_password', confirmPassword);

        // Envoyer la requête
        fetch('/account/change-password', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus(statusDiv, 'Mot de passe modifié avec succès', 'success');
                // Réinitialiser le formulaire
                passwordInputs.forEach(input => {
                    input.value = '';
                });

                // Réinitialiser l'indicateur de robustesse
                const strengthMeter = document.getElementById('password-strength');
                if (strengthMeter) {
                    const bars = strengthMeter.querySelectorAll('.strength-bar');
                    bars.forEach(bar => bar.classList.remove('active'));
                    strengthMeter.className = 'password-strength-meter';
                }
            } else {
                // Afficher le message d'erreur spécifique s'il existe, sinon utiliser un message par défaut
                const errorMessage = data.error || 'Échec de la modification du mot de passe. Vérifiez votre mot de passe actuel.';
                showStatus(statusDiv, errorMessage, 'error');
            }
        })
        .catch(_ => {
            showStatus(statusDiv, 'Une erreur est survenue. Veuillez réessayer.', 'error');
        });
    }

    /**
     * Affiche un message d'état dans l'élément spécifié
     * @param {HTMLElement} element - L'élément où afficher le message
     * @param {string} message - Le message à afficher
     * @param {string} type - Le type de message ('success' ou 'error')
     */
    function showStatus(element, message, type) {
        element.textContent = message;
        element.style.color = type === 'success' ? '#00e676' : 'rgba(207,15,31,0.92)';
        element.className = 'form-status';
        element.classList.add(`status-${type}`);

        // Faire disparaître le message après un certain temps pour les succès
        if (type === 'success') {
            setTimeout(() => {
                element.textContent = '';
                element.className = 'form-status';
            }, 5000);
        }
    }

    /**
     * Évalue la robustesse du mot de passe et met à jour l'indicateur visuel
     * @param {Event} event - L'événement d'entrée
     */
    function evaluatePasswordStrength(event) {
        const password = event.target.value;
        const strengthMeter = document.getElementById('password-strength');
        const bars = strengthMeter.querySelectorAll('.strength-bar');

        // Réinitialiser toutes les barres
        bars.forEach(bar => bar.classList.remove('active'));

        // Si le mot de passe est vide, ne pas afficher de barres
        if (password.length === 0) {
            strengthMeter.className = 'password-strength-meter';
            return;
        }

        // Critères de robustesse (correspondant aux regex du backend)
        const hasMinLength = password.length >= 12;
        const hasLowerCase = /[a-z]/.test(password);
        const hasUpperCase = /[A-Z]/.test(password);
        const hasNumbers = /[0-9]/.test(password);
        const hasSpecialChars = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        // Calculer le score
        let score = 0;
        if (hasMinLength) score++;
        if (hasLowerCase && hasUpperCase) score++;
        if (hasNumbers) score++;
        if (hasSpecialChars) score++;

        // Déterminer la force du mot de passe (1, 2 ou 3 barres)
        let strength;
        if (score <= 1) {
            strength = 1; // Faible
        } else if (score <= 3) {
            strength = 2; // Moyen
        } else {
            strength = 3; // Fort (tous les critères satisfaits)
        }

        // Mettre à jour les barres en fonction de la robustesse
        for (let i = 0; i < strength; i++) {
            bars[i].classList.add('active');
        }

        // Ajouter une classe indiquant le niveau global
        strengthMeter.className = 'password-strength-meter';
        const levels = ['weak', 'medium', 'strong'];
        strengthMeter.classList.add(levels[strength - 1]);
    }

    /**
     * Initialise les gestionnaires d'événements pour l'authentification à deux facteurs
     */
    function initA2FHandlers() {
        // Récupérer les éléments A2F
        const a2fToggleBtn = document.getElementById('a2f-toggle-btn');
        const a2fActivateModal = document.getElementById('a2f-activate-modal');
        const a2fQrcodeModal = document.getElementById('a2f-qrcode-modal');
        const a2fDeactivateModal = document.getElementById('a2f-deactivate-modal');

        // Gestionnaires pour le nouveau champ de vérification
        const a2fVerificationSubmit = document.getElementById('a2f-verification-submit');
        const a2fVerificationCode = document.getElementById('a2f-verification-code');
        const a2fVerificationStatus = document.getElementById('a2f-verification-status');

        // Vérifier si les éléments existent
        if (!a2fToggleBtn) return;

        // Événement pour vérifier le code TOTP
        if (a2fVerificationSubmit) {
            // Retirer l'ancien gestionnaire s'il existe
            a2fVerificationSubmit.removeEventListener('click', handleA2FVerification);
            a2fVerificationSubmit.addEventListener('click', handleA2FVerification);
        }

        /**
         * Gestionnaire pour la vérification du code A2F
         */
        function handleA2FVerification() {
            const code = a2fVerificationCode.value.trim();

            // Vérifier que le code a été entré
            if (!code) {
                showA2FStatus(a2fVerificationStatus, 'Veuillez entrer le code généré par votre application', 'error');
                return;
            }

            // Vérifier que le code a la bonne longueur
            if (code.length !== 6 || !/^\d+$/.test(code)) {
                showA2FStatus(a2fVerificationStatus, 'Le code doit contenir 6 chiffres', 'error');
                return;
            }

            // Envoyer la requête de validation
            const formData = new FormData();
            formData.append('code', code);

            fetch('/account/validation_a2f', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showA2FStatus(a2fVerificationStatus, 'Code validé avec succès! L\'authentification à deux facteurs est maintenant active.', 'success');
                    checkA2FStatus();
                    // Fermer la modale après un court délai
                    setTimeout(() => {
                        a2fQrcodeModal.style.display = 'none';
                    }, 1000);
                } else {
                    showA2FStatus(a2fVerificationStatus, data.error || 'Code incorrect. Veuillez réessayer.', 'error');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la validation du code:', error);
                showA2FStatus(a2fVerificationStatus, 'Une erreur est survenue lors de la validation du code.', 'error');
            });
        }

        /**
         * Affiche un message d'état dans l'élément spécifié pour l'A2F
         * @param {HTMLElement} element - L'élément où afficher le message
         * @param {string} message - Le message à afficher
         * @param {string} type - Le type de message ('success' ou 'error')
         */
        function showA2FStatus(element, message, type) {
            if (!element) return;

            element.textContent = message;
            element.style.color = type === 'success' ? '#00e676' : 'rgba(207,15,31,0.92)';
            element.className = 'form-status';
            element.classList.add(`status-${type}`);

            // Faire disparaître le message après un certain temps pour les succès
            if (type === 'success') {
                setTimeout(() => {
                    element.textContent = '';
                    element.className = 'form-status';
                }, 5000);
            }
        }

        /**
         * Vérifie le statut A2F et met à jour l'interface
         */
        function checkA2FStatus() {
            fetch('/account/check_a2f_status', {
                method: 'GET',
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                // Mise à jour de l'interface en fonction du statut
                updateA2FInterface(data.active);
            })
            .catch(error => {
                console.error('Erreur lors de la vérification du statut A2F:', error);
            });
        }

        /**
         * Met à jour l'interface utilisateur en fonction du statut A2F
         * @param {boolean} isActive - Indique si l'A2F est actif
         */
        function updateA2FInterface(isActive) {
            const statusIndicator = document.getElementById('a2f-status-indicator');
            const statusDot = statusIndicator ? statusIndicator.querySelector('.status-dot') : null;
            const statusText = document.getElementById('a2f-status-text');
            const toggleButton = document.getElementById('a2f-toggle-btn');

            if (!statusIndicator || !statusText || !toggleButton) return;

            // Mettre à jour l'indicateur de statut
            if (isActive) {
                statusIndicator.classList.add('status-active');
                statusIndicator.classList.remove('status-inactive');
                if (statusDot) statusDot.style.backgroundColor = '#00e676';
                statusText.textContent = 'Activée';
                toggleButton.textContent = 'Désactiver';
                toggleButton.classList.remove('btn-primary');
                toggleButton.classList.add('btn-danger');
            } else {
                statusIndicator.classList.add('status-inactive');
                statusIndicator.classList.remove('status-active');
                if (statusDot) statusDot.style.backgroundColor = '#cccccc';
                statusText.textContent = 'Désactivée';
                toggleButton.textContent = 'Activer';
                toggleButton.classList.remove('btn-danger');
                toggleButton.classList.add('btn-primary');
            }

            // Configurer le bouton pour ouvrir la bonne modale en fonction du statut
            toggleButton.onclick = function() {
                if (isActive) {
                    // Ouvrir la modale de désactivation
                    const deactivateModal = document.getElementById('a2f-deactivate-modal');
                    if (deactivateModal) {
                        deactivateModal.style.display = 'block';
                        // Réinitialiser les champs
                        const passwordInput = document.getElementById('a2f-deactivate-password');
                        const codeInput = document.getElementById('a2f-deactivate-code');
                        if (passwordInput) passwordInput.value = '';
                        if (codeInput) codeInput.value = '';
                    }
                } else {
                    // Ouvrir la modale d'activation
                    const activateModal = document.getElementById('a2f-activate-modal');
                    if (activateModal) {
                        activateModal.style.display = 'block';
                        // Réinitialiser le champ de mot de passe
                        const passwordInput = document.getElementById('a2f-activate-password');
                        if (passwordInput) passwordInput.value = '';
                    }
                }
            };
        }

        // Vérifier le statut A2F au chargement de la page
        checkA2FStatus();

        // Gestionnaires pour les boutons d'activation et de désactivation
        const a2fActivateSubmit = document.getElementById('a2f-activate-submit');
        const a2fDeactivateSubmit = document.getElementById('a2f-deactivate-submit');

        if (a2fActivateSubmit) {
            // Retirer l'ancien gestionnaire s'il existe
            a2fActivateSubmit.removeEventListener('click', handleA2FActivation);
            a2fActivateSubmit.addEventListener('click', handleA2FActivation);
        }

        if (a2fDeactivateSubmit) {
            // Retirer l'ancien gestionnaire s'il existe
            a2fDeactivateSubmit.removeEventListener('click', handleA2FDeactivation);
            a2fDeactivateSubmit.addEventListener('click', handleA2FDeactivation);
        }

        /**
         * Gestionnaire pour l'activation de l'A2F
         */
        function handleA2FActivation() {
            const password = document.getElementById('a2f-activate-password').value;
            if (!password) {
                alert('Veuillez entrer votre mot de passe');
                return;
            }

            // Requête AJAX pour activer l'A2F
            const formData = new FormData();
            formData.append('active', 'true');
            formData.append('password', password);

            fetch('/account/active_a2f', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Fermer la modal d'activation
                    document.getElementById('a2f-activate-modal').style.display = 'none';

                    // Afficher le QR code reçu du serveur
                    document.getElementById('a2f-secret-key').textContent = data.secret;
                    const qrcodeContainer = document.getElementById('qrcode-container');
                    qrcodeContainer.innerHTML = '';

                    // Créer une image avec le QR code base64 fourni par le serveur
                    const qrImage = document.createElement('img');
                    qrImage.src = data.qrcode;
                    qrImage.alt = 'QR Code pour authentification';
                    qrImage.style.width = '200px';
                    qrImage.style.height = '200px';
                    qrcodeContainer.appendChild(qrImage);

                    document.getElementById('a2f-qrcode-modal').style.display = 'block';
                } else {
                    alert(data.error || 'Une erreur est survenue lors de l\'activation de l\'A2F');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                alert('Une erreur est survenue lors de la communication avec le serveur');
            });
        }

        /**
         * Gestionnaire pour la désactivation de l'A2F
         */
        function handleA2FDeactivation() {
            const password = document.getElementById('a2f-deactivate-password').value;
            const code = document.getElementById('a2f-deactivate-code').value;

            if (!password) {
                alert('Veuillez entrer votre mot de passe');
                return;
            }

            if (!code || code.length !== 6 || !/^\d+$/.test(code)) {
                alert('Veuillez entrer un code de vérification valide à 6 chiffres');
                return;
            }

            // Requête AJAX pour désactiver l'A2F
            const formData = new FormData();
            formData.append('active', 'false');
            formData.append('password', password);
            formData.append('code', code);

            fetch('/account/active_a2f', {
                method: 'POST',
                body: formData
            }).then(response => response.json()).then(data => {
                if (data.success) {
                    document.getElementById('a2f-deactivate-modal').style.display = 'none';
                    alert('L\'authentification à deux facteurs a été désactivée avec succès');
                    checkA2FStatus(); // Mettre à jour l'interface
                } else {
                    alert(data.error || 'Une erreur est survenue lors de la désactivation de l\'A2F');
                }
            }).catch(error => {
                console.error('Erreur:', error);
                alert('Une erreur est survenue lors de la communication avec le serveur');
            });
        }
    }
});