# 🏕️ CampOrga

🇫🇷 [Français](./README.md) | 🇬🇧 English

> A web platform for organizing and managing coding & tech summer camps — from camp creation through to participant registration.

![Status](https://img.shields.io/badge/status-in%20development-F9646A)
![License](https://img.shields.io/badge/license-MIT-2F3C7E)
![Made with](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20PostgreSQL-1B2454)

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
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Team](#-team)
- [Roadmap](#-roadmap)
- [License](#-license)

## 🎯 The Problem

Teams that organize coding summer camps currently have no centralized tool: each camp is managed separately, visibility across the organization's camps is poor, and the registration process for participants is neither standardized nor engaging.

**CampOrga** centralizes camp creation, exposes a public landing page per camp, and gives both organizers and the super admin a clear view of the whole platform.

## ✨ Features

- 🗓️ **Camp creation and management** — dates, description, eligibility criteria (minors/adults, required level)
- 🌐 **Public landing page per camp** — countdown, presentation, LinkedIn sharing
- ✍️ **Online registration** — first name, last name, email, comment, attendance confirmation
- 📊 **Organizer dashboard** — overview of managed camps and recent registrations
- 👥 **User and role management** (SEM, SWE, SSM, campus director, technical director) by a super admin
- 💾 **Database backup export** in SQL and CSV, restricted to the super admin
- 💬 **Contact** — hotline and AI chatbot on every landing page

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, TypeScript, Tailwind CSS, TanStack Query, React Hook Form, React Router |
| Backend | Python, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Database | PostgreSQL |
| Infrastructure | Docker, Docker Compose |
| Quality | Pytest, Vitest, React Testing Library, ESLint, Prettier, Ruff, Black |

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

The detailed database schema is available in [`docs/database-schema.sql`](./docs/database-schema.sql).

## 🚀 Installation

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ (for frontend development outside the container)
- Python 3.11+ (for backend development outside the container)

### With Docker (recommended)

```bash
git clone https://github.com/<your-org>/camporga.git
cd camporga
docker compose up --build
```

- Frontend available at `http://localhost:5173`
- API available at `http://localhost:8000`
- API Swagger docs at `http://localhost:8000/docs`

### Without Docker

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

## 📁 Project Structure

```
camporga/
├── backend/          # FastAPI API (routes, models, services)
├── frontend/          # React interface
├── docs/              # Project documentation (see below)
├── docker-compose.yml
└── README.md
```

## 📚 Documentation

The full project documentation (Holberton reports, data schema) is available in the [`docs/`](./docs/README.md) folder.

## 👥 Team

| Member | Role |
|---|---|
| Thélyaan Dufrénoy | Fullstack Developer / Lead (+ Frontend) |
| Collins Odi Obi | Backend / DevOps Developer (+ Frontend) |

> The team was initially formed with 3 members; Harold NGuementa stepped away from the project. Frontend development is now shared between the two remaining members.

## 🗺️ Roadmap

- [x] Idea development and MVP validation with the client
- [x] Database schema
- [ ] New graphic identity (outside Holberton's branding)
- [ ] MVP development
- [ ] SQL/CSV backup feature
- [ ] ML-based camp recommendations *(out of scope for the MVP)*

## 📄 License

Distributed under the MIT License. See [`LICENSE`](./LICENSE) for details.
