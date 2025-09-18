# Threatlab
![Status](https://img.shields.io/badge/Status-In_Development-purple.svg)

![image_banner](https://github.com/user-attachments/assets/4721f90b-7ea8-486c-a294-47e80a87ac41)

Threatlab est une plateforme centralisée pour déployer, superviser et orchestrer des honeypots. Elle collecte les événements d’attaque en temps réel, fournit un tableau de bord pour l’analyse, et s’intègre de manière modulaire avec des systèmes externes d’ingestion et de CTI (ELK/Elastic, OpenCTI, etc.).

- Supervision des honeypots (état, type, volume d’alertes)
- Collecte d’alertes et événements d’attaque et samples
- Architecture modulaire pensée pour l’export des données (ELK, OpenCTI)
---

## Fonctionnalité

- Gestion des honeypots
  - Vue d’ensemble des instances (nom, type, statut, niveau d’activité)
  - Vision rapide des alertes récentes
- Collecte & alerting
  - Exposition d’API pour récupérer les événements (simulation par défaut pour le développement)
  - Normalisation des payloads pour faciliter l’export
- Intégrations
  - Connecteurs prévus pour:
    - ELK / Elastic (Ingest pipelines / Indexation)
    - OpenCTI (enrichissement et contextualisation des IOC)
  - Architecture extensible pour d’autres bus et SIEM
- Sécurité
  - Sessions serveur
  - Flux A2F (deuxième facteur) sur les routes sensibles
- UX / UI
  - SPA moderne (Vue) servie par le backend pour une intégration simple

---

## Installation

Prérequis:
- Python 3.10+
- Node.js et npm (pour builder le frontend)
- Accès internet pour installer les dépendances

Étapes:
1) Cloner le dépôt, puis builder le frontend
   - Se placer dans le dossier frontend
   - Installer les dépendances npm
   - Builder les assets de production
   - Le build génère un dossier dist servi par le backend

2) Lancer le backend Flask
   - Exporter au besoin les variables d’environnement (voir Configuration)
   - Lancer l’application
   - Accéder à l’interface via http://localhost:5000

Exemple de commandes (adaptées à votre environnement):
- Frontend:
  - cd frontend
  - npm install
  - npm run build
- Backend:
  - cd ..
  - python app.py
---

## ⚙️ Configuration

Variables et paramètres utiles (exemples):
- SECRET_KEY: clé secrète pour les sessions côté Flask
- DATABASE: chemin de la base (ex: ./honeypot.db)
- Intégrations (à adapter selon vos connecteurs):
  - ELK/Elastic:
    - ELASTIC_URL, ELASTIC_API_KEY, ELASTIC_INDEX, ELASTIC_PIPELINE
  - OpenCTI:
    - OPENCTI_URL, OPENCTI_TOKEN, OPENCTI_ORG
---

## 🔌 Intégrations (ELK / OpenCTI)

Le modèle d’intégration repose sur des connecteurs modulaires:
- Mapping des événements (timestamp, type d’attaque, honeypot/source, sévérité, IP source, etc.)
- Envoi vers:
  - ELK: indexation pour dashboards Kibana et corrélations
  - OpenCTI: enrichissement des IOC et partage CTI
---

# Documentation d’architecture, de conception et des endpoints

Cette documentation présente l’architecture globale de l’application, les principes de conception retenus, et la spécification des endpoints exposés par l’API. Elle couvre également les technologies utilisées, la base de données et les aspects de sécurité et d’extensibilité.

---

## 1) Vue d’ensemble

Threatlab est une plateforme centrale de supervision et d’orchestration d’honeypots. Elle collecte les événements d’attaque (bruteforce SSH, interactions SMTP, etc.), les normalise et les rend disponibles via un tableau de bord web (SPA) et des API. L’architecture sépare clairement:
- Le frontend (SPA Vue) livré en statique par le backend.
- Le backend (Flask) exposant les endpoints REST et gérant la logique métier, l’authentification et l’accès aux données.
- La couche de persistance (base locale) pilotée par des gestionnaires de BDD dédiés.

---

## 2) Technologies

- Backend:
  - Python 3 (Flask, Jinja2, Werkzeug)
  - Architecture par Blueprints pour modulariser les domaines (auth, configuration, agent)
