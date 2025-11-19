<script lang="ts">
import { defineComponent } from 'vue'
import { useRouter } from 'vue-router'

export default defineComponent({
  name: "deploy",
  setup() {
    const router = useRouter()

    const deployHoneypot = (type: string) => {
      if (type === 'SSH') {
        router.push({ name: 'ssh-agent-creation' })
      } else if (type === 'FTP') {
        router.push({ name: 'ftp-agent-creation' })
      }
    }

    return {
      deployHoneypot
    }
  }
})
</script>

<template>
  <div class="content-wrapper">
    <h1 class="page-title">
        Déployer un Honeypot
    </h1>

    <!-- Options de déploiement -->
    <div class="grid-container">

        <!-- SSH Honeypot -->
        <div class="honeypot-template card">
            <div class="card-header">
                <h3 class="card-title">SSH</h3>
                <span class="badge badge-warning">Avancé</span>
            </div>
            <div class="card-body">
                <div class="template-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="3" y1="9" x2="21" y2="9"></line>
                        <line x1="9" y1="21" x2="9" y2="9"></line>
                    </svg>
                </div>
                <div class="template-description">
                    <p>Émule un serveur SSH pour capturer les tentatives d'accès non autorisées et les commandes exécutées.</p>
                    <ul class="feature-list">
                        <li>Capture des identifiants</li>
                        <li>Journalisation des commandes</li>
                        <li>Émulation de système de fichiers</li>
                    </ul>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary deploy-honeypot-btn" @click="deployHoneypot('SSH')">Déployer</button>
                <button class="btn btn-secondary">Détails</button>
            </div>
        </div>

              <!-- FTP Honeypot -->
        <div class="honeypot-template card">
            <div class="card-header">
                <h3 class="card-title">FTP</h3>
            </div>
            <div class="card-body">
                <div class="template-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"></path>
                        <polyline points="7 9 12 4 17 9"></polyline>
                        <line x1="12" y1="4" x2="12" y2="16"></line>
                    </svg>
                </div>
                <div class="template-description">
                    <p>Simule un serveur FTP avec des vulnérabilités pour surveiller les tentatives d'accès et de téléchargement.</p>
                    <ul class="feature-list">
                        <li>Capture des identifiants</li>
                        <li>Surveillance des téléchargements</li>
                        <li>Analyse des fichiers malveillants</li>
                    </ul>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary deploy-honeypot-btn" @click="deployHoneypot('FTP')">Déployer</button>
                <button class="btn btn-secondary">Détails</button>
            </div>
        </div>

        <!-- Web Server Honeypot -->
        <div class="honeypot-template card">
            <div class="card-header">
                <h3 class="card-title">Serveur Web</h3>
                <span class="badge badge-primary">Populaire</span>
            </div>
            <div class="card-body">
                <div class="template-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                        <line x1="8" y1="21" x2="16" y2="21"></line>
                        <line x1="12" y1="17" x2="12" y2="21"></line>
                    </svg>
                </div>
                <div class="template-description">
                    <p>Simule un serveur web avec des vulnérabilités connues pour détecter les tentatives d'exploitation.</p>
                    <ul class="feature-list">
                        <li>Détection de SQL Injection</li>
                        <li>Détection de XSS</li>
                        <li>Surveillance des tentatives de brute force</li>
                    </ul>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary deploy-honeypot-btn" data-type="Web Server">Déployer</button>
                <button class="btn btn-secondary">Détails</button>
            </div>
        </div>

        <!-- SMTP Honeypot -->
        <div class="honeypot-template card">
            <div class="card-header">
                <h3 class="card-title">SMTP</h3>
            </div>
            <div class="card-body">
                <div class="template-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                        <polyline points="22,6 12,13 2,6"></polyline>
                    </svg>
                </div>
                <div class="template-description">
                    <p>Émule un serveur de messagerie pour capturer les tentatives de spam et de phishing.</p>
                    <ul class="feature-list">
                        <li>Détection de spam</li>
                        <li>Analyse des pièces jointes</li>
                        <li>Suivi des campagnes de phishing</li>
                    </ul>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary deploy-honeypot-btn" data-type="SMTP">Déployer</button>
                <button class="btn btn-secondary">Détails</button>
            </div>
        </div>

        <!-- IoT Honeypot -->
        <div class="honeypot-template card">
            <div class="card-header">
                <h3 class="card-title">IoT</h3>
                <span class="badge badge-info">Nouveau</span>
            </div>
            <div class="card-body">
                <div class="template-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                        <path d="M16 2v5"></path>
                        <path d="M8 2v5"></path>
                        <path d="M9 16H4"></path>
                        <path d="M20 16h-5"></path>
                        <path d="M12 7v9"></path>
                    </svg>
                </div>
                <div class="template-description">
                    <p>Émule des appareils IoT vulnérables pour détecter les botnets et autres menaces ciblant l'IoT.</p>
                    <ul class="feature-list">
                        <li>Émulation de caméras IP</li>
                        <li>Émulation de routeurs</li>
                        <li>Détection de Mirai et autres botnets</li>
                    </ul>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary deploy-honeypot-btn" data-type="IoT">Déployer</button>
                <button class="btn btn-secondary">Détails</button>
            </div>
        </div>

        <!-- LLM Honeypot -->
        <div class="honeypot-template card">
            <div class="card-header">
                <h3 class="card-title">LLM</h3>
                <span class="badge badge-warning">Avancé</span>
            </div>
            <div class="card-body">
                <div class="template-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="3" y1="9" x2="21" y2="9"></line>
                        <line x1="9" y1="21" x2="9" y2="9"></line>
                    </svg>
                </div>
                <div class="template-description">
                    <p>Émule un serveur llm pour détecter les types d'attaque réalisé sur les llm vulnérables</p>
                    <ul class="feature-list">
                        <li>Capture des payloads</li>
                        <li>Journalisation</li>
                        <li>Émulation d'application</li>
                    </ul>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary deploy-honeypot-btn" data-type="SSH">Déployer</button>
                <button class="btn btn-secondary">Détails</button>
            </div>
        </div>

        <!-- Custom Honeypot -->
        <div class="honeypot-template card">
            <div class="card-header">
                <h3 class="card-title">Personnalisé</h3>
                <span class="badge badge-danger">Expert</span>
            </div>
            <div class="card-body">
                <div class="template-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7m0-18H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h7m0-18v18"></path>
                    </svg>
                </div>
                <div class="template-description">
                    <p>Créez un honeypot personnalisé avec des services et des vulnérabilités spécifiques.</p>
                    <ul class="feature-list">
                        <li>Choix de services multiples</li>
                        <li>Configurations avancées</li>
                        <li>Scripts personnalisés</li>
                    </ul>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary deploy-honeypot-btn" data-type="Custom">Déployer</button>
                <button class="btn btn-secondary">Détails</button>
            </div>
        </div>
    </div>

    <!-- Informations sur le déploiement -->
    <div class="section-card">
        <div class="card-header" style="padding: 0 0 16px 0; margin-bottom: 16px;">
            <h3 class="card-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                Guide de déploiement
            </h3>
        </div>

        <div class="deployment-guide">
            <div class="deployment-step">
                <div class="step-number">1</div>
                <div class="step-content">
                    <h4>Choisir un type de honeypot</h4>
                    <p>Sélectionnez le type de honeypot qui correspond le mieux à vos besoins de surveillance et à vos objectifs de sécurité.</p>
                </div>
            </div>

            <div class="deployment-step">
                <div class="step-number">2</div>
                <div class="step-content">
                    <h4>Configurer les paramètres</h4>
                    <p>Définissez un nom, un emplacement et des options spécifiques pour votre honeypot dans la fenêtre de configuration.</p>
                </div>
            </div>

            <div class="deployment-step">
                <div class="step-number">3</div>
                <div class="step-content">
                    <h4>Déployer</h4>
                    <p>Lancez le déploiement et attendez que le système configure et démarre le honeypot.</p>
                </div>
            </div>

            <div class="deployment-step">
                <div class="step-number">4</div>
                <div class="step-content">
                    <h4>Surveiller</h4>
                    <p>Une fois déployé, vous pouvez surveiller l'activité et les alertes depuis le tableau de bord principal.</p>
                </div>
            </div>
        </div>
    </div>
