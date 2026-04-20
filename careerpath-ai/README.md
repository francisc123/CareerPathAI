# CareerPath AI — Enterprise Microservices Architecture

> **Multi-Agent AI platform** for IT career preparation.
> Docker-first · Event-driven · Production-ready · 21 containers

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Directory Structure](#2-directory-structure)
3. [Service Catalog](#3-service-catalog)
4. [Technology Market Research & Justification](#4-technology-market-research--justification)
5. [Data Flows — The 3 Core User Journeys](#5-data-flows--the-3-core-user-journeys)
6. [Data Layer Design](#6-data-layer-design)
7. [Event Bus — Kafka Topics](#7-event-bus--kafka-topics)
8. [Security Architecture](#8-security-architecture)
9. [Observability Stack](#9-observability-stack)
10. [Getting Started](#10-getting-started)
11. [Production Deployment](#11-production-deployment)

---

## 1. Architecture Overview

CareerPath AI uses a **domain-driven microservices architecture** with **event-driven async communication** via Redpanda (Kafka-compatible). Every long-running operation — CV analysis, job scraping, course generation, interview simulation — is decoupled through events so no user request ever blocks on AI processing.

```
┌─────────────────────────────────────────────────────────────┐
│  Browser                                                    │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTPS / WSS
┌──────────────────▼──────────────────────────────────────────┐
│  Frontend  (Next.js 14)          Port 3000                  │
└──────────────────┬──────────────────────────────────────────┘
                   │ REST + WebSocket
┌──────────────────▼──────────────────────────────────────────┐
│  API Gateway  (NestJS)           Port 8000   ← ONLY PUBLIC  │
│  JWT auth · Rate limit · Proxy · WS proxy                   │
└────┬──────┬──────┬──────┬────────┬───────────┬──────────────┘
     │      │      │      │        │           │
  User    CV    Scraper Notif  Orchestrator  Interview
  Svc    Svc    Svc     Svc    Agents        Agents
 8001   8002   8003    8004   8005-8008     8009-8010
     │      │      │      │        │           │
     └──────┴──────┴──────┴────────┴───────────┘
                          │
              ┌───────────▼───────────┐
              │   Redpanda (Kafka)    │  ← Event Bus
              │   10 async topics     │
              └───────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   PostgreSQL           Redis            Qdrant
  (relational)         (cache)          (vectors)
  users/progress     sessions/RL        RAG/matching
        │
      MinIO
  (object storage)
  CVs / courses
```

**Architecture v2 key upgrades** over the initial draft:

| What changed | Why |
|---|---|
| 2 monoliths → 12 microservices | Independent deploy, scale, failure isolation |
| HTTP-only → Kafka event bus | AI tasks are long-running; never block the user |
| Kafka + ZooKeeper → **Redpanda** | No ZooKeeper dependency, 10x simpler ops, same API |
| No observability → **Grafana LGTM stack** | Logs + Metrics + Traces in one platform |
| No object storage → **MinIO** | CVs and course files need durable, S3-compatible storage |
| Monolith AI → **LangGraph orchestrator** | Stateful multi-agent workflows with checkpointing |
| Express/Flask → **NestJS + FastAPI** | Enterprise-grade: DI, modules, async, OpenAPI auto-docs |
| JWT HS256 → **JWT RS256** | Asymmetric: services can verify tokens without the private key |

---

## 2. Directory Structure

```
careerpath-ai/
│
├── docker-compose.yml               # Dev orchestration (21 containers)
├── docker-compose.prod.yml          # Production overrides (replicas, limits)
├── .env.example                     # All required environment variables
├── Makefile                         # make up / down / migrate / keys
│
├── frontend/                        # [01] Next.js 14 App Router UI
│   ├── Dockerfile
│   └── src/
│       ├── app/                     # Pages: dashboard, cv-upload, learning, jobs, interview
│       ├── components/              # ChatWindow, CodeEditor, CVScoreGauge, JobCard
│       ├── lib/                     # api-client.ts, socket.ts
│       └── store/zustand/           # Global state (auth, progress)
│
├── api-gateway/                     # [02] NestJS gateway — JWT, rate-limit, proxy
│   └── Dockerfile
│
├── services/
│   ├── user-service/                # [03] Auth + Profiles — NestJS + Prisma + PostgreSQL
│   ├── cv-service/                  # [04] CV upload + OCR parsing — FastAPI + MinIO
│   ├── job-scraper-service/         # [05] Job scraping — FastAPI + Playwright + Celery
│   ├── notification-service/        # [06] Email + SSE + Push — NestJS
│   ├── agent-orchestrator/          # [07] Workflow router — LangGraph
│   ├── cv-analyzer-agent/           # [08] CV scoring + gap analysis — Claude + Qdrant
│   ├── learning-path-agent/         # [09] AI Professor — Claude + Udemy/YouTube APIs
│   ├── job-match-agent/             # [10] Semantic job matching — Qdrant + Claude reranker
│   ├── hr-interview-agent/          # [11] HR simulator — Claude WebSocket
│   └── technical-interview-agent/   # [12] Tech interviewer — Claude + Judge0 sandbox
│
├── infrastructure/
│   ├── postgres/init/01_schema.sql  # Full DB schema (auto-run on first start)
│   ├── redis/redis.conf
│   ├── qdrant/config.yaml           # 3 collections: cv, job, course embeddings
│   ├── redpanda/
│   │   ├── console-config.yaml      # Redpanda Console UI config
│   │   └── create-topics.sh         # Creates all 10 event topics
│   └── minio/init-buckets.sh        # Creates 3 buckets with lifecycle rules
│
├── observability/
│   ├── otel/otel-collector.yaml     # OpenTelemetry collector (traces → Tempo)
│   ├── prometheus/prometheus.yml    # Scrape all 12 services + infra
│   ├── loki/loki-config.yaml        # Log aggregation
│   ├── tempo/tempo-config.yaml      # Distributed tracing storage
│   └── grafana/
│       ├── provisioning/            # Auto-provision datasources + dashboards
│       └── dashboards/              # Services overview, Kafka lag, AI agent metrics
│
├── shared/
│   └── types/
│       ├── kafka-events.ts          # TypeScript interfaces for all Kafka events
│       └── kafka_events.py          # Pydantic models for all Kafka events
│
└── k8s/                             # Kubernetes manifests for cloud production
    ├── deployments/
    ├── services/
    ├── ingress/
    ├── hpa/                         # Auto-scaling for AI agents
    └── secrets/
```

---

## 3. Service Catalog

### [01] Frontend — Next.js 14
The client application. Communicates with the API Gateway via REST for data and WebSocket for real-time interview chat. Uses Server-Sent Events to receive background task progress updates (CV analysis, job scraping).

**Key pages:**
- `/cv-upload` — Upload CV, display real-time analysis progress bar
- `/dashboard` — CV score, top job matches, learning progress, interview scores
- `/learning/path` — Weekly learning plan with modules and quizzes
- `/interview/hr` — Chat-based HR simulation with WebSocket
- `/interview/technical` — Monaco code editor + chat for technical interviews

---

### [02] API Gateway — NestJS
**Single point of entry.** Every external request passes through here. No internal service is directly reachable from outside.

**Responsibilities:**
- Verify JWT (RS256) on every protected route
- Rate limit per IP (100 req/min default)
- HTTP reverse proxy to internal services
- WebSocket proxy to interview agents
- Request-ID injection for distributed tracing

---

### [03] User Service — NestJS + Prisma
Handles all identity and profile concerns. Signs JWT tokens using the RS256 private key; all other services only need the public key to verify.

**Endpoints:** `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /profile`, `PUT /profile`, `GET /dashboard`, `PUT /progress`

**Publishes:** `user.registered`

---

### [04] CV Service — FastAPI
Accepts CV file uploads (PDF, DOCX, image). Extracts text using `pdfplumber` (structured PDFs) or `pytesseract` (scanned/image CVs). Stores raw file in MinIO. Publishes `cv.uploaded` event — the actual AI analysis happens asynchronously in the CV Analyzer Agent.

**Returns immediately** a `job_id` so the frontend can poll for status.

---

### [05] Job Scraper Service — FastAPI + Playwright + Celery
Triggered by the Orchestrator when a candidate scores ≥ 70. Uses Playwright (headless Chromium) to scrape LinkedIn Jobs, Indeed, eJobs.ro, and BestJobs. Scrapers run as Celery background workers so the API returns immediately. URL hashing prevents duplicate jobs.

**Consumes:** HTTP trigger from Orchestrator
**Publishes:** `jobs.scraped`

---

### [06] Notification Service — NestJS
Listens to completion events on Redpanda and fans them out to:
- **Email** — Nodemailer + SendGrid SMTP
- **Server-Sent Events** — Live progress updates pushed to the frontend (no polling needed)
- **Web Push** — Browser push notifications via VAPID

---

### [07] Agent Orchestrator — LangGraph
The brain of the platform. Listens to `cv.analyzed` events and decides which flow to trigger based on the CV score. Manages stateful multi-agent workflows using LangGraph `StateGraph` with checkpointing — if a workflow fails mid-way, it can resume from the last checkpoint.

**Flow routing:**
- Score ≥ 70 → Flow 1 (Job Search)
- Score < 70 → Flow 2 (Learning Path)
- After learning completed → Flow 3 (Interview Prep)

---

### [08] CV Analyzer Agent — Claude Sonnet 4.6 + Qdrant
The most critical AI service. Receives CV text, runs it through structured LLM prompts to extract skills, experience, and education, then scores the CV 0–100. Generates an embedding and stores it in Qdrant for future semantic job matching.

**Gap analysis** compares extracted skills against a target-role skill taxonomy stored in Qdrant.

---

### [09] Learning Path Agent — AI Professor
When gaps are identified, this agent designs a personalized curriculum. It uses Claude to generate a week-by-week learning plan, then enriches it with real resources from the Udemy API (courses, rating ≥ 4.5) and YouTube Data API v3 (video tutorials). Also generates multiple-choice quizzes per module.

---

### [10] Job Match Agent — Qdrant + Claude Reranker
Indexes all scraped jobs as vector embeddings in Qdrant. Performs cosine-similarity search between the CV embedding and all job embeddings. Takes the top-50 matches and passes them through a Claude reranker prompt to produce the final top-10 with explanations and a personalized cover letter per job.

---

### [11] HR Interview Agent — Claude WebSocket
Maintains a persistent WebSocket connection per interview session. Uses a system prompt that defines a specific HR persona (e.g., "Google HR Manager, 10 years experience"). Stores the full conversation history in Redis (TTL 2 hours). At session end, runs a final LLM pass to generate structured feedback with scores for communication, confidence, motivation, and culture fit.

---

### [12] Technical Interview Agent — Claude + Judge0
Same WebSocket architecture as the HR agent, but specialized for technical interviews. Selects algorithm problems or system design questions based on the candidate's tech stack. Receives code submissions via WebSocket, forwards them to the Judge0 API for safe sandbox execution (40+ languages), then passes the code + test results to Claude for a detailed feedback analysis (time complexity, edge cases, code quality).

---

## 4. Technology Market Research & Justification

This section documents the technology selection process for every component. Each decision was made after evaluating at least 3 alternatives against enterprise criteria: performance, operational complexity, ecosystem maturity, vendor lock-in risk, and total cost of ownership.

---

### 4.1 Frontend Framework

| Option | Stars (GitHub) | Verdict |
|---|---|---|
| **Next.js 14** | 124k | ✅ CHOSEN |
| Remix | 29k | Rejected |
| SvelteKit | 18k | Rejected |
| Nuxt 3 | 55k | Rejected |

**Why Next.js 14 App Router:**
Next.js is the undisputed enterprise standard for React applications. The App Router introduced in v13/v14 brings React Server Components (RSC), which move data-fetching to the server — eliminating waterfall requests and reducing bundle sizes by 40–60%. The `output: "standalone"` mode produces a self-contained Node.js server perfectly suited for Docker. The ecosystem is the largest of any meta-framework: 3,000+ compatible libraries, official support from Vercel, used by Hulu, TikTok, Twitch, and the majority of Fortune 500 tech companies.

**Remix** was rejected because its file-based routing for complex nested layouts becomes unwieldy, and it lacks the Server Component model that makes RSC so powerful. **SvelteKit** is excellent but the Svelte ecosystem is an order of magnitude smaller, making hiring and third-party integrations harder. **Nuxt** is Vue-based, and Vue's enterprise adoption in B2B SaaS is significantly lower than React.

**State management: Zustand** over Redux/Jotai/Recoil — because it requires zero boilerplate, has a tiny bundle (1.1kb), and its hook-based API is the most intuitive of the options. Redux remains the correct choice only for extremely large teams with multiple developers touching the same state slices.

---

### 4.2 API Gateway

| Option | Type | Verdict |
|---|---|---|
| **NestJS + Fastify adapter** | Custom code | ✅ CHOSEN |
| Kong Gateway | Dedicated gateway | Considered |
| Traefik | Reverse proxy | Rejected |
| NGINX | Web server | Rejected |

**Why NestJS with Fastify adapter:**
NestJS is the most mature enterprise Node.js framework (64k GitHub stars). Its decorator-based architecture, dependency injection system, and module structure are directly inspired by Angular/Spring Boot — making it the most approachable framework for developers coming from Java/Spring or C#/.NET backgrounds. The framework has first-party modules for JWT (`@nestjs/jwt`), throttling (`@nestjs/throttler`), WebSockets, and OpenAPI documentation generation.

By swapping the default Express adapter for Fastify, the gateway gains **~2x throughput** (Fastify benchmarks at ~76,000 req/sec vs Express at ~40,000 req/sec) while keeping the full NestJS programming model.

**Kong** is the enterprise-grade dedicated API gateway (used by Nasdaq, Rakuten) and would be the correct choice if you needed plugin-based extensibility without writing code. For this architecture, a code-first NestJS gateway provides more flexibility for custom business logic (e.g., injecting user profile data into request headers, complex WebSocket routing). Kong could replace this in a future iteration.

**Traefik** is excellent as a reverse proxy and load balancer but is not a suitable place to write custom business logic like JWT validation and rate limiting.

---

### 4.3 Backend Microservices

#### Node.js services (User, Notification): NestJS

**Why NestJS over Express/Fastify standalone:**
For services with complex domain logic (user authentication, profile management), NestJS's dependency injection and module system dramatically reduce coupling and improve testability. The `@nestjs/prisma` integration and `@nestjs/jwt` modules handle 80% of the boilerplate. Enterprise teams report 30–40% faster feature development after switching from Express.

**ORM: Prisma over TypeORM/Drizzle/Sequelize:**

| ORM | Type Safety | Migration UX | Performance | Maturity |
|---|---|---|---|---|
| **Prisma** | ✅ Full generated types | ✅ Excellent CLI | Good | ✅ High |
| TypeORM | Partial | Fragile | Good | High |
| Drizzle | ✅ Excellent | Manual | ✅ Best | Low |
| Sequelize | Poor | Acceptable | Good | High |

Prisma generates TypeScript types from the schema, making it impossible to query a field that doesn't exist. Its migration system is the most developer-friendly available. Drizzle is faster at runtime and has better type inference, but it is too young (2022) for enterprise use where the ORM needs to have survived multiple production incidents. TypeORM is notoriously buggy in complex relation scenarios.

#### Python services (all AI agents): FastAPI

**Why FastAPI over Django REST Framework / Flask / Litestar:**

| Framework | Async Native | Auto Docs | Pydantic v2 | Perf (req/sec) |
|---|---|---|---|---|
| **FastAPI** | ✅ | ✅ OpenAPI | ✅ | ~100k |
| Django REST | ❌ WSGI | Partial | ❌ | ~25k |
| Flask | ❌ | Manual | ❌ | ~30k |
| Litestar | ✅ | ✅ | ✅ | ~110k |

FastAPI is the de facto standard for Python AI services in 2024–2025. Every major AI company (Anthropic, OpenAI, Hugging Face) publishes FastAPI examples. Its native async support means a single worker can handle hundreds of concurrent LLM streaming responses without blocking. Pydantic v2 (used internally by FastAPI) is now written in Rust, making validation 5–17x faster than v1. The automatic OpenAPI documentation generation means you always have accurate API docs for free.

**Litestar** is a legitimate competitor and marginally faster, but FastAPI's ecosystem advantage is decisive. The `opentelemetry-instrumentation-fastapi` package, thousands of Stack Overflow answers, and the Anthropic/OpenAI SDK all target FastAPI first.

---

### 4.4 Message Broker

| Option | Throughput | Ops Complexity | Kafka-Compatible | Self-Hosted |
|---|---|---|---|---|
| **Redpanda** | 10M msg/sec | ✅ Low (no ZK) | ✅ Full API compat | ✅ |
| Apache Kafka | 10M msg/sec | ❌ High (ZK needed) | N/A | ✅ |
| RabbitMQ | 50k msg/sec | Medium | ❌ | ✅ |
| NATS JetStream | 50M msg/sec | Low | ❌ | ✅ |
| Redis Streams | 1M msg/sec | Low | ❌ | ✅ |

**Why Redpanda:**
Redpanda is a re-implementation of the Kafka protocol in C++ (no JVM, no ZooKeeper). It is **100% Kafka API-compatible** — every Kafka client library (kafka-python, aiokafka, kafkajs) works with zero changes. The critical advantage for this architecture is **operational simplicity**: Kafka requires ZooKeeper as a separate coordination service (3 ZK nodes + 3 Kafka nodes = 6 containers minimum for a resilient cluster). Redpanda is a single binary with integrated Raft consensus — **one container** for development, three for production.

Benchmark data (Redpanda 2024 vs Confluent Kafka): at P99 latency, Redpanda delivers 10x lower tail latency. At equivalent throughput, Redpanda uses 6x less CPU.

**Why not RabbitMQ:** AMQP is excellent for complex routing patterns (topic exchanges, fanout, dead-letter queues), but Kafka's log-based model is the correct choice for an event-sourcing architecture because events are **durable and replayable**. If the CV Analyzer Agent crashes during analysis, it can restart and re-read the `cv.uploaded` event from exactly where it left off. With RabbitMQ, the message is gone.

**Why not NATS:** NATS JetStream is faster but lacks the mature consumer group semantics that Kafka provides — horizontal scaling of consumers with automatic partition rebalancing is essential for the AI agent services that need to scale independently.

---

### 4.5 Vector Database

| Option | Written In | Self-Hosted | Performance | Filtering | Cloud |
|---|---|---|---|---|---|
| **Qdrant** | Rust | ✅ | ✅ Best | ✅ Excellent | ✅ Managed |
| Pinecone | Proprietary | ❌ | ✅ Best | Good | ✅ Only |
| Weaviate | Go | ✅ | Good | ✅ GraphQL | ✅ |
| Milvus | Go/C++ | ✅ Complex | Good | Good | ✅ |
| ChromaDB | Python | ✅ | Weak | Basic | ❌ |
| pgvector | C (PG ext) | ✅ | Moderate | ✅ SQL | ✅ |

**Why Qdrant:**
Qdrant is written in Rust, giving it memory safety guarantees and benchmark performance that surpasses every Go-based or Python-based competitor. In the ANN-benchmarks suite (2024), Qdrant achieves the best recall-vs-throughput tradeoff in the 768–1536 dimension range used by OpenAI embeddings.

Its **payload filtering** feature is critical for this architecture: when matching a CV against jobs, you can filter by `seniority_level == "senior" AND location == "Remote"` at the vector search level — not as a post-processing step. This maintains sub-millisecond search latency even with millions of job vectors.

**Pinecone** would be the correct choice for a fully managed, zero-ops setup in production, but it costs ~$70/month minimum and introduces vendor lock-in. Qdrant has a managed cloud offering (Qdrant Cloud) that provides a migration path when you're ready, without changing any client code.

**pgvector** is worth considering for smaller datasets (< 1M vectors) because it eliminates an infrastructure dependency. For this platform — where millions of job embeddings will be indexed as the platform grows — a dedicated vector DB is the correct architectural choice.

---

### 4.6 AI / LLM Framework

| Option | Strength | Weakness | Best For |
|---|---|---|---|
| **LangGraph** | Stateful workflows, checkpointing | Learning curve | ✅ Orchestrator |
| LangChain | Rich tool ecosystem | Abstraction leaks | Agent components |
| CrewAI | Role-based agents, simple API | Limited state control | Simple pipelines |
| AutoGen | Multi-agent conversation | Microsoft lock-in | Research |
| Semantic Kernel | .NET/C# native | Python second-class | .NET shops |

**Why LangGraph for the Orchestrator:**
LangGraph is the correct tool for **stateful, conditional multi-agent workflows** — exactly what the 3 user flows require. The `StateGraph` primitive models each flow as a directed graph where nodes are agent calls and edges are conditional routing logic (`score >= 70 → scrape jobs`, `score < 70 → generate learning path`). LangGraph adds **checkpointing** built on top of this: every state transition is persisted so a crashed workflow can resume from the exact node it failed at.

**Why direct Anthropic SDK in individual agents:**
For the leaf agents (CV Analyzer, Learning Path, etc.), using the Anthropic SDK directly rather than LangChain gives better control over streaming, tool use, and the exact prompts being sent. LangChain's abstractions add latency and make debugging harder. The `langchain-anthropic` package is used only in the Orchestrator to keep the inter-agent communication layer consistent.

---

### 4.7 LLM Selection

| Model | Context | Speed | Reasoning | Cost (per 1M tok in/out) |
|---|---|---|---|---|
| **Claude Sonnet 4.6** | 200k | Fast | ✅ Best | $3 / $15 |
| GPT-4o | 128k | Fast | Good | $5 / $15 |
| Gemini 1.5 Pro | 1M | Medium | Good | $3.50 / $10.50 |
| Llama 3.1 70B | 128k | Self-hosted | Good | Infrastructure cost |
| Claude Haiku 4.5 | 200k | ✅ Fastest | Moderate | $0.80 / $4 |

**Why Claude Sonnet 4.6 as the primary model:**
Claude Sonnet 4.6 offers the best reasoning capability per dollar in the mid-tier model category. For CV analysis, gap identification, and curriculum generation — tasks that require nuanced understanding of career trajectories — Claude's instruction-following and structured output generation is consistently more reliable than GPT-4o at the same price point. The 200k context window allows the full CV plus a detailed system prompt to fit in a single request without chunking.

**Claude Haiku 4.5** is used for high-frequency, lower-complexity tasks like quiz question generation and cover letter personalization where cost-efficiency matters.

**OpenAI text-embedding-3-small** for embeddings: despite using Claude as the primary LLM, OpenAI's embedding models remain the benchmark for semantic similarity tasks. `text-embedding-3-small` (1536 dimensions) outperforms all open-source alternatives in the MTEB leaderboard and costs $0.02 per million tokens — making it negligible at this scale.

---

### 4.8 Primary Database

| Option | ACID | JSON Support | Scaling | Maturity |
|---|---|---|---|---|
| **PostgreSQL 16** | ✅ Full | ✅ JSONB + operators | Read replicas | ✅ 35+ years |
| MySQL 8 | ✅ | Partial | Read replicas | ✅ |
| CockroachDB | ✅ | ✅ | ✅ Horizontal | Medium |
| MongoDB | Partial | ✅ Native | ✅ Horizontal | High |

**Why PostgreSQL 16:**
PostgreSQL is the most feature-rich and standards-compliant open-source relational database. For this platform's relational data (users, progress, interview sessions), ACID guarantees are non-negotiable — you cannot lose a completed interview score or CV upload record. PostgreSQL 16 introduced logical replication improvements and query parallelism enhancements that make it viable for analytical workloads as the platform scales.

The **JSONB** column type (used for `skills`, `gaps`, `modules`, `feedback`) provides document-like flexibility for semi-structured data while maintaining full indexing capability with GIN indexes. This avoids the need for a separate MongoDB instance.

`pg_trgm` extension enables fuzzy text search on job titles and skills without adding Elasticsearch.

---

### 4.9 Cache & Session Store

| Option | Type | Speed | Data Structures | Notes |
|---|---|---|---|---|
| **Redis Stack 7.4** | In-memory | Sub-ms | ✅ Rich | ✅ CHOSEN |
| Valkey | In-memory | Sub-ms | ✅ Rich | Redis open-source fork |
| DragonflyDB | In-memory | Sub-ms | ✅ Rich | 25x faster than Redis |
| Memcached | In-memory | Sub-ms | Strings only | Too limited |

**Why Redis Stack 7.4:**
Redis is the industry standard for multi-purpose caching with a 20-year track record. Redis Stack bundles **RedisJSON** (native JSON type with path queries), **RediSearch** (full-text and vector search), and **RedisTimeSeries** into the base image — all needed by this platform without running separate modules.

Usage patterns in this architecture:
- **JWT blacklist** — `SET jti:abc123 revoked EX 900` (expires with the token)
- **Interview session state** — `JSON.SET session:xyz $ {...conversation history}` (TTL 2h)
- **Rate limiting** — `INCR rate:ip:endpoint` with EXPIRE
- **Celery broker** — Scraper workers queue via Redis List
- **BullMQ job queues** — Node.js background jobs

**Valkey** (Linux Foundation Redis fork, created when Redis changed its license in 2024) is the correct long-term choice for companies that cannot accept the SSPL license. For a startup, Redis's commercial license is acceptable, and its ecosystem is more mature.

**DragonflyDB** is architecturally impressive (Raft-based, multi-threaded), benchmarking at 25x Redis throughput, but it's too young (2022) for production use in a critical data path. Track for 2026.

---

### 4.10 Object Storage

| Option | Self-Hosted | S3 Compatible | Cost (GB/month) | Notes |
|---|---|---|---|---|
| **MinIO** | ✅ | ✅ Full | Infrastructure | ✅ CHOSEN for dev/self-hosted |
| AWS S3 | ❌ | N/A | $0.023 | Standard for cloud |
| Cloudflare R2 | ❌ | ✅ | $0.015 | No egress fees |
| Backblaze B2 | ❌ | ✅ | $0.006 | Cheapest |

**Why MinIO:**
MinIO implements the full AWS S3 API — the `boto3` Python client and AWS SDK work without any code changes when switching between MinIO (development) and S3/R2 (production). This makes the architecture fully portable. MinIO is the fastest self-hosted object storage, with benchmark throughput exceeding 325 GiB/sec on NVMe hardware.

**Production recommendation:** Switch to **Cloudflare R2** in production. R2 charges $0/GB for egress (vs S3's $0.09/GB), which is significant when serving CV files and course materials globally. Zero code changes required — just update the endpoint URL.

---

### 4.11 Web Scraping

| Option | JS Rendering | Speed | API | Detection Evasion |
|---|---|---|---|---|
| **Playwright** | ✅ Full | Fast | ✅ Modern async | ✅ Best |
| Puppeteer | ✅ Full | Fast | Good | Good |
| Selenium | ✅ Full | Slow | Legacy | Poor |
| Scrapy | ❌ | ✅ Best | Good | Basic |
| requests+BS4 | ❌ | ✅ Best | Simple | N/A |

**Why Playwright:**
LinkedIn Jobs and modern job boards heavily use JavaScript rendering — a plain HTTP request returns an empty shell. Playwright controls a real Chromium browser, executes JavaScript, waits for network idle, and captures the fully rendered DOM. Its `auto-wait` feature automatically waits for elements to be visible before interacting — eliminating the `time.sleep()` calls that make Selenium scripts brittle. Playwright also supports **network interception** for mocking API responses in tests and **browser contexts** for isolated sessions (running multiple scrapers in parallel without cookie contamination).

**BeautifulSoup4 + lxml** is used as a fast HTML parser after Playwright renders the page, and for static pages (eJobs.ro, BestJobs) that don't require JavaScript execution.

---

### 4.12 Observability Stack

| Stack | Logs | Metrics | Traces | Cost | Notes |
|---|---|---|---|---|---|
| **Grafana LGTM** | Loki | Prometheus | Tempo | Free OSS | ✅ CHOSEN |
| Datadog | ✅ | ✅ | ✅ | $$$$ | Enterprise SaaS |
| New Relic | ✅ | ✅ | ✅ | $$$ | Enterprise SaaS |
| ELK Stack | Elasticsearch | Manual | Jaeger | $$ | High memory |
| OpenTelemetry only | — | — | — | Free | Protocol, not storage |

**Why Grafana LGTM Stack (Loki + Grafana + Tempo + Mimir):**
The Grafana LGTM stack provides the three pillars of observability (logs, metrics, traces) in a single, correlated platform with zero licensing cost. The critical feature is **exemplars** — a Prometheus metric can link directly to the Tempo trace that caused a spike, and a Loki log line can link to the same trace. This makes debugging a slow CV analysis or a failed interview session dramatically faster.

**OpenTelemetry Collector** sits as a vendor-neutral receiver, decoupling instrumentation from the backend. All services emit traces to the OTel Collector using the OTLP protocol; the Collector fans out to Tempo and Prometheus. This means switching from Tempo to Datadog or Jaeger in the future requires only a one-line change in `otel-collector.yaml` — not a change to every service.

**Datadog** would be the correct choice above $10k MRR when operational simplicity justifies the cost (~$15/host/month). It has the best alert correlation and ML-based anomaly detection.

---

### 4.13 Code Execution Sandbox

**Why Judge0:**
Technical interviews require safe execution of user-submitted code in 40+ programming languages. Building a secure sandbox is a significant infrastructure investment (seccomp profiles, cgroups, container isolation). Judge0 is an open-source code execution system that handles all of this — it can be self-hosted via Docker or used as an API. It supports C, C++, Java, Python, JavaScript, Go, Rust, and 37 other languages with configurable memory and time limits.

**Security consideration:** Code execution is intentionally isolated from the main infrastructure. The Technical Interview Agent calls Judge0 via HTTP API; there is no direct network path from Judge0 to any internal service.

---

## 5. Data Flows — The 3 Core User Journeys

### Flow 1 — Strong Candidate (CV Score ≥ 70)

```
User uploads CV (PDF/DOCX)
  → CV Service: parse text, store in MinIO, publish cv.uploaded
  → CV Analyzer Agent: score CV (Claude), embed (OpenAI), store in Qdrant
  → Agent Orchestrator: score ≥ 70 → trigger job scraping
  → Job Scraper: Playwright scrapes LinkedIn/Indeed/eJobs → publish jobs.scraped
  → Job Match Agent: embed jobs → cosine similarity vs CV → Claude reranker → top 10
  → Notification Service: SSE to frontend + email with top 10 + cover letters
```

**User sees:** CV score, top 10 matched jobs with match percentage, AI-written cover letter for each.

---

### Flow 2 — Candidate Needs Prep (CV Score < 70)

```
CV Analyzer Agent: score < 70, gaps identified → publish cv.analyzed
  → Agent Orchestrator: route to learning flow → publish gaps.identified
  → Learning Path Agent: Claude designs curriculum → Udemy API + YouTube API for resources
    → publish learning.path.created
  → User completes modules + quizzes → User Service updates progress
  → Progress = 100% → publish learning.completed
  → Agent Orchestrator: auto-triggers Flow 3
```

**User sees:** Week-by-week learning plan, curated course links, AI-generated quizzes, progress tracker.

---

### Flow 3 — Interview Simulation

```
Orchestrator triggers interview prep (after Flow 1 or Flow 2)

  HR Interview:
    WebSocket connect → HR Agent loads candidate profile from PostgreSQL
    Claude (HR persona) ↔ User: 15–20 questions via real-time chat
    Session state in Redis → Feedback generated at session end → saved to PostgreSQL
    publish interview.hr.completed

  Technical Interview:
    WebSocket connect → Tech Agent selects problems by candidate's tech stack
    Claude (Senior Dev persona) ↔ User: algorithm + system design questions
    User submits code → Judge0 sandbox → Claude analyzes results
    publish interview.tech.completed

  Notification Service → full report email (HR score + Tech score + recommendations)
```

**User sees:** Live chat interview, Monaco code editor, real-time AI responses, final report card.

---

## 6. Data Layer Design

```
PostgreSQL 16 (ACID relational)
├── user-service        → users, profiles, sessions
├── cv-service          → cv_uploads (metadata, status, minio_path)
├── job-scraper         → scraped_jobs, scraping_runs
├── job-match-agent     → job_matches (user_id, job_id, score, cover_letter)
├── learning-path-agent → learning_paths, learning_modules, quiz_attempts, user_progress
└── interview-agents    → interview_sessions, interview_feedback

Qdrant Vector DB (semantic search, RAG)
├── collection: cv_embeddings    dim=1536, metric=Cosine, payload: {user_id, skills[]}
├── collection: job_embeddings   dim=1536, metric=Cosine, payload: {title, company, url, source}
└── collection: course_embeddings dim=1536, metric=Cosine, payload: {title, provider, url}

Redis Stack 7.4 (ephemeral, sub-millisecond)
├── api-gateway         → rate limiting counters         TTL: 60s
├── user-service        → JWT blacklist (revoked tokens)  TTL: token_exp
├── hr-interview-agent  → conversation history            TTL: 2h
├── tech-interview-agent → interview state + code buffer  TTL: 2h
└── job-scraper-service → Celery broker + result backend

MinIO Object Storage (binary files)
├── bucket: cvs-raw           → original uploaded CV files       lifecycle: 90d delete
├── bucket: cvs-processed     → OCR-extracted text + metadata    lifecycle: versioned
└── bucket: course-materials  → PDFs, images for learning content
```

---

## 7. Event Bus — Kafka Topics

All topics use Redpanda (Kafka-compatible). Retention: 7 days. Partitions: 3 (dev: 1).

| Topic | Producer | Consumer | Payload |
|---|---|---|---|
| `user.registered` | user-service | notification-service | userId, email |
| `cv.uploaded` | cv-service | cv-analyzer-agent | userId, jobId, minioPath |
| `cv.analyzed` | cv-analyzer-agent | agent-orchestrator | userId, score, skills[], gaps[] |
| `gaps.identified` | agent-orchestrator | learning-path-agent | userId, gaps[], targetRole |
| `jobs.scraped` | job-scraper-service | job-match-agent | userId, scrapeRunId |
| `jobs.matched` | job-match-agent | notification-service | userId, topJobIds[] |
| `learning.path.created` | learning-path-agent | notification-service | userId, pathId |
| `learning.completed` | user-service | agent-orchestrator | userId, pathId |
| `interview.hr.completed` | hr-interview-agent | notification-service | userId, score, sessionId |
| `interview.tech.completed` | technical-interview-agent | notification-service | userId, score, sessionId |

---

## 8. Security Architecture

```
External traffic
  │  HTTPS only (TLS termination at load balancer / NGINX)
  ▼
API Gateway                       ← JWT RS256 verification
  │  Rate limit: 100 req/min/IP
  │  CORS: whitelist origin
  │  Inject x-request-id
  ▼
Internal services (no public port) ← Zero Trust: only reachable from internal-net
  │  Service-to-service: HTTP (mTLS in K8s with Istio)
  │  JWT public key only (no private key in AI services)
  ▼
Infrastructure
  │  PostgreSQL: password auth, no superuser
  │  Redis: requirepass + bind 0.0.0.0 (internal only)
  │  MinIO: presigned URLs (15min expiry) — no public buckets
  │  Secrets: .env in dev, HashiCorp Vault in production
```

**Additional hardening:**
- All containers run as non-root users (`USER appuser`)
- Multi-stage Docker builds — no build tools in production images
- Input validation at every service boundary: Pydantic (Python) + class-validator (NestJS)
- Judge0 code execution is completely isolated from the internal network
- GDPR: raw CV files are deleted after 90 days (MinIO lifecycle rule)

---

## 9. Observability Stack

**Grafana LGTM** (Logs + Metrics + Traces) unified in one dashboard.

| Component | Role | Port |
|---|---|---|
| OTel Collector | Receives OTLP traces from all services, fans out | 4317, 4318 |
| Prometheus | Scrapes `/metrics` from all 12 services | 9090 |
| Loki | Log aggregation (structured JSON logs via Promtail) | 3100 |
| Tempo | Distributed trace storage | 3200 |
| Grafana | Unified dashboard: logs + metrics + traces correlated | 3001 |

**Key dashboards:**
- **Services Overview** — P50/P95/P99 latency, error rate, throughput per service
- **Redpanda Topics** — Consumer lag, messages/sec, partition health
- **AI Agents** — LLM token usage, agent execution time, Qdrant query latency
- **Interview Load** — Active WebSocket connections, session duration distribution

---

## 10. Getting Started

### Prerequisites

- Docker Desktop 4.30+
- Docker Compose v2.27+
- Make
- openssl (for JWT key generation)

### First-time setup

```bash
# 1. Clone and enter project
git clone https://github.com/your-org/careerpath-ai
cd careerpath-ai

# 2. Generate RS256 JWT key pair
make keys

# 3. Configure environment
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY, OPENAI_API_KEY, SMTP credentials

# 4. Start all 21 containers
make up

# 5. Wait for healthy state (~60 seconds), then run DB migrations
make migrate

# 6. Create Redpanda topics
make redpanda-topics

# 7. Initialize MinIO buckets
docker compose exec minio bash /scripts/init-buckets.sh
```

### Service URLs (development)

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API Gateway | http://localhost:8000 |
| Redpanda Console | http://localhost:8080 |
| Grafana | http://localhost:3001 (admin/admin) |
| Prometheus | http://localhost:9090 |
| MinIO Console | http://localhost:9001 |
| Qdrant Dashboard | http://localhost:6333/dashboard |

### Useful commands

```bash
make logs              # Tail all logs
make logs-agents       # Tail only AI agent logs
make logs-interview    # Tail interview agent logs
make ps                # Container status
make down              # Stop everything
make clean             # Stop + delete all volumes (destructive)
```

---

## 11. Production Deployment

### Docker Swarm / Docker Compose

```bash
make prod-up
```

Uses `docker-compose.prod.yml` overrides: 2–3 replicas for high-traffic services, resource limits, no exposed ports for infrastructure services.

### Kubernetes (AWS EKS / GKE)

```bash
# Apply all K8s manifests
make k8s-apply

# HorizontalPodAutoscaler targets (auto-scaling):
# cv-analyzer-agent: 2–10 replicas (CPU > 70%)
# hr-interview-agent: 2–10 replicas (WebSocket connections > 50/pod)
# technical-interview-agent: 2–10 replicas
# job-scraper-service: 2–8 replicas
```

**Recommended cloud architecture:**
- **EKS** (AWS) or **GKE** (GCP) for Kubernetes cluster
- **RDS PostgreSQL** — managed, automated backups, Multi-AZ failover
- **ElastiCache Redis** — managed Redis, cluster mode
- **Qdrant Cloud** — managed vector DB (zero code changes)
- **Redpanda Cloud** — managed Kafka-compatible streaming
- **Cloudflare R2** — replace MinIO for zero-egress-cost object storage
- **AWS Secrets Manager** / **HashiCorp Vault** — replace `.env` files

---

## Architecture Decision Record Summary

| Decision | Chosen | Key Reason |
|---|---|---|
| Frontend | Next.js 14 App Router | RSC, SSR, largest ecosystem |
| Node.js framework | NestJS | DI, modules, enterprise-grade |
| Python framework | FastAPI | Async native, Pydantic v2, auto-docs |
| ORM | Prisma | Generated types, best migration DX |
| Message broker | Redpanda | Kafka-compatible, no ZooKeeper, simpler ops |
| Vector DB | Qdrant | Rust performance, payload filtering, OSS |
| Primary DB | PostgreSQL 16 | ACID, JSONB, pg_trgm, most mature |
| Cache | Redis Stack 7.4 | JSON + Search + TimeSeries in one image |
| Object storage | MinIO → R2 (prod) | S3-compatible, zero lock-in |
| LLM | Claude Sonnet 4.6 | Best reasoning/cost ratio, 200k context |
| AI orchestration | LangGraph | Stateful workflows, checkpointing |
| Web scraping | Playwright | JS rendering, auto-wait, parallel contexts |
| Code sandbox | Judge0 | 40+ languages, open-source, self-hostable |
| Observability | Grafana LGTM | Logs+Metrics+Traces correlated, free OSS |
| Tracing protocol | OpenTelemetry | Vendor-neutral, future-proof |