- Frontend:
  - Vue 3, Vite, Vue Router, Pinia, TypeScript
  - Build en assets statiques dans frontend/dist, servis par Flask
- Base de données:
  - Base locale stockée dans le répertoire db
  - Gestion assurée par des gestionnaires dédiés (création et accès via DatabaseManagerUser et DatabaseManagerHoneypot)
- Outils:
  - virtualenv pour l’environnement Python
  - npm pour la partie frontend

---

## 3) Architecture logique

- Présentation (Frontend SPA):
  - Application Vue unique, routage côté client (Vue Router).
  - Les routes front sont toutes servies par le backend sur le même host (pour simplifier le déploiement).
  - State management avec Pinia pour le tableau de bord (honeypots, alertes, état de session).

- API Backend (Flask):
  - Entrée unique de l’application avec configuration du SECRET_KEY et du chemin de base de données.
  - Blueprints:
    - Authentification/Session (auth_bp): gestion de session, login, état de session, flux A2F.
    - Configuration sécurité (config_account_bp): gestion des paramètres de sécurité du compte.
    - Agent (agent_create_bp): génération de clé agent et collecte des rapports d’attaque.
  - Middlewares:
    - before_request: contrôle d’accès par session, liste d’endpoints publics, blocage conditionnel si l’A2F n’est pas validée.

- Persistance:
  - Initialisation de la base si absente (création des répertoires et schémas via DatabaseManagerUser et DatabaseManagerHoneypot).
  - Séparation logique des données “utilisateurs/sessions” et “événements honeypot”.
  - Pour la partie honeypot/agents, stockage des:
    - Agents et tokens,
    - IP malveillantes observées,
    - Journaux d’attaque normalisés,
    - Données spécifiques par service (ex. SSH: credentials compromis; SMTP: interactions, pièces jointes).

- Servir le Frontend:
  - Route racine “/” et fallback “/<path>” renvoient index.html pour supporter le routage SPA.

---

## 4) Flux d’exécution (request lifecycle)

1) L’utilisateur ou l’agent effectue une requête HTTP vers le backend.
2) Le middleware before_request évalue:
   - Si la route est publique ou non.
   - Si la session est connectée (logged_in).
   - Si l’A2F est requise et validée.
3) Si autorisée, la requête est routée vers le blueprint cible.
4) La logique métier opère (validation des champs, écriture BDD, agrégation).
5) Réponse JSON pour l’API ou renvoi des assets front pour l’interface.

Les endpoints d’agent sont explicitement publics pour permettre la remontée de données depuis des honeypots déployés et non authentifiés via session web.

---

## 5) Sécurité

- SECRET_KEY:
  - Clé robuste générée au démarrage de l’application (utilisée pour sessions et signatures).
- Sessions:
  - Basées serveur, contrôlées au middleware (avant chaque requête).
- A2F (second facteur):
  - Contrôle fin via before_request: certaines routes exigent l’A2F validée.
- Accès public contrôlé:
  - Les paths d’agent (création de token, rapport d’attaque) sont publics par design pour ingestion.
- Génération de clé agent:
  - Clé dérivée d’éléments aléatoires, timestamp et SECRET_KEY, hachée (SHA-256) et préfixée.
- Bonnes pratiques recommandées:
  - Terminer en HTTPS derrière un reverse proxy.
  - Ajouter un contrôle d’origine/whitelist si agents gérés.
  - Ajouter throttling/rate limiting et signature HMAC ou token par agent pour /agent/report en production.
  - Journaliser et tracer les erreurs côté serveur.

---

## 6) Modèle de données (vue conceptuelle)

Sans détailler le schéma exact, la couche de persistance couvre ces entités logiques:
- Utilisateurs:
  - Comptes, hachage de mot de passe, empreintes A2F, paramètres sécurité.
- Agents:
  - Enregistrement des agents et de leur secret_token.
- IP malveillantes:
  - Observations d’IP source, type de service attaqué, géolocalisation (code, pays), classification.
- Journaux d’attaque (normalisés):
  - Référencent l’agent, la source, le service, les ports, les tentatives d’identifiants, hash de malware, payloads.
- Détails spécifiques:
  - SSH: username/password compromis.
  - SMTP: expéditeur, destinataire, sujet, corps, pièces jointes.

