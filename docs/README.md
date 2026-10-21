
# 🏕️ CampOrga

🇫🇷 Français | 🇬🇧 [English](./README.en.md)

> Plateforme web pour organiser et gérer des summer camps de code & d'informatique — de la création du camp jusqu'à l'inscription des participants.

![Status](https://img.shields.io/badge/status-MVP%20valid%C3%A9-success)
![Tests](https://img.shields.io/badge/tests-50%20passed-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-2F3C7E)

Projet réalisé dans le cadre du **Portfolio Project** — Holberton School France.

---

## 📸 Aperçu

<!-- Remplacer par une vraie capture une fois le nouveau design (hors charte Holberton) finalisé -->
<p align="center">
  <img src="docs/screenshots/landing.png" alt="Landing page d'un camp CampOrga" width="700">
</p>

## 📋 Sommaire

- [Le problème](#-le-problème)
- [Fonctionnalités](#-fonctionnalités)
- [Stack technique](#-stack-technique)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Tests](#-tests)
- [Structure du projet](#-structure-du-projet)
- [Documentation](#-documentation)
- [Équipe](#-équipe)
- [Roadmap](#-roadmap)
- [Licence](#-licence)

## 🎯 Le problème

Les équipes qui organisent des summer camps de code n'ont aujourd'hui pas d'outil centralisé : chaque camp est géré séparément, la visibilité d'ensemble est faible, et le processus d'inscription n'est ni standardisé ni engageant pour les participants.

**CampOrga** centralise la création des camps, expose une landing page publique par camp, et donne aux organisateurs comme au super admin une vue claire sur l'ensemble de la plateforme.

## ✨ Fonctionnalités (MVP)

- 🗓️ **Création et gestion de camps** — dates, description, modalités d'éligibilité
- 🌐 **Landing page publique par camp** — compte à rebours, présentation, partage LinkedIn
- ✍️ **Inscription en ligne** — nom, prénom, email, commentaire, confirmation de venue
- 📊 **Dashboard organisateur** — vue sur les camps gérés et les inscriptions récentes
- 👥 **Gestion des utilisateurs et des rôles** par un super admin (JWT)
- 💾 **Export de backup** de la base de données en SQL et CSV (super admin)
- 💬 **Contact** — hotline et chatbot IA (mock) sur chaque landing page

## 🛠️ Stack technique

| Couche | Technologies |
|---|---|
| Frontend | React, Vite, TypeScript, Tailwind CSS, TanStack Query, React Hook Form, React Router |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Auth | JWT (HS256), bcrypt, passlib |
| Base de données | PostgreSQL 16 |
| Infrastructure | Docker, Docker Compose |
| Qualité | Pytest (50 tests), httpx, Ruff, Black |

## 🏗️ Architecture

```text
┌──────────────┐      HTTP/JSON      ┌──────────────┐        SQL        ┌──────────────┐
│   Frontend   │  ─────────────────▶ │   Backend    │ ─────────────────▶│  PostgreSQL  │
│ React + TS   │ ◀───────────────── │   FastAPI    │ ◀───────────────── │              │
└──────────────┘                     └──────────────┘                   └──────────────┘
                                             │
                                             ▼
                                   pg_dump (SQL) / CSV
                                      exports (backup)
Le schéma détaillé de la base de données est disponible dans docs/database-schema.sql.

🚀 Installation
Prérequis
Docker et Docker Compose

Python 3.11+ (pour le développement hors conteneur)

Avec Docker (recommandé)
bash
git clone https://github.com/BlackGhostMatrixx555/holbertonschool-portfolio.git
cd holbertonschool-portfolio
cp backend/.env.example backend/.env
# Modifier backend/.env en y ajoutant une SECRET_KEY générée via :
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
docker compose up --build -d
docker compose exec backend alembic upgrade head
API disponible sur http://localhost:8000

Documentation Swagger de l'API sur http://localhost:8000/docs

Créer le premier super admin
bash
docker compose exec backend python -c "
from app.database import SessionLocal
from app.models import UserRole
from app.schemas.user import UserCreate
from app.services.user_service import UserService

db = SessionLocal()
try:
    UserService(db).create(UserCreate(
        first_name='Admin',
        last_name='CampOrga',
        email='admin@camporga.fr',
        password='ChangeMe123!',
        role=UserRole.SUPER_ADMIN,
    ))
    print('✅ Super admin créé')
finally:
    db.close()
"
🧪 Tests
bash
# Lancer tous les tests (50)
docker compose exec backend pytest

# Lancer avec la couverture (~96%)
docker compose exec backend pytest --cov=app --cov-report=term-missing
📁 Structure du projet
text
holbertonschool-portfolio/
├── backend/           # API FastAPI (routes, modèles, services)
│   ├── app/
│   ├── alembic/       # Migrations
│   └── tests/         # 50 tests Pytest
├── frontend/          # Interface React (en cours)
├── docs/              # Documentation du projet
├── docker-compose.yml
└── README.md
📚 Documentation
Toute la documentation détaillée du projet (rapports Holberton, schéma de données) se trouve dans le dossier docs/.

👥 Équipe
Membre	Rôle
Thélyaan Dufrénoy	Fullstack Developer / Lead (+ Frontend)
Collins Odi Obi	Backend / DevOps Developer (+ Frontend)
Équipe initialement composée de 3 personnes ; Harold NGuementa s'est retiré du projet. Le frontend est désormais partagé entre les deux membres restants.

🗺️ Roadmap
☑ Idéation et validation du MVP avec le client
☑ Schéma de base de données
☑ Développement du backend MVP (CRUD, Auth JWT, Backups, Chatbot)
☑ Suite de tests (50 tests, ~96% de couverture)
□ Développement du frontend React
□ Scalabilité (voir docs/scalability-roadmap.md)
□ Nouvelle charte graphique (hors identité Holberton)
□ Recommandation de camps par ML (hors scope MVP)

📄 Licence
Distribué sous licence MIT. Voir LICENSE pour plus de détails.
