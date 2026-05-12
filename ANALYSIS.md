# CareerPath AI — Analiză proiect + Market Research

**Branch:** `chore/project-analysis`
**Data:** 2026-05-12
**Autor:** Rareș (analiză generată cu Claude)

---

## 1. Sinteză executivă

Proiectul are **scheletul complet** (Docker Compose, 10 microservicii, frontend Next.js, infrastructură PostgreSQL + Redpanda + Qdrant + MinIO) și **2 flow-uri funcționale** la nivel de pipeline:

- ✅ **Flow 0 (conversational triage)** — agent-orchestrator chat WebSocket + shadow profiling funcționează
- ✅ **Flow 1 parțial (CV → analiză)** — CV upload → cv-analyzer → score + skills → publish `cv.analyzed`

**Gap-ul major:** mai mult de jumătate dintre serviciile listate ca "implementate" în backlog sunt **stub-uri** sau au piese critice lipsă. La frontend lipsesc complet 2 din 5 pagini-cheie (HR interview, Tech interview). Job scraping nu există deloc.

**Verdict:** demo-ul tehnic se poate face pe Flow 0 + Flow 1 până la score. Restul (job matching real, learning path quiz, interviu) nu sunt user-ready.

---

## 2. Inventar real al implementării (servicii backend)

| # | Serviciu | Status real | Ce e implementat | Ce lipsește (P0/P1) |
|---|---|---|---|---|
| 1 | **agent-orchestrator** (8005) | 🟢 **70%** | Chat WebSocket, shadow profiling (Gemini), LangGraph routing score≥70/<70, DLQ pentru evenimente invalide, retry pentru job-scraper | **P0**: monitoring API (`GET /workflows/active`, `POST /retry`) — backlog CP-051; consumer pe `learning.completed`, `interview.hr.completed`, `interview.tech.completed` (CP-033) |
| 2 | **cv-analyzer-agent** (8006) | 🟢 **80%** | Consumer `cv.uploaded`, scoring + gap analysis prin Gemini, Qdrant embedding save, pipeline cu retry, prompts în fișiere | **P1**: nu actualizează tabelul `cv_uploads` în PostgreSQL cu rezultatul (doar publică `cv.analyzed`); fără DLQ structurat pentru CV-uri eșuate; embedding-ul folosește dim 3072 dar nu confirmă model `gemini-embedding-001` peste tot |
| 3 | **job-scraper-service** (8003) | 🔴 **5% — STUB** | Doar `GET /scrape/{user_id}` returnează `"queued, not yet implemented"`. Folderele `scrapers/`, `services/`, `tasks/`, `routers/` sunt **goale** | **P0 ÎNTREG**: scraperele LinkedIn/Indeed/eJobs cu Playwright + BS4, Celery workers, dedup pe URL hash, insert în `scraped_jobs`, publish `jobs.scraped` (backlog CP-026) |
| 4 | **job-match-agent** (8007) | 🟡 **40%** | Consumer + matcher.py (101 linii), qdrant_client, GET `/jobs/{user_id}` din DB | **P0**: depinde 100% de job-scraper (care nu există), deci pipeline-ul nu poate fi testat live; **P1**: reranker prompt există dar nu e validat end-to-end; cover letter generation nu există |
| 5 | **learning-path-agent** (8008) | 🟡 **50%** | Consumer pe `gaps.identified`, generator.py cu Gemini, GET `/learning/{user_id}` din DB | **P0**: `GET /learning/quiz/{module_id}` și `POST .../submit` returnează **501 Not Implemented** (CP-050); **P1**: integrarea Udemy API + YouTube API nu e wiring-uită (există `integrations/` dar nu e clar dacă funcționează) |
| 6 | **hr-interview-agent** (8009) | 🟡 **45%** | WebSocket `/interview/hr/{user_id}/{session_id}`, streaming Gemini, post-interview analysis cu transcript → JSON score | **P0**: fără autentificare JWT pe WS (oricine se poate conecta); fără încărcare profil user din PostgreSQL (system prompt nu are context); fără limit la 15 turns (poate rula la infinit); **P1**: nu publică `interview.hr.completed` event când termină |
| 7 | **technical-interview-agent** (8010) | 🟡 **35%** | WebSocket basic streaming Gemini, identic cu HR | **P0 ÎNTREG**: lipsește integrarea **Judge0** pentru execuție cod (CP-032), problem selector, code submission handler, evaluare structurată cu test results |
| 8 | **cv-service** (8002) | 🟢 **70%** | FastAPI upload, extraction (PDF/DOCX), MinIO storage, Redpanda publish `cv.uploaded` | **P1**: nu am verificat OCR pe imagini cu pytesseract; status polling endpoint? |
| 9 | **user-service** (8001, Java/Spring) | 🟡 necunoscut | Java + Maven, scheletul există | **P0**: backlog-ul descrie NestJS + Prisma, dar implementarea actuală e **Java Spring** — drift între design și cod |
| 10 | **notification-service** (8004) | 🟡 **30%** | NestJS skeleton, package.json + main.ts adăugate recent | **P0**: SSE endpoint pe `/sse/:userId`, consumer Kafka pe toate event-urile, Email service (Nodemailer + templates) |
| 11 | **api-gateway** (8000) | 🟢 **65%** | NestJS + Fastify, JWT guard, proxy routes, WebSocket proxy stubs | **P1**: rute proxy pentru toate AI agents (HR/Tech WS), rate limiting confirmat în prod |

