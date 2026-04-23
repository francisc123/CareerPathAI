# CV Analyzer Agent

Primul agent AI din platforma CareerPath. Primeste un CV brut, il analizeaza cu Gemini,
genereaza un scor si identifica lipsurile, apoi publica rezultatul pentru ceilalti agenti.

---

## Cum functioneaza (citeste asta primul)

```
[Redpanda] → consumer.py aude "cv.uploaded"
                    │
                    ▼
            ia CV-ul text din eveniment
                    │
                    ▼
            cv_scoring_tool.py → trimite la Gemini
            Gemini returneaza JSON: {score, skills, gaps}
                    │
                    ▼
            embedding_tool.py → transforma CV-ul in vector
            salveaza vectorul in Qdrant
                    │
                    ▼
            salveaza scorul in PostgreSQL
                    │
                    ▼
[Redpanda] ← publisher.py publica "cv.analyzed"
```

Agentul nu are interfata grafica. Nu il deschizi in browser.
El traieste in fundal si reactioneaza la evenimente.

---

## Structura folderelor — ce pui unde

```
cv-analyzer-agent/
│
├── README.md                        ← esti aici
├── Dockerfile                       ← exista deja, nu modifica
├── requirements.txt                 ← dependintele Python
│
├── prompts/                         ← CREEZI acest folder
│   ├── cv_scoring.txt               ← promptul pentru scoring (CP-007)
│   └── gap_analysis.txt             ← promptul pentru gap analysis (CP-007)
│
└── src/
    ├── main.py                      ← CREEZI — punctul de intrare al agentului
    │
    ├── consumers/
    │   └── cv_upload_consumer.py    ← CREEZI — asculta "cv.uploaded" pe Redpanda
    │
    ├── publishers/
    │   └── cv_analyzed_publisher.py ← CREEZI — trimite "cv.analyzed" pe Redpanda
    │
    ├── agents/
    │   └── cv_analyzer.py           ← CREEZI — logica principala, leaga totul
    │
    ├── rag/
    │   ├── qdrant_client.py         ← CREEZI — conexiunea la Qdrant
    │   └── embedding_tool.py        ← CREEZI — genereaza vectori cu Gemini
    │
    └── routers/
        └── health.py                ← CREEZI — endpoint /health pentru Docker
```

**Regula simpla:** fiecare fisier face UN singur lucru.
`consumer.py` doar asculta. `cv_analyzer.py` doar analizeaza. `publisher.py` doar trimite.

---

## Tehnologii folosite si DE CE

| Tehnologie | Rol | De studiat |
|---|---|---|
| **FastAPI** | serverul web al agentului (expune /health) | `fastapi.tiangolo.com` |
| **Gemini API** | modelul AI care analizeaza CV-ul | `ai.google.dev/gemini-api/docs` |
| **Qdrant** | baza de date vectoriala — stocheaza "amprenta" CV-ului | `qdrant.tech/documentation` |
| **aiokafka** | citeste/scrie mesaje pe Redpanda | `aiokafka.readthedocs.io` |
| **asyncpg** | salveaza scorul in PostgreSQL | — |
| **Pydantic** | valideaza ca JSON-ul de la Gemini are forma corecta | `docs.pydantic.dev` |

**De ce Gemini si nu OpenAI pentru embeddings?**
Gemini are `text-embedding-004` gratuit. OpenAI `text-embedding-3-small` e platit.
Vectorii au dimensiunea 768 (Gemini) vs 1536 (OpenAI) — ajusteaza Qdrant in consecinta.

---

## Taskurile in ordine — ce faci la fiecare pas

---

### TASK 1 — CP-007: Scrie prompturile (fara cod, fara Docker)

**Ce inveti:** cum sa "programezi" un model AI prin text (prompt engineering)
**Resurse:** `ai.google.dev/gemini-api/docs/function-calling`

**Ce faci concret:**

Creezi folderul `prompts/` si doua fisiere text.

**`prompts/cv_scoring.txt`** — promptul de scoring:
```
Esti un expert recruiter cu 15 ani experienta.
Primesti textul brut al unui CV.

Analizeaza-l si returneaza un JSON cu structura EXACTA de mai jos.
Nu adauga text in afara JSON-ului.

Schema JSON:
{
  "score": <numar intreg 0-100>,
  "seniority": <"junior" | "mid" | "senior" | "lead">,
  "target_role": <string - rolul cel mai potrivit pentru acest CV>,
  "skills": [<lista de tehnologii identificate>],
  "strengths": [<lista de puncte forte, maxim 3>],
  "gaps": [<lista de lipsuri fata de rolul target, maxim 5>]
}

Rubric de scoring:
- Ani experienta relevanta: maxim 30 puncte
- Stack tehnologic relevant: maxim 25 puncte
- Calitatea proiectelor descrise: maxim 20 puncte
- Educatie: maxim 15 puncte
- Certificari: maxim 10 puncte
```

