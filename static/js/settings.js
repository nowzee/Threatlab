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
            } else {
                showStatus(statusDiv, 'Échec de la modification du mot de passe. Vérifiez votre mot de passe actuel.', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
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
});
