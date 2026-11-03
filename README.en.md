# 🏕️ CampOrga

🇫🇷 [Français](./README.md) | 🇬🇧 English

> A web platform for organizing and managing coding & tech summer camps — from camp creation through to participant registration.

![Status](https://img.shields.io/badge/status-working%20MVP-success)
![Backend tests](https://img.shields.io/badge/backend-127%20tests%20%C2%B7%2097%25-brightgreen)
![Frontend tests](https://img.shields.io/badge/frontend-37%20tests-brightgreen)
![License](https://img.shields.io/badge/license-MIT-2F3C7E)
![Made with](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20PostgreSQL%20%7C%20MongoDB-1B2454)

Built as part of the **Portfolio Project** — Holberton School France.

---

## 📋 Table of contents

- [The problem](#-the-problem)
- [Features](#-features)
- [Tech stack](#️-tech-stack)
- [Architecture](#️-architecture)
- [Installation](#-installation)
- [Tests](#-tests)
- [Project structure](#-project-structure)
- [Documentation](#-documentation)
- [Team](#-team)
- [Roadmap](#️-roadmap)
- [License](#-license)

## 🎯 The problem

Teams running coding summer camps have no centralized tool today: each camp is managed separately, there is little overall visibility, and the registration process is neither standardized nor engaging for participants.

**CampOrga** centralizes camp creation, provides a public landing page for each camp, and gives organizers and the super admin a clear view of the whole platform.

## ✨ Features

**Visitors (no account)**
- 🌐 **Public landing page per camp** — seasonal theme, countdown, remaining places, minimum age, LinkedIn sharing
- ✍️ **Online registration** — first name, last name, email, comment
- 💬 **Contact** — hotline form and chatbot (intent-based answers, history stored in MongoDB)

**Organizers**
- 📝 **Sign-up** — the account is created as "pending" and activated by the super admin
- 🔐 **Secure login** — JWT, optional TOTP two-factor authentication (QR code), email/SMS verification code
- 🗓️ **Camp management** — dates, city, minimum age (`age`, empty = all ages), capacity, modalities, draft/published/archived status
- 📊 **Dashboard** — managed camps, recent registrations, attendance, messages, chatbot statistics
- 👤 **My account** — profile, phone number, 2FA, account deletion

**Super admin**
- 👥 **User management** — creation, roles (SEM, SWE, SSM, DC, DT…), activation of pending accounts, protected deletion
- 💾 **Backups** — SQL (`pg_dump`) or CSV export, history and download

## 🛠️ Tech stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, TypeScript (strict), Vite, Tailwind CSS 4, React Router 7, TanStack Query 5, React Hook Form + Zod 4 |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Auth | JWT (HS256, `scope` claim), bcrypt, TOTP (pyotp + QR code), hashed verification codes (SHA-256) |
| Databases | PostgreSQL 16 (business data) · MongoDB 7 (chatbot conversations, verification codes, with TTL indexes) |
| Infrastructure | Docker / Podman Compose, `camporga.sh` script |
| Quality | Pytest + mongomock (127 tests, 97%), Vitest + Testing Library (37 tests), Playwright, axe-core, ESLint, Ruff, Black |

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

The backend is layered: `api/` (thin routes) → `services/` (business logic, authorization rules) → `models/` (SQLAlchemy); `schemas/` validates input/output and `core/` holds configuration, security, dependencies and exceptions.

The data schema is described in [`docs/database-schema.sql`](./docs/database-schema.sql) and the diagram in [`docs/diagram_database.png`](./docs/diagram_database.png) (Mermaid source: [`docs/diagram_database.mmd`](./docs/diagram_database.mmd)).

## 🚀 Installation

### Prerequisites
- Docker (or Podman) with Compose
- Node.js 20+ (frontend)
- Python 3.11+ (only for backend development outside the container)

### With the `camporga.sh` script (recommended)

```bash
git clone https://github.com/BlackGhostMatrixx555/holbertonschool-portfolio.git
cd holbertonschool-portfolio
./camporga.sh start      # creates .env if needed, starts PostgreSQL + MongoDB + API, applies migrations
./camporga.sh admin      # creates the first super admin
./camporga.sh frontend   # starts the Vite frontend on http://localhost:5173
```

| Command | Effect |
|---|---|
| `start` / `stop` / `restart` | Start, stop, restart the services |
| `test` | Run the backend tests on a dedicated `camporga_test` database |
| `admin` / `admin-reset` | Create the super admin / delete it (with its camps and backups) and recreate it |
| `frontend` / `frontend-stop` | Start / stop the frontend |
| `format` | Format the Python code (Ruff + Black) |
| `logs` / `ps` | Backend logs / service status |
| `cleanup` | Remove containers and volumes |

### With Docker Compose directly

```bash
cp .env.example .env          # then replace the passwords and SECRET_KEY
docker compose up --build -d  # Alembic migrations run at startup
docker compose exec backend python -m scripts.bootstrap_admin
cd frontend && npm install && npm run dev
```

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000` — Swagger: `http://localhost:8000/docs`

In production, set `ENVIRONMENT=production`, a strong private `SECRET_KEY`, and `CORS_ORIGINS` with the exact frontend origins. In development only, the API returns the email/SMS verification code in the response (`debug_code`) since no sending provider is plugged in.

## 🧪 Tests

```bash
./camporga.sh test                 # backend: 127 tests, 97% coverage
cd frontend && npm test            # frontend: 37 tests (Vitest)
cd frontend && npm run typecheck && npm run lint
```

Backend tests use a dedicated PostgreSQL database (`camporga_test`) and `mongomock` for MongoDB: they never touch development data.

## 📁 Project structure

```text
holbertonschool-portfolio/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routes (auth, users, camps, registrations, landing_pages,
│   │   │                   #   contact_messages, chat, dashboard, backups)
│   │   ├── services/       # Business logic + permissions + 2FA + verification + backups
│   │   ├── models/         # SQLAlchemy models (7 tables)
│   │   ├── schemas/        # Pydantic v2 validation
│   │   ├── core/           # config, security (JWT/bcrypt), deps, exceptions
│   │   ├── db/             # PostgreSQL sessions + MongoDB connection (TTL indexes)
│   │   └── main.py         # App, CORS, error handling, /health, /ready
│   ├── alembic/versions/   # 5 migrations (including the collins + tete-work merge)
│   ├── scripts/            # bootstrap_admin.py
│   ├── tests/              # 127 Pytest tests
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── api/            # Typed HTTP client + endpoints
│       ├── auth/           # AuthContext (session, 2FA), RequireAuth
│       ├── components/     # UI, forms, ChatWidget, countdown
│       ├── pages/          # Public, organizer/ (dashboard, camps, account), admin/ (users, backups)
│       └── lib/            # Zod schemas, formatting, seasonal themes
├── docs/                   # Documentation (see docs/README.en.md)
├── scripts/                # Tools (compat_evaluator, visualize_repo, run_all_tests)
├── camporga.sh             # Lifecycle management script
├── docker-compose.yml      # PostgreSQL + MongoDB + backend
└── .env.example
```

## 📚 Documentation

All detailed documentation (Holberton reports, data schema, presentation, changelog) is in the [`docs/`](./docs/README.en.md) folder.

## 👥 Team

| Member | Role |
|---|---|
| Thélyaan Dufrénoy | Fullstack Developer / Lead (+ Frontend) |
| Collins Odi Obi | Backend / DevOps Developer (+ Frontend) |

> The team was initially formed with 3 members; Harold NGuementa stepped away from the project. Frontend development is now shared between the two remaining members.

## 🗺️ Roadmap

- [x] Idea development and MVP validation with the client
- [x] Database schema (PostgreSQL + MongoDB)
- [x] MVP backend: CRUD, JWT + 2FA auth, sign-up, chatbot, SQL/CSV backups
- [x] React frontend: public area, organizer area, administration
- [x] Merge of the `collins` and `tete-work` branches (single age field, no payment)
- [ ] Continuous integration (GitHub Actions) and online deployment
- [ ] Real sending of verification emails/SMS
- [ ] Scalability (see [`docs/scalability-roadmap.md`](./docs/scalability-roadmap.md))
- [ ] ML-based camp recommendations *(out of scope for the MVP)*

## 📄 License

Distributed under the MIT license.