---

## 3. Inventar frontend (Next.js)

| Pagină | Status | Note |
|---|---|---|
| `/login`, `/register` | 🟢 există | Auth pages |
| `/dashboard` | 🟢 există | De verificat dacă folosește date reale sau mock |
| `/upload` (CV upload) | 🟢 există | În backlog era `/cv-upload` — există drift de rute |
| `/jobs` | 🟢 există | De verificat că consumă `/api/jobs/{userId}` real |
| `/learning/path` | 🟢 există | |
| `/learning/quiz/[id]` | 🟢 există | Dar backend-ul răspunde 501 — pagina nu poate funcționa |
| **`/interview/hr`** | 🔴 **LIPSEȘTE** | Backlog CP-034 — neimplementat |
| **`/interview/technical`** | 🔴 **LIPSEȘTE** | Backlog CP-035 — neimplementat |
| **`/chat`** (orchestrator) | 🟡 inclus probabil în dashboard via `chat-panel.tsx` | De confirmat poziționarea |

**Lipsuri P0 la frontend:** ambele pagini de interviu (HR + Tech cu Monaco Editor).

---

## 4. Infrastructură & quality concerns

| Aspect | Status | Notă |
|---|---|---|
| Docker Compose + profile (agents/backend/frontend) | 🟢 OK | |
| PostgreSQL init schema | 🟢 OK | `01_schema.sql` + `02_agents_schema.sql` |
| Redpanda 9 topice + DLQ | 🟢 OK | DLQ pentru orchestrator există |
| Qdrant 3 colecții (dim=3072) | 🟢 OK | |
| MinIO `cvs-raw` bucket | 🟢 OK | |
| JWT RS256 keys | 🟢 OK | `make keys` setup |
| **OpenTelemetry → Grafana** | 🔴 stack există în compose, **dashboards nu** | CP-045 — fără dashboards `services.json`, `kafka.json`, `ai-agents.json` |
| **Health checks consistente** | 🟡 parțial | Toate au `/health`, dar fără `service_healthy` peste tot în compose |
| **Teste E2E** | 🔴 lipsesc | CP-038, CP-039, CP-043 — fără `tests/e2e/flow1_test.sh` etc |
| **CI/CD** | 🔴 lipsește | Fără GitHub Actions / pipeline |
| **Production overlay** | 🟡 fișier există | `docker-compose.prod.yml` — neclar dacă a fost validat |
| **Secret management** | 🔴 risc | API key-uri în `.env` plain; pentru prod ar trebui Vault sau secrets manager |
| **k8s manifests** | 🟡 folder există | `k8s/` — fără claritate că manifesturile sunt complete |

