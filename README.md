# 🏕️ CampOrga

🇫🇷 Français | 🇬🇧 [English](./README.en.md)

> Plateforme web pour organiser et gérer des summer camps de code & d'informatique — de la création du camp jusqu'à l'inscription des participants.

![Status](https://img.shields.io/badge/status-MVP%20fonctionnel-success)
![Backend tests](https://img.shields.io/badge/backend-127%20tests%20%C2%B7%2097%25-brightgreen)
![Frontend tests](https://img.shields.io/badge/frontend-37%20tests-brightgreen)
![License](https://img.shields.io/badge/license-MIT-2F3C7E)
![Made with](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20PostgreSQL%20%7C%20MongoDB-1B2454)

Projet réalisé dans le cadre du **Portfolio Project** — Holberton School France.

---

## 📋 Sommaire

- [Le problème](#-le-problème)
- [Fonctionnalités](#-fonctionnalités)
- [Stack technique](#️-stack-technique)
- [Architecture](#️-architecture)
- [Installation](#-installation)
- [Tests](#-tests)
- [Structure du projet](#-structure-du-projet)
- [Documentation](#-documentation)
- [Équipe](#-équipe)
- [Roadmap](#️-roadmap)
- [Licence](#-licence)

## 🎯 Le problème

Les équipes qui organisent des summer camps de code n'ont aujourd'hui pas d'outil centralisé : chaque camp est géré séparément, la visibilité d'ensemble est faible, et le processus d'inscription n'est ni standardisé ni engageant pour les participants.

**CampOrga** centralise la création des camps, expose une landing page publique par camp, et donne aux organisateurs comme au super admin une vue claire sur l'ensemble de la plateforme.

## ✨ Fonctionnalités

**Visiteurs (sans compte)**
- 🌐 **Landing page publique par camp** — thème de saison, compte à rebours, places restantes, âge minimum, partage LinkedIn
- ✍️ **Inscription en ligne** — nom, prénom, email, commentaire
- 💬 **Contact** — formulaire hotline et chatbot (réponses par intention, historique dans MongoDB)

**Organisateurs**
- 📝 **Création de compte** — le compte est créé « en attente » et activé par le super admin
- 🔐 **Connexion sécurisée** — JWT, double authentification TOTP optionnelle (QR code), vérification par code email/SMS
- 🗓️ **Gestion des camps** — dates, ville, âge minimum (`age`, vide = tous âges), capacité, modalités, statut brouillon/publié/archivé
- 📊 **Dashboard** — camps gérés, inscriptions récentes, présences, messages, statistiques du chatbot
- 👤 **Mon compte** — profil, téléphone, 2FA, suppression du compte

**Super admin**
- 👥 **Gestion des utilisateurs** — création, rôles (SEM, SWE, SSM, DC, DT…), activation des comptes en attente, suppression protégée
- 💾 **Backups** — export SQL (`pg_dump`) ou CSV, historique et téléchargement

## 🛠️ Stack technique

| Couche | Technologies |
|---|---|
| Frontend | React 19, TypeScript (strict), Vite, Tailwind CSS 4, React Router 7, TanStack Query 5, React Hook Form + Zod 4 |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Auth | JWT (HS256, claim `scope`), bcrypt, TOTP (pyotp + QR code), codes de vérification hachés (SHA-256) |
| Bases de données | PostgreSQL 16 (données métier) · MongoDB 7 (conversations du chatbot, codes de vérification, avec index TTL) |
| Infrastructure | Docker / Podman Compose, script `camporga.sh` |
| Qualité | Pytest + mongomock (127 tests, 97 %), Vitest + Testing Library (37 tests), Playwright, axe-core, ESLint, Ruff, Black |

## 🏗️ Architecture

```text
┌──────────────┐   HTTP/JSON (JWT)   ┌──────────────────────────┐    SQL    ┌──────────────┐
│   Frontend   │ ──────────────────▶ │         Backend          │ ────────▶ │ PostgreSQL16 │
│ React + TS   │ ◀────────────────── │         FastAPI          │ ◀──────── │ users, camps │
│ (Vite :5173) │                     │  api/ → services/ → db   │           │ backups …    │
└──────────────┘                     └──────────────────────────┘           └──────────────┘
                                        │                 │
                                        │ pymongo         │ pg_dump / CSV
                                        ▼                 ▼
                                 ┌──────────────┐   ┌──────────────┐
                                 │  MongoDB 7   │   │  backend/    │
                                 │ chat, codes  │   │  backups/    │
                                 └──────────────┘   └──────────────┘
```

Le backend est organisé en couches : `api/` (routes fines) → `services/` (logique métier, règles d'autorisation) → `models/` (SQLAlchemy) ; `schemas/` valide les entrées/sorties et `core/` regroupe configuration, sécurité, dépendances et exceptions.

Le schéma de données est décrit dans [`docs/database-schema.sql`](./docs/database-schema.sql) et le diagramme dans [`docs/diagram_database.png`](./docs/diagram_database.png) (source Mermaid : [`docs/diagram_database.mmd`](./docs/diagram_database.mmd)).

## 🚀 Installation

### Prérequis
- Docker (ou Podman) avec Compose
- Node.js 20+ (frontend)
- Python 3.11+ (seulement pour le développement backend hors conteneur)

### Avec le script `camporga.sh` (recommandé)

```bash
git clone https://github.com/BlackGhostMatrixx555/holbertonschool-portfolio.git
cd holbertonschool-portfolio
./camporga.sh start      # crée .env si besoin, lance PostgreSQL + MongoDB + API, applique les migrations
./camporga.sh admin      # crée le premier super admin
./camporga.sh frontend   # lance le frontend Vite sur http://localhost:5173
```

| Commande | Effet |
|---|---|
| `start` / `stop` / `restart` | Démarre, arrête, redémarre les services |
| `test` | Lance les tests backend sur une base dédiée `camporga_test` |
| `admin` / `admin-reset` | Crée le super admin / le supprime (avec ses camps et backups) puis le recrée |
| `frontend` / `frontend-stop` | Lance / arrête le frontend |
| `format` | Formate le code Python (Ruff + Black) |
| `logs` / `ps` | Logs du backend / état des services |
| `cleanup` | Supprime conteneurs et volumes |

### Avec Docker Compose directement

```bash
cp .env.example .env          # puis remplacer les mots de passe et SECRET_KEY
docker compose up --build -d  # les migrations Alembic sont appliquées au démarrage
docker compose exec backend python -m scripts.bootstrap_admin
cd frontend && npm install && npm run dev
```

- Frontend : `http://localhost:5173`
- API : `http://localhost:8000` — Swagger : `http://localhost:8000/docs`

En production, définissez `ENVIRONMENT=production`, une `SECRET_KEY` robuste et privée, et `CORS_ORIGINS` avec les origines exactes du frontend. En développement uniquement, l'API renvoie le code de vérification email/SMS dans la réponse (`debug_code`) puisqu'aucun fournisseur d'envoi n'est branché.

## 🧪 Tests

```bash
./camporga.sh test                 # backend : 127 tests, couverture 97 %
cd frontend && npm test            # frontend : 37 tests (Vitest)
cd frontend && npm run typecheck && npm run lint
```

Les tests backend utilisent une base PostgreSQL dédiée (`camporga_test`) et `mongomock` pour MongoDB : ils ne touchent jamais aux données de développement.

## 📁 Structure du projet

```text
holbertonschool-portfolio/
├── backend/
│   ├── app/
│   │   ├── api/            # Routes FastAPI (auth, users, camps, registrations, landing_pages,
│   │   │                   #   contact_messages, chat, dashboard, backups)
│   │   ├── services/       # Logique métier + permissions + 2FA + vérification + backups
│   │   ├── models/         # Modèles SQLAlchemy (7 tables)
│   │   ├── schemas/        # Validation Pydantic v2
│   │   ├── core/           # config, security (JWT/bcrypt), deps, exceptions
│   │   ├── db/             # Sessions PostgreSQL + connexion MongoDB (index TTL)
│   │   └── main.py         # Application, CORS, gestion des erreurs, /health, /ready
│   ├── alembic/versions/   # 5 migrations (dont la fusion collins + tete-work)
│   ├── scripts/            # bootstrap_admin.py
│   ├── tests/              # 127 tests Pytest
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── api/            # Client HTTP typé + endpoints
│       ├── auth/           # AuthContext (session, 2FA), RequireAuth
│       ├── components/     # UI, formulaires, ChatWidget, compte à rebours
│       ├── pages/          # Public, organizer/ (dashboard, camps, compte), admin/ (users, backups)
│       └── lib/            # Schémas Zod, formatage, thèmes de saison
├── docs/                   # Documentation (voir docs/README.md)
├── scripts/                # Outils (compat_evaluator, visualize_repo, run_all_tests)
├── camporga.sh             # Script de gestion du cycle de vie
├── docker-compose.yml      # PostgreSQL + MongoDB + backend
└── .env.example
```

## 📚 Documentation

Toute la documentation détaillée (rapports Holberton, schéma de données, présentation, changelog) se trouve dans le dossier [`docs/`](./docs/README.md).

## 👥 Équipe

| Membre | Rôle |
|---|---|
| Thélyaan Dufrénoy | Fullstack Developer / Lead (+ Frontend) |
| Collins Odi Obi | Backend / DevOps Developer (+ Frontend) |
| Quentin Moussous | Frontend |

> Équipe initialement composée de 3 personnes ; Harold NGuementa s'est retiré du projet. 

## 🗺️ Roadmap

- [x] Idéation et validation du MVP avec le client
- [x] Schéma de base de données (PostgreSQL + MongoDB)
- [x] Backend MVP : CRUD, auth JWT + 2FA, inscription, chatbot, backups SQL/CSV
- [x] Frontend React : espace public, espace organisateur, administration
- [x] Fusion des branches `collins` et `tete-work` (âge unique, sans paiement)
- [ ] Intégration continue (GitHub Actions) et déploiement en ligne
- [ ] Envoi réel des emails/SMS de vérification
- [ ] Scalabilité (voir [`docs/scalability-roadmap.md`](./docs/scalability-roadmap.md))
- [ ] Recommandation de camps par ML *(hors scope MVP)*

## 📄 Licence

Distribué sous licence MIT.