**`prompts/gap_analysis.txt`** — promptul de gap analysis:
```
Esti un expert in dezvoltare profesionala.
Primesti profilul unui candidat in format JSON.

Analizeaza lipsurile si returneaza un JSON cu structura EXACTA:
{
  "gaps": [<toate lipsurile identificate>],
  "priority_gaps": [<top 3 lipsuri critice de rezolvat primul>],
  "estimated_weeks_to_close": <numar intreg - saptamani necesare>
}

Nu adauga text in afara JSON-ului.
```

**Testare:** Scrie un script separat `prompt_testing/cv_scoring.py` care:
1. Ia un CV text hardcodat
2. Il trimite la Gemini cu promptul de mai sus
3. Printeaza JSON-ul primit
4. Verifica ca JSON-ul e valid

Testeaza cu 5 CV-uri diferite pana JSON-ul e consistent 100%.

---

### TASK 2 — CP-008: Configureaza Qdrant (fara Docker nou — il ai deja)

**Ce inveti:** ce sunt vectorii si cum functioneaza o baza de date vectoriala
**Resurse:** `qdrant.tech/documentation/quick-start`

**Qdrant ruleaza deja** la `localhost:6333` din `docker-compose --profile agents up`.
Nu trebuie sa instalezi nimic. Trebuie doar sa creezi colectiile.

**Ce faci concret:**

Creezi `rag_testing/qdrant_setup.py` (fisier separat, pentru testare):

```python
# Ce face acest script:
# 1. Se conecteaza la Qdrant local
# 2. Creaza 3 colectii (ca niste "tabele" pentru vectori)
# 3. Verifica ca s-au creat

# Colectia cv_embeddings:
# - dimensiune vector: 768 (dimensiunea Gemini text-embedding-004)
# - metrica: Cosine (masoara similaritatea intre vectori)
# - payload (date extra): user_id, skills, seniority, target_role, score

# Colectia job_embeddings:
# - dimensiune: 768
# - payload: title, company, url, source, location

# Colectia course_embeddings:
# - dimensiune: 768
# - payload: title, provider, url, topic
```

Dupa ce creezi colectiile, scrie `rag_testing/embedding_pipeline.py`:
1. Ia 3 CV-uri text hardcodate
2. Genereaza embeddings cu Gemini `text-embedding-004`
3. Le urca in Qdrant `cv_embeddings`
4. Cauta: "gaseste CV-urile similare cu un Python developer"
5. Printeaza rezultatele si verifica ca au sens

**Ce sa inveti inainte de a scrie codul:**
- Ce este un vector (embedding): `platform.openai.com/docs/guides/embeddings` (conceptul e acelasi pentru Gemini)
- Cosine similarity: cauta "cosine similarity explained simply" pe YouTube

---

### TASK 3 — CP-009: Scheletul agentului

**Ce inveti:** cum se structureaza o aplicatie FastAPI, cum asculti Redpanda cu aiokafka
**Resurse:** `fastapi.tiangolo.com/tutorial`, `aiokafka.readthedocs.io`

**Ce faci concret:**

**`src/main.py`** — punctul de intrare:
```python
# Ce face acest fisier:
# 1. Creeaza aplicatia FastAPI
# 2. La startup: porneste consumer-ul Redpanda in background
# 3. La shutdown: opreste consumer-ul curat
# Include router-ul de health check
```

**`src/routers/health.py`** — endpoint pentru Docker:
```python
# Un singur endpoint: GET /health
# Returneaza: {"status": "ok"}
# Docker il apeleaza la fiecare 30 secunde ca sa stie ca agentul traieste
```

**`src/consumers/cv_upload_consumer.py`** — asculta Redpanda:
```python
# Ce face:
# 1. Se conecteaza la Redpanda (adresa din variabila de mediu)
# 2. Se aboneaza la topicul "cv.uploaded"
# 3. Intr-un loop infinit: asteapta mesaje
# 4. Cand primeste un mesaj: il deserializeaza din JSON
# 5. Apeleaza cv_analyzer.py cu datele primite
# 6. Logheaza ce s-a intamplat

# Structura mesajului primit:
# {
#   "user_id": "uuid",
#   "cv_text": "textul brut al CV-ului",
#   "cv_id": "uuid"
# }
```

**`src/publishers/cv_analyzed_publisher.py`** — trimite pe Redpanda:
```python
# Ce face:
# 1. Primeste rezultatul analizei
# 2. Il serialzeaza in JSON
# 3. Il publica pe topicul "cv.analyzed"

# Structura mesajului trimis:
# {
#   "user_id": "uuid",
#   "cv_id": "uuid",
#   "score": 74,
#   "seniority": "mid",
#   "skills": ["Python", "FastAPI"],
#   "gaps": ["Docker", "Kubernetes"],
#   "target_role": "Backend Developer"
# }
```

