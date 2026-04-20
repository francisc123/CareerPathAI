-- CareerPath AI — PostgreSQL Schema
-- Runs automatically on first container start

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- trigram index for text search

-- ── Users & Auth ──────────────────────────────────────────────────────────────
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE profiles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    full_name       VARCHAR(255),
    title           VARCHAR(255),
    location        VARCHAR(255),
    linkedin_url    VARCHAR(500),
    target_role     VARCHAR(255),
    seniority_level VARCHAR(50),   -- junior | mid | senior | lead
    cv_score        SMALLINT,      -- 0-100
    current_flow    VARCHAR(20),   -- ready | needs_prep | interview
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── CV Uploads ────────────────────────────────────────────────────────────────
CREATE TABLE cv_uploads (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    minio_path   TEXT NOT NULL,
    file_name    TEXT NOT NULL,
    status       VARCHAR(30) DEFAULT 'uploaded',  -- uploaded | analyzing | completed | failed
    score        SMALLINT,
    skills       JSONB,
    gaps         JSONB,
    raw_text     TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── Job Scraping ──────────────────────────────────────────────────────────────
CREATE TABLE scraped_jobs (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    title        VARCHAR(500) NOT NULL,
    company      VARCHAR(255),
    location     VARCHAR(255),
    url          TEXT UNIQUE,
    description  TEXT,
    source       VARCHAR(50),   -- linkedin | indeed | ejobs | bestjobs
    scraped_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE job_matches (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    job_id        UUID REFERENCES scraped_jobs(id),
    match_score   NUMERIC(5,2),
    cover_letter  TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── Learning Paths ────────────────────────────────────────────────────────────
CREATE TABLE learning_paths (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    modules      JSONB NOT NULL,   -- array of {title, resources, quizId, weekNumber}
    total_weeks  SMALLINT,
    status       VARCHAR(20) DEFAULT 'active',  -- active | completed
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE quiz_attempts (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    module_id    VARCHAR(100),
    score        NUMERIC(5,2),
    answers      JSONB,
    passed       BOOLEAN,
    attempted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_progress (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    modules_completed   SMALLINT DEFAULT 0,
    modules_total       SMALLINT DEFAULT 0,
    quizzes_passed      SMALLINT DEFAULT 0,
    last_activity       TIMESTAMPTZ DEFAULT NOW()
);

-- ── Interview Sessions ────────────────────────────────────────────────────────
CREATE TABLE interview_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    type            VARCHAR(20) NOT NULL,   -- hr | technical
    status          VARCHAR(20) DEFAULT 'active',  -- active | completed
    score           NUMERIC(5,2),
    feedback        JSONB,
    transcript      JSONB,
    duration_secs   INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX idx_cv_uploads_user_id   ON cv_uploads(user_id);
CREATE INDEX idx_job_matches_user_id  ON job_matches(user_id);
CREATE INDEX idx_quiz_attempts_user   ON quiz_attempts(user_id);
CREATE INDEX idx_interview_user       ON interview_sessions(user_id);
CREATE INDEX idx_scraped_jobs_user    ON scraped_jobs(user_id);
