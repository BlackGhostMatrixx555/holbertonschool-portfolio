# Changelog — CampOrga

Toutes les modifications notables du projet sont documentées dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et le projet respecte le [Semantic Versioning](https://semver.org/lang/fr/).

---

## [2.0.0] — 2026-11-03 — Fusion des branches `collins` et `tete-work`

Une seule version du projet : le back-end en couches et le front-end de `collins`,
enrichis des fonctionnalités de `tete-work`.

### Ajouté (repris de `tete-work`, réécrit dans la structure `api/` + `services/` + `schemas/`)
- **Inscription publique** des organisateurs (`POST /api/auth/register`) — compte créé
  inactif, à valider par le super admin (gestion des accès prévue par le cahier des charges).
- **Double authentification TOTP** : QR code, activation, désactivation, connexion en 2 étapes
  (`/api/auth/2fa/*`).
- **Vérification email / SMS** (envoi simulé) : codes stockés dans MongoDB, sous forme
  d'empreinte, avec expiration automatique (index TTL) et nombre d'essais limité.
- **Historique des sauvegardes** : table `backups`, `POST /api/backups`, `GET /api/backups`,
  `GET /api/backups/{id}/download`.
- **Mon compte** (`PATCH /api/users/me`, `DELETE /api/users/me`) et suppression d'un compte
  par le super admin (`DELETE /api/users/{id}`).
- Rôle **directeur technique** (`dt`).
- Front-end : pages `/inscription` et `/espace/compte`, étape « code à 6 chiffres » à la
  connexion, demandes d'accès en attente dans Utilisateurs, historique dans Sauvegardes.

### Modifié
- **Camps** : une seule colonne `age` (âge minimum, vide = tous âges) remplace
  `min_age` / `max_age`. Migration Alembic `e7a1c3f90b21` avec conversion des données.
- **`camporga.sh`** : adapté à la fusion (`.env` à la racine généré avec des secrets
  aléatoires ; `test` utilise la base `camporga_test` au lieu de vider la base de dev).

### Retiré
- **Paiement** : non repris, hors périmètre du MVP selon le cahier des charges
  (reste disponible sur la branche `tete-work`).

### Sécurité
- Le jeton temporaire 2FA ne peut plus servir de jeton de session (portée `scope` dans le JWT).
- La désactivation de la 2FA exige un code valide ; une 2FA active ne peut plus être écrasée.
- Codes de vérification générés avec `secrets`, code de test renvoyé uniquement en développement.
- Le super admin ne peut plus modifier son propre rôle.
- Suppression d'un compte refusée tant qu'il gère des camps ou a réalisé des sauvegardes.
- CORS : en-tête `Content-Disposition` exposé (nom réel des fichiers téléchargés).

### Documentation
- `database-schema.sql` réécrit d'après la base migrée (téléphone, 2FA, `status` des messages,
  enums actuels) avec la description des collections MongoDB.
- `diagram_database.png` / `database-schema.pdf` régénérés (source Mermaid `diagram_database.mmd`) :
  ajout du `status` des messages et des collections MongoDB.
- README (FR/EN), index `docs/README.md` et `project-presentation.md` mis à jour.
- `camporga.sh admin-reset` : suppression des données liées aux camps avant les camps.

### Testé
- Back-end : 127 tests, 97 % de couverture. Front-end : 37 tests.
- Scénario navigateur complet et audit axe-core : 0 violation WCAG 2.1 AA.

---

## [1.7.0] — 2026-11-02 — Outils d'ingénierie & Documentation

### Ajouté
- **`scripts/compat_evaluator.py`** — Outil d'audit multi-projets :
  - Détecte les routes API manquantes par rapport au contrat commun.
  - Compte les créations de Super Admin (sans faux positifs).
  - Scanne les failles de sécurité (secrets en dur, CORS permissif, DEBUG).
  - Génère un rapport Markdown par projet + un rapport global avec score sur 100.
  - Supporte `--full` pour exporter l'arborescence complète d'un projet.
- **`scripts/run_all_tests.sh`** — Script de tests automatisés (8 phases) :
  - Nettoyage, build, migrations, tests Pytest, sécurité, santé.
  - Génère un récapitulatif complet à la fin.
- **`docs/project-presentation.md`** — Présentation complète du projet (12 slides).
- **`docs/frontend-routing.md`** — Guide de routage React pour Quentin (guards, layouts, AuthContext).
- **`docs/diagram_database.png`** — Diagramme ERD de la base de données.

### Modifié
- **`camporga.sh`** — Détection automatique de Docker ou Podman.
- **`camporga.sh`** — Ajout de la commande `admin-reset` et affichage des identifiants par défaut.
- **`README.md` / `README.en.md`** — Section "Démarrage rapide avec camporga.sh".