**Verificare:** `docker-compose --profile agents up` → agentul porneste → in loguri apare "Consumer connected to Redpanda". Inca nu face nimic, dar traieste.

---

### TASK 4 — CP-020: Implementarea completa

**Ce inveti:** cum legi toate componentele intr-un flow real
**Resurse:** `ai.google.dev/gemini-api/docs/function-calling`

**`src/agents/cv_analyzer.py`** — creierul agentului:
```python
# Ce face (in ordine):
# 1. Primeste cv_text si user_id
# 2. Citeste promptul din prompts/cv_scoring.txt
# 3. Trimite la Gemini → primeste JSON cu scorul
# 4. Valideaza JSON-ul cu Pydantic (daca nu e valid → retry de 3 ori)
# 5. Genereaza embedding pentru cv_text cu Gemini text-embedding-004
# 6. Salveaza vectorul in Qdrant (cu payload: user_id, score, skills)
# 7. Salveaza scorul in PostgreSQL (tabela cv_uploads)
# 8. Returneaza rezultatul pentru publisher
```

**`src/rag/embedding_tool.py`**:
```python
# O singura functie: generate_embedding(text) → vector (lista de 768 numere)
# Foloseste Gemini text-embedding-004
```

**`src/rag/qdrant_client.py`**:
```python
# Doua functii:
# save_cv_embedding(user_id, vector, payload) → salveaza in Qdrant
# search_similar_jobs(cv_vector, filters) → returneaza top-5 joburi similare
```

---

### TASK 5 — CP-021: Testarea cautarii

**Ce inveti:** cum validezi ca un sistem RAG functioneaza corect

**Ce faci concret:**
Scrii `rag_testing/search_validation.py`:
1. Inserezi 50 joburi mock in Qdrant `job_embeddings`
2. Dai 5 CV-uri diferite
3. Pentru fiecare CV, cauti top-5 joburi similare
4. Verifici manual: are sens rezultatul?
   - CV de Python developer → joburile returnate sunt de Python? ✓
   - CV de junior → nu returneaza joburi de senior? ✓

---

## Cum e legat la Docker (nu trebuie sa faci nimic)

Dockerfile-ul exista deja. Agentul e deja definit in `docker-compose.yml`.
Cand dai `docker-compose --profile agents up`, Docker:
1. Construieste imaginea din Dockerfile
2. Instaleaza tot din `requirements.txt`
3. Porneste `uvicorn src.main:app`
4. Conecteaza automat la Redpanda, PostgreSQL, Qdrant din reteaua interna Docker

Variabilele de mediu (adresele serviciilor, API keys) vin din `.env`.
In cod folosesti `os.getenv("GEMINI_API_KEY")` — nu hardcodezi niciodata chei.

---

## Ordinea de lucru recomandata

```
[ ] CP-007 — scrie si testeaza prompturile (2-3 zile)
      Nu ai nevoie de Docker. Doar Python + Gemini API.

[ ] CP-008 — configureaza Qdrant si testeaza embeddings (1-2 zile)
      Ai nevoie de: docker-compose --profile agents up

[ ] CP-009 — scheletul FastAPI + consumer Redpanda (1-2 zile)
      Ai nevoie de: docker-compose --profile agents up

[ ] CP-020 — implementarea completa (3-4 zile)
      Ai nevoie de: docker-compose --profile agents up

[ ] CP-021 — validarea cautarii in Qdrant (1 zi)
      Ai nevoie de: docker-compose --profile agents up
```

---

## Unde scrii codul — rezumat rapid

| Ce faci | Unde scriei |
|---|---|
| Promptul pentru Claude/Gemini | `prompts/cv_scoring.txt` |
| Testezi promptul izolat | `prompt_testing/cv_scoring.py` |
| Configurezi Qdrant | `rag_testing/qdrant_setup.py` |
| Testezi embeddings | `rag_testing/embedding_pipeline.py` |
| Logica principala AI | `src/agents/cv_analyzer.py` |
| Ascultare Redpanda | `src/consumers/cv_upload_consumer.py` |
| Trimitere Redpanda | `src/publishers/cv_analyzed_publisher.py` |
| Generare vectori | `src/rag/embedding_tool.py` |
| Salvare/cautare Qdrant | `src/rag/qdrant_client.py` |
| Pornire aplicatie | `src/main.py` |
| Health check Docker | `src/routers/health.py` |

---

## Primul pas — fa asta acum

Deschide `prompt_testing/cv_scoring.py` si scrie un script care:
1. Hardcodeaza un CV text de 10 randuri
2. Il trimite la Gemini cu promptul din `prompts/cv_scoring.txt`
3. Printeaza JSON-ul primit

Daca JSON-ul e valid si are sens → CP-007 e pe drumul cel bun.
