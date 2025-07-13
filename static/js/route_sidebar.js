/**
 * Gestion de la navigation dans la sidebar
 * Configure les liens de la barre latérale pour charger les bonnes pages
 */

// Mapping des boutons vers leurs URLs correspondantes
const buttonUrlMap = {
    'dashboard-btn': '/dashboard',
    'manage-btn': '/manage',
    'manage-agent-btn': '/manage',
    'deploy-btn': '/deploy',
    'config-btn': '/config',
    'logs-btn': '/logs',
    'reports-btn': '/reports',
    'alerts-btn': '/alerts',
    'templates-btn': '/templates',
    'help-btn': '/help'
};

document.addEventListener('DOMContentLoaded', function () {
    // Sélectionner tous les boutons de la sidebar
    const sidebarButtons = document.querySelectorAll('.btn-sidebar');

    // Ajouter des écouteurs d'événements à chaque bouton
    sidebarButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            // Empêcher la navigation par défaut si le lien n'a pas d'attribut href
            if (!this.getAttribute('href')) {
                e.preventDefault();
                navigateToPage(this.id);
            }

            // Fermer la sidebar mobile si elle est ouverte
            const sidebar = document.querySelector('.container-sidebar');
            if (sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        });
    });

    // Gestionnaire spécifique pour le bouton de déconnexion
    const deconnexionBtn = document.getElementById('deconnexion');
    if (deconnexionBtn) {
        deconnexionBtn.addEventListener('click', function (e) {
            e.preventDefault();
            window.location.href = '/auth/logout';
        });
    }

    // Marquer le bouton actif en fonction de l'URL actuelle
    highlightActiveButton();
});

/**
 * Navigation vers une page spécifique basée sur l'ID du bouton
 * Évite le rechargement si on est déjà sur la page
 */
function navigateToPage(buttonId) {
    const targetUrl = buttonUrlMap[buttonId] || '/dashboard';

    // Vérifier si on est déjà sur la page cible
    const currentPath = window.location.pathname;
    if (currentPath === targetUrl) {
        // Ne pas recharger si on est déjà sur la page
        return;
    }

    // Rediriger vers l'URL cible seulement si différente
    window.location.href = targetUrl;
}

/**
 * Met en évidence le bouton actif en fonction de l'URL actuelle
 */
function highlightActiveButton() {
    const currentPath = window.location.pathname;
    const sidebarButtons = document.querySelectorAll('.btn-sidebar');

    // Supprimer la classe 'active' de tous les boutons
    sidebarButtons.forEach(button => {
        button.classList.remove('active');
    });

    // Déterminer quel bouton doit être actif
    let activeButtonId = Object.entries(buttonUrlMap).find(([id, url]) => {
        return currentPath === '/' && url === '/dashboard' ||
            currentPath === url ||
            (url !== '/dashboard' && currentPath.includes(url));
    })?.[0] || '';

    // Appliquer la classe 'active' au bouton correspondant
    if (activeButtonId) {
        const activeButton = document.getElementById(activeButtonId);
        if (activeButton) {
            activeButton.classList.add('active');
        }
    }
}