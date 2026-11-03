-- ============================================================
-- CampOrga — Schéma de base de données (PostgreSQL 16)
-- ============================================================
-- Ce fichier est une version LISIBLE du schéma réel, obtenue après
-- `alembic upgrade head` (révision e7a1c3f90b21, fusion collins + tete-work).
-- La source de vérité reste les migrations Alembic (backend/alembic/versions/)
-- et les modèles SQLAlchemy (backend/app/models/).
--
-- Remarques :
--  * Les valeurs d'enum sont stockées en MAJUSCULES (nom des membres Python).
--  * Les UUID sont générés par l'application (uuid4), pas par la base.
--  * Les suppressions en cascade (camp -> inscriptions, modalités, landing
--    page, messages) sont gérées par l'ORM (cascade="all, delete-orphan").
--  * Les données non relationnelles (conversations du chatbot, codes de
--    vérification) sont dans MongoDB : voir la fin de ce fichier.
-- ============================================================

CREATE TYPE userrole       AS ENUM ('ORGANIZER', 'ADMIN', 'SUPER_ADMIN', 'SEM', 'SWE', 'SSM', 'DC', 'DT');
CREATE TYPE userstatus     AS ENUM ('ACTIVE', 'INACTIVE', 'DISABLED');
CREATE TYPE campstatus     AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED');
CREATE TYPE modalitytype   AS ENUM ('INCLUDED', 'OPTION', 'AGE_RESTRICTION', 'EDUCATION_LEVEL', 'OTHER');
CREATE TYPE seasontheme    AS ENUM ('SUMMER', 'WINTER', 'SPRING', 'AUTUMN');
CREATE TYPE contactchannel AS ENUM ('HOTLINE', 'CHATBOT');
CREATE TYPE messagestatus  AS ENUM ('UNREAD', 'READ', 'ARCHIVED');
CREATE TYPE backupformat   AS ENUM ('SQL', 'CSV');

-- ------------------------------------------------------------
-- USERS — comptes de la plateforme (organisateurs + super admin)
-- Une inscription publique crée un compte INACTIVE (rôle SEM) que le
-- super admin doit activer. La 2FA TOTP est optionnelle.
-- ------------------------------------------------------------
CREATE TABLE users (
  id             UUID PRIMARY KEY,
  first_name     VARCHAR,
  last_name      VARCHAR,
  email          VARCHAR NOT NULL,
  password_hash  VARCHAR NOT NULL,            -- bcrypt
  role           userrole NOT NULL,
  status         userstatus NOT NULL,
  phone_number   VARCHAR(20),                 -- pour l'envoi de code par SMS
  totp_secret    VARCHAR(32),                 -- secret TOTP (2FA)
  is_2fa_enabled BOOLEAN NOT NULL DEFAULT false,
  created_at     TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX ix_users_email ON users(email);

-- ------------------------------------------------------------
-- CAMPS — les summer camps créés par les organisateurs
-- `age` = âge minimum (NULL = tous âges). Remplace min_age / max_age.
-- ------------------------------------------------------------
CREATE TABLE camps (
  id            UUID PRIMARY KEY,
  organizer_id  UUID NOT NULL REFERENCES users(id),
  name          VARCHAR NOT NULL,
  slug          VARCHAR NOT NULL,
  description   TEXT,
  start_date    DATE NOT NULL,
  end_date      DATE NOT NULL,                -- end_date >= start_date (validé par l'API)
  city          VARCHAR NOT NULL,
  age           SMALLINT,                     -- 0 à 99, NULL = tous âges
  capacity      INTEGER NOT NULL,
  status        campstatus NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX ix_camps_slug ON camps(slug);

-- ------------------------------------------------------------
-- CAMP_MODALITIES — ce qui est inclus, options, critères d'éligibilité
-- ------------------------------------------------------------
CREATE TABLE camp_modalities (
  id       UUID PRIMARY KEY,
  camp_id  UUID NOT NULL REFERENCES camps(id),
  type     modalitytype NOT NULL,
  label    VARCHAR NOT NULL
);

-- ------------------------------------------------------------
-- LANDING_PAGES — page publique associée à chaque camp (1-1)
-- ------------------------------------------------------------
CREATE TABLE landing_pages (
  id               UUID PRIMARY KEY,
  camp_id          UUID NOT NULL UNIQUE REFERENCES camps(id),
  season_theme     seasontheme NOT NULL,
  hero_title       VARCHAR NOT NULL,
  hero_description TEXT,
  published_at     TIMESTAMPTZ
);

-- ------------------------------------------------------------
-- REGISTRATIONS — inscriptions des visiteurs à un camp
-- ------------------------------------------------------------
CREATE TABLE registrations (
  id          UUID PRIMARY KEY,
  camp_id     UUID NOT NULL REFERENCES camps(id),
  first_name  VARCHAR NOT NULL,
  last_name   VARCHAR NOT NULL,
  email       VARCHAR NOT NULL,
  comment     TEXT,
  confirmed   BOOLEAN NOT NULL,               -- présence confirmée par l'organisateur
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------
-- CONTACT_MESSAGES — messages envoyés via la hotline d'un camp
-- ------------------------------------------------------------
CREATE TABLE contact_messages (
  id          UUID PRIMARY KEY,
  camp_id     UUID NOT NULL REFERENCES camps(id),
  name        VARCHAR NOT NULL,
  email       VARCHAR NOT NULL,
  message     TEXT NOT NULL,
  channel     contactchannel NOT NULL,
  status      messagestatus NOT NULL,         -- non lu / lu / archivé
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------
-- BACKUPS — historique des exports déclenchés par le super admin
-- ON DELETE RESTRICT : un compte qui a déclenché un backup ne peut pas
-- être supprimé (traçabilité).
-- ------------------------------------------------------------
CREATE TABLE backups (
  id            UUID PRIMARY KEY,
  format        backupformat NOT NULL,
  triggered_by  UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  file_path     VARCHAR(500) NOT NULL,        -- jamais exposé par l'API
  file_size_kb  INTEGER,
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ix_backups_triggered_by ON backups(triggered_by);

-- ============================================================
-- MongoDB (base NoSQL `camporga`) — pour information
-- ============================================================
-- Collection chat_conversations : une conversation du chatbot par session
--   { _id, session_id (unique), camp_id, camp_slug,
--     messages: [ { role: "visitor"|"bot", content, intent, at } ],
--     created_at, updated_at }
--   Index : session_id unique ; (camp_id, updated_at desc) ;
--           TTL sur updated_at (CHAT_RETENTION_DAYS = 90 jours, RGPD).
--
-- Collection verification_codes : un code email/SMS actif par utilisateur
--   { _id, user_id (unique), method: "email"|"sms", code_hash (SHA-256),
--     attempts, created_at, expires_at }
--   Index : user_id unique ; TTL sur expires_at (expiration à 5 minutes).
