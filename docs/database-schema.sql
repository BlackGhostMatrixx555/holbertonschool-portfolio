-- ============================================================
-- CampOrga — Schéma de base de données (PostgreSQL)
-- ============================================================

CREATE TYPE user_role AS ENUM (
  'super_admin', 'sem', 'swe', 'ssm', 'directeur_campus', 'directeur_technique'
);
CREATE TYPE user_status AS ENUM ('active', 'invited', 'disabled');
CREATE TYPE camp_status AS ENUM ('draft', 'published', 'archived');
CREATE TYPE modality_type AS ENUM ('age_restriction', 'education_level', 'other');
CREATE TYPE season_theme AS ENUM ('printemps', 'ete', 'automne', 'hiver');
CREATE TYPE contact_channel AS ENUM ('hotline', 'chatbot');
CREATE TYPE backup_format AS ENUM ('sql', 'csv');

-- ------------------------------------------------------------
-- USERS — comptes de la plateforme (organisateurs + super admin)
-- ------------------------------------------------------------
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name    VARCHAR(100) NOT NULL,
  last_name     VARCHAR(100) NOT NULL,
  email         VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role          user_role NOT NULL,
  status        user_status NOT NULL DEFAULT 'invited',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- CAMPS — les summer camps créés par les organisateurs
-- ------------------------------------------------------------
CREATE TABLE camps (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organizer_id   UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  name           VARCHAR(150) NOT NULL,
  slug           VARCHAR(160) NOT NULL UNIQUE,
  description    TEXT,
  start_date     DATE NOT NULL,
  end_date       DATE NOT NULL,
  city           VARCHAR(100),
  age            SMALLINT,
  capacity       INTEGER NOT NULL DEFAULT 0,
  status         camp_status NOT NULL DEFAULT 'draft',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (end_date >= start_date)
);

CREATE INDEX idx_camps_organizer ON camps(organizer_id);
CREATE INDEX idx_camps_status ON camps(status);

-- ------------------------------------------------------------
-- CAMP_MODALITIES — critères d'éligibilité par camp
-- ------------------------------------------------------------
CREATE TABLE camp_modalities (
  id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  camp_id  UUID NOT NULL REFERENCES camps(id) ON DELETE CASCADE,
  type     modality_type NOT NULL,
  label    VARCHAR(255) NOT NULL
);

CREATE INDEX idx_modalities_camp ON camp_modalities(camp_id);

-- ------------------------------------------------------------
-- LANDING_PAGES — page publique associée à chaque camp (1-1)
-- ------------------------------------------------------------
CREATE TABLE landing_pages (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  camp_id          UUID NOT NULL UNIQUE REFERENCES camps(id) ON DELETE CASCADE,
  season_theme     season_theme NOT NULL DEFAULT 'ete',
  hero_title       VARCHAR(200),
  hero_description TEXT,
  published_at     TIMESTAMPTZ
);

-- ------------------------------------------------------------
-- REGISTRATIONS — inscriptions des visiteurs à un camp
-- ------------------------------------------------------------
CREATE TABLE registrations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  camp_id     UUID NOT NULL REFERENCES camps(id) ON DELETE CASCADE,
  first_name  VARCHAR(100) NOT NULL,
  last_name   VARCHAR(100) NOT NULL,
  email       VARCHAR(255) NOT NULL,
  comment     TEXT,
  confirmed   BOOLEAN NOT NULL DEFAULT false,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_registrations_camp ON registrations(camp_id);
CREATE INDEX idx_registrations_email ON registrations(email);

-- ------------------------------------------------------------
-- CONTACT_MESSAGES — messages envoyés via hotline / chatbot IA
-- ------------------------------------------------------------
CREATE TABLE contact_messages (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  camp_id     UUID REFERENCES camps(id) ON DELETE SET NULL,
  name        VARCHAR(150),
  email       VARCHAR(255),
  message     TEXT NOT NULL,
  channel     contact_channel NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_contact_camp ON contact_messages(camp_id);

-- ------------------------------------------------------------
-- BACKUPS — exports déclenchés par le super admin (SQL / CSV)
-- ------------------------------------------------------------
CREATE TABLE backups (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  format        backup_format NOT NULL,
  triggered_by  UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  file_path     VARCHAR(500) NOT NULL,
  file_size_kb  INTEGER,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_backups_triggered_by ON backups(triggered_by);