</div>

  <!-- Conteneur pour les notifications -->
  <div id="notification-container"></div>

</template>

<style scoped>
    /* Styles spécifiques à la page de déploiement */
    .honeypot-template {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    .template-icon {
        background-color: rgba(0, 200, 255, 0.1);
        width: 64px;
        height: 64px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
    }

    .template-description {
        flex: 1;
    }

    .template-description p {
        color: var(--text-color);
        margin-bottom: 16px;
        font-size: 14px;
        line-height: 1.5;
    }

    .feature-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .feature-list li {
        padding: 4px 0;
        color: var(--text-color-muted);
        font-size: 13px;
        display: flex;
        align-items: center;
    }

    .feature-list li::before {
        content: "✓";
        margin-right: 8px;
        color: var(--accent-color);
        font-weight: bold;
    }

    .card-footer {
        margin-top: auto;
        display: flex;
        gap: 8px;
    }

    /* Styles pour le guide de déploiement */
    .deployment-guide {
        display: flex;
        flex-direction: column;
        gap: 24px;
    }

    .deployment-step {
        display: flex;
        gap: 16px;
    }

    .step-number {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: var(--accent-color);
        color: var(--white);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        flex-shrink: 0;
    }

    .step-content {
        flex: 1;
    }

    .step-content h4 {
        margin: 0 0 8px 0;
        color: var(--white);
        font-size: 16px;
        font-weight: 600;
    }

    .step-content p {
        margin: 0;
        color: var(--text-color-muted);
        font-size: 14px;
        line-height: 1.5;
    }
</style>