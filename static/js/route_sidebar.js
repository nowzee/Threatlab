
/**
 * Gestion de la navigation dans la sidebar
 * Configure les liens de la barre latérale pour charger les bonnes pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Sélectionner tous les boutons de la sidebar
    const sidebarButtons = document.querySelectorAll('.btn-sidebar');

    // Ajouter des écouteurs d'événements à chaque bouton
    sidebarButtons.forEach(button => {
        button.addEventListener('click', function(e) {
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
        deconnexionBtn.addEventListener('click', function(e) {
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
    let targetUrl = '/';

    // Déterminer l'URL cible en fonction de l'ID du bouton
    switch (buttonId) {
        case 'dashboard-btn':
            targetUrl = '/dashboard';
            break;
        case 'manage-btn':
        case 'manage-agent-btn':
            targetUrl = '/manage';
            break;
        case 'deploy-btn':
            targetUrl = '/deploy';
            break;
        case 'config-btn':
            targetUrl = '/config';
            break;
        case 'logs-btn':
            targetUrl = '/logs';
            break;
        case 'reports-btn':
            targetUrl = '/reports';
            break;
        case 'alerts-btn':
            targetUrl = '/alerts';
            break;
        case 'templates-btn':
            targetUrl = '/templates';
            break;
        case 'help-btn':
            targetUrl = '/help';
            break;
        default:
            targetUrl = '/dashboard';
    }

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
    let activeButtonId = '';

    if (currentPath === '/' || currentPath === '/dashboard') {
        activeButtonId = 'dashboard-btn';
    } else if (currentPath === '/manage') {
        activeButtonId = 'manage-btn';
    } else if (currentPath === '/deploy') {
        activeButtonId = 'deploy-btn';
    } else if (currentPath === '/config') {
        activeButtonId = 'config-btn';
    } else if (currentPath.includes('/logs')) {
        activeButtonId = 'logs-btn';
    } else if (currentPath.includes('/reports')) {
        activeButtonId = 'reports-btn';
    } else if (currentPath.includes('/alerts')) {
        activeButtonId = 'alerts-btn';
    } else if (currentPath.includes('/templates')) {
        activeButtonId = 'templates-btn';
    } else if (currentPath.includes('/help')) {
        activeButtonId = 'help-btn';
    }

    // Appliquer la classe 'active' au bouton correspondant
    if (activeButtonId) {
        const activeButton = document.getElementById(activeButtonId);
        if (activeButton) {
            activeButton.classList.add('active');
        }
    }
}