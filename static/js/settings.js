/**
 * Fichier JavaScript pour gérer les fonctionnalités de la page de paramètres
 * Inclut la gestion du changement de mot de passe
 */

// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', function() {
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

        // Vérifier que tous les champs sont remplis
        let isValid = true;
        passwordInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('invalid');
            } else {
                input.classList.remove('invalid');
            }
        });

        if (!isValid) {
            showStatus(statusDiv, 'Tous les champs sont obligatoires', 'error');
            return;
        }

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

        // Ajouter un texte d'aide basé sur les critères manquants
        const helpText = document.querySelector('.form-help');
        if (helpText) {
            let message = 'Exigences: au moins 12 caractères';
            if (!hasLowerCase) message += ', une lettre minuscule';
            if (!hasUpperCase) message += ', une lettre majuscule';
            if (!hasNumbers) message += ', un chiffre';
            if (!hasSpecialChars) message += ', un caractère spécial';

            helpText.textContent = message;
        }
    }
});
