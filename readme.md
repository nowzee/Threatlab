# Threatlab
![Status](https://img.shields.io/badge/Status-In_Development-green.svg)

---
Under in development, need to convert in english and pass to rust, the python version is open-source.
Some feature need to be developed and you can find some bugs.


![image_banner](https://github.com/user-attachments/assets/4721f90b-7ea8-486c-a294-47e80a87ac41)

Threatlab est une plateforme centralisée pour déployer, superviser et orchestrer des honeypots. Elle collecte les événements d'attaque en temps réel, fournit un tableau de bord pour l'analyse, et s'intègre de manière modulaire avec des systèmes externes d'ingestion et de CTI (ELK/Elastic, OpenCTI, etc.).

- Supervision des honeypots (état, type, volume d'alertes)
- Collecte d'alertes et événements d'attaque et samples
- Architecture modulaire pensée pour l'export des données (ELK, OpenCTI)

---

## Exemple
<img width="1885" height="994" alt="image" src="https://github.com/user-attachments/assets/1d367251-0ff1-4ada-bbdb-92b2ca48d810" />


## Fonctionnalités

- **Gestion des honeypots**
  - Vue d'ensemble des instances (nom, type, statut, niveau d'activité)
  - Vision rapide des alertes récentes
- **Collecte & alerting**
  - Exposition d'API pour récupérer les événements (simulation par défaut pour le développement)
  - Normalisation des payloads pour faciliter l'export
- **Intégrations**
  - Connecteurs prévus pour:
    - ELK / Elastic (Ingest pipelines / Indexation)
    - OpenCTI (enrichissement et contextualisation des IOC)
  - Architecture extensible pour d'autres bus et SIEM
- **Sécurité**
  - Sessions serveur
  - Flux A2F (deuxième facteur) sur les routes sensibles
- **UX / UI**
  - SPA moderne (Vue) servie par le backend pour une intégration simple

---

## Installation

### Prérequis
- Python 3.10+
- Node.js et npm (pour builder le frontend)
- Accès internet pour installer les dépendances
- docker compose

### Install & setup

```bash
git clone https://github.com/nowzee/Threatlab
```

```bash
cd Threatlab
```

```bash
docker compose build
```

```bash
docker compose up
```

Accéder à l'interface via http://localhost:5000

---

## Configuration

Variables d'environnement et paramètres:
- `SECRET_KEY`: clé secrète pour les sessions côté Flask
- `DATABASE`: chemin de la base (ex: ./honeypot.db)

**Intégrations (à adapter selon vos connecteurs)**:
- **ELK/Elastic**:
  - `ELASTIC_URL`, `ELASTIC_API_KEY`, `ELASTIC_INDEX`, `ELASTIC_PIPELINE`
- **OpenCTI**:
  - `OPENCTI_URL`, `OPENCTI_TOKEN`, `OPENCTI_ORG`

---

## Intégrations (ELK / OpenCTI)

Le modèle d'intégration repose sur des connecteurs modulaires:
- Mapping des événements (timestamp, type d'attaque, honeypot/source, sévérité, IP source, etc.)
- Envoi vers:
  - **ELK**: indexation pour dashboards Kibana et corrélations
  - **OpenCTI**: enrichissement des IOC et partage CTI

---

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - Architecture technique et principes de conception
- [API](docs/API.md) - Spécification des endpoints et contrats API

---

## Auteur

Dev with ❤️ by Insomnia