---

## 5. Probleme cross-cutting (de fixat oriunde)

1. **Drift între backlog și implementare reală.** Backlog-ul descrie NestJS+Prisma pentru user-service, codul real e Java Spring. Backlog-ul vorbește de `text-embedding-3-small` (OpenAI, 1536 dim), codul folosește `gemini-embedding-001` (3072 dim). Reranker prompt-ul cere Claude, codul folosește Gemini. **Recomandare:** un audit + update al backlog-ului ca să reflecte realitatea.

2. **Modelele LLM amestecate.** Avem Gemini Flash 2.0 (hr-interview), Gemini 2.5 Flash (orchestrator, cv-analyzer). Inconsistent. **Recomandare:** standardize pe Gemini 2.5 Flash peste tot (sau pe Claude unde calitatea contează — interviu tehnic, reranker).

3. **Fără autentificare end-to-end pe WebSocket-uri.** HR/Tech interview agents acceptă orice conexiune WS fără verificare JWT. **Risc:** oricine poate consuma quota Gemini cu request-uri anonime.

4. **Fără rate limiting per-user.** Un user poate spama upload-uri CV → cv-analyzer va arde quota Gemini.

5. **Fără logica de "session complete" în interviu.** HR și Tech rulează la infinit până la disconnect, fără limită de turns sau timer. Backlog cere 15 turns + post-interview analysis. Implementarea face analysis doar pe disconnect = user pleacă, analysis se face. Dar dacă userul rămâne și pune 200 de întrebări consumi $$.

6. **Lipsește persistența istoricului conversațional dincolo de Redis TTL.** Chat și interviuri se șterg după 1-7 zile. Dacă user vrea să revadă, nu poate.

---

## 6. Market Research — Platforme similare

### A. Lideri actuali (2026)

| Platformă | Focus principal | Diferențiator |
|---|---|---|
| **AiApply** | Auto-apply la 1000+ job-uri/zi, AI Interview Buddy (real-time copilot în video interview), Resume Builder, Job Tracker | "All-in-one" — volum aplicări automate |
| **Careerflow** | Resume builder + LinkedIn optimizer + Interview prep + Cover letter generator + Application autofill | Coach uman opțional + full job tracking |
| **Jobscan** | ATS keyword matching (target ≥75% match rate), gap analysis, format fixes | Bench de aliniere CV ↔ job description, "ATS pass-or-fail" |
| **Final Round AI** | **Interview Copilot real-time** (transcript live, sugestii de răspuns în timp real), AI Mock Interview | Real-time assistance during live interviews |
| **Coursera Coach** | AI tutor + career guidance + skills pathway, integrat pe biblioteca Coursera | Conținut educațional masiv + AI conversational |
| **LinkedIn Learning AI Coaching** | Skills pathways personalizate, feedback real-time pe lecții | Network LinkedIn + content vast |
| **Pramp** (gratuit) | Mock interview peer-to-peer (2 engineeri se interviewează reciproc) | Free, unlimited, real human practice |
| **Interviewing.io** ($225+/sesiune) | Mock interview cu inginer senior din FAANG | Calitate premium, feedback expert |

### B. Feature-uri must-have în 2026 (din research)

1. **Skills-based screening** (nu doar keyword match) — peste 60% din enterprise hiring teams US filtrează pe skill-uri, nu pe job title.
2. **ATS score concret** (Jobscan target = 75%) — userul vrea un număr clar.
3. **Auto-apply** la job-uri pe baza profilului (Sonara, AiApply scan + submit zilnic).
4. **Real-time interview copilot** — sugestii în timpul interviului live (controversial dar e standard la Final Round AI).
5. **Behavioral question framework STAR** — generare structurată de răspunsuri cu metoda STAR (Situation, Task, Action, Result).
6. **Cross-reference cu LinkedIn** — verificare consistență CV ↔ profil LinkedIn.
7. **Salary negotiation tools** — feature-ul lipsă din mai toate platformele open-source.
8. **Cover letter cu evidence-based personalization** — nu doar template, ci cu context de company research.

