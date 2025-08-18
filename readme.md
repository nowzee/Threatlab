# Threatlab — Plateforme de gestion de honeypots

Threatlab est une plateforme centralisée pour déployer, superviser et orchestrer des honeypots. Elle collecte les événements d’attaque en temps réel, fournit un tableau de bord pour l’analyse, et s’intègre de manière modulaire avec des systèmes externes d’ingestion et de CTI (ELK/Elastic, OpenCTI, etc.).

- Supervision des honeypots (état, type, volume d’alertes)
- Collecte d’alertes et événements d’attaque
- Authentification avec session et second facteur (A2F) côté application
- Architecture modulaire pensée pour l’export des données (ELK, OpenCTI…)
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

## 🚀 Démarrage rapide (développement)

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

Astuce: En développement, vous pouvez lancer le frontend en mode dev (hot reload) et configurer un proxy vers l’API Flask si nécessaire.

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

Recommandations:
- Générer une SECRET_KEY robuste en production
- Utiliser des variables d’environnement et un store de secrets sécurisé
- Protéger l’accès en amont (WAF/Reverse proxy, TLS)

---

## 🔌 Intégrations (ELK / OpenCTI)

Le modèle d’intégration repose sur des connecteurs modulaires:
- Mapping des événements (timestamp, type d’attaque, honeypot/source, sévérité, IP source, etc.)
- Envoi vers:
  - ELK: indexation pour dashboards Kibana et corrélations
  - OpenCTI: enrichissement des IOC et partage CTI

Bonnes pratiques:
- Définir une taxonomie d’alertes (type, sévérité)
- Normaliser les champs (IP source, geoloc, signatures)
- Utiliser des files/bus (ex: Kafka, Redis Streams) si le volume augmente

---

## 🧩 API (aperçu)

Endpoints disponibles pour l’interface et l’écosystème:
- GET /api/honeypots
  - Retourne la liste des honeypots et leur statut
- GET /api/alerts
  - Retourne les dernières alertes collectées
---

## 🧭 Roadmap

- Connecteurs officiels ELK et OpenCTI (stabilisées, avec configuration UI)
- Normalisation avancée des événements (ECS, STIX 2.1)
- Système d’agents/honeypots déployables à la demande
- Règles de détection, scoring et corrélations
- Webhooks et intégrations SIEM supplémentaires

---

## 📬 Support & contact

- Ouvrez une issue pour les bugs et demandes de fonctionnalités
---

## 📝 Licence

Ce projet est sous licence [MIT](LICENSE).

## Me

Développé avec ❤️ by Insomnia