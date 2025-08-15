// Initialisation du dashboard
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadHoneypotStatus();
});

/**
 * Configure les écouteurs d'événements pour l'interface
 */
function setupEventListeners() {
    // Gestion des boutons de déploiement
    const deployButtons = document.querySelectorAll('.deploy-honeypot-btn');
    deployButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const honeypotType = this.getAttribute('data-type');
            showDeployModal(honeypotType);
        });
    });

    // Gestion des boutons d'arrêt de honeypot
    const stopButtons = document.querySelectorAll('.stop-honeypot-btn');
    stopButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const honeypotId = this.getAttribute('data-id');
            confirmStopHoneypot(honeypotId);
        });
    });

    // Écouteur pour le basculement du thème (si implémenté)
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Écouteur pour le bouton de bascule du menu mobile
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', toggleMobileMenu);
    }
}

/**
 * Affiche une modale pour configurer et déployer un honeypot
 */
function showDeployModal(honeypotType) {
    // Crée et affiche une modale pour le déploiement
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-container">
            <div class="modal-header">
                <h3>Déployer un Honeypot ${honeypotType}</h3>
                <button class="modal-close-btn">&times;</button>
            </div>
            <div class="modal-body">
                <form id="deploy-form">
                    <div class="form-group">
                        <label class="form-label" for="honeypot-name">Nom du Honeypot</label>
                        <input type="text" id="honeypot-name" class="form-control" placeholder="Mon Honeypot" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="honeypot-location">Emplacement</label>
                        <select id="honeypot-location" class="form-control">
                            <option value="local">Local</option>
                            <option value="cloud">Cloud</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Configuration</label>
                        <div class="checkbox-group">
                            <label class="checkbox-label">
                                <input type="checkbox" checked> Journalisation avancée
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox" checked> Alertes en temps réel
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox"> Leurres automatiques
                            </label>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" id="cancel-deploy">Annuler</button>
                <button class="btn btn-primary" id="confirm-deploy">Déployer</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Gestion des événements de la modale
    modal.querySelector('.modal-close-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
    });

    modal.querySelector('#cancel-deploy').addEventListener('click', () => {
        document.body.removeChild(modal);
    });

    modal.querySelector('#confirm-deploy').addEventListener('click', () => {
        const name = document.getElementById('honeypot-name').value;
        const location = document.getElementById('honeypot-location').value;

        // Simuler un déploiement
        showNotification('Déploiement en cours...', 'info');

        // Dans une application réelle, cela enverrait une requête au serveur
        setTimeout(() => {
            document.body.removeChild(modal);
            showNotification(`Honeypot ${name} déployé avec succès!`, 'success');
            // Recharger la liste des honeypots
            loadHoneypotStatus();
        }, 1500);
    });
}

/**
 * Demande confirmation avant d'arrêter un honeypot
 */
function confirmStopHoneypot(honeypotId) {
    if (confirm('Êtes-vous sûr de vouloir arrêter ce honeypot?')) {
        // Simuler l'arrêt
        showNotification('Arrêt du honeypot en cours...', 'info');

        // Dans une application réelle, cela enverrait une requête au serveur
        setTimeout(() => {
            showNotification('Honeypot arrêté avec succès', 'success');
            // Mettre à jour l'interface
            const statusElement = document.querySelector(`[data-honeypot-id="${honeypotId}"] .status-indicator`);
            if (statusElement) {
                statusElement.className = 'status-indicator status-offline';
                statusElement.innerHTML = '<span class="status-dot"></span> Hors ligne';
            }
        }, 1000);
    }
}

/**
 * Charge l'état des honeypots (simulé)
 */
function loadHoneypotStatus() {
    const honeypotList = document.getElementById('honeypot-list');
    if (!honeypotList) return;

    // Dans une application réelle, ces données proviendraient d'une API
    const honeypots = [
        { id: 1, name: 'Web-Honeypot-1', type: 'Web Server', status: 'online', alerts: 12, uptime: '3j 7h' },
        { id: 2, name: 'SSH-Trap', type: 'SSH', status: 'online', alerts: 5, uptime: '1j 15h' },
        { id: 3, name: 'FTP-Decoy', type: 'FTP', status: 'offline', alerts: 0, uptime: '0' }
    ];

    // Générer le HTML pour chaque honeypot
    let html = '';
    honeypots.forEach(hp => {
        const statusClass = hp.status === 'online' ? 'status-online' : 'status-offline';
        const statusText = hp.status === 'online' ? 'En ligne' : 'Hors ligne';

        html += `
            <div class="honeypot-card card" data-honeypot-id="${hp.id}">
                <div class="card-header">
                    <h3 class="card-title">${hp.name}</h3>
                    <div class="status-indicator ${statusClass}">
                        <span class="status-dot"></span>
                        ${statusText}
                    </div>
                </div>
                <div class="card-body">
                    <div class="honeypot-details">
                        <div class="detail-item">
                            <span class="detail-label">Type:</span>
                            <span class="detail-value">${hp.type}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Alertes:</span>
                            <span class="detail-value">${hp.alerts}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Temps d'activité:</span>
                            <span class="detail-value">${hp.uptime}</span>
                        </div>
                    </div>
                </div>
                <div class="card-footer">
                    <button class="btn btn-secondary btn-sm view-logs-btn" data-id="${hp.id}">Manager</button>
                    ${hp.status === 'online' ? 
                        `<button class="btn btn-danger btn-sm stop-honeypot-btn" data-id="${hp.id}">Arrêter</button>` : 
                        `<button class="btn btn-primary btn-sm restart-honeypot-btn" data-id="${hp.id}">Redémarrer</button>`
                    }
                </div>
            </div>
        `;
    });

    honeypotList.innerHTML = html;

    // Réattacher les écouteurs d'événements pour les nouveaux boutons
    setupEventListeners();
}

/**
 * Affiche une notification à l'utilisateur
 */
function showNotification(message, type = 'info') {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
        </div>
        <button class="notification-close">&times;</button>
    `;

    // Ajouter au conteneur de notifications ou au body
    const container = document.getElementById('notification-container') || document.body;
    container.appendChild(notification);

    // Configurer la fermeture automatique
    setTimeout(() => {
        notification.classList.add('notification-hiding');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);

    // Configurer le bouton de fermeture
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.classList.add('notification-hiding');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    });
}