### C. Unde CareerPath AI poate diferenția

| Feature | Cine îl are bine | Cum am putea face mai bine |
|---|---|---|
| **CV scoring multi-criterion** | Jobscan (keyword-based) | Avem deja rubric structurat (experience 30 + stack 25 + projects 20 + edu 15 + certs 10) — mai obiectiv decât keyword match |
| **Conversational triage înainte de CV** | Nimeni nu face asta natively | **Shadow profiling-ul nostru** prin chat e unic — user îți construiește profilul natural, fără să completeze 30 de câmpuri |
| **Routing automat score → flow** | Nicio platformă | Logica score≥70 → jobs, <70 → learning path e o decizie de produs interesantă |
| **Learning path cu quiz + tracking modular** | Coursera/LinkedIn (general) | Niche pentru target role specific (Frontend, QA, Data) cu integrare Udemy + YouTube |
| **Interviu HR + Tech cu code execution** | Final Round AI (HR), Pramp (free P2P) | Combinație + Judge0 sandbox + Monaco editor (când va fi gata) |
| **Localizare RO + jobs eJobs.ro** | Nimeni | **Niche puternic pe piața RO** — Jobscan/Final Round sunt EN-only |
| **Open source / self-hostable** | Nimeni | Avantaj pentru companii care vor on-prem privacy |

### D. Feature-uri PE CARE NU LE AVEM și sunt așteptate de utilizatori

| Feature | Prioritate | Justificare |
|---|---|---|
| **ATS keyword match score** | P1 | Jobscan = produs de $50/lună fix pe asta. Userul vrea număr concret. |
| **Cover letter generator personalizat per job** | P1 | Backlog îl menționează (CP-028) dar nu e implementat |
| **LinkedIn profile import / sync** | P2 | Reduce friction la onboarding |
| **Salary expectations + market data** | P2 | "Ce salariu să cer la $target_role în $location" |
| **Application tracker (Kanban)** | P2 | Teal-ul face mult pe asta |
| **STAR framework pentru răspunsuri behavioral** | P2 | Foarte util în HR interview |
| **Recording video interview + feedback corp lang** | P3 | Niche dar diferențiator |
| **Salary negotiation simulator** | P3 | Aproape nimeni nu îl are |
| **Community / peer matching pentru mock interviews** | P3 | Pramp-style, free |
| **Real-time interview copilot (controversial)** | P3 | Final Round AI vinde fix asta, dar e gri etic |

---

## 7. Roadmap recomandat (priorizat)

### Sprint 1 — "Make Flow 1 actually work end-to-end" (1-2 săptămâni)

**Obiectiv:** un user să poată face upload CV → să vadă job matches reale.

1. **P0** Implementează `job-scraper-service` complet (CP-026): măcar eJobs.ro (BeautifulSoup, simplu) + 1 alt sursă. LinkedIn poate fi V2.
2. **P0** Validează `job-match-agent` end-to-end: embed jobs scrapate → similarity search → top-10 → publish `jobs.matched`.
3. **P0** Adaugă cover letter generation în job-match-agent (Gemini cu CV + job description).
4. **P0** Wire-uiește `notification-service` SSE: user vede notificare live "10 job matches gata".
5. **P1** `cv-analyzer-agent` să update-eze și tabelul `cv_uploads` cu rezultatul (acum doar publică event).

### Sprint 2 — "Make Flow 2 work" (1 săptămână)

6. **P0** Implementează `GET /learning/quiz/{module_id}` și `POST .../submit` în learning-path-agent (CP-050).
7. **P0** Verifică integrarea Udemy + YouTube API în generator (pot fi mock dacă API-urile sunt scumpe).
8. **P1** Quiz UI funcțional pe frontend (deja există pagina, leag-o la backend).

### Sprint 3 — "Make interview actually safe" (1-2 săptămâni)

