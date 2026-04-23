#!/bin/bash
set -e

echo "Initializare arhitectura Microservicii (5 baze de date)..."

# 1. Crearea bazelor de date fizice
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE user_db;
    CREATE DATABASE cv_db;
    CREATE DATABASE jobs_db;
    CREATE DATABASE learning_db;
    CREATE DATABASE interview_db;
EOSQL

echo "Baze de date create. Aplicare scheme..."

# 2. Schema pentru USER-SERVICE
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "user_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE IF NOT EXISTS users (
        id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email         VARCHAR(255) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at    TIMESTAMPTZ DEFAULT NOW(),
        updated_at    TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS profiles (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id         UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE, -- Permis (aceeasi baza de date)
        full_name       VARCHAR(255),
        title           VARCHAR(255),
        location        VARCHAR(255),
        linkedin_url    VARCHAR(500),
        target_role     VARCHAR(255),
        seniority_level VARCHAR(50),
        cv_score        SMALLINT,
        current_flow    VARCHAR(20),
        updated_at      TIMESTAMPTZ DEFAULT NOW()
    );
EOSQL

# 3. Schema pentru CV-SERVICE
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "cv_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE IF NOT EXISTS cv_uploads (
        id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id      UUID NOT NULL, -- Eliminat FK
        minio_path   TEXT NOT NULL,
        file_name    TEXT NOT NULL,
        status       VARCHAR(30) DEFAULT 'uploaded',
        score        SMALLINT,
        skills       JSONB,
        gaps         JSONB,
        raw_text     TEXT,
        created_at   TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_cv_uploads_user_id ON cv_uploads(user_id);
EOSQL

# 4. Schema pentru JOB-SCRAPER-SERVICE
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "jobs_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    CREATE TABLE IF NOT EXISTS scraped_jobs (
        id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id      UUID, -- Eliminat FK
        title        VARCHAR(500) NOT NULL,
        company      VARCHAR(255),
        location     VARCHAR(255),
        url          TEXT UNIQUE,
        description  TEXT,
        source       VARCHAR(50),
        scraped_at   TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS job_matches (
        id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id       UUID NOT NULL, -- Eliminat FK
        job_id        UUID REFERENCES scraped_jobs(id) ON DELETE CASCADE, -- Permis (aceeasi baza de date)
        match_score   NUMERIC(5,2),
        cover_letter  TEXT,
        created_at    TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_scraped_jobs_user ON scraped_jobs(user_id);
    CREATE INDEX IF NOT EXISTS idx_job_matches_user_id ON job_matches(user_id);
EOSQL

# 5. Schema pentru LEARNING-PATH-AGENT
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "learning_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE IF NOT EXISTS learning_paths (
        id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id      UUID UNIQUE NOT NULL, -- Eliminat FK
        modules      JSONB NOT NULL,
        total_weeks  SMALLINT,
        status       VARCHAR(20) DEFAULT 'active',
        created_at   TIMESTAMPTZ DEFAULT NOW(),
        completed_at TIMESTAMPTZ
    );

    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id      UUID NOT NULL, -- Eliminat FK
        module_id    VARCHAR(100),
        score        NUMERIC(5,2),
        answers      JSONB,
        passed       BOOLEAN,
        attempted_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS user_progress (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id             UUID UNIQUE NOT NULL, -- Eliminat FK
        modules_completed   SMALLINT DEFAULT 0,
        modules_total       SMALLINT DEFAULT 0,
        quizzes_passed      SMALLINT DEFAULT 0,
        last_activity       TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user ON quiz_attempts(user_id);
EOSQL

# 6. Schema pentru INTERVIEW-AGENTS
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "interview_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE IF NOT EXISTS interview_sessions (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id         UUID NOT NULL, -- Eliminat FK
        type            VARCHAR(20) NOT NULL,
        status          VARCHAR(20) DEFAULT 'active',
        score           NUMERIC(5,2),
        feedback        JSONB,
        transcript      JSONB,
        duration_secs   INTEGER,
        created_at      TIMESTAMPTZ DEFAULT NOW(),
        completed_at    TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS idx_interview_user ON interview_sessions(user_id);
EOSQL

echo "Configurarea microserviciilor finalizata cu succes!"