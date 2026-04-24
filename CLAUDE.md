# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

All runnable code lives under `careerpath-ai/`. The root contains only `arhitectura.txt` and git/IDE config.
Run every command from `careerpath-ai/` unless stated otherwise.

## Common commands

All day-to-day operations go through `make` (run from `careerpath-ai/`):

```bash
make up           # docker compose up -d --build (all profiles)
make down         # stop everything
make logs         # tail all container logs
make logs-agents  # tail orchestrator + all AI agents
make logs-cv      # tail cv-service + cv-analyzer-agent
make migrate      # prisma migrate dev (user-service)
make db-studio    # open Prisma Studio
make keys         # generate RS256 JWT key pair → keys/private.pem + keys/public.pem
make clean        # remove all containers, volumes, prune images
make prod-up      # start with docker-compose.prod.yml overlay
```

### Selective startup with profiles (preferred for development)

```bash
docker-compose --profile agents up      # Rares — AI agents + infrastructure
docker-compose --profile backend up     # Francis — core services + infrastructure
docker-compose --profile frontend up    # Vlad — UI + api-gateway + user-service
docker-compose --profile observability up  # Grafana LGTM stack only
```

Infrastructure (postgres, redis, qdrant, redpanda, minio) starts with **every** profile — it has no profile tag.

### Hot reload

`docker-compose.override.yml` is applied automatically on every `docker-compose up`.
It mounts local source directories into containers and enables watch mode:
- Next.js: `WATCHPACK_POLLING=true`
- NestJS services: `npm run start:dev`
- FastAPI services: `uvicorn --reload`

No rebuild needed when editing source files during development.

### First-time setup

```bash
cp .env.example .env   # fill in API keys and passwords
make keys              # generate JWT RS256 key pair
make up
```

PostgreSQL schema (`infrastructure/postgres/init/01_schema.sql`) runs automatically on first container start.

## Architecture

### Two-layer AI design

```
Layer 1 — agent-orchestrator (port 8005)
  Conversational agent. Talks to users via WebSocket.
  Builds a user profile silently (shadow profiling) from natural conversation.
  Decides when to invoke backend workers by publishing Redpanda events.

Layer 2 — worker agents (ports 8006–8010)
  Never interact with users directly.
  Each listens on one Redpanda topic, processes, publishes result to next topic.
```

### Event flow (Redpanda topics)

```
cv.uploaded → cv-analyzer-agent → cv.analyzed
                                        │
                              agent-orchestrator routes:
                              score ≥ 70 → job-scraper → jobs.scraped → job-match-agent → jobs.matched
                              score < 70 → gaps.identified → learning-path-agent → learning.path.created
                                                                                          │
                                                                              learning.completed
                                                                                          │
                                                                              hr/tech interview agents
```

### Service tech stack

| Layer | Service | Stack |
|---|---|---|
| Frontend | frontend | Next.js 14, Tailwind, shadcn/ui, Zustand |
| Gateway | api-gateway | NestJS + Fastify |
| Core | user-service | NestJS + Prisma + PostgreSQL |
| Core | cv-service | FastAPI + pdfplumber + MinIO + aiokafka |
| Core | job-scraper-service | FastAPI + Playwright (headless Chromium) |
| Core | notification-service | NestJS + SSE + aiokafka |
| AI | agent-orchestrator | FastAPI + LangGraph + aiokafka |
| AI | cv-analyzer-agent | FastAPI + Gemini + Qdrant + aiokafka |
| AI | learning-path-agent | FastAPI + Gemini + Udemy/YouTube APIs |
| AI | job-match-agent | FastAPI + Qdrant semantic search + Gemini reranker |
| AI | hr/tech-interview-agents | FastAPI + WebSocket + Gemini streaming |

### Databases and ownership

| Database | Owner | Purpose |
|---|---|---|
| PostgreSQL | Francis (backend) | users, profiles, cv_uploads, scraped_jobs, job_matches |
| PostgreSQL | Rares (AI agents) | learning_paths, quiz_attempts, interview_sessions |
| Redis | Francis | JWT sessions, rate limiting, workflow state (TTL) |
| Qdrant | Rares | cv_embeddings, job_embeddings, course_embeddings (dim=3072, Cosine) |
| MinIO | Francis | Raw CV files (bucket: cvs-raw) |

Services access only their own tables. Cross-service data flows exclusively through Redpanda events.

### Qdrant collections

All collections use dimension `3072` (Gemini `gemini-embedding-001`). The model `text-embedding-004` is no longer available — use `gemini-embedding-001` instead. Qdrant collection setup is in `rag_testing/qdrant_setup.py`.

### JWT authentication

RS256 asymmetric keys (not HS256). Generated with `make keys`.
API Gateway extracts user identity from JWT and injects `x-user-id` header into proxied requests — downstream services never re-verify the token.

### cv-analyzer-agent prompts

Plain-text prompt files live in `services/cv-analyzer-agent/prompts/`.
`cv_scoring.txt` defines the scoring rubric (experience 30pts, stack 25pts, projects 20pts, education 15pts, certs 10pts).
`gap_analysis.txt` produces `{gaps, priority_gaps, estimated_weeks_to_close}`.
Prompt iteration scripts are in `prompt_testing/`.

### Production

`docker-compose.prod.yml` overlays on `docker-compose.yml` (the `override.yml` is NOT used).
Kubernetes manifests are in `k8s/` — applied with `make k8s-apply`.