9. **P0** Implementează paginile `/interview/hr` și `/interview/technical` în frontend (CP-034, CP-035).
10. **P0** Adaugă JWT auth pe WebSocket-uri (HR + Tech).
11. **P0** Adaugă limită de turns (15) în HR + post-interview analysis automat la limit.
12. **P0** Integrează **Judge0** în tech-interview-agent (problem selector + code execution + evaluation).
13. **P1** Load user profile din PostgreSQL în system prompt (interviul e generic acum, fără context CV).
14. **P1** Publish `interview.hr.completed` / `interview.tech.completed` events.

### Sprint 4 — "Production readiness" (1 săptămână)

15. **P0** Teste E2E Flow 1 + Flow 2 + Flow 3 (CP-038, CP-039, CP-043).
16. **P0** Grafana dashboards (CP-045): services latency, Kafka lag, AI cost/throughput.
17. **P0** Error handling + DLQ peste tot (CP-044).
18. **P1** Rate limiting per-user pe API Gateway (max X CV uploads / zi).
19. **P1** Secret management — scoate API key-urile din `.env` plain pentru prod.

### Sprint 5+ — Diferențiatori vs piață (când Sprint 1-4 e gata)

20. **ATS keyword match score** — al doilea scoring în paralel cu cel actual (target = match% vs job description specific).
21. **Cover letter cu company research** — Gemini scrape news + about page, personalizează.
22. **LinkedIn import** la onboarding (parser pentru export-ul de profil PDF/CSV).
23. **Application tracker (Kanban)** — Trello-like, salvează aplicațiile din `jobs.matched`.
24. **Salary insights** — date din Glassdoor/payscale (scraping atent) per target_role + location.
25. **Localizare RO completă** — UI, prompt-uri Gemini, scraping eJobs/Hipo/MyJob/BestJobs.

---

## 8. Concluzii cheie

1. **Proiectul are oase bune** — arhitectură event-driven solidă, separation of concerns OK, infrastructură production-grade gândită (Qdrant, Redpanda, observability stack).
2. **Lipsește carne pe oase pe ~50% din servicii** — job-scraper și tech-interview sunt aproape inexistente; learning quiz e 501.
3. **Cel mai bun MVP demonstrabil acum** = doar Flow 0 (chat) + Flow 1 până la score (fără jobs reale).
4. **Diferențiator unic pe piață** = shadow profiling prin conversație + routing automat learning/jobs. Nimeni din competitori nu face asta nativ.
5. **Quick win pentru piața RO** = localizare + scraping eJobs.ro. Jobscan/Final Round nu deservesc piața românească.
6. **Risc major:** scope creep. Backlog-ul are 51 task-uri, multe pieces; rezistă tentația de a începe Sprint 5 (diferențiatori) înainte ca Sprint 1-4 (basics) să fie complete.

---

## Surse market research

- [Top 7 AI Job Search Platforms 2026 — Analytics Insight](https://www.analyticsinsight.net/artificial-intelligence/top-7-ai-job-search-platforms-navigating-the-2026-algorithmic-career-landscape)
- [Best AI Job Search Tools 2026 — Jobscan](https://www.jobscan.co/blog/ai-job-search-tools/)
- [Final Round AI Review 2026 — Interview Sidekick](https://interviewsidekick.com/blog/final-round-ai-review)
- [Best AI Mock Interview Platforms 2026 — Revarta](https://www.revarta.com/blog/best-ai-mock-interview-platforms-2026)
- [Pramp vs Interviewing.io — Lodely](https://www.lodely.com/blog/pramp-vs-interviewing-io)
- [Coursera Coach](https://www.coursera.org/explore/coach)
- [LinkedIn Learning AI Coaching](https://learning.linkedin.com/resources/learner-engagement/linkedin-learning-ai-powered-coaching)
- [ATS Resume Optimization Guide 2026 — ResumeVera](https://resumevera.com/blogs/ats-resume-optimization-guide-2026)
- [Careerflow](https://www.careerflow.ai/)
- [AiApply](https://aiapply.co/)
