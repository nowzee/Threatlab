# Dossier BTS - Diagrammes PlantUML ThreatLab

Ce dossier contient l'ensemble des diagrammes PlantUML documentant le projet **ThreatLab** (plateforme centralisée de gestion de honeypots et de threat intelligence).

## Comment générer les images

- **En ligne** : copier-coller le contenu `.puml` sur https://www.plantuml.com/plantuml
- **VS Code** : extension *PlantUML* (prévisualisation `Alt+D`)
- **CLI** :
  ```bash
  plantuml docs/bts/*.puml
  ```

---

## 1. Architecture globale — `01_architecture_globale.puml`

**Type** : diagramme de composants
**Objectif** : vue d'ensemble des briques logicielles et de leurs interactions.

**Texte à placer sous le schéma :**
> ThreatLab repose sur une architecture 3-tiers conteneurisée. Le **frontend Vue 3** (SPA) communique par API REST avec un **backend Flask** structuré en modules (authentification, agents, analyse de logs, CTI, intégrations). Les données persistantes sont centralisées dans une base **MySQL**. Les agents honeypot déployés sur des hôtes distants remontent leurs événements via l'endpoint `/api/agent/report` sécurisé par **JWT**. Deux intégrations externes permettent l'enrichissement et le partage de renseignements : **Elasticsearch/Kibana** pour l'indexation et la visualisation, et **OpenCTI** pour le partage d'IOC au format STIX.

---

## 2. Cas d'utilisation — `02_cas_utilisation.puml`

**Type** : diagramme de cas d'utilisation (UML)
**Objectif** : recenser les fonctionnalités par acteur.

**Texte à placer sous le schéma :**
> Trois acteurs humains interagissent avec la plateforme : l'**administrateur SOC** qui déploie et configure les honeypots, l'**analyste** qui exploite les données collectées, et les **agents honeypot** qui remontent automatiquement les attaques détectées. Les cas d'utilisation sont regroupés par domaine fonctionnel : authentification (incluant la 2FA), gestion des honeypots, analyse des attaques, threat intelligence et configuration. Le système s'interface également avec des plateformes externes (ELK, OpenCTI) pour l'export des IOC.

---

## 3. Séquence — Authentification — `03_sequence_authentification.puml`

**Type** : diagramme de séquence
**Objectif** : décrire le flux de connexion avec double authentification.

**Texte à placer sous le schéma :**
> La connexion à ThreatLab se fait en deux étapes pour renforcer la sécurité. L'utilisateur saisit d'abord ses identifiants, qui sont vérifiés par rapport aux données enregistrées en base (le mot de passe n'est jamais stocké en clair). Si la double authentification est activée sur le compte, une seconde vérification est demandée sous la forme d'un code à usage unique à 6 chiffres, généré par une application d'authentification. Toutes les tentatives de connexion (réussies ou échouées) sont enregistrées pour garantir la traçabilité.

---

## 4. Séquence — Déploiement d'un agent — `04_sequence_deploiement_agent.puml`

**Type** : diagramme de séquence
**Objectif** : montrer la création et l'enrôlement d'un agent honeypot.

**Texte à placer sous le schéma :**
> Le déploiement d'un agent honeypot s'effectue via un assistant de création. L'administrateur renseigne les paramètres de l'agent (nom, adresse IP, service à simuler, bannière) qui sont transmis au serveur. Celui-ci génère un jeton d'authentification unique, que seul cet agent pourra utiliser pour remonter des informations. Le jeton est affiché une seule fois à l'administrateur, qui le place dans la configuration de l'agent avant de le déployer sur la machine cible. Une fois actif, l'agent se signale au serveur pour confirmer qu'il est opérationnel.

---

## 5. Séquence — Remontée d'une attaque — `05_sequence_remontee_attaque.puml`

**Type** : diagramme de séquence
**Objectif** : illustrer la capture et la persistance d'une attaque.

**Texte à placer sous le schéma :**
> Lorsqu'un attaquant interagit avec un honeypot (tentative de connexion SSH par exemple), l'agent capture l'ensemble des informations pertinentes : adresse IP d'origine, identifiants testés, commandes envoyées. Ces informations sont transmises au serveur de façon authentifiée. Le serveur vérifie l'identité de l'agent, uniformise les données reçues puis les enregistre dans différentes catégories : le journal d'attaques, la liste des IP malveillantes (avec un score de dangerosité), les statistiques par service attaqué, et les identifiants compromis. L'analyste peut ensuite consulter ces informations via le tableau de bord qui affiche l'évolution des attaques sur 24h, 7 jours ou 30 jours.

---

## 6. Séquence — Export CTI — `06_sequence_export_cti.puml`

**Type** : diagramme de séquence
**Objectif** : décrire l'export des IOC vers les plateformes externes.

**Texte à placer sous le schéma :**
> Le partage de renseignements sur la menace s'effectue vers deux plateformes externes. L'analyste déclenche un export depuis l'interface dédiée : le serveur collecte les indicateurs de compromission (IP malveillantes au-delà d'un seuil de dangerosité, identifiants compromis, empreintes de malwares) puis les transforme au format attendu par chaque destination. Les deux envois s'exécutent en parallèle pour réduire le temps d'attente. Un rapport final est affiché à l'analyste précisant le nombre d'indicateurs transmis à chaque plateforme.