### Testé
- 74 tests, 91% de couverture.

---

## [1.6.0] — 2026-11-02 — Système de paiement (Mock)

### Ajouté
- **`backend/app/models/payment.py`** — Modèle `Payment` avec `PaymentStatus` (pending, success, failed).
- **`backend/app/schemas/payment.py`** — `PaymentCreate`, `PaymentRead`.
- **`backend/app/services/payment_service.py`** — `PaymentService` avec commission de 10% pour la plateforme.
- **`backend/app/routes/payments.py`** — `POST /api/payments/checkout`.
- **`price`** ajouté au modèle `Camp` (prix en centimes).

### Modifié
- **`camporga.sh`** — Nettoyage de la base avant les tests (`TRUNCATE`).
- **`tests/test_auth.py`** — Email unique par test (`uuid`) pour éviter les conflits.

### Testé
- 74 tests, 91% de couverture.
- Le paiement Mock calcule correctement :
  - `amount_total: 5000` (50€)
  - `platform_fee: 500` (5€ de commission)
  - `organizer_amount: 4500` (45€ pour l'organisateur)

### Notes
- En V2, le Mock sera remplacé par Stripe Connect pour gérer les vrais paiements (carte, Apple Pay, PayPal) et les transferts automatiques vers les comptes bancaires des organisateurs.

---

## [1.5.0] — 2026-10-23 — Vérification SMS/Email

### Ajouté
- **`backend/app/services/verification_service.py`** — `VerificationService` :
  - `send_sms_code()` : génère un code à 6 chiffres et le "logge" (mock).
  - `send_email_code()` : idem pour l'email.
  - `verify_code()` : valide le code, gère l'expiration (5 min) et la consommation unique.
- **`backend/app/routes/verification.py`** — 3 endpoints :
  - `POST /api/auth/verify/send-sms`
  - `POST /api/auth/verify/send-email`
  - `POST /api/auth/verify/check-code`
- **`backend/tests/test_verification.py`** — 7 tests.

### Modifié
- **`backend/app/models/user.py`** — Ajout du champ `phone_number`.
- **`backend/app/schemas/user.py`** — Exposition de `phone_number` dans `UserRead`.
- **`backend/app/main.py`** — Branchement du router `verification`, version `0.6.0`.
- **`backend/alembic/versions/f2abce421ba7_*.py`** — Migration pour `phone_number`.

### Notes
- **Mode Mock** : en MVP, les codes sont affichés dans les logs (`📱 [MOCK SMS]`, `📧 [MOCK EMAIL]`) au lieu d'être réellement envoyés. En production, il suffira de remplacer le `print()` par un appel à Twilio/SendGrid.
- **Sécurité** : les codes sont valides 5 minutes et à usage unique (consommés à la première validation).

### Testé
- 74 tests, ~96% de couverture.

---

## [1.4.0] — 2026-10-22 — Double Authentification (2FA)

### Ajouté
- **`backend/app/schemas/two_factor.py`** — Schémas `TwoFactorSetupResponse`, `TwoFactorVerifyRequest`, `TwoFactorLoginRequest`.
- **`backend/app/services/two_factor_service.py`** — `TwoFactorService` :
  - `generate_secret()` : secret TOTP + QR code en base64.
  - `verify_code()` : valide un code TOTP.
  - `enable_2fa()`, `disable_2fa()`.
  - `create_temp_token()`, `verify_temp_token()`.
- **`backend/app/routes/two_factor.py`** — 4 endpoints :
  - `POST /api/auth/2fa/setup`
  - `POST /api/auth/2fa/enable`
  - `POST /api/auth/2fa/disable`
  - `POST /api/auth/2fa/login`
- **`backend/tests/test_2fa.py`** — 7 tests.

### Modifié
- **`backend/app/models/user.py`** — Ajout de `totp_secret` et `is_2fa_enabled`.
- **`backend/app/schemas/auth.py`** — Ajout de `requires_2fa` et `temp_token`.
- **`backend/app/routes/auth.py`** — Le login renvoie un `temp_token` si 2FA activée.
- **`backend/app/main.py`** — Branchement du router, version `0.5.0`.
- **`backend/requirements.txt`** — Ajout de `pyotp==2.9.0` et `qrcode[pil]==7.4.2`.

### Notes de sécurité
- Les codes TOTP sont valides **30 secondes** (tolérance de 1 fenêtre = 90 secondes max).
- Le `temp_token` expire après **5 minutes**.
- La 2FA est **optionnelle** : l'utilisateur peut l'activer/désactiver à tout moment.

### Testé
- 67 tests, ~96% de couverture.

---

## [1.3.0] — 2026-10-22 — Inscriptions publiques & Hiérarchie des rôles

### Ajouté — Inscriptions
- **`backend/app/schemas/registration.py`** — `RegistrationCreate`, `RegistrationRead`.
- **`backend/app/services/registration_service.py`** — `RegistrationService` :
  - `create()` : inscription avec vérification de la capacité.
  - `list_for_camp()` : liste des inscrits.
  - `count_for_camp()` : compteur d'inscrits.
- **`POST /api/camps/{id}/registrations`** — Endpoint public.
- **`GET /api/camps/{id}/registrations`** — Liste des inscrits.
- **`DELETE /api/camps/{id}/registrations/{reg_id}`** — Suppression d'une inscription.
- **`CampPublicRead`** — Ajout de `capacity` et `registration_count`.

### Ajouté — Hiérarchie des rôles
- **Super Admin éternel** : impossible à supprimer (ni par lui-même, ni par un autre Super Admin).
- **Super Admin tout-puissant** : `DELETE /api/users/{id}` pour supprimer n'importe qui.
- **Directeurs superviseurs** : `directeur_campus` et `directeur_technique` peuvent gérer tous les camps.
- **Organisateurs limités** : `sem`, `swe`, `ssm` gèrent uniquement leurs propres camps.

### Modifié
- **`backend/app/routes/camps.py`** — Logique de vérification des droits basée sur la hiérarchie.
- **`backend/app/routes/users.py`** — Protection du Super Admin + suppression par ID.

### Testé
- 59 tests, ~96% de couverture.

---

## [1.2.0] — 2026-10-21 — Inscription publique & Self-Service

### Ajouté
- **`POST /api/auth/register`** — Inscription publique (rôle `SEM` par défaut). Aucune authentification requise.
- **`DELETE /api/users/me`** — Suppression de son propre compte (self-service).
- **`RegisterRequest`** — Schéma Pydantic.
- **5 nouveaux tests** dans `tests/test_auth.py`.

### Modifié
- **`backend/app/routes/auth.py`** — Ajout du endpoint `register`.
- **`backend/app/routes/users.py`** — Ajout du endpoint `delete_my_account`.
- **`backend/app/schemas/auth.py`** — Ajout du schéma `RegisterRequest`.

### Notes
- **Sécurité** : L'endpoint `/register` attribue **toujours** le rôle `SEM`. Impossible de créer un `super_admin` via cet endpoint public.
- **Self-service** : Si un utilisateur a créé des camps, la contrainte `ON DELETE RESTRICT` l'empêchera de supprimer son compte (erreur `400`).

### Testé
- 55 tests, 95% de couverture.

---

## [1.1.0] — 2026-10-21 — Chatbot & Roadmap de scalabilité

### Ajouté
- **`backend/app/schemas/chat.py`** — `ChatRequest`, `ChatResponse`, `ContactMessageCreate`.
- **`backend/app/services/chat_service.py`** — `ChatService` (mock basé sur des règles).
- **`backend/app/routes/chat.py`** — `POST /api/contact/chat` et `POST /api/contact/hotline`.
- **`backend/tests/test_chat.py`** — 4 tests.
- **`docs/scalability-roadmap.md`** — Plan de scalabilité de 10 à 100 000 utilisateurs.
- **`docs/demo-guide.md`** — Script de démo pour la soutenance.

### Modifié
- **`README.md` / `README.en.md`** — Ajout des endpoints de contact et lien vers la roadmap.

### Testé
- 50 tests.

---

## [0.6.0] — 2026-10-20 — Backups SQL/CSV

### Ajouté
- **`backend/app/services/backup_service.py`** — `BackupService` :
  - `create()` : génère un backup SQL (via `pg_dump`) ou CSV (ZIP de tous les CSV).
  - `list()`, `get_by_id()`, `get_file_path()`.
- **`backend/app/schemas/backup.py`** — `BackupCreate`, `BackupRead`.
- **`backend/app/routes/backups.py`** — 3 endpoints (super admin uniquement) :
  - `POST /api/backups`
  - `GET /api/backups`
  - `GET /api/backups/{id}/download`
- **`backend/Dockerfile`** — Ajout de `postgresql-client` (pour `pg_dump`).
- **`backend/tests/test_backups.py`** — 11 tests.

### Modifié
- **`backend/app/main.py`** — Branchement du router `backups`, version `0.3.0`.

### Corrigé
- **Bug SQLAlchemy 2.0** : `self.db.execute("SELECT ...")` n'accepte plus les chaînes brutes. Correctif : envelopper dans `text(...)`.

### Testé
- 50 tests, 98% de couverture.

---

## [0.5.0] — 2026-10-09 — Authentification JWT

### Ajouté
- **`backend/app/security.py`** — hachage bcrypt + JWT HS256 :
  - `hash_password()`, `verify_password()`.
  - `create_access_token()`, `decode_access_token()`.
- **`backend/app/schemas/types.py`** — `DevEmailStr` (autorise les TLD `.test`).
- **`backend/app/schemas/auth.py`** — `LoginRequest`, `TokenResponse`.
- **`backend/app/schemas/user.py`** — `UserCreate`, `UserRead` (sans `password_hash`).
- **`backend/app/services/user_service.py`** — `UserService` :
  - `create()`, `get_by_id()`, `get_by_email()`, `list()`, `authenticate()`.
- **`backend/app/routes/auth.py`** — `POST /api/auth/login`.
- **`backend/app/routes/users.py`** — `POST /api/users`, `GET /api/users` (super admin only).
- **`backend/app/dependencies.py`** — vrai `get_current_user` (JWT) + `require_role(...)`.
- **`backend/tests/test_auth.py`** — 10 tests.

### Modifié
- **`backend/app/dependencies.py`** — suppression du stub `X-User-Id`, remplacé par JWT.
- **`backend/tests/conftest.py`** — fixture `auth_headers` génère un vrai JWT.
- **`backend/tests/test_camps.py`** — 3 tests adaptés au JWT.
- **`backend/requirements.txt`** — ajout `bcrypt==4.0.1`, `email-validator==2.2.0`.

### Corrigé
- **Bug `passlib` + `bcrypt 5.0.0`** : incompatibilité (attribut `__about__` supprimé, refus des mots de passe > 72 bytes). Correctif : épingler `bcrypt==4.0.1`.
- **Bug `email-validator`** : refus des TLD `.test` (RFC 6761). Correctif : `DevEmailStr` avec `test_environment=True`.

### Testé
- 35 tests, ~96% de couverture.

---

## [0.2.0] — 2026-10-05 — Étape 4 : Endpoints CRUD Camps

### Ajouté
- **`backend/app/schemas/camp.py`** — `CampCreate`, `CampUpdate`, `CampRead`, `CampPublicRead`, `ModalityCreate`, `ModalityRead`, `LandingPageRead`.
- **`backend/app/services/camp_service.py`** — `CampService` :
  - `create()`, `list()`, `get_by_slug()`, `update()`.
  - `slugify()` et `_generate_unique_slug()`.
- **`backend/app/routes/camps.py`** — 3 endpoints CRUD :
  - `POST /api/camps`
  - `GET /api/camps`
  - `GET /api/camps/{slug}/public`
- **`backend/app/dependencies.py`** — stub `get_current_user` (header `X-User-Id`).
- **Validator Pydantic `check_dates`** — retourne `422` au lieu de `500` pour les dates invalides.

### Modifié
- **`backend/app/main.py`** — branchement du router `camps`.
- **`backend/app/database.py`** — helper `pg_enum()` (fix Alembic).
- **`backend/app/models/*`** — utilisation de `pg_enum()`.
- **`backend/alembic/versions/c51e59a870dc_*.py`** — migration régénérée avec les bonnes valeurs d'enum.
- **`backend/alembic/script.py.mako`** — ajout du fichier template manquant.

### Corrigé
- **Bug Alembic — enums en majuscules** : `alembic revision --autogenerate` générait les `sa.Enum(...)` avec les names au lieu des values. Correctif : helper `pg_enum()` avec `values_callable`.
- **Bug Alembic — `DROP TYPE` manquant** : `downgrade()` ne supprimait pas les types ENUM. Correctif : bloc `DROP TYPE IF EXISTS` en fin de `downgrade()`.
- **Bug 500 sur dates invalides** : correctif `@model_validator` Pydantic → `422`.

### Testé
- 24 tests, 98% de couverture.

---

## [0.1.0] — 2026-09-24 — Étapes 1 à 3 : Fondations

### Ajouté
- **Étape 1** : `config.py`, `database.py`, `main.py`, `Dockerfile`, `docker-compose.yml`, `backend/.env.example`.
- **Étape 2** : 7 modèles SQLAlchemy (`User`, `Camp`, `CampModality`, `LandingPage`, `Registration`, `ContactMessage`, `Backup`).
- **Étape 3** : migration Alembic initiale (`ecdd986c3849_initial_schema.py`).

### Corrigé
- **Bug Alembic — `DROP TYPE` manquant** : `downgrade()` supprimait les tables mais pas les types ENUM. Correctif : bloc `DROP TYPE IF EXISTS` en fin de `downgrade()`.

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
