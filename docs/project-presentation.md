Voici le fichier complet à créer dans `docs/project-presentation.md`. Tu peux copier-coller le contenu ci-dessous.

---

### 📄 `docs/project-presentation.md`

```markdown
# 🏕️ CampOrga — Présentation Complète du Projet

**Auteur :** Thélyaan Dufrénoy (Lead Developer)
**Équipe :** Collins Odi Obi (Backend/DevOps), Quentin (Frontend)
**Contexte :** Portfolio Project — Holberton School France
**Version :** 1.0.0 (MVP)
**Date :** Octobre 2026

---

## 📋 Sommaire

1. [Le Problème](#1-🎯-le-problème)
2. [La Solution](#2-💡-la-solution)
3. [L'Architecture Technique](#3-🏗️-larchitecture-technique)
4. [Le Backend (API FastAPI)](#4-🔌-le-backend-api-fastapi)
5. [La Base de Données](#5-🗄️-la-base-de-données-7-tables)
6. [La Sécurité](#6-🛡️-la-sécurité)
7. [Les Tests et la Qualité](#7-🧪-les-tests-et-la-qualité)
8. [L'Infrastructure et le Déploiement](#8-🐳-linfrastructure-et-le-déploiement)
9. [L'État d'Avancement](#9-📊-létat-davancement)
10. [La Roadmap (V2)](#10-🗺️-la-roadmap-v2)
11. [Comment Contribuer](#11-🤝-comment-contribuer)

---

## 1. 🎯 Le Problème

Les équipes qui organisent des summer camps de code n'ont aujourd'hui **aucun outil centralisé** :
- Chaque camp est géré séparément (Excel, papier, emails).
- Aucune visibilité d'ensemble sur les camps de l'organisation.
- Le processus d'inscription n'est ni standardisé ni engageant.
- Les données sont dispersées et difficiles à sauvegarder.

**Conséquence :** perte de temps, erreurs de saisie, difficulté à suivre les inscriptions.

---

## 2. 💡 La Solution

**CampOrga** est une plateforme web qui centralise tout :

- 🗓️ **Création et gestion de camps** (dates, description, modalités d'éligibilité).
- 🌐 **Landing page publique par camp** (compte à rebours, présentation, partage LinkedIn).
- ✍️ **Inscription en ligne** (nom, prénom, email, commentaire, confirmation).
- 📊 **Dashboard organisateur** (vue sur les camps gérés et les inscriptions récentes).
- 👥 **Gestion des utilisateurs et des rôles** par un Super Admin (JWT + 2FA).
- 💾 **Export de backup** de la base (SQL et CSV), réservé au Super Admin.
- 💬 **Contact** (hotline + chatbot IA) sur chaque landing page.

---

## 3. 🏗️ L'Architecture Technique

```text
┌──────────────┐      HTTP/JSON      ┌──────────────┐        SQL        ┌──────────────┐
│   Frontend   │  ─────────────────▶ │   Backend    │ ─────────────────▶│  PostgreSQL  │
│ React + TS   │ ◀───────────────── │   FastAPI    │ ◀───────────────── │              │
└──────────────┘                     └──────────────┘                   └──────────────┘
                                             │
                                             ▼
                                   pg_dump (SQL) / CSV
                                      exports (backup)
