# Architecture de Threatlab

Cette documentation présente l'architecture globale de l'application et les principes de conception retenus.

---

## 1) Vue d'ensemble

Threatlab est une plateforme centrale de supervision et d'orchestration d'honeypots. Elle collecte les événements d'attaque (bruteforce SSH, interactions SMTP, etc.), les normalise et les rend disponibles via un tableau de bord web (SPA) et des API. L'architecture sépare clairement:
- Le frontend (SPA Vue) livré en statique par le backend.
- Le backend (Flask) exposant les endpoints REST et gérant la logique métier, l'authentification et l'accès aux données.
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
  - virtualenv pour l'environnement Python
  - npm pour la partie frontend

---

## 3) Architecture logique

- Présentation (Frontend SPA):
  - Application Vue unique, routage côté client (Vue Router).
  - Les routes front sont toutes servies par le backend sur le même host (pour simplifier le déploiement).
  - State management avec Pinia pour le tableau de bord (honeypots, alertes, état de session).

- API Backend (Flask):
  - Entrée unique de l'application avec configuration du SECRET_KEY et du chemin de base de données.
  - Blueprints:
    - Authentification/Session (auth_bp): gestion de session, login, état de session, flux A2F.
    - Configuration sécurité (config_account_bp): gestion des paramètres de sécurité du compte.
    - Agent (agent_create_bp): génération de clé agent et collecte des rapports d'attaque.
  - Middlewares:
    - before_request: contrôle d'accès par session, liste d'endpoints publics, blocage conditionnel si l'A2F n'est pas validée.

- Persistance:
  - Initialisation de la base si absente (création des répertoires et schémas via DatabaseManagerUser et DatabaseManagerHoneypot).
  - Séparation logique des données "utilisateurs/sessions" et "événements honeypot".
  - Pour la partie honeypot/agents, stockage des:
    - Agents et tokens,
    - IP malveillantes observées,
    - Journaux d'attaque normalisés,
    - Données spécifiques par service (ex. SSH: credentials compromis; SMTP: interactions, pièces jointes).

- Servir le Frontend:
  - Route racine "/" et fallback "/<path>" renvoient index.html pour supporter le routage SPA.

---

## 4) Flux d'exécution (request lifecycle)

1) L'utilisateur ou l'agent effectue une requête HTTP vers le backend.
2) Le middleware before_request évalue:
   - Si la route est publique ou non.
   - Si la session est connectée (logged_in).
   - Si l'A2F est requise et validée.
3) Si autorisée, la requête est routée vers le blueprint cible.
4) La logique métier opère (validation des champs, écriture BDD, agrégation).
5) Réponse JSON pour l'API ou renvoi des assets front pour l'interface.

Les endpoints d'agent sont explicitement publics pour permettre la remontée de données depuis des honeypots déployés et non authentifiés via session web.

---

## 5) Sécurité

- SECRET_KEY:
  - Clé robuste générée au démarrage de l'application (utilisée pour sessions et signatures).
- Sessions:
  - Basées serveur, contrôlées au middleware (avant chaque requête).
- A2F (second facteur):
  - Contrôle fin via before_request: certaines routes exigent l'A2F validée.
- Accès public contrôlé:
  - Les paths d'agent (création de token, rapport d'attaque) sont publics par design pour ingestion.
- Génération de clé agent:
  - Clé dérivée d'éléments aléatoires, timestamp et SECRET_KEY, hachée (SHA-256) et préfixée.
- Bonnes pratiques recommandées:
  - Terminer en HTTPS derrière un reverse proxy.
  - Ajouter un contrôle d'origine/whitelist si agents gérés.
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
  - Observations d'IP source, type de service attaqué, géolocalisation (code, pays), classification.
- Journaux d'attaque (normalisés):
  - Référencent l'agent, la source, le service, les ports, les tentatives d'identifiants, hash de malware, payloads.
- Détails spécifiques:
  - SSH: username/password compromis.
  - SMTP: expéditeur, destinataire, sujet, corps, pièces jointes.

---

## 7) Conception et principes

- Séparation des responsabilités:
  - Blueprints thématiques (auth, config, agents) pour isoler les domaines.
  - Gestionnaires de base (DatabaseManagerUser/Honeypot) cloisonnant la logique de persistance.
- Normalisation des événements:
  - Payloads d'attaque ramenés à une structure commune, puis enrichissement par service.
- Ouverture à l'ingestion:
  - Endpoints publics d'ingestion pour faciliter le déploiement d'agents distribués.
- Extensibilité:
  - Ajout de nouveaux services (ex. RDP, HTTP) en dupliquant le pattern de traitement dans le endpoint de report.
  - Connecteurs externes (ELK/OpenCTI) branchables sur la couche de persistance via workers/exporters.
- Observabilité:
  - Messages d'erreur JSON explicites; journalisation côté serveur.
- Sécurité progressive:
  - Design permettant d'ajouter facilement HMAC/token par agent, filtrage IP, rate limiting.