---

## 7. Modèle Conceptuel de Données — `07_mcd_base_donnees.puml`

**Type** : diagramme entité-association (MCD)
**Objectif** : représenter le schéma relationnel de la base MySQL.

**Texte à placer sous le schéma :**
> Le modèle de données est organisé autour de trois grandes familles. **L'authentification** (tables `users` et `log_attempt_account`) gère les comptes et la traçabilité des connexions. **Les honeypots et attaques** constituent le cœur métier : `honey_agents` référence les sondes déployées, `attack_logs` journalise chaque événement, et des tables d'agrégation (`malicious_ips`, `ip_service_attacks`, `ip_agent_relations`) permettent des requêtes analytiques performantes sans recalculer à chaque fois. **Les wordlists** (`compromised_credentials`, `password_attempted`, `username_viewed`) capitalisent les identifiants testés par les attaquants, utiles en red team et en sensibilisation. Enfin, `api_keys` stocke les credentials d'intégration aux plateformes externes.

---

## 8. Déploiement Docker — `08_deploiement_docker.puml`

**Type** : diagramme de déploiement
**Objectif** : représenter l'infrastructure conteneurisée.

**Texte à placer sous le schéma :**
> L'ensemble de ThreatLab est orchestré via **Docker Compose** et se déploie en trois conteneurs distincts sur un réseau bridge privé. Le conteneur **frontend** sert le build statique Vue 3 derrière un reverse proxy Nginx qui termine le TLS. Le conteneur **backend** exécute Flask derrière Gunicorn et communique avec la base uniquement via le réseau interne. Le conteneur **database** (MySQL 8) persiste ses données sur un volume Docker. Les secrets et variables d'environnement sont isolés dans un fichier `.env` non versionné. Les agents honeypot sont déployés **sur des hôtes distincts** et communiquent avec le backend via HTTPS.

---

## 9. Activité — Traitement d'une attaque — `09_activite_traitement_attaque.puml`

**Type** : diagramme d'activité
**Objectif** : vue transverse du cycle de vie d'une attaque, du scan initial à la réaction SOC.

**Texte à placer sous le schéma :**
> Ce diagramme représente le cycle complet d'une attaque. L'attaquant initie un scan puis tente une connexion, capturée par l'agent honeypot qui enrichit et signe le rapport. Le backend vérifie le JWT, normalise le payload puis alimente **en parallèle** plusieurs tables pour optimiser les performances (journalisation, scoring d'IP, wordlists). Si l'export automatique est activé, les IOC sont simultanément envoyés vers Elasticsearch et OpenCTI. Côté analyste, le dashboard matérialise ces événements sous forme de timeline. En cas de menace critique, l'analyste effectue une investigation approfondie et peut enrichir les règles de détection du SIEM pour prévenir une attaque similaire en production.

---

## Suggestions pour le dossier BTS

- **Diagrammes obligatoires** : architecture globale (1), cas d'utilisation (2), au moins deux séquences (3, 5), MCD (7).
- **Diagrammes "bonus"** qui valorisent la note : déploiement Docker (8), activité transverse (9).
- Pour chaque diagramme : **un paragraphe d'explication + une légende sous le schéma** (les textes ci-dessus sont prêts à copier).
- Pensez à citer les **technologies** employées dans chaque section (Flask, Vue 3, JWT HS256, TOTP, STIX 2, ECS, Docker Compose, MySQL 8).
- À l'oral : insistez sur les **choix de sécurité** (2FA, hash SHA-256 du token agent, session HttpOnly+SameSite, JWT signé, isolation réseau Docker) — c'est un point fort d'un projet cybersécurité pour un jury BTS.
