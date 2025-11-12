# Documentation de l'API Threatlab

Cette documentation présente la spécification des endpoints exposés par l'API.

---

## Endpoints et contrats

Tous les chemins API sont préfixés par /api lorsque portés par le blueprint agent, et par la racine /api pour certaines routes de démonstration.

### 1) POST /api/agent/create
- **Description**: Génère un token secret d'agent et l'enregistre en base.
- **Authentification**: Non (endpoint public).
- **Corps JSON**:
  - `agent_name`: string (optionnel mais conseillé pour traçabilité).
- **Réponses**:
  - 200: `{ success: true, secret_token: string }`
  - 500: `{ success: false }`
- **Remarques**:
  - Le token retourné est à stocker côté agent et utilisé à terme pour signer ou authentifier ses rapports.

---

### 2) POST /api/agent/report
- **Description**: Remontée d'un événement d'attaque par un agent. Normalise et persiste les données.
- **Authentification**: Non (endpoint public), mais à durcir en production.
- **Corps JSON (minimum requis)**:
  - `source_ip`: string (requis)
  - `service_type`: string (requis; ex: "ssh" ou "smtp")
- **Corps JSON (champs supportés selon service)**:
  - **Champs généraux**:
    - `agent_id`: string
    - `source_port`: int
    - `target_port`: int
    - `username_attempt`: string
    - `password_attempt`: string
    - `payload`: string | objet
    - `malware_hash`: string
    - `classification`: string
    - `country_code`: string
    - `country_name`: string
  - **Spécifique SSH**:
    - `username_attempt`, `password_attempt`: si présents, enregistrés comme credentials compromis.
  - **Spécifique SMTP**:
    - `sender_email`: string
    - `recipient_email`: string
    - `subject`: string
    - `message_content`: string
    - `attachments`: liste d'objets ou métadonnées de pièces jointes
- **Réponses**:
  - 200: `{ success: true, message: "<SERVICE> attack data processed successfully" }`
  - 400: `{ success: false, error: "Missing required field: <...>" }`
  - 500: `{ success: false, error: "<message>" }`
- **Effets côté persistance**:
  - Ajoute l'IP malveillante observée.
  - Ajoute un journal d'attaque normalisé.
  - Ajoute des détails spécifiques selon le type de service (SSH/SMTP).

---

### 3) GET /api/honeypots
- **Description**: Renvoyé pour la vue d'ensemble des honeypots (actuellement simulé).
- **Authentification**: Oui (middleware de session), mais listée dans les publics selon la configuration actuelle d'accès via SPA.
- **Réponse**: `{ honeypots: [...] }`

---

### 4) GET /api/alerts
- **Description**: Renvoyé pour l'onglet d'alertes (actuellement simulé).
- **Authentification**: Oui (middleware de session), mais accessible via l'interface SPA.
- **Réponse**: `{ alerts: [...] }`

---

### 5) Frontend SPA et static
- **GET /**: renvoie index.html du build frontend.
- **GET/POST /<path>**: fallback pour permettre le routage côté client (Vue Router).
- **404/500**: gestionnaires renvoyant des templates d'erreur.

---

## Authentification et A2F

- Le middleware before_request liste explicitement des endpoints publics (notamment les routes agent). Les autres routes nécessitent une session valide, et potentiellement l'A2F validée.
- Les endpoints d'authentification existent via un blueprint "auth", incluant typiquement:
  - login
  - session_state
  - a2f
  (Les détails exacts des chemins et payloads dépendront de l'implémentation de ce module.)
