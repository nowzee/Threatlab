# Documentation technique

Ce document décrit l’architecture, l’environnement, les dépendances, les conventions et les procédures pour développer, tester, construire, déployer et exploiter le projet. Enregistrez-le sous: docs/documentation-technique.md

## 1. Vue d’ensemble

- Pile applicative principale:
  - Backend: Python 3.13.7 (virtualenv)
  - Web: TypeScript 5.8, Vue 3, Vite, Pinia, Vue Router
- Gestion des paquets:
  - Python: virtualenv + pip
  - Node.js: npm
- Packages Python disponibles: click, flask, jinja2, pillow, requests, werkzeug
- Packages Node: vue, vue-router, pinia, vite, @vitejs/plugin-vue, typescript, @vue/tsconfig, vue-tsc, vite-plugin-vue-devtools, @tsconfig/node22, @types/node, npm-run-all2

Note: adaptez ce document selon vos conventions et modules effectifs.

## 2. Architecture

- Frontend (SPA):
  - Vue 3 (composition API), Pinia (store), Vue Router (routing)
  - Vite (dev server, bundling, HMR)
  - TypeScript pour typage et DX
- Backend:
  - Flask pour les endpoints HTTP/REST
  - Jinja2 si rendu serveur nécessaire
  - Requests pour appels sortants
  - Pillow pour traitement d’images
  - Click pour CLIs éventuelles
- Communication:
  - JSON sur HTTP (REST). Convention d’API: chemin en kebab-case, JSON camelCase côté frontend, snake_case côté backend (adapter si besoin).
- Gestion d’état:
  - Pinia côté client
- Authentification/Autorisation:
  - À définir (JWT/Bearer/Session). Recommandé: JWT Access + Refresh, cookies HttpOnly + SameSite.

## 3. Structure recommandée du dépôt

- backend/
  - app/ (modules Flask, blueprints, services)
  - tests/ (tests unitaires/intégration)
  - requirements.txt ou constraints.txt (si utilisé)
  - wsgi.py (si déploiement WSGI)
- frontend/
  - src/
    - main.ts, App.vue
    - router/, store/, components/, views/, assets/
    - types/ (définitions TS communes)
  - index.html
  - vite.config.ts
- docs/
  - documentation-technique.md (ce fichier)
  - api/ (spécifications OpenAPI si disponibles)
- readme.md
- scripts/ (outils de build/devops)
- .env.example, .env.development, .env.production (voir section Config)

Adaptez aux dossiers existants.

## 4. Environnements

- Local (développement): variables dans .env ou .env.local
- CI: variables/Secrets injectés par le provider CI
- Recette/Staging: proche de la prod avec fonctionnalités de test
- Production: durcie, observabilité et sauvegardes

Convention: ne jamais commiter de secrets. Utiliser un gestionnaire de secrets (vault, variables CI, KMS).

## 5. Pré-requis

- Python 3.13.7
- virtualenv (pip install virtualenv)
- Node.js (version compatible avec TypeScript/Vite), npm
- Git

Optionnel:
- Docker (pour reproductibilité)
- Make (cibles de commodité)

## 6. Installation

Backend:
- Créer l’environnement virtuel:
  - python3.13 -m venv .venv
- Activer:
  - Linux/macOS: source .venv/bin/activate
  - Windows (PowerShell): .venv\Scripts\Activate.ps1
- Mettre à jour pip:
  - python -m pip install --upgrade pip
- Installer les dépendances:
  - python -m pip install flask jinja2 pillow requests werkzeug click
  - Ajouter ici d’autres paquets requis par le projet

Frontend:
- Se placer dans frontend/
- Installer les dépendances:
  - npm ci (ou npm install la première fois)
- Vérifier TypeScript:
  - npx vue-tsc --version

## 7. Lancement en développement

Backend:
- Variables:
  - FLASK_APP=app/main.py (ou entrypoint)
  - FLASK_ENV=development
  - FLASK_DEBUG=1
- Démarrer:
  - flask run --host=127.0.0.1 --port=5000
  - ou python app/main.py selon votre script d’entrée

Frontend:
- Démarrer le serveur Vite:
  - npm run dev
- Proxy API:
  - Configurer server.proxy dans vite.config.ts pour rediriger /api vers http://127.0.0.1:5000

## 8. Build et artefacts

Frontend:
- Build de production:
  - npm run build
- Prévisualiser:
  - npm run preview
- Artefacts générés: frontend/dist

Backend:
- Mode production:
  - Lancer derrière un serveur WSGI (gunicorn, uwsgi) ou un ASGI wrapper si nécessaire
  - Exemple: gunicorn -w 4 -b 0.0.0.0:5000 "app.main:create_app()"
  - Adapter selon votre fabrique d’application Flask

Intégration:
- Servir le dist/ via un serveur statique (Nginx) et reverse-proxy vers Flask
- Alternative: servir dist/ depuis Flask si requis (moins recommandé en prod)

## 9. Configuration

Fichiers:
- .env.example: modèle des variables
- .env.development, .env.production: spécifiques aux environnements

Variables typiques:
- Backend:
  - FLASK_ENV, FLASK_DEBUG
  - APP_HOST, APP_PORT
  - SECRET_KEY
  - API_BASE_PATH=/api
  - EXTERNAL_API_BASE_URL
