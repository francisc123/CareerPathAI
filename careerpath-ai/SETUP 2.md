# CareerPath AI — Setup Guide

This guide takes a developer from a clean machine to a fully working CareerPath AI stack in **under 15 minutes** on a reasonable broadband connection.

The system is a 24-container microservices platform. Everything runs locally in Docker; no cloud account is needed for development.

---

## 1. Prerequisites

| Tool             | Minimum version | How to install (macOS)          | How to install (Linux)              |
| ---------------- | --------------- | ------------------------------- | ----------------------------------- |
| Docker Desktop   | 4.30 (engine 26)| https://docker.com/products/docker-desktop | `curl -fsSL https://get.docker.com \| sh` |
| Docker Compose v2| bundled with Docker Desktop | — | `apt install docker-compose-plugin` |
| Git              | 2.30+           | `brew install git`              | `apt install git`                   |
| GNU Make         | 3.81+           | preinstalled                    | `apt install make`                  |
| OpenSSL          | 1.1.1+          | preinstalled                    | preinstalled                        |
| `jq`             | 1.6+            | `brew install jq`               | `apt install jq`                    |
| `curl`           | 7.x+            | preinstalled                    | preinstalled                        |

**Docker Desktop resources** — open Settings → Resources and allocate at least **8 GB RAM and 4 CPUs**. The stack will refuse to behave on less.

> **Apple Silicon note.** Everything builds natively except `mailhog`, which is forced to `linux/amd64` and runs through Rosetta. This is fine — MailHog is a dev-only fake SMTP server, not on the hot path.

---

## 2. Clone the repository

```bash
git clone <repo-url> careerpath-ai
cd careerpath-ai
```

---

## 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in **the four variables that have no sensible default**:

```dotenv
ANTHROPIC_API_KEY=sk-ant-...        # required by the AI agents
OPENAI_API_KEY=sk-...               # required for embeddings used by cv-analyzer
JUDGE0_API_KEY=...                  # required by technical-interview-agent
YOUTUBE_API_KEY=...                 # required by learning-path-agent
```

If you only want to run Flow 1 (CV upload → analysis → job matches), you can skip `JUDGE0_API_KEY` and `YOUTUBE_API_KEY`; they're only consumed by the interview and learning agents.

