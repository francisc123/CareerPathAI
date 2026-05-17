# E2E Test Issues — careerpath-ai

**Test run**: 2026-05-17, branch `master` (after merge `b13f1e3`)
**Test user**: registered via `POST /api/auth/register` → uploaded `tests/fixtures/cv_strong.pdf`

Each entry has severity, evidence (paste from logs), and proposed fix.

---

## P0 — Blocking the E2E pipeline

### 1. cv-analyzer ↔ orchestrator event contract mismatch
- **Where**: `services/cv-analyzer-agent/src/agents/cv_analyzer.py:125-134` publishes event with key `gaps_identified`; `services/agent-orchestrator/src/state.py:8` requires field `gaps`.
- **Symptom (orchestrator log)**:
  ```
  CRITICAL - An unexpected error occurred: 1 validation error for CvAnalyzedEvent
  gaps
    Field required [type=missing, input_value={'user_id': 'dGVz...', ...'gaps_identified': [...]}]
  ```
- **Effect**: orchestrator never executes the workflow → `/learning/{uid}` and `/jobs/{uid}` stay empty (404).
- **Fix**: align names. Either rename `gaps_identified` → `gaps` in cv-analyzer publisher, OR add `gaps_identified: List[str]` to orchestrator `CvAnalyzedEvent` and keep `gaps` as alias.

### 2. notification-service missing runtime deps
- **Where**: `services/notification-service/package.json` — `src/email/email.service.ts` imports `nodemailer` and `web-push`, but neither is in `dependencies`.
- **Symptom**:
  ```
  src/email/email.service.ts:2:30 - error TS2307: Cannot find module 'nodemailer'
  src/email/email.service.ts:3:26 - error TS2307: Cannot find module 'web-push'
  ```
- **Fix**: `npm i nodemailer web-push @types/nodemailer @types/web-push` in `services/notification-service/`.

### 3. job-scraper-service `redis` import fails despite being in requirements
- **Where**: `services/job-scraper-service/src/main.py:2` does `import redis`. Image fails on startup.
- **Symptom**:
  ```
  File "/app/src/main.py", line 2, in <module>
      import redis
  ModuleNotFoundError: No module named 'redis'
  ```
- **Cause**: `requirements.txt` does list `redis==5.0.7`, but the Docker image was cached. Need a clean rebuild OR ensure CI invalidates cache when requirements change.
- **Fix**: `docker compose build --no-cache job-scraper-service`. Long-term: add `--no-cache-dir` to `pip install` in Dockerfile won't help here; switch to a multi-stage build with explicit `pip install -r requirements.txt` after `COPY requirements.txt`.

### 4. MinIO buckets not auto-created on `docker compose up`
- **Where**: `infrastructure/minio/init-buckets.sh` exists but only runs via `make minio-init` manually.
- **Symptom (cv-service log)**:
  ```
  {"detail":"MinIO upload failed: An error occurred (NoSuchBucket) when calling the PutObject operation:
  The specified bucket does not exist"}
  ```
- **Fix**: add a one-shot `minio-init` service to `docker-compose.yml` with `depends_on: minio: service_healthy`, running the script automatically.

### 5. Qdrant collections not auto-created
- **Where**: `init_qdrant.py` is a manual script. `services/cv-analyzer-agent/src/rag/qdrant_client.py` assumes `cv_embeddings` exists.
- **Symptom**:
  ```
  PUT http://qdrant:6333/collections/cv_embeddings/points?wait=true 404 Not Found
  Collection `cv_embeddings` doesn't exist!
  ```
- **Fix**: add a `qdrant-init` one-shot service to compose, OR make each agent create-if-missing on startup (the safer pattern).

### 6. `init-buckets.sh` has CRLF line endings
- **Where**: `infrastructure/minio/init-buckets.sh` saved as Windows CRLF; bash inside Linux container fails.
- **Symptom**:
  ```
  /tmp/init-buckets.sh: line 3: $'\r': command not found
  mc: <ERROR> Unable to make bucket `local/cvs-raw\r`. Bucket name contains invalid characters
  ```
- **Fix**: convert to LF (run `dos2unix` or save with LF). Add `* text=lf` for `.sh` in `.gitattributes`.

---

## P1 — Functional gaps

### 7. api-gateway `/health` is JWT-protected (returns 401)
- **Where**: `api-gateway/src/app.controller.ts:13` defines `GET /health` but has no `@Public()` decorator; the global `JwtAuthGuard` rejects unauthenticated requests.
- **Symptom**: `curl http://localhost:8000/health` → `401 Unauthorized`.
- **Fix**: add `@Public()` to `getHealth()` in `app.controller.ts`.

### 8. api-gateway `JWT_PUBLIC_KEY_PATH` fallback points to private.pem
- **Where**: `api-gateway/src/main.ts:21`
  ```ts
  const keyPath = process.env.JWT_PUBLIC_KEY_PATH || './keys/private.pem';
  ```
- **Effect**: if env var is unset, gateway uses the *private* key as the *public* verifier — JWT verification on the CV proxy preHandler silently succeeds OR fails depending on which key is loaded.
- **Fix**: change fallback to `'./keys/public.pem'`.

### 9. auth is mocked — no link to user-service
- **Where**: `api-gateway/src/auth.controller.ts:30-41`. `register` and `login` just base64 the email and sign a JWT — there is no DB call, no password hashing, no duplicate check.
- **Effect**: anyone can "register" the same email twice and get a different `userId` each time (since `userId = base64(email)` actually returns the same id deterministically — but no DB row is ever created). Downstream services may try to look up `users.id = userId` and find nothing.
- **Fix**: proxy `/api/auth/register` and `/api/auth/login` to user-service:8001 instead of generating tokens locally. user-service is up and listening on 8001 today.

