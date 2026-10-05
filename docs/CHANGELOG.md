# Changelog — CampOrga

Toutes les modifications notables du projet sont documentées dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et le projet respecte le [Semantic Versioning](https://semver.org/lang/fr/).

---

## [Non publié]

### En cours — Étape 5 : Authentification & rôles

- **À venir** : remplacement du stub `get_current_user` par une vraie authentification JWT.
- **À venir** : hachage des mots de passe avec `passlib[bcrypt]`.
- **À venir** : endpoint `POST /api/auth/login`.
- **À venir** : vérification des rôles (`super_admin`, `sem`, `swe`, `ssm`, `directeur_campus`, `directeur_technique`).

---

## [0.2.0] — 2026-10-05 — Étape 4 : Endpoints CRUD Camps

### Ajouté

- **`backend/app/schemas/`** — Nouveau dossier de schémas Pydantic :
  - `schemas/__init__.py`
  - `schemas/camp.py` — schémas `CampCreate`, `CampUpdate`, `CampRead`, `CampPublicRead`, `ModalityCreate`, `ModalityRead`, `LandingPageRead`.
- **`backend/app/dependencies.py`** — Dépendance `get_current_user` (stub temporaire via header `X-User-Id`, en attendant l'Étape 5).
- **`backend/app/services/camp_service.py`** — Service métier `CampService` :
  - `create(data, organizer_id)` — création d'un camp + ses modalités, avec génération de slug unique.
  - `list(status, organizer_id)` — liste filtrée des camps.
  - `get_by_slug(slug)` — récupération par slug (route publique).
  - `update(camp, data)` — mise à jour partielle.
  - Helper `slugify(name)` — génération de slug lisible (accents, tirets, casse).
- **`backend/app/routes/camps.py`** — 3 endpoints HTTP :
  - `POST /api/camps` — créer un camp (authentifié).
  - `GET /api/camps` — lister les camps (filtres `status` et `organizer_id` optionnels).
  - `GET /api/camps/{slug}/public` — consulter un camp via son slug (vue publique filtrée).
- **`backend/app/routes/__init__.py`** — package des routers.
- **Validator Pydantic `check_dates`** dans `CampCreate` et `CampUpdate` :
  - Vérifie `end_date >= start_date` **avant** d'atteindre la base.
  - Retourne un `422 Unprocessable Entity` clair au lieu d'un `500 Internal Server Error`.

### Modifié

- **`backend/app/main.py`** — branchement du router `camps` avec `prefix="/api"`.
- **`backend/app/database.py`** — ajout du helper `pg_enum()` :
  - Force SQLAlchemy à utiliser les **values** Python (minuscules) au lieu des **names** (majuscules) pour les types ENUM PostgreSQL.
  - Résout définitivement l'incohérence Python ↔ PostgreSQL.
- **`backend/app/models/user.py`** — utilisation de `pg_enum()` pour `role` et `status`.
- **`backend/app/models/camp.py`** — utilisation de `pg_enum()` pour `status` (Camp) et `type` (CampModality).
- **`backend/app/models/landing_page.py`** — utilisation de `pg_enum()` pour `season_theme`.
- **`backend/app/models/contact_backup.py`** — utilisation de `pg_enum()` pour `channel` (ContactMessage) et `format` (Backup).
- **`backend/alembic/versions/c51e59a870dc_initial_schema.py`** — migration régénérée avec les bonnes valeurs d'enum :
  - Les 7 enums contiennent désormais les **values en minuscules** (`'super_admin'`, `'draft'`, etc.).
  - Ajout du bloc `DROP TYPE IF EXISTS` en fin de `downgrade()` pour supprimer proprement les enums PostgreSQL lors d'un rollback.
- **`backend/alembic/script.py.mako`** — ajout du fichier template manquant (nécessaire à `alembic revision --autogenerate`).

### Corrigé

- **Bug Alembic — enums en majuscules** : `alembic revision --autogenerate` générait les `sa.Enum(...)` avec les **names** Python (`'SUPER_ADMIN'`, `'DRAFT'`, etc.) au lieu des **values** (`'super_admin'`, `'draft'`). Résultat : `LookupError: 'super_admin' is not among the defined enum values` à la lecture, et `invalid input value for enum user_role` à l'écriture.
  - **Correctif** : helper `pg_enum()` avec `values_callable`, migration régénérée.
- **Bug Alembic — `DROP TYPE` manquant** (déjà corrigé en Étape 3, re-confirmé) : `downgrade()` ne supprimait pas les types ENUM, ce qui cassait un `upgrade` suivant avec `type "user_role" already exists`.
  - **Correctif** : bloc `for enum_name in (...) : op.execute("DROP TYPE IF EXISTS ...")` en fin de `downgrade()`.
- **Bug 500 sur dates invalides** : envoyer `end_date < start_date` déclenchait la `CheckConstraint` PostgreSQL et renvoyait un `500` opaque.
  - **Correctif** : `@model_validator` Pydantic dans `CampCreate` et `CampUpdate` → renvoie un `422` avec message clair.

### Testé

Tous les tests ont été réalisés manuellement via Swagger UI sur une base PostgreSQL réelle (via Docker Compose) :

| # | Test | Attendu | Résultat |
|---|---|---|---|
| 1 | `POST /api/camps` avec données valides | `201 Created` | ✅ |
| 2 | `GET /api/camps` | `200 OK` (liste) | ✅ |
| 3 | `GET /api/camps/{slug}/public` | `200 OK` (filtré) | ✅ |
| 4a | `POST /api/camps` sans header `X-User-Id` | `401` | ✅ |
| 4b | `POST /api/camps` avec UUID inexistant | `401` | ✅ |
| 4c | `POST /api/camps` avec dates inversées | `422` | ✅ |
| 4d | `POST /api/camps` avec dates valides | `201` | ✅ |

### Notes techniques

- **Le slug est non modifiable** via `PATCH /api/camps/{id}` : il sert d'identifiant public stable et le changer casserait les liens partagés. Si besoin, on ajoutera un endpoint dédié plus tard.
- **`capacity` et `organizer_id` ne sont pas exposés** dans `CampPublicRead` : ce sont des données internes qui ne concernent pas le visiteur.
- **Pas de vérification de rôle** pour l'instant : tout utilisateur authentifié peut créer un camp. À restreindre en Étape 5 (`organizer` ou `super_admin`).
- **Le stub `get_current_user`** lit un header `X-User-Id` et charge l'utilisateur en base. Il sera remplacé par une vraie vérification JWT en Étape 5.

---

## [0.1.0] — 2026-09-24 — Étapes 1 à 3 : Fondations

### Ajouté

- **Étape 1 — Structure + connexion DB** :
  - `backend/app/config.py` — configuration Pydantic Settings (lit `.env`).
  - `backend/app/database.py` — engine SQLAlchemy, `SessionLocal`, `get_db()`, `Base`.
  - `backend/app/main.py` — app FastAPI, CORS pour `localhost:5173`, route `/health`.
  - `backend/Dockerfile`, `backend/.env.example`, `docker-compose.yml` (PostgreSQL 16 + backend).

- **Étape 2 — Modèles SQLAlchemy** :
  - `backend/app/models/enums.py` — 7 enums Python (`UserRole`, `UserStatus`, `CampStatus`, `ModalityType`, `SeasonTheme`, `ContactChannel`, `BackupFormat`).
  - `backend/app/models/user.py` — modèle `User`.
  - `backend/app/models/camp.py` — modèles `Camp` et `CampModality` (avec `CheckConstraint` sur les dates).
  - `backend/app/models/landing_page.py` — modèle `LandingPage` (relation 1-1).
  - `backend/app/models/registration.py` — modèle `Registration`.
  - `backend/app/models/contact_backup.py` — modèles `ContactMessage` et `Backup`.
  - `backend/app/models/__init__.py` — regroupe tous les modèles.

- **Étape 3 — Migrations Alembic** :
  - `backend/alembic.ini`
  - `backend/alembic/env.py` (branché sur `Base.metadata` et `settings.database_url`)
  - `backend/alembic/versions/ecdd986c3849_initial_schema.py` — migration initiale (remplacée plus tard par `c51e59a870dc`).

### Corrigé

- **Bug Alembic — `DROP TYPE` manquant** : `downgrade()` supprimait les tables mais pas les types ENUM PostgreSQL, provoquant `type "user_role" already exists` au prochain `upgrade`.
  - **Correctif** : bloc `DROP TYPE IF EXISTS` en fin de `downgrade()`.

### Testé

- `docker compose up --build` → `/health` retourne `{"status":"ok"}`.
- `/docs` affiche Swagger UI.
- `alembic upgrade head` crée les 7 tables + `alembic_version`.
- Cycle `downgrade base` → `upgrade head` testé 3 fois avec succès.

---

## [0.0.1] — 2026-08-29 — Stage 4 lancé

### Ajouté

- Début du Stage 4 (MVP Development) : plan en 6 étapes.
  - ✅ Étape 1 — Structure + connexion DB
  - ✅ Étape 2 — Modèles SQLAlchemy
  - ✅ Étape 3 — Migrations Alembic
  - 🔄 Étape 4 — Endpoints CRUD
  - ⏳ Étape 5 — Auth & rôles
  - ⏳ Étape 6 — Backup SQL/CSV

---

## Format des versions

- **MAJOR** : changement incompatible avec l'API publique.
- **MINOR** : ajout de fonctionnalité compatible.
- **PATCH** : correction de bug compatible.

## Types de changements

- **Ajouté** : nouvelles fonctionnalités.
- **Modifié** : changements dans les fonctionnalités existantes.
- **Déprécié** : fonctionnalités bientôt supprimées.
- **Supprimé** : fonctionnalités retirées.
- **Corrigé** : corrections de bugs.
- **Sécurité** : correctifs de sécurité.
- **Testé** : tests ajoutés ou modifiés.

### Testé

Suite Pytest de **11 tests** couvrant tous les cas d'usage de l'Étape 4 :

- `test_health.py` — 1 test (route `/health`).
- `test_camps.py` — 10 tests :
  - Création avec succès (`201`).
  - Unicité des slugs (`camp-duplique`, `camp-duplique-2`).
  - Création sans authentification (`401`).
  - Création avec UUID inexistant (`401`).
  - Création avec dates inversées (`422`).
  - Liste vide (`200` + `[]`).
  - Liste avec un camp créé (`200`).
  - Filtre par statut (`?status=draft`).
  - Vue publique (`200`, filtrage correct).
  - Vue publique avec slug inexistant (`404`).

**Fixtures** (`conftest.py`) :
- `db_session` : session SQLAlchemy avec rollback automatique en fin de test.
- `client` : `TestClient` FastAPI branché sur `db_session` via `dependency_overrides`.
- `test_user` : super_admin de test avec UUID fixe.
- `auth_headers` : header `X-User-Id` prêt à l'emploi.

**Résultat** : `11 passed in 0.20s`. Aucune donnée n'est laissée en base après les tests grâce au rollback.