The other passwords (`POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `MINIO_SECRET_KEY`, …) already have working defaults for local dev. **Change them before any non-local deployment.**

---

## 4. Generate JWT keys

```bash
make keys
```

This creates `keys/private.pem` and `keys/public.pem` (RS256, 2048-bit). The API gateway uses them to sign and verify JWTs. The target is idempotent — running it again won't overwrite existing keys.

---

## 5. Start the stack

```bash
make up
```

On a fresh machine this runs three phases:

1. **Pull base images** — Postgres, Redis, Keycloak, Redpanda, Qdrant, MinIO, Grafana, Loki, Tempo, Prometheus, OTel collector, MailHog (~2.5 GB of images, dominated by Keycloak at ~700 MB).
2. **Build local services** — 13 application containers built from the repo (~5–8 min on Apple Silicon with broadband, longer on slower disks).
3. **Wait for health** — `make up` blocks until every service with a healthcheck reports `healthy`, or 5 minutes pass.

When it finishes, you'll see:

```
✅ Stack is up. Open:
   Frontend          http://localhost:3000
   API Gateway       http://localhost:8000/health
   Keycloak          http://localhost:8484  (admin / admin)
   Redpanda Console  http://localhost:8080
   Grafana           http://localhost:3001  (admin / admin)
   MailHog           http://localhost:8025
```

---

## 6. Create Kafka topics

```bash
make redpanda-topics
```

Postgres initialises its own schema automatically on first start (init scripts under `infrastructure/postgres/init/` run via `docker-entrypoint-initdb.d`), so there is **no separate migration step** for a cold start. The `make redpanda-topics` call is the only post-`up` step.

---

## 7. Verify the install

The fastest end-to-end check:

```bash
make smoke
```

This runs both `test-flow1` (CV upload → analysis → job matching) and `test-flow2` (CV upload → learning path → progress → interview-ready transition). A green run is the cold-start success criterion.

If you want to inspect things manually:

| What                | Where                                      |
| ------------------- | ------------------------------------------ |
| Service status      | `make ps`                                  |
| All logs (tail)     | `make logs`                                |
| Gateway logs only   | `make logs-gateway`                        |
| Agent logs          | `make logs-agents`                         |
| Postgres shell      | `make db-psql`                             |
| Kafka topics & lag  | http://localhost:8080  (Redpanda Console)  |
| Traces & dashboards | http://localhost:3001  (Grafana)           |

---

## 8. Daily development loop

```bash
make up        # start everything
make ps        # see what's healthy
make logs-*    # tail specific services
make down      # stop the stack but keep data
make clean     # stop AND wipe all data (fast next start, images reused)
```

After modifying code in a service, `make up` rebuilds only that service's image automatically — no need to `make build` first.

---

## 9. Resetting

| Goal                                       | Command          | Next `make up` takes |
| ------------------------------------------ | ---------------- | -------------------- |
| Stop everything, keep all data             | `make down`      | ~30 s                |
| Wipe all data, keep built images           | `make clean`     | ~2 – 3 min           |
| Full cold start, simulate a fresh machine  | `make clean-deep`| ~10 – 15 min         |

`clean-deep` is what you run when validating that this very document still works.

---

## 10. Troubleshooting

### `make up` hangs at "Waiting for all services to report healthy"

Run `make ps` in another terminal. Look for any service in state `unhealthy` or stuck in `starting`. Tail its logs (e.g. `docker logs -f cp-orchestrator`) to see the real error.

The most common causes:

| Symptom                                                              | Cause                              | Fix                                                          |
| -------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------ |
| `cp-user-service` stays `starting` for 60 s                          | Spring Boot cold start             | This is normal — its `start_period` is 45 s.                 |
| `cp-keycloak` stays `unhealthy` past 90 s                            | Slow disk or under-provisioned RAM | Raise Docker Desktop memory to 8 GB+.                        |
| Any agent logs `KafkaConnectionError`                                 | Redpanda still rebalancing         | The retry decorator handles it; wait 30 s.                   |
| `cp-postgres` exits with "role does not exist"                       | Stale volume from older `.env`     | `make clean` and retry.                                      |
| Port 5432 / 6379 / 3000 already in use                               | A local Postgres/Redis/dev server  | Stop the conflicting service or change host ports in compose.|

### `make redpanda-topics` says "container not found"

The Redpanda container is named `cp-redpanda`. If `docker ps` doesn't show it, Redpanda hasn't started yet — wait for `make up` to finish first.

### Flow 2 fails at step 7 with `(nil)`

The `agent-orchestrator` isn't consuming `learning.completed`. Tail its logs (`docker logs cp-orchestrator --tail 100`). If you see Kafka rebalance errors but never `Consumer started on topic 'learning.completed'...`, restart it (`docker compose restart agent-orchestrator`).

### Loki or Tempo restarts in a loop

This was a known bug in older versions of the compose file. If you still see it, you have a stale `loki-config.yaml` or `tempo-config.yaml`. Pull the latest from `main` and `make clean-deep`.

### "Cannot connect to the Docker daemon"

Docker Desktop is not running. On macOS, open it from Applications.

---

## 11. What "fully functional" means

After `make up` completes and `make redpanda-topics` runs, the following should all be true:

- `make ps` shows every service as `Up (healthy)`.
- `curl http://localhost:8000/health` returns `{"status":"ok"}`.
- `curl http://localhost:8484/health/ready` returns HTTP 200 (Keycloak).
- `docker exec cp-redpanda rpk topic list` shows 9 topics.
- `make smoke` passes both E2E flows.

If any of these fails, **the system is not ready** — see the troubleshooting section above before running real work against it.

---

## 12. Useful URLs reference

| Service           | URL                          | Credentials              |
| ----------------- | ---------------------------- | ------------------------ |
| Frontend          | http://localhost:3000        | sign up in-app           |
| API Gateway       | http://localhost:8000/health | —                        |
| Keycloak admin    | http://localhost:8484        | admin / admin            |
| Redpanda Console  | http://localhost:8080        | —                        |
| MailHog UI        | http://localhost:8025        | —                        |
| MinIO Console     | http://localhost:9001        | minioadmin / change_me_minio |
| Grafana           | http://localhost:3001        | admin / admin            |
| Prometheus        | http://localhost:9090        | —                        |
| Qdrant dashboard  | http://localhost:6333/dashboard | —                     |