- Frontend:
  - VITE_API_BASE_URL
  - VITE_APP_ENV

Note: les variables Vite doivent commencer par VITE_ pour être exposées.

## 10. Journalisation et observabilité

Backend:
- Niveau de logs via LOG_LEVEL (INFO/DEBUG/WARN/ERROR)
- Format JSON recommandé en prod
- Corrélation: x-request-id injecté côté reverse proxy, propagé dans les logs

Frontend:
- Logger applicatif léger (console en dev, niveau WARN en prod)
- Capture des erreurs non gérées (window.onunhandledrejection, errorHandler Vue)

Tracing/Monitoring (optionnel):
- OpenTelemetry pour traces
- Export vers un backend (Jaeger, OTEL collector)
- Metrics: Prometheus (exporter côté backend)

## 11. Sécurité

- En-têtes HTTP: Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, Referrer-Policy
- Cookies: HttpOnly, Secure, SameSite
- CORS: restreindre origins, méthodes, headers
- Validation d’entrées: schémas stricts (pydantic/marshmallow) côté backend; types côté frontend
- Gestion des secrets: jamais en dépôt; rotation régulière
- Dépendances: scans réguliers (npm audit, pip-audit)
- Limitation de débit (rate limiting) côté API si exposée

## 12. Conventions de code

Backend (Python):
- Style: PEP 8
- Typage: PEP 484 (annotations)
- Organisation: blueprints/services/repositories
- Gestion d’erreurs: exceptions spécifiques, réponses JSON structurées

Frontend (TypeScript/Vue):
- Composition API, SFC <script setup> recommandé
- State global: stores Pinia par domaine
- Router: lazy-loading des routes
- TS strict (noImplicitAny, strictNullChecks)
- Nommage: kebab-case pour fichiers Vue, PascalCase pour composants

Outils qualité (recommandés):
- Python: black, isort, ruff/flake8, mypy
- Frontend: eslint, prettier, vue-tsc

## 13. Tests

Types:
- Unitaires: fonctions/services isolés
- Intégration: endpoints Flask, stores Pinia, composants critiques
- End-to-end (optionnel): Playwright/Cypress

Backend:
- Framework: pytest (recommandé) ou unittest
- Démarrage d’app test: app test Flask avec client de test
- Couverture: viser >= 80%

Frontend:
- Unitaires: Vitest/Jest + @vue/test-utils
- Typage: npx vue-tsc --noEmit pour vérifier les types
- Lint: npm run lint

Commandes (exemples à adapter):
- Backend: pytest -q
- Frontend: npm run test, npm run type-check, npm run lint

## 14. CI/CD

- Pipelines:
  - Install deps (cache npm/pip)
  - Lint + type-check + tests + couverture
  - Build frontend
  - Build artefacts (container ou tarballs)
  - Scan vulnérabilités
  - Déploiement staging puis production avec approbation
- Stratégies:
  - Branches: main (protégée), develop, feature/*
  - SemVer pour versions
  - Conventional Commits pour messages

## 15. Déploiement

- Conteneurisation (recommandée):
  - Image backend Python slim
  - Image frontend Nginx pour servir dist/
  - Reverse proxy (Nginx/Traefik) vers Flask
- Variables d’environnement injectées à l’exécution
- Santé:
  - Liveness/Readiness endpoints (/health, /ready)
- Scalabilité:
  - Backend stateless; session via token/JWT ou store partagé

## 16. Gestion des erreurs

- Backend:
  - Handlers globaux (404, 422, 500) renvoyant JSON:
    - { error: { code, message, details?, correlationId? } }
- Frontend:
  - Intercepteurs HTTP (401/403/5xx), UI de fallback, retry avec backoff si applicable

## 17. Internationalisation (i18n)

- Frontend: vue-i18n (recommandé) pour messages et formats
- Convention: messages par domaine, fallback locale
- Backend: messages d’erreurs en codes stables et localisables côté UI

## 18. Stockage et données

- Base de données: à préciser (ex: Postgres, MySQL, SQLite)
- Migrations: outil recommandé (Alembic) si SQL
- Connexions: pool, timeouts, retries
- Sauvegardes: stratégie et rétention

## 19. Performance

- Frontend:
  - Code splitting, lazy loading, prefetching
  - Optimisation images (Pillow côté backend si traitement)
- Backend:
  - Caching (ETag/Cache-Control côté HTTP, cache applicatif si nécessaire)
  - Timeouts et limites de taille requêtes

## 20. Check-list avant livraison

- [ ] Tests verts et couverture suffisante
- [ ] Lint/Type-check sans erreurs
- [ ] Build prod vérifié (frontend/ backend)
- [ ] Variables d’environnement définies
- [ ] Endpoint health vérifié
- [ ] Logs au bon niveau
- [ ] Scans de vulnérabilités passés

## 21. Annexes

Exemple de .env.example (adapter aux besoins):

- Backend:
  - FLASK_ENV=production
  - FLASK_DEBUG=0
  - APP_HOST=0.0.0.0
  - APP_PORT=5000
  - SECRET_KEY=change-me
  - API_BASE_PATH=/api
  - EXTERNAL_API_BASE_URL=
  - LOG_LEVEL=INFO

- Frontend:
  - VITE_API_BASE_URL=http://localhost:5000/api
  - VITE_APP_ENV=development