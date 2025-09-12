<script lang="ts">
import {defineComponent} from 'vue'

export default defineComponent({
  name: "home"
})
</script>

<template>
<div class="content-wrapper">
    <h1 class="page-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
        </svg>
        Tableau de bord
    </h1>

    <!-- Résumé statistique -->
    <div class="grid-container">
        <div class="card">
            <div class="card-body">
                <div class="stat-card">
                    <div class="stat-icon" style="color: var(--accent-color);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                            <line x1="12" y1="19" x2="12" y2="22"></line>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">3</div>
                        <div class="stat-label">Honeypots actifs</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-body">
                <div class="stat-card">
                    <div class="stat-icon" style="color: var(--warning-color);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">89</div>
                        <div class="stat-label">Tentatives d'accès</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-body">
                <div class="stat-card">
                    <div class="stat-icon" style="color: var(--success-color);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 7h-9"></path>
                            <path d="M14 17H5"></path>
                            <circle cx="17" cy="17" r="3"></circle>
                            <circle cx="7" cy="7" r="3"></circle>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">12</div>
                        <div class="stat-label">IP collectées</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-body">
                <div class="stat-card">
                    <div class="stat-icon" style="color: var(--danger-color);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 7h-9"></path>
                            <path d="M14 17H5"></path>
                            <circle cx="17" cy="17" r="3"></circle>
                            <circle cx="7" cy="7" r="3"></circle>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">14</div>
                        <div class="stat-label">Samples téléchargés</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Liste des honeypots -->
    <div class="section-card" style="margin-top: 1.5%;">
        <div class="card-header" style="padding: 0 0 16px 0; margin-bottom: 16px;">
            <h3 class="card-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 11V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"></path>
                    <path d="M12 16H7"></path>
                    <path d="M12 12H7"></path>
                    <path d="M12 8H7"></path>
                    <path d="M16 16v6"></path>
                    <path d="M19 19l-3-3-3 3"></path>
                </svg>
                Honeypots déployés
            </h3>
            <button class="btn btn-primary btn-sm">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                Nouveau honeypot
            </button>
        </div>

        <div id="honeypot-list" class="grid-container">
            <!-- Contenu généré dynamiquement par le script -->
        </div>
    </div>

    <!-- Alertes récentes -->
    <div class="section-card">
        <div class="card-header" style="padding: 0 0 16px 0; margin-bottom: 16px;">
            <h3 class="card-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                Alertes récentes
            </h3>
            <a href="#" class="view-all-link">Voir tout</a>
        </div>

        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Honeypot</th>
                        <th>Type d'attaque</th>
                        <th>IP Source</th>
                        <th>Sévérité</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>2023-07-10 15:42</td>
                        <td>Web-Honeypot-1</td>
                        <td>SQL Injection</td>
                        <td>198.51.100.32</td>
                        <td><span class="badge badge-danger">Élevée</span></td>
                        <td><button class="btn btn-sm btn-secondary">Détails</button></td>
                    </tr>
                    <tr>
                        <td>2023-07-10 14:28</td>
                        <td>SSH-Trap</td>
                        <td>Brute Force</td>
                        <td>203.0.113.45</td>
                        <td><span class="badge badge-warning">Moyenne</span></td>
                        <td><button class="btn btn-sm btn-secondary">Détails</button></td>
                    </tr>
                    <tr>
                        <td>2023-07-10 12:15</td>
                        <td>Web-Honeypot-1</td>
                        <td>XSS</td>
                        <td>192.0.2.18</td>
                        <td><span class="badge badge-warning">Moyenne</span></td>
                        <td><button class="btn btn-sm btn-secondary">Détails</button></td>
                    </tr>
                    <tr>
                        <td>2023-07-09 23:51</td>
                        <td>FTP-Decoy</td>
                        <td>Directory Traversal</td>
                        <td>203.0.113.112</td>
                        <td><span class="badge badge-info">Faible</span></td>
                        <td><button class="btn btn-sm btn-secondary">Détails</button></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Conteneur pour les notifications -->
<div id="notification-container"></div>
</template>

<style src="@/assets/css/dashboard/notifications.css"></style>
<style>
    /* Styles spécifiques à la page dashboard */
    .stat-card {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .stat-icon {
        width: 48px;
        height: 48px;
        background-color: rgba(0, 0, 0, 0.2);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .stat-content {
        flex: 1;
    }

    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--white);
        margin-bottom: 4px;
    }

    .stat-label {
        font-size: 14px;
        color: var(--text-color-muted);
    }

    .view-all-link {
        color: var(--accent-color);
        font-size: 14px;
        text-decoration: none;
        font-weight: 500;
    }

    .view-all-link:hover {
        text-decoration: underline;
    }

    .honeypot-details {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .detail-item {
        display: flex;
        justify-content: space-between;
    }

    .detail-label {
        color: var(--text-color-muted);
        font-size: 14px;
    }

    .detail-value {
        color: var(--text-color);
        font-size: 14px;
        font-weight: 500;
    }

    .threat-item {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
    }

    .threat-label {
        width: 100px;
        font-size: 14px;
        color: var(--text-color);
    }

    .threat-bar-container {
        flex: 1;
        height: 8px;
        background-color: var(--container-background-lighter);
        border-radius: 4px;
        overflow: hidden;
        margin: 0 10px;
    }

    .threat-bar {
        height: 100%;
        background-color: var(--accent-color);
        border-radius: 4px;
    }

    .threat-value {
        width: 40px;
        font-size: 14px;
        color: var(--text-color-muted);
        text-align: right;
    }

    .card-actions {
        display: flex;
        gap: 8px;
    }
</style>