```

**Stack :**

| Couche | Technologies |
|---|---|
| Frontend | React, Vite, TypeScript, Tailwind CSS, TanStack Query |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Auth | JWT (HS256), bcrypt, passlib, TOTP (2FA) |
| Base de données | PostgreSQL 16 |
| Infrastructure | Docker, Docker Compose |
| Tests | Pytest (96 tests, ~96% couverture) |

---

## 4. 🔌 Le Backend (API FastAPI)

### Structure des dossiers

```text
backend/app/
├── routes/          # Endpoints HTTP
├── schemas/         # Validation Pydantic
├── services/        # Logique métier
├── models/          # Modèles SQLAlchemy (7 tables)
├── security.py      # bcrypt + JWT
├── dependencies.py  # get_current_user, require_role
└── main.py          # Point d'entrée
```

### Endpoints principaux

| Méthode | Route | Auth | Rôle requis |
|---|---|---|---|
| `POST` | `/api/auth/login` | ❌ | — |
| `POST` | `/api/auth/register` | ❌ | — |
| `POST` | `/api/auth/2fa/setup` | ✅ | tous |
| `POST` | `/api/auth/2fa/login` | ❌ | — |
| `GET` | `/api/camps` | ❌ | — |
| `POST` | `/api/camps` | ✅ | organizer/admin |
| `GET` | `/api/camps/{slug}/public` | ❌ | — |
| `PATCH` | `/api/camps/{id}` | ✅ | owner/director/admin |
| `DELETE` | `/api/camps/{id}` | ✅ | owner/director/admin |
| `POST` | `/api/camps/{id}/registrations` | ❌ | — |
| `GET` | `/api/camps/{id}/registrations` | ✅ | owner/director/admin |
| `POST` | `/api/users` | ✅ | super_admin |
| `GET` | `/api/users` | ✅ | super_admin |
| `POST` | `/api/backups` | ✅ | super_admin |
| `GET` | `/api/backups` | ✅ | super_admin |
| `POST` | `/api/contact/chat` | ❌ | — |
| `POST` | `/api/contact/hotline` | ❌ | — |

**Documentation interactive :** `http://localhost:8000/docs` (Swagger UI)

---

## 5. 🗄️ La Base de Données (7 tables)

**Modèle relationnel :**

```text
users (1) ──< (N) camps (1) ──< (N) registrations
                        │
                        ├──< (N) camp_modalities
                        ├──(1)── landing_pages
                        └──< (N) contact_messages
```

- **`users`** : comptes (Super Admin, Organisateurs, Directeurs).
- **`camps`** : table centrale (dates, description, capacité).
- **`camp_modalities`** : critères d'éligibilité (âge, niveau).
- **`landing_pages`** : page publique par camp (1-1).
- **`registrations`** : inscriptions des visiteurs.
- **`contact_messages`** : messages hotline/chatbot.
- **`backups`** : historique des exports SQL/CSV.

**Contraintes d'intégrité :**
- `ON DELETE CASCADE` : supprimer un camp supprime ses données liées.
- `ON DELETE RESTRICT` : supprimer un utilisateur qui a créé des camps est bloqué.
- `ON DELETE SET NULL` : supprimer un camp ne supprime pas les messages de contact.

---

## 6. 🛡️ La Sécurité

| Aspect | Implémentation |
|---|---|
| **Mots de passe** | Hachage Bcrypt (jamais en clair) |
| **Sessions** | JWT stateless (HS256), expiration 24h |
| **2FA** | TOTP (compatible Google/Microsoft Authenticator) |
| **Vérification** | SMS et Email (mockés pour le MVP) |
| **Rôles (RBAC)** | `super_admin`, `sem`, `swe`, `ssm`, `directeur_campus`, `directeur_technique` |
| **Validation** | Pydantic (bloque les injections et données invalides) |
| **CORS** | Restreint à `http://localhost:5173` |

**Règles métier :**
- Le Super Admin est **éternel** (ne peut pas être supprimé).
- Les Directeurs peuvent superviser tous les camps.
- Les Organisateurs ne gèrent que leurs propres camps.
- Les Visiteurs n'ont pas de compte (inscriptions via `registrations`).

---

## 7. 🧪 Les Tests et la Qualité

**96 tests automatisés** avec Pytest :
- `test_auth.py` (16 tests) : login, register, JWT, rôles.
- `test_2fa.py` (8 tests) : setup, enable, login en 2 étapes.
- `test_verification.py` (7 tests) : SMS, Email, check-code.
- `test_camps.py` (23 tests) : CRUD, inscriptions, compteur.
- `test_backups.py` (11 tests) : SQL, CSV, download.
- `test_chat.py` (4 tests) : chatbot, hotline.
- `test_health.py` (3 tests) : `/health`, `/ready`, CORS.
- `test_models.py` (6 tests) : `__repr__`.

**Couverture :** ~96%

**Lancer les tests :**
```bash
./camporga.sh test
```

---

## 8. 🐳 L'Infrastructure et le Déploiement

**Docker Compose** orchestre 3 services :

