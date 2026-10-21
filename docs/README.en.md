
# 🏕️ CampOrga

🇫🇷 [Français](./README.md) | 🇬🇧 English

> A web platform for organizing and managing coding & tech summer camps — from camp creation through to participant registration.

![Status](https://img.shields.io/badge/status-MVP%20validated-success)
![Tests](https://img.shields.io/badge/tests-50%20passed-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-2F3C7E)

Built as part of the **Portfolio Project** — Holberton School France.

---

## 📸 Preview

<!-- Replace with a real screenshot once the new design (outside Holberton's brand) is finalized -->
<p align="center">
  <img src="docs/screenshots/landing.png" alt="CampOrga camp landing page" width="700">
</p>

## 📋 Table of Contents

- [The Problem](#-the-problem)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Tests](#-tests)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Team](#-team)
- [Roadmap](#-roadmap)
- [License](#-license)

## 🎯 The Problem

Teams that organize coding summer camps currently have no centralized tool: each camp is managed separately, visibility across the organization's camps is poor, and the registration process for participants is neither standardized nor engaging.

**CampOrga** centralizes camp creation, exposes a public landing page per camp, and gives both organizers and the super admin a clear view of the whole platform.

## ✨ Features (MVP)

- 🗓️ **Camp creation and management** — dates, description, eligibility criteria
- 🌐 **Public landing page per camp** — countdown, presentation, LinkedIn sharing
- ✍️ **Online registration** — first name, last name, email, comment, attendance confirmation
- 📊 **Organizer dashboard** — overview of managed camps and recent registrations
- 👥 **User and role management** by a super admin (JWT)
- 💾 **Database backup export** in SQL and CSV (super admin only)
- 💬 **Contact** — hotline and AI chatbot (mock) on every landing page

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, TypeScript, Tailwind CSS, TanStack Query, React Hook Form, React Router |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Auth | JWT (HS256), bcrypt, passlib |
| Database | PostgreSQL 16 |
| Infrastructure | Docker, Docker Compose |
| Quality | Pytest (50 tests), httpx, Ruff, Black |

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
The detailed database schema is available in docs/database-schema.sql.

🚀 Installation
Prerequisites
Docker and Docker Compose

Python 3.11+ (for development outside the container)

With Docker (recommended)
bash
git clone https://github.com/BlackGhostMatrixx555/holbertonschool-portfolio.git
cd holbertonschool-portfolio
cp backend/.env.example backend/.env
# Edit backend/.env and add a SECRET_KEY generated via:
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
docker compose up --build -d
docker compose exec backend alembic upgrade head
API available at http://localhost:8000

API Swagger docs at http://localhost:8000/docs

Create the first super admin
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
    print('✅ Super admin created')
finally:
    db.close()
"
🧪 Tests
bash
# Run all tests (50)
docker compose exec backend pytest

# Run with coverage (~96%)
docker compose exec backend pytest --cov=app --cov-report=term-missing
📁 Project Structure
text
holbertonschool-portfolio/
├── backend/           # FastAPI API (routes, models, services)
│   ├── app/
│   ├── alembic/       # Migrations
│   └── tests/         # 50 Pytest tests
├── frontend/          # React interface (in progress)
├── docs/              # Project documentation
├── docker-compose.yml
└── README.md
📚 Documentation
The full project documentation (Holberton reports, data schema) is available in the docs/ folder.

👥 Team
Member	Role
Thélyaan Dufrénoy	Fullstack Developer / Lead (+ Frontend)
Collins Odi Obi	Backend / DevOps Developer (+ Frontend)
The team was initially formed with 3 members; Harold NGuementa stepped away from the project. Frontend development is now shared between the two remaining members.

🗺️ Roadmap
☑ Idea development and MVP validation with the client
☑ Database schema
☑ Backend MVP development (CRUD, JWT Auth, Backups, Chatbot)
☑ Test suite (50 tests, ~96% coverage)
□ React frontend development
□ Scalability (see docs/scalability-roadmap.md)
□ New graphic identity (outside Holberton's branding)
□ ML-based camp recommendations (out of scope for the MVP)

📄 License
Distributed under the MIT License. See LICENSE for details.