### 10. job-match Qdrant client version incompatible with server
- **Where**: `services/job-match-agent/requirements.txt` pulls `qdrant-client` (latest = 1.18) but server image is `qdrant:v1.10.0`.
- **Symptom**:
  ```
  UserWarning: Qdrant client version 1.18.0 is incompatible with server version 1.10.0
  ```
- **Fix**: pin `qdrant-client==1.10.*` in `requirements.txt`, or bump the server image.

---

## P2 — Cosmetic / non-blocking

### 11. cv-service has no `/health` endpoint (returns 404)
- **Where**: `services/cv-service/src/main.py` — only `/upload` and `/status/{job_id}`.
- **Fix**: add `@app.get("/health")` returning `{"status": "ok"}`. Required for docker healthcheck.

### 12. user-service has no `/health` endpoint
- Same as #11 for the Spring Boot service. Add a `/health` controller.

### 13. hr-interview-agent + technical-interview-agent use deprecated `google.generativeai`
- **Symptom**:
  ```
  import google.generativeai as genai
  ...
  Please switch to the `google.genai` package as soon as possible.
  ```
- **Fix**: migrate to `from google import genai` (already done in cv-analyzer + learning-path).

### 14. `docker-compose.yml` declares obsolete `version:` key
- **Symptom**: `docker compose config` prints `the attribute version is obsolete`.
- **Fix**: remove the top-level `version: '3.x'` line.

### 15. cv-analyzer Pydantic v2 deprecation warnings — none observed but worth verifying

### 16. `tests/e2e/flow1_test.sh` requires bash + jq — not portable on Windows
- **Where**: `Makefile:67` runs `bash tests/e2e/flow1_test.sh`. Windows devs cannot run `make test-flow1` without WSL.
- **Fix**: port to Python like `flow3_test.py`, or document the bash/jq requirement explicitly.

---

## What actually works (good news)

- ✅ `docker compose up` builds & starts all profiles after the postgres port was freed
- ✅ api-gateway routes mapped correctly (`/api/auth/*`, `/api/cv/*`, `/ws/hr-interview/*`, `/ws/tech-interview/*`, `/api/users/*`)
- ✅ Auth: register + login return a valid RS256 JWT, verified by gateway
- ✅ CV upload: `POST /api/cv/upload` reaches cv-service (after MinIO bucket exists)
- ✅ cv-uploaded → cv-analyzer pipeline: PDF extracted, Gemini called for scoring + gap analysis, embedding generated (3072 dim), upserted into `cv_embeddings`, status `analyzed` in `cv_uploads`
- ✅ Event published on `cv.analyzed` topic (verified by orchestrator log "received event")
- ✅ All 12 service containers stay up

## What fails E2E

- ❌ orchestrator workflow (broken by P0 #1)
- ❌ learning-path & job-match endpoints return 404 because no workflow output exists for the user
- ❌ notification-service email/push not testable (P0 #2)
- ❌ job-scraper not running (P0 #3)

---

## Additional issues found while fixing

### 17. [P1] job-scraper-service Dockerfile does NOT install requirements.txt
- **Where**: `services/job-scraper-service/Dockerfile:8`
  ```
  RUN pip install --no-cache-dir fastapi==0.111.0 "uvicorn[standard]==0.30.1" pydantic==2.7.4
  ```
  Only 3 packages, despite `requirements.txt` listing 12 (redis, celery, playwright, aiokafka, …).
- **Fix**: `RUN pip install --no-cache-dir -r requirements.txt` ✅ done.

### 18. [P1] job-scraper-service: `from tasks import` (relative import broken in container)
- **Where**: `services/job-scraper-service/src/main.py:7` does `from tasks import run_scraping_pipeline` — works only if `/app/src` is on PYTHONPATH. Inside the container, `python -m uvicorn src.main:app` puts `/app` (not `/app/src`) on PYTHONPATH.
- **Fix**: change to `from .tasks import run_scraping_pipeline` (relative) or `from src.tasks import run_scraping_pipeline`.

### 19. [P1] notification-service: SseController injected as dependency without being a provider
- **Where**: `services/notification-service/src/app.module.ts:10` lists `SseController` only under `controllers:`, but `KafkaConsumerService` injects it via constructor.
- **Symptom**: `Nest can't resolve dependencies of the KafkaConsumerService (HttpService, EmailService, ?). The argument at index 2 is missing.`
- **Fix**: add `SseController` to `providers:` array so NestJS treats it as injectable (same singleton serves both the HTTP route and Kafka pushes). ✅ done.

### 20. [P1] notification-service: VAPID setup crashes on placeholder keys
- **Where**: `services/notification-service/src/email/email.service.ts:26-30` calls `setVapidDetails` with `'default_public_key'` fallback. `web-push` validates this and throws `Vapid public key should be 65 bytes long when decoded.` → entire service crash-loops.
- **Fix**: skip `setVapidDetails` when env vars are not set; log a warning instead. Push won't work without real keys, but email + Kafka still start. ✅ done.

### 21. [P2] learning-path-agent: external API keys not provided
- **Symptom**: `your-youtube-data-api-key` literally passed as the key, returns 400 from YouTube and 403 from Udemy.
- **Effect**: learning path is *generated* (Gemini works), but `resources[]` will be empty for each module.
- **Fix**: document `YOUTUBE_DATA_API_KEY` and `UDEMY_CLIENT_ID`/`UDEMY_CLIENT_SECRET` in `.env.example`; have integration code degrade gracefully when missing (don't log spam).

### 22. [P2] minio/mc:RELEASE.2024-07-16T03-15-26Z tag does not exist on Docker Hub
- Caught while wiring up `minio-init`. Switched to `:latest`. ✅