---

## 7) Endpoints et contrats

Tous les chemins API sont préfixés par /api lorsque portés par le blueprint agent, et par la racine /api pour certaines routes de démonstration.

1) POST /api/agent/create
   - Description: Génère un token secret d’agent et l’enregistre en base.
   - Authentification: Non (endpoint public).
   - Corps JSON:
     - agent_name: string (optionnel mais conseillé pour traçabilité).
   - Réponses:
     - 200: { success: true, secret_token: string }
     - 500: { success: false }
   - Remarques:
     - Le token retourné est à stocker côté agent et utilisé à terme pour signer ou authentifier ses rapports.

2) POST /api/agent/report
   - Description: Remontée d’un événement d’attaque par un agent. Normalise et persiste les données.
   - Authentification: Non (endpoint public), mais à durcir en production.
   - Corps JSON (minimum requis):
     - source_ip: string (requis)
     - service_type: string (requis; ex: "ssh" ou "smtp")
   - Corps JSON (champs supportés selon service):
     - Champs généraux:
       - agent_id: string
       - source_port: int
       - target_port: int
       - username_attempt: string
       - password_attempt: string
       - payload: string | objet
       - malware_hash: string
       - classification: string
       - country_code: string
       - country_name: string
     - Spécifique SSH:
       - username_attempt, password_attempt: si présents, enregistrés comme credentials compromis.
     - Spécifique SMTP:
       - sender_email: string
       - recipient_email: string
       - subject: string
       - message_content: string
       - attachments: liste d’objets ou métadonnées de pièces jointes
   - Réponses:
     - 200: { success: true, message: "<SERVICE> attack data processed successfully" }
     - 400: { success: false, error: "Missing required field: <...>" }
     - 500: { success: false, error: "<message>" }
   - Effets côté persistance:
     - Ajoute l’IP malveillante observée.
     - Ajoute un journal d’attaque normalisé.
     - Ajoute des détails spécifiques selon le type de service (SSH/SMTP).

3) GET /api/honeypots
   - Description: Renvoyé pour la vue d’ensemble des honeypots (actuellement simulé).
   - Authentification: Oui (middleware de session), mais listée dans les publics selon la configuration actuelle d’accès via SPA.
   - Réponse: { honeypots: [...] }

4) GET /api/alerts
   - Description: Renvoyé pour l’onglet d’alertes (actuellement simulé).
   - Authentification: Oui (middleware de session), mais accessible via l’interface SPA.
   - Réponse: { alerts: [...] }

5) Frontend SPA et static
   - GET /: renvoie index.html du build frontend.
   - GET/POST /<path>: fallback pour permettre le routage côté client (Vue Router).
   - 404/500: gestionnaires renvoyant des templates d’erreur.

Remarques sur l’authentification et l’A2F:
- Le middleware before_request liste explicitement des endpoints publics (notamment les routes agent). Les autres routes nécessitent une session valide, et potentiellement l’A2F validée.
- Les endpoints d’authentification existent via un blueprint “auth”, incluant typiquement:
  - login
  - session_state
  - a2f
  (Les détails exacts des chemins et payloads dépendront de l’implémentation de ce module.)

---

## 8) Conception et principes

- Séparation des responsabilités:
  - Blueprints thématiques (auth, config, agents) pour isoler les domaines.
  - Gestionnaires de base (DatabaseManagerUser/Honeypot) cloisonnant la logique de persistance.
- Normalisation des événements:
  - Payloads d’attaque ramenés à une structure commune, puis enrichissement par service.
- Ouverture à l’ingestion:
  - Endpoints publics d’ingestion pour faciliter le déploiement d’agents distribués.
- Extensibilité:
  - Ajout de nouveaux services (ex. RDP, HTTP) en dupliquant le pattern de traitement dans le endpoint de report.
  - Connecteurs externes (ELK/OpenCTI) branchables sur la couche de persistance via workers/exporters.
- Observabilité:
  - Messages d’erreur JSON explicites; journalisation côté serveur.
- Sécurité progressive:
  - Design permettant d’ajouter facilement HMAC/token par agent, filtrage IP, rate limiting.

---
## 📝 Licence

Ce projet est sous licence [MIT](LICENSE).

## Me

Dev with ❤️ by Insomnia
