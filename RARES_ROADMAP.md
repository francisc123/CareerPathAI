# 🗺️ Roadmap Rareș — CareerPath AI

**Owner:** Rareș Constantinescu
**Branch curent:** `chore/project-analysis`
**Data:** 2026-05-12
**Scop:** ghidare end-to-end pentru a duce proiectul la "ready for production"

---

## 📚 Cuprins

1. [Arhitectura proiectului](#1-arhitectura-proiectului)
2. [Taskurile mele rămase (Rareș)](#2-taskurile-mele-rămase-rareș)
3. [Detalii pe fiecare task](#3-detalii-pe-fiecare-task)
4. [Ce mai trebuie pentru production-ready (dincolo de taskurile mele)](#4-ce-mai-trebuie-pentru-production-ready-dincolo-de-taskurile-mele)
5. [Ordine recomandată](#5-ordine-recomandată)

---

## 1. Arhitectura proiectului

### Big picture

CareerPath AI e o platformă care primește un CV, îl analizează cu AI, și automat ghidează userul spre **una din 3 căi**:
- **Flow 1** — dacă CV-ul e bun (score ≥ 70) → caută joburi potrivite + generează cover letters
- **Flow 2** — dacă CV-ul e slab (score < 70) → generează plan de învățare personalizat
- **Flow 3** — după ce userul completează planul → simulări de interviu HR + tehnic

### Two-layer AI design

```
┌─────────────────────────────────────────────────────┐
│  LAYER 1 — agent-orchestrator (port 8005)           │
│  Vorbește cu userul prin WebSocket                  │
│  Shadow profiling — îl cunoaște pe user din chat    │
│  Decide ce worker să apeleze prin Kafka events      │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼ (Kafka events pe Redpanda)
┌─────────────────────────────────────────────────────┐
│  LAYER 2 — worker agents (ports 8006-8010)          │
│  Nu vorbesc niciodată direct cu userul              │
│  Fiecare ascultă un topic, procesează, publish rezultat │
└─────────────────────────────────────────────────────┘
```

### Flow-ul complet de evenimente

```
USER upload CV
    │
    ▼
[cv-service] ──► cv.uploaded
                    │
                    ▼
              [cv-analyzer-agent] ──► cv.analyzed
                                          │
                                          ▼
                                  [agent-orchestrator]
                                  routing pe scor:
                       ┌──────────────┴──────────────┐
                       │                             │
              score ≥ 70                       score < 70
                       │                             │
                       ▼                             ▼
              [job-scraper] ──► jobs.scraped   gaps.identified ──► [learning-path-agent]
                                  │                                      │
                                  ▼                                      ▼
                          [job-match-agent]                       learning.path.created
                                  │                                      │
                                  ▼                                      ▼
                          jobs.matched                              learning.completed
                                                                          │
                                                                          ▼
                                                          [hr-interview-agent] + [tech-interview-agent]
                                                                          │
                                                                          ▼
                                                          interview.hr.completed
                                                          interview.tech.completed
```

### Stack tehnologic per serviciu

| Layer | Service | Stack | Port |
|---|---|---|---|
| Frontend | frontend | Next.js 14, Tailwind, shadcn/ui, Zustand | 3000 |
| Gateway | api-gateway | NestJS + Fastify | 8000 |
| Core | user-service | NestJS + Prisma + PostgreSQL | 8001 |
| Core | cv-service | FastAPI + pdfplumber + MinIO | 8002 |
| Core | job-scraper-service | FastAPI + Playwright (Chromium) | 8003 |
| Core | notification-service | NestJS + SSE | 8004 |
| AI | **agent-orchestrator** | FastAPI + LangGraph + aiokafka | 8005 |
| AI | **cv-analyzer-agent** | FastAPI + Gemini + Qdrant | 8006 |
| AI | **learning-path-agent** | FastAPI + Gemini + Udemy/YouTube API | 8008 |
| AI | **job-match-agent** | FastAPI + Qdrant semantic search + Gemini | 8007 |
| AI | **hr-interview-agent** | FastAPI + WebSocket + Gemini streaming | 8009 |
| AI | **technical-interview-agent** | FastAPI + WebSocket + Gemini + Judge0 | 8010 |

**Serviciile mele (Rareș):** toate cele 5 AI agents (în bold).

### Infrastructură

| Componentă | Rol | Owner-ul datelor |
|---|---|---|
| **PostgreSQL** | DB relațional principal | Francisc (users, cv_uploads, scraped_jobs) + Rareș (learning_paths, quiz_attempts, interview_sessions) |
| **Redis** | Cache + session storage + Kafka workflow state | Francisc |
| **Qdrant** | Vector DB pentru semantic search (3 colecții, dim=3072) | Rareș |
| **Redpanda (Kafka)** | Event streaming între servicii | Shared |
| **MinIO** | Object storage pentru CV-uri raw | Francisc |
| **OpenTelemetry + Grafana** | Distributed tracing + metrics | Shared (CP-045 e taskul meu) |

### Topicuri Redpanda

`user.registered`, `cv.uploaded`, `cv.analyzed`, `gaps.identified`, `jobs.scraped`, `jobs.matched`, `learning.path.created`, `learning.completed`, `interview.hr.completed`, `interview.tech.completed`

### Decizii arhitecturale-cheie

- **Event-driven cu Kafka** — servicii nu se cunosc între ele, comunică prin events. Asta înseamnă că poți schimba job-match-agent fără să afectezi cv-analyzer.
- **JWT RS256 (asymmetric)** — API Gateway verifică tokenul cu cheie publică, downstream services primesc `x-user-id` în header (nu re-verifică tokenul).
- **Embedding dim = 3072** cu `gemini-embedding-001`. **NU** folosi `text-embedding-004` (e deprecated).
- **Prompts în fișiere `.txt`** (nu inline în cod) — `services/cv-analyzer-agent/prompts/cv_scoring.txt`, `gap_analysis.txt`. Iterezi pe prompt fără rebuild.

---

## 2. Taskurile mele rămase (Rareș)

**Status global:** din 19 taskuri totale, am **8 gata**, **6 parțiale**, **5 nu sunt începute**.

| # | Task ID | Status | Dificultate | Timp estimat |
|---|---|---|---|---|
| 1 | **CP-050** | 🟡 În lucru (am început acum) | ⭐ ușor | 2-3h |
| 2 | **CP-020** fix | 🟡 80% — lipsește update tabel `cv_uploads` | ⭐ ușor | 1h |
| 3 | **CP-031** fix | 🟡 45% — JWT auth + limit 15 turns + publish event | ⭐⭐ mediu | 3-4h |
| 4 | **CP-051** | 🔴 Necepiut | ⭐⭐ mediu | 3h |
| 5 | **CP-033** | 🔴 Necepiut | ⭐⭐ mediu | 3-4h |
| 6 | **CP-030** finalizare | 🟡 50% — Udemy + YouTube integration | ⭐⭐ mediu | 4h |
| 7 | **CP-032** | 🔴 35% — Judge0 + problem selector lipsesc | ⭐⭐⭐ greu | 1-2 zile |
| 8 | **CP-044** | 🟡 parțial — DLQ doar pe orchestrator | ⭐⭐ mediu | 4h |
| 9 | **CP-042** | 🔴 Necepiut | ⭐⭐ mediu | 4h |
| 10 | **CP-045** | 🔴 Necepiut | ⭐⭐ mediu | 3h |
| 11 | **CP-043** | 🔴 Necepiut (depinde de CP-031 + CP-032) | ⭐⭐ mediu | 3h |

**Total estimat:** ~5-7 zile de muncă focusată.

---

## 3. Detalii pe fiecare task

### 🟡 CP-050 — Learning Path Quiz API (în lucru)

**Ce face:** 3 endpoint-uri REST în `learning-path-agent` pentru ca frontend-ul să afișeze și să submitease quiz-uri.

**De ce:**
Pagina `/learning/quiz/[id]` din frontend e deja gata (Vlad), dar primește `501 Not Implemented`.

**Fișiere atinse:**
- `services/learning-path-agent/src/generator.py` — adaugi `QuizQuestion` în schema Pydantic + câmp `quiz` pe `Module`
- `services/learning-path-agent/src/prompts.py` — modifici prompt-ul Gemini să genereze quiz
- `services/learning-path-agent/src/database.py` — adaugi helper `find_module_in_path()`
- `services/learning-path-agent/src/main.py` — implementezi cele 2 endpoint-uri

**Pași:**
1. Extinde schema Pydantic (`QuizQuestion` + `Module.quiz`) ✅ făcut
2. Modifică prompt-ul Gemini să genereze 10 întrebări per modul (în curs)
3. Adaugă helper `find_module_in_path(plan_data, week, module_idx)`
4. Implementează `GET /learning/quiz/{module_id}` (strip `correct_index` din response!)
5. Implementează `POST /learning/quiz/{module_id}/submit` (compară, calculează scor, salvează în `quiz_attempts`)

**Tehnologii:**
- **FastAPI** — endpoints HTTP
- **Pydantic** — validare + 2 modele (`QuizQuestion` cu correct_index pentru DB, `QuizQuestionPublic` fără pentru response)
- **asyncpg** — query-uri în PostgreSQL fără să blochezi event loop-ul
- **PostgreSQL JSONB** — `plan_data` are quiz nested în structura modulelor
- **Gemini 2.5 Flash** — generează quiz-ul

**Cum decoding `module_id`:** format compozit `{user_id}__{week_num}__{module_idx}`. Stateless, fără tabelă în plus.

---

### 🟡 CP-020 fix — Update tabel `cv_uploads` din cv-analyzer-agent

**Ce face:** după ce CV-ul e analizat, scriem rezultatul (score, skills, gaps) și în PostgreSQL, nu doar publicăm event Kafka.

**De ce:**
Acum, cv-analyzer publish `cv.analyzed` pe Kafka, dar tabelul `cv_uploads` nu se update-ează cu rezultatul. Asta înseamnă că `GET /api/cv/status/{job_id}` returnează mereu `status="processing"` chiar dacă analiza e gata. Frontend-ul nu știe niciodată că s-a terminat dacă SSE-ul are vreo problemă.

**Fișiere atinse:**
- `services/cv-analyzer-agent/src/database.py` — adaugi funcție `update_cv_upload_result()`
- `services/cv-analyzer-agent/src/consumers/cv_upload_consumer.py` — apelezi funcția nouă

**Pași:**
1. Scrie `async def update_cv_upload_result(pool, job_id, status, score, skills, gaps)` — face UPDATE pe `cv_uploads`
2. În consumer, după ce primești rezultatul de la Gemini și înainte de publish `cv.analyzed`, apelează update-ul
3. Handle errori: dacă DB e down, log dar nu fail tot pipeline-ul (eventul Kafka e sursa de adevăr)

**Tehnologii:** asyncpg, PostgreSQL UPDATE

---

### 🟡 CP-031 fix — HR Interview safety (auth + limit + event)

**Ce face:** 3 fix-uri critice pe `hr-interview-agent`:
1. **JWT auth pe WebSocket** — fără asta oricine se conectează și consumă quota Gemini
2. **Limită 15 turns** — fără asta sesiunea poate rula la infinit
3. **Publish `interview.hr.completed`** — fără asta orchestrator-ul nu știe că interviul s-a terminat (Flow 3 e blocat)

**De ce:**
- Auth lipsește = vulnerability de cost (oricine spam-uiește API-ul, plătești tu Gemini)
- Limita lipsește = un user uitat conectat poate face 1000 turns
- Event lipsește = orchestrator-ul nu poate trece la pasul următor (CP-033 e blocat)

**Fișiere atinse:**
- `services/hr-interview-agent/src/main.py` sau `routers/` — adaugi dependency `verify_jwt_ws(token: str = Query(...))`
- `services/hr-interview-agent/src/conversation.py` — adaugi counter de turns + check
- `services/hr-interview-agent/src/database.py` (sau publishers) — publish event nou

**Pași:**
1. Citește JWT din query param (`?token=...` pentru WS) — verifică cu cheia publică din `/keys/public.pem`
2. La fiecare mesaj de user, incrementează `turn_count` în Redis sau în session state
3. Dacă `turn_count >= 15`: rulează analiza post-interview, salvează în DB, publică event, închide WS
4. Schema event `interview.hr.completed`: `{user_id, session_id, score, feedback, transcript, completed_at}`

**Tehnologii:**
- **python-jose** sau **PyJWT** — verifică JWT cu cheia publică RS256
- **WebSocket query params** — singura cale de auth în WS (header-urile nu se setează ușor)
- **aiokafka** — pentru publish event

---

### 🔴 CP-051 — Agent Orchestrator monitoring API

**Ce face:** endpoint-uri admin pentru a vedea/manipula workflow-urile active.

**De ce:**
Fără monitoring, dacă un workflow se blochează (ex. job-scraper crapă), nu știi care useri sunt afectați. Ops/admin trebuie să poată retry.

**Endpoint-uri:**
- `GET /workflow/{user_id}` — istoric complet workflow (de la cv.uploaded la fin)
- `GET /workflow/{user_id}/status` — versiune lightweight pentru polling frontend
- `POST /workflow/{user_id}/retry` — admin: resetează state Redis + re-publish event eșuat
- `GET /workflows/active` — count active per flow type (pentru Grafana ops dashboard)

**Fișiere atinse:**
- `services/agent-orchestrator/src/routers/monitoring.py` (creezi nou)
- `services/agent-orchestrator/src/main.py` — register router-ul

**Pași:**
1. Definește Pydantic response models (`WorkflowStatus`, `WorkflowHistory`)
2. Implementează GET endpoints citind din Redis (`workflow:{user_id}` key)
3. POST retry: șterge cheia Redis + re-publish eventul de la check-point
4. Adaugă HTTP Basic Auth pe `/retry` și `/workflows/active` (admin only) — credențiale din env

**Tehnologii:**
- **FastAPI dependency injection** pentru auth
- **redis-py** — citire/scriere Redis async (probabil deja folosit)
- **aiokafka producer** — pentru retry

---

### 🔴 CP-033 — Agent Orchestrator full LangGraph wiring

**Ce face:** orchestrator-ul ascultă toate cele 3 evenimente de "completare" (learning, hr, tech) și completează flow-ul.

**De ce:**
Acum, orchestrator-ul gestionează doar tranziția `cv.analyzed → routing`. Dar după ce learning path e completat, nu trece la următorul pas (interviu). Flow 3 nu e wired.

**Consumeri noi de adăugat:**
1. `learning.completed` consumer:
   - Update workflow state în Redis: `current_node = "interview_ready"`
   - Trimite SSE notification la user: "You're ready for interviews!"
2. `interview.hr.completed` consumer:
   - Update workflow state
   - Trimite SSE nudge dacă user nu a făcut tech: "Now try the Technical Interview"
3. `interview.tech.completed` consumer:
   - Mark workflow `fully_completed`
   - Calculează `final_score = cv_score*0.3 + hr_score*0.3 + tech_score*0.4`
   - Update tabel `profiles.final_score`
   - Publică `workflow.completed` event

**Fișiere atinse:**
- `services/agent-orchestrator/src/consumers/learning_completed_consumer.py` (nou)
- `services/agent-orchestrator/src/consumers/interview_hr_completed_consumer.py` (nou)
- `services/agent-orchestrator/src/consumers/interview_tech_completed_consumer.py` (nou)
- `services/agent-orchestrator/src/main.py` — register noile consumere

**Tehnologii:**
- **aiokafka** — multi-topic consumer
- **LangGraph state updates** — extinde grafu de stări existent
- **httpx** — apel către notification-service pentru SSE push

---

### 🟡 CP-030 finalizare — Udemy + YouTube API integration

**Ce face:** când learning-path-agent generează planul, în loc de URL-uri inventate de Gemini, face apeluri reale la API-uri pentru a găsi cursuri reale.

**De ce:**
Acum, Gemini halucinează URL-uri Udemy/YouTube care nu există. User intră, dă 404.

**Pași:**
1. **Udemy Affiliate API**:
   - Register la Udemy Affiliate Program (gratuit)
   - `GET /api-2.0/courses/` cu parametri `search`, `price=price-free` sau `price<=20`, `ratings>=4.5`
   - Salvează API key în `.env`
2. **YouTube Data API v3**:
   - Activează în Google Cloud Console (1000 unități/zi gratuit)
   - `search.list` cu `q=topic + tutorial`, `order=viewCount`, `videoEmbeddable=true`
3. **Pipeline nou** în generator:
   - Gemini generează doar **topicurile** și **structura modulelor** (fără resurse)
   - Pentru fiecare topic, apelezi Udemy + YouTube API
   - Combini rezultatele în câmpul `resources` al modulului
4. **Fallback dacă API down**: dacă API-ul return error, folosește un placeholder ("Search YouTube for: {topic}")

**Fișiere atinse:**
- `services/learning-path-agent/src/integrations/udemy.py` (creezi)
- `services/learning-path-agent/src/integrations/youtube.py` (creezi)
- `services/learning-path-agent/src/generator.py` — modifici flow-ul

**Tehnologii:**
- **httpx** — async HTTP client pentru API calls
- **tenacity** — retry cu backoff dacă API rate-limit hit

---

### 🔴 CP-032 — Technical Interview Agent + Judge0

**Ce face:** interviu tehnic cu probleme algoritmice, execuție cod în sandbox Judge0, evaluare automată.

**De ce:**
Acum, technical-interview-agent are doar WebSocket streaming generic. Nu poate executa cod, nu selectează probleme, nu evaluează soluții.

**Pași:**
1. **Problem selector prompt** (Gemini): input `{skills, seniority}`, output 1 problemă algoritmică + 1 system design
2. **Judge0 integration**:
   - Self-host Judge0 cu Docker (pentru a evita rate limits ale variantei public) sau folosește RapidAPI
   - `POST /submissions` cu `{source_code, language_id, stdin}`
   - Poll `GET /submissions/{token}` pentru rezultat (status, stdout, stderr, time, memory)
3. **WebSocket message handler**:
   - `{"type": "code_submission", "content": code, "language": "python"}` → trimite la Judge0
   - Așteaptă rezultatul (max 10s timeout)
   - Trimite înapoi `{"type": "test_results", ...}`
4. **Code evaluation prompt** (Gemini): input `{problem, user_code, test_results}`, output `{correctness, complexity, code_quality, feedback}`
5. **Session end**: după 2 probleme rezolvate, generează raport final, salvează în `interview_sessions`, publică `interview.tech.completed`

**Fișiere atinse:**
- `services/technical-interview-agent/src/integrations/judge0.py` (nou)
- `services/technical-interview-agent/src/prompts.py` — adaugi 2 prompturi noi
- `services/technical-interview-agent/src/conversation.py` — rescrii pentru a gestiona code submissions
- `docker-compose.yml` — adaugi Judge0 service local

**Tehnologii:**
- **Judge0** — sandbox open-source pentru execuție cod în 60+ limbaje
- **httpx** — apeluri la Judge0
- **Pydantic** — modele pentru `CodeSubmission`, `TestResult`

---

### 🟡 CP-044 — Error handling consistent peste tot

**Ce face:** retry + DLQ + fallback pentru toate AI agents.

**De ce:**
Acum, dacă Gemini API e down 30 secunde, jumătate din agents crapă. Production-ul trebuie să fie resilient.

**Per agent:**
1. **Gemini API failures**:
   - `tenacity` retry 3x cu exponential backoff (1s, 2s, 4s)
   - După 3 eșecuri: mark job ca `failed` în DB, publish la DLQ topic (`{topic}.dlq`)
   - SSE error la user: "Service temporarily unavailable"
2. **Qdrant failures**:
   - Dacă Qdrant down, skip vector storage, continuă cu LLM-only
3. **Embedding failures**:
   - Fallback la `sentence-transformers` local (model `all-MiniLM-L6-v2`)
   - Dimensiuni diferite (384 vs 3072) — folosește colecție separată `cv_embeddings_fallback`
4. **Judge0 timeout** (CP-032 prerequisit):
   - Timeout 10s, mesaj clar la user, nu fail tot interviul

**Fișiere atinse:** toate AI agents (cv-analyzer, learning-path, job-match, hr-interview, tech-interview) — adăugi decoratorul `@retry` pe funcțiile externe.

**Tehnologii:**
- **tenacity** — retry decorator
- **sentence-transformers** — embedding fallback local
- **Kafka DLQ pattern** — topic dedicat pentru mesaje eșuate

---

### 🔴 CP-042 — AI Quality Review (eval framework)

**Ce face:** test automat care rulează 10 CV-uri prin cv-analyzer și verifică consistența scoring-ului.

**De ce:**
Scoring-ul Gemini poate varia. Dacă rulezi același CV de 3 ori și primesti scoruri 75, 82, 68, prompt-ul tău e instabil. Userul îl observă și pierde încrederea.

**Pași:**
1. Colectează 10 CV-uri reale (sanitized) — 2 senior, 2 mid, 3 junior, 1 bootcamp, 1 career changer, 1 weak
2. Build `evals/cv_scoring_eval.py`:
   - Loop prin cele 10 CV-uri
   - Pentru fiecare, rulează prin cv-analyzer-agent (sau direct prin Gemini cu prompt-ul)
   - Rulează de 3 ori, calculează deviația standard a scorului
   - Generează tabel de comparație
3. **Criteriu de pass**: deviația < ±3 puncte per CV
4. Dacă nu trece: tunează prompt-ul (adaugi few-shot examples — exemple de CV-uri cu scorurile lor așteptate)

**Fișiere atinse:**
- `prompt_testing/cv_scoring_eval.py` (creezi)
- `prompt_testing/samples/` — 10 CV-uri PDF/text
- `services/cv-analyzer-agent/prompts/cv_scoring.txt` — actualizare cu few-shot dacă e nevoie

**Tehnologii:**
- **anthropic SDK** sau **google-genai** (cum e configurat) — apeluri directe la LLM
- **statistics** (Python stdlib) — calcul deviație standard

---

### 🔴 CP-045 — Grafana dashboards (observability)

**Ce face:** 3 dashboards JSON care arată metrici production.

**De ce:**
Fără dashboards, când userul zice "e lent" nu știi dacă e DB, Kafka, Gemini, sau frontend. Cu dashboards vezi instant unde e problema.

**3 dashboard-uri:**

1. **`services.json`** — overview general
   - p50/p95/p99 latency per serviciu
   - Error rate per serviciu (% requests cu 5xx)
   - Requests/sec
   - Container CPU + RAM
2. **`kafka.json`** — sănătate Redpanda
   - Consumer lag per topic + partition
   - Messages/sec per topic
   - Active consumer groups
3. **`ai-agents.json`** — costuri AI
   - Gemini API calls/min
   - Avg time per scoring/quiz generation
   - Qdrant query p95 latency
   - Cost estimat AI/zi

**Pași:**
1. Build dashboards în Grafana UI manual (e mai ușor)
2. Export ca JSON
3. Salvează în `observability/grafana/dashboards/`
4. Configurează `grafana.ini` să auto-import-eze dashboards la pornire

**Fișiere atinse:**
- `observability/grafana/dashboards/services.json`
- `observability/grafana/dashboards/kafka.json`
- `observability/grafana/dashboards/ai-agents.json`
- `observability/grafana/provisioning/dashboards.yml`

**Tehnologii:**
- **OpenTelemetry** — surse de tracing/metrics (deja configurat)
- **Prometheus** — agregare metrics
- **Tempo** — distributed tracing
- **Grafana** — vizualizare

---

### 🔴 CP-043 — E2E test Flow 3 (Interview)

**Ce face:** test automatizat care simulează un interviu HR + tech complet de la browser.

**De ce:**
Verifică că tot pipeline-ul interviu funcționează: WS streaming, JWT auth, code execution, post-interview analysis, event publication.

**Pași:**
1. Script `tests/e2e/flow3_test.sh`:
   - Register user
   - Connect WS la HR interview
   - Trimite 15 mesaje (simulează turns)
   - Verifică streaming response (delta + done frames)
   - Verifică `interview.hr.completed` published în Kafka
   - Connect WS la tech interview
   - Trimite cod Python
   - Verifică Judge0 result în max 10s
   - Verifică `interview.tech.completed` published
   - Verifică `interview_sessions` table populated
2. Manual smoke test în browser pentru UX issues

**Fișiere atinse:**
- `tests/e2e/flow3_test.sh` (nou)
- `tests/e2e/helpers/ws_client.py` (helper pentru WS testing)
- `Makefile` — adaugi `make test-flow3`

**Depinde de:** CP-031 + CP-032 finalizate.

**Tehnologii:**
- **websockets** (Python) — client WebSocket pentru test
- **httpx** — pentru REST calls de setup
- **pytest** sau bash — runner

---

## 4. Ce mai trebuie pentru production-ready (dincolo de taskurile mele)

Astea NU sunt în taskurile mele (Rareș), dar fără ele platforma nu e production-ready.

### A. Lucruri pe care le face altcineva (Francisc/Vlad)

| Owner | Ce trebuie făcut | Status |
|---|---|---|
| **Francisc** | **CP-026** — job-scraper-service (LinkedIn, Indeed, eJobs). Acum e stub 5%, returnează `"not yet implemented"` | 🔴 critic — blochează tot Flow 1 |
| Francisc | **CP-028** — job-match-agent end-to-end (depinde de CP-026) | 🔴 critic |
| Francisc | **CP-029** — notification-service email + SSE polish | 🟡 30% |
| Francisc | **CP-018** — wire-uire toate routes API Gateway | 🟡 65% |
| **Vlad** | **CP-034** — pagină `/interview/hr` (lipsește complet) | 🔴 critic |
| Vlad | **CP-035** — pagină `/interview/technical` cu Monaco editor | 🔴 critic |
| Vlad | **CP-036, CP-037** — wire toate paginile la API real (nu mock) | 🟡 parțial |
| Vlad | **CP-046, CP-047, CP-048, CP-049** — testing, bug fixing, responsive, demo prep | 🔴 |
| Francisc | **CP-038, CP-039** — E2E tests Flow 1 + Flow 2 | 🔴 |
| Francisc | **CP-040, CP-041** — Docker health checks + performance audit | 🟡 |

### B. Lucruri cross-cutting (echipă, nu doar 1 owner)

| # | Ce | De ce | Cine |
|---|---|---|---|
| 1 | **Drift backlog vs cod** — user-service e Java/Spring în cod, backlog zice NestJS+Prisma. Aliniem. | Confuzia documentație/realitate face onboarding nou-veniți imposibil | Francisc |
| 2 | **Standardize model LLM** — acum amestec Gemini 2.0 + 2.5. Alege unul | Consistency în costuri/comportament | Rareș |
| 3 | **CI/CD pipeline** — GitHub Actions cu build + test + deploy | Fără CI nu poți avea încredere că push-ul nu strică prod | Francisc + Rareș |
| 4 | **Secret management** — API keys nu trebuie să fie în `.env` plain pentru prod. Folosește HashiCorp Vault sau cloud secrets manager | Compromise = costuri Gemini explodează | Francisc |
| 5 | **Rate limiting per-user** — un user să nu poată face 1000 CV uploads/zi | Cost protection | Francisc (API Gateway) |
| 6 | **Persistență istoric conversație** — Redis TTL șterge după 1-7 zile. Mută în PostgreSQL pentru long-term | UX: user vrea să revadă conversațiile vechi | Rareș |
| 7 | **GDPR compliance** — drept la ștergere, export date | Legal requirement EU | Francisc |
| 8 | **Backup automat PostgreSQL** — daily snapshot | Disaster recovery | Francisc |
| 9 | **Load testing** — k6 sau locust cu 100 useri simultani | Validare capacitate înainte de lansare | Francisc (CP-041) |
| 10 | **Logs centralizate** — Loki + Grafana, retention 30 zile | Debug în prod | Francisc + Rareș (CP-045) |
| 11 | **HTTPS + SSL certificates** — Let's Encrypt cu auto-renewal | Browser requirement | Francisc |
| 12 | **Documentație onboarding** — `SETUP.md` step-by-step | Nou dev să poată porni proiectul în < 15 min | Francisc (CP-040) |

### C. Features lipsă vs competiție (diferențiatori)

Astea NU sunt blocking pentru "ready for production", dar sunt importante ca produsul să fie competitiv vs Jobscan/Final Round AI/AiApply:

| Feature | Prioritate | Cine |
|---|---|---|
| **ATS keyword match score** (target ≥75% match rate vs job description) — Jobscan vinde fix asta | P1 | Rareș (Gemini prompt nou) |
| **LinkedIn profile import** la onboarding | P2 | Francisc + Vlad |
| **Application tracker (Kanban)** — track aplicări | P2 | Vlad |
| **Salary insights** per role + location | P2 | Francisc (scraping) |
| **Localizare RO** — UI, prompts, eJobs scraping | P1 — diferențiator pe piața RO | Toți |
| **STAR framework** pentru răspunsuri behavioral | P2 | Rareș (prompt HR interview) |
| **Cover letter cu company research** — Gemini scrape news + about page | P2 | Rareș (job-match) |

---

## 5. Ordine recomandată

Strategia: **fundație → safety → features → polish**.

### Săptămâna 1 (zile 1-5) — Unblock & Safety
1. **CP-050** Quiz API ← *acum, în curs*
2. **CP-020 fix** Update `cv_uploads` (rapid, 1h)
3. **CP-031 fix** HR Interview safety (CRITICAL — securitate)

### Săptămâna 2 (zile 6-10) — Wire everything
4. **CP-051** Orchestrator monitoring API
5. **CP-033** Orchestrator full LangGraph wiring
6. **CP-030 finalizare** Udemy + YouTube integration

### Săptămâna 3 (zile 11-17) — Heavy lifting
7. **CP-032** Tech Interview + Judge0 (2 zile)
8. **CP-044** Error handling consistent peste tot

### Săptămâna 4 (zile 18-25) — Quality + Observability
9. **CP-042** AI Quality Review
10. **CP-045** Grafana dashboards
11. **CP-043** E2E test Flow 3

---

## Resurse utile

- **README principal:** `careerpath-ai/README.md`
- **Backlog Jira:** `careerpath-ai/jira_tasks_backlog.md`
- **Status snapshot:** `careerpath-ai/PROJECT_STATUS.md`
- **Analiză completă:** `ANALYSIS.md`
- **CLAUDE.md (instrucțiuni Claude):** `CLAUDE.md`
- **Documentație Gemini:** https://ai.google.dev/docs
- **Documentație Qdrant:** https://qdrant.tech/documentation/
- **Documentație FastAPI:** https://fastapi.tiangolo.com/
- **Judge0 self-host:** https://github.com/judge0/judge0

---

**Last updated:** 2026-05-12
**Maintainer:** Rareș Constantinescu