| Service | Image | Port | Rôle |
|---|---|---|---|
| `db` | postgres:16 | 5432 | Base de données |
| `backend` | build local | 8000 | API FastAPI |
| `frontend` | build local | 5173 | Interface React |

**Script de gestion :** `camporga.sh`

```bash
./camporga.sh start      # Démarre DB + Backend + Frontend
./camporga.sh admin      # Crée le Super Admin
./camporga.sh test       # Lance les tests
./camporga.sh stop       # Arrête les services
./camporga.sh cleanup    # Détruit tout (conteneur + DB)
```

**Démarrage rapide :**
```bash
git clone https://github.com/BlackGhostMatrixx555/holbertonschool-portfolio.git
cd holbertonschool-portfolio
./camporga.sh start
./camporga.sh admin
```

**Accès :**
- API : `http://localhost:8000`
- Swagger : `http://localhost:8000/docs`
- Frontend : `http://localhost:5173`

---

## 9. 📊 L'État d'Avancement

| Composant | Statut |
|---|---|
| Backend (FastAPI) | ✅ 100% |
| Base de données (PostgreSQL) | ✅ 100% |
| Authentification (JWT + 2FA + SMS/Email) | ✅ 100% |
| Tests (96 tests, ~96% couverture) | ✅ 100% |
| Documentation (README, CHANGELOG, etc.) | ✅ 100% |
| Outil d'audit (`compat_evaluator.py`) | ✅ 100% |
| Frontend (React) | 🔄 En cours (Quentin) |
| Déploiement (Railway/Render) | ⏳ À venir |

---

## 10. 🗺️ La Roadmap (V2)

### Court terme
- Finaliser le frontend React (Quentin).
- Intégrer le frontend avec le backend.
- Déployer sur Railway ou Render.

### Moyen terme
- Remplacer le chatbot mock par une vraie API LLM (Claude/OpenAI).
- Ajouter un cache Redis pour les requêtes fréquentes.
- Migrer les backups vers un Object Storage (S3/MinIO).

### Long terme
- Scalabilité horizontale : Load Balancer, réplicas DB, Kubernetes.
- Multi-langue (FR/EN).
- Recommandation de camps par Machine Learning.

---

## 11. 🤝 Comment Contribuer

### Prérequis
- Docker et Docker Compose.
- Python 3.11+ (optionnel).
- Node.js 20+ (pour le frontend).

### Workflow Git
- `main` : branche stable (production).
- `dev` : branche d'intégration.
- `feature/*` : une branche par tâche.

### Convention de commits
- `feat:` : nouvelle fonctionnalité.
- `fix:` : correction de bug.
- `docs:` : documentation.
- `test:` : tests.
- `chore:` : tâches diverses.

### Lancer les tests avant chaque commit
```bash
./camporga.sh test
```

---

## 📎 Annexes

- **Repo GitHub :** `https://github.com/BlackGhostMatrixx555/holbertonschool-portfolio`
- **Branche de développement :** `tete-work`
- **Documentation technique :** `docs/stage3-technical-documentation.pdf`
- **Cahier des charges :** `docs/cahier-des-charges.pdf`
- **Roadmap de scalabilité :** `docs/scalability-roadmap.md`
- **Guide de démo :** `docs/demo-guide.md`
- **Guide frontend :** `docs/frontend-onboarding.md`

---

## 🎓 Conclusion

CampOrga est un projet **de niveau professionnel**, avec :
- Une API REST complète et sécurisée.
- Une base de données relationnelle solide.
- 96 tests automatisés (~96% de couverture).
- Une documentation exhaustive.
- Un outil d'audit multi-projets.
- Une roadmap claire pour la V2.

**Prochaine étape :** Finaliser le frontend avec Quentin, puis déployer la plateforme.
```

---

### 📋 Procédure

1.  **Crée le fichier** `docs/project-presentation.md` et colle le contenu ci-dessus.
2.  **Commit et push** :
    ```bash
    git add docs/project-presentation.md
    git commit -m "docs: add complete project presentation"
    git push origin tete-work
    ```
3.  **Partage le lien** avec Collins et Quentin (sur GitHub).

Ce document servira de **référence unique** pour toute l'équipe. Il est structuré pour être lu en 10 minutes et donne une vision complète du projet. 🚀
