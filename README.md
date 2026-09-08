# 🏕️ CampOrga

🇫🇷 Français | 🇬🇧 [English](./README.en.md)

> Plateforme web pour organiser et gérer des summer camps de code & d'informatique — de la création du camp jusqu'à l'inscription des participants.

![Status](https://img.shields.io/badge/status-en%20d%C3%A9veloppement-F9646A)
![License](https://img.shields.io/badge/license-MIT-2F3C7E)
![Made with](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20PostgreSQL-1B2454)

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
- [Structure du projet](#-structure-du-projet)
- [Documentation](#-documentation)
- [Équipe](#-équipe)
- [Roadmap](#-roadmap)
- [Licence](#-licence)

## 🎯 Le problème

Les équipes qui organisent des summer camps de code n'ont aujourd'hui pas d'outil centralisé : chaque camp est géré séparément, la visibilité d'ensemble est faible, et le processus d'inscription n'est ni standardisé ni engageant pour les participants.

**CampOrga** centralise la création des camps, expose une landing page publique par camp, et donne aux organisateurs comme au super admin une vue claire sur l'ensemble de la plateforme.

## ✨ Fonctionnalités

- 🗓️ **Création et gestion de camps** — dates, description, modalités d'éligibilité (mineurs/majeurs, niveau requis)
- 🌐 **Landing page publique par camp** — compte à rebours, présentation, partage LinkedIn
- ✍️ **Inscription en ligne** — nom, prénom, email, commentaire, confirmation de venue
- 📊 **Dashboard organisateur** — vue sur les camps gérés et les inscriptions récentes
- 👥 **Gestion des utilisateurs et des rôles** (SEM, SWE, SSM, directeur de campus, directeur technique) par un super admin
- 💾 **Export de backup** de la base de données en SQL et CSV, réservé au super admin
- 💬 **Contact** — hotline et chatbot IA sur chaque landing page

## 🛠️ Stack technique

| Couche | Technologies |
|---|---|
| Frontend | React, Vite, TypeScript, Tailwind CSS, TanStack Query, React Hook Form, React Router |
| Backend | Python, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Base de données | PostgreSQL |
| Infrastructure | Docker, Docker Compose |
| Qualité | Pytest, Vitest, React Testing Library, ESLint, Prettier, Ruff, Black |

## 🏗️ Architecture

```
┌──────────────┐      HTTP/JSON      ┌──────────────┐        SQL        ┌──────────────┐
│   Frontend   │  ─────────────────▶ │   Backend    │ ─────────────────▶│  PostgreSQL  │
│ React + TS   │ ◀───────────────── │   FastAPI    │ ◀───────────────── │              │
└──────────────┘                     └──────────────┘                   └──────────────┘
                                             │
                                             ▼
                                   pg_dump (SQL) / CSV
                                      exports (backup)
```

Le schéma détaillé de la base de données est disponible dans [`docs/database-schema.sql`](./docs/database-schema.sql).

## 🚀 Installation

### Prérequis
- Docker et Docker Compose
- Node.js 20+ (pour le développement frontend hors conteneur)
- Python 3.11+ (pour le développement backend hors conteneur)

### Avec Docker (recommandé)

```bash
git clone https://github.com/<votre-org>/camporga.git
cd camporga
docker compose up --build
```

- Frontend disponible sur `http://localhost:5173`
- API disponible sur `http://localhost:8000`
- Documentation Swagger de l'API sur `http://localhost:8000/docs`

### Sans Docker

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
# Frontend
cd frontend
npm install
npm run dev
```

## 📁 Structure du projet

```
camporga/
├── backend/          # API FastAPI (routes, modèles, services)
├── frontend/          # Interface React
├── docs/              # Documentation du projet (voir ci-dessous)
├── docker-compose.yml
└── README.md
```

## 📚 Documentation

Toute la documentation détaillée du projet (rapports Holberton, schéma de données) se trouve dans le dossier [`docs/`](./docs/README.md).

## 👥 Équipe

| Membre | Rôle |
|---|---|
| Thélyaan Dufrénoy | Fullstack Developer / Lead (+ Frontend) |
| Collins Odi Obi | Backend / DevOps Developer (+ Frontend) |

> Équipe initialement composée de 3 personnes ; Harold NGuementa s'est retiré du projet. Le frontend est désormais partagé entre les deux membres restants.

## 🗺️ Roadmap

- [x] Idéation et validation du MVP avec le client
- [x] Schéma de base de données
- [ ] Nouvelle charte graphique (hors identité Holberton)
- [ ] Développement du MVP
- [ ] Fonctionnalité de backup SQL/CSV
- [ ] Recommandation de camps par ML *(hors scope MVP)*

## 📄 Licence

Distribué sous licence MIT. Voir [`LICENSE`](./LICENSE) pour plus de détails.
