# CV Analyzer Agent

**Rolul sau in arhitectura:** Este un Worker invizibil pentru utilizator.
Nu vorbeste cu nimeni. Primeste o sarcina, o executa, raporteaza rezultatul.

---

## Arhitectura in doua straturi — citeste asta PRIMUL

Cel mai important lucru de inteles inainte de orice linie de cod:

```
STRATUL 1 — Conversational Agent (agent-orchestrator)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Vorbeste cu utilizatorul.
  Construieste profilul din conversatie naturala (Shadow Profiling).
  Decide CAND sa apeleze uneltele din fundal prin Dynamic Tool Calling.

  Exemplu de conversatie:
  Agent: "Buna! Spune-mi, cu ce te ocupi in prezent?"
  User:  "Sunt developer Python, lucrez de 2 ani."
  Agent: [in fundal: extrage {seniority: "junior", skills: ["Python"]}]
  Agent: "Super! Ai un CV pe care sa mi-l trimiti?"
  User:  [uploadeaza CV]
  Agent: [APELEAZA UNEALTA: analizeaza_cv] ← declanseaza Stratul 2
  Agent: "Am analizat CV-ul. Vad ca stii Python solid, dar..."

STRATUL 2 — CV Analyzer Agent (acest serviciu)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NU vorbeste cu utilizatorul. Niciodata.
  Primeste eveniment pe Redpanda → executa → returneaza rezultat.
  Este o unealta invizibila, ca un motor in masina.
```

**De ce aceasta separare?**
Conversatia si procesarea sunt doua probleme complet diferite.
Daca le pui in acelasi loc, codul devine imposibil de intretinut.
Daca le separi, poti schimba modelul AI din Stratul 2 fara sa atingi conversatia.

---

## Cum comunica cele doua straturi

```
[Utilizator] ←→ [agent-orchestrator] ←→ [Redpanda] ←→ [cv-analyzer-agent]
                      │                                         │
                      │ publica "cv.uploaded"                   │
                      │ ─────────────────────────────────────► │
                      │                                         │ analizeaza
                      │                                         │ cu Gemini
                      │ primeste "cv.analyzed"                  │
                      │ ◄───────────────────────────────────── │
                      │
                      │ continua conversatia cu utilizatorul
                      │ "Scorul tau e 74, hai sa vedem..."
```

Redpanda e "cutia postala" dintre cei doi agenti.
Niciodata nu se apeleaza direct unul pe celalalt.

---

## Shadow Profiling — profilare invizibila

In timp ce conversatia curge natural, orchestratorul construieste un profil
JSON in fundal fara ca utilizatorul sa simta ca este evaluat:

```json
{
  "nume": null,
  "seniority": null,
  "skills": [],
  "personalitate": null,
  "facultate": null,
  "cv_score": null,
  "gaps": []
}
```

Dupa fiecare mesaj al utilizatorului, modelul AI extrage entitati si
completeaza campurile. Cand profilul e complet, orchestratorul stie
ca poate trimite utilizatorul catre agentii RAG.

**Concept de studiat:** `"entity extraction with LLMs"` si `"function calling"`

---

## Dynamic Tool Calling — cum decide orchestratorul cand sa actioneze

Orchestratorul primeste acces la "unelte" predefinite:

```
analizeaza_cv(cv_text)         → declanseaza cv-analyzer-agent
creeaza_profil_manual(date)    → construieste profilul fara CV
trimite_la_tutor_rag(profil)   → porneste learning path
```

LLM-ul din spate decide **singur** cand e momentul potrivit sa activeze
o unealta, pe baza conversatiei. Nu exista `if/else` hardcodat.

**Concept de studiat:** `ai.google.dev/gemini-api/docs/function-calling`

---

## Validarea conversationala a CV-ului

Dupa ce cv-analyzer-agent returneaza scorul, orchestratorul nu il
spune direct. Il VALIDEAZA mai intai prin conversatie:

```
CV zice: "Senior React Developer"
Scor Gemini: 62/100

Orchestrator: "Super, am vazut ca ai multa experienta pe React.
               Apropo, cum gestionezi re-randarile costisitoare
               in proiectele mari?"

User raspunde vag    → scorul real e probabil 55, nu 62
User raspunde detaliat → scorul e confirmat
```

Asta face profilul mult mai precis decat orice analiza automata.

---

## Cum functioneaza CV Analyzer Agent (worker-ul)

```
[Redpanda] → consumer.py aude "cv.uploaded"
                    │
                    ▼
            ia CV-ul text din eveniment
                    │
                    ▼
            cv_analyzer.py → trimite la Gemini cu promptul din prompts/
            Gemini returneaza JSON: {score, skills, gaps}
                    │
                    ▼
            embedding_tool.py → transforma CV-ul in vector (3072 dim)
            salveaza vectorul in Qdrant
                    │
                    ▼
            salveaza scorul in PostgreSQL
                    │
                    ▼
[Redpanda] ← publisher.py publica "cv.analyzed"
```

---

## Structura folderelor — ce pui unde

```
cv-analyzer-agent/
│
├── README.md                        ← esti aici
├── Dockerfile                       ← exista, nu modifica
├── requirements.txt                 ← dependintele Python
│
├── prompts/                         ← exista deja
│   ├── cv_scoring.txt               ← promptul pentru scoring (CP-007) ✓
│   └── gap_analysis.txt             ← promptul pentru gap analysis (CP-007) ✓
│
└── src/
    ├── main.py                      ← CREEZI — punctul de intrare
    │
    ├── consumers/
    │   └── cv_upload_consumer.py    ← CREEZI — asculta "cv.uploaded"
    │
    ├── publishers/
    │   └── cv_analyzed_publisher.py ← CREEZI — trimite "cv.analyzed"
    │
    ├── agents/
    │   └── cv_analyzer.py           ← CREEZI — logica principala
    │
    ├── rag/
    │   ├── qdrant_client.py         ← CREEZI — conexiunea la Qdrant
    │   └── embedding_tool.py        ← CREEZI — genereaza vectori cu Gemini
    │
    └── routers/
        └── health.py                ← CREEZI — endpoint /health pentru Docker
```

---

## Tehnologii folosite si DE CE

| Tehnologie | Rol | Resursa |
|---|---|---|
| **Gemini API** | analizeaza CV-ul, genereaza embeddings | `ai.google.dev/gemini-api/docs` |
| **Qdrant** | baza de date vectoriala — stocheaza "amprenta" CV-ului | `qdrant.tech/documentation` |
| **FastAPI** | serverul web al agentului (expune /health) | `fastapi.tiangolo.com` |
| **aiokafka** | citeste/scrie mesaje pe Redpanda | `aiokafka.readthedocs.io` |
| **asyncpg** | salveaza scorul in PostgreSQL | — |
| **Pydantic** | valideaza ca JSON-ul de la Gemini e corect | `docs.pydantic.dev` |

**De ce Gemini pentru embeddings?**
Gemini `gemini-embedding-001` e gratuit. Vectorii au dimensiunea **3072**.
Qdrant e configurat cu `dim=3072, metric=Cosine`.
Nota: modelul vechi `text-embedding-004` nu mai este disponibil.

---

## Taskurile in ordine — ce faci la fiecare pas

### TASK 1 — CP-007: Prompturile ✓ (DONE)

Fisierele `prompts/cv_scoring.txt` si `prompts/gap_analysis.txt` exista deja.

**Ce mai trebuie facut:**
Scrie `prompt_testing/cv_scoring.py` — un script care:
1. Ia un CV text hardcodat
2. Il trimite la Gemini cu promptul din `prompts/cv_scoring.txt`
3. Printeaza JSON-ul primit
4. Verifica ca JSON-ul e valid

Testeaza cu 5 CV-uri diferite (junior, mid, senior, career-changer, bootcamp).
JSON-ul trebuie sa fie consistent 100% din incercari.

---

### TASK 2 — CP-008: Configureaza Qdrant

**Qdrant ruleaza deja** la `localhost:6333` din `docker-compose --profile agents up`.

---

#### Ce este un "vector" si de ce il folosim

Gemini transforma orice text intr-un sir de 3072 numere (un vector).
Texte cu sens similar produc vectori apropiati matematic.

```
"Python Developer cu FastAPI"  →  [0.12, -0.87, 0.34, ...]  ← 3072 numere
"Backend Engineer Python"      →  [0.11, -0.85, 0.36, ...]  ← aproape de primul
"Bucatar sef"                  →  [0.91,  0.54, -0.77, ...] ← departe de primii
```

Qdrant stocheaza acesti vectori si raspunde la intrebarea:
**"Gaseste-mi CV-urile cel mai aproape de acest job."**

---

#### Pasul 1 — Porneste Qdrant

```bash
docker-compose --profile agents up
```

Qdrant este disponibil la `http://localhost:6333`.
Poti verifica in browser: `http://localhost:6333/dashboard`

---

#### Pasul 2 — Creaza fisierul `rag_testing/qdrant_setup.py`

**Ce trebuie sa faca scriptul:**

1. Se conecteaza la Qdrant pe `localhost:6333`
2. Creeaza 3 colectii (daca nu exista deja):

```
cv_embeddings
  → size=3072, distance=Cosine
  → payload per document: {user_id, skills, seniority, score}

job_embeddings
  → size=3072, distance=Cosine
  → payload per document: {title, company, url, source}

course_embeddings
  → size=3072, distance=Cosine
  → payload per document: {title, provider, url, topic}
```

3. Printeaza confirmarea ca fiecare colectie a fost creata

**Biblioteca de folosit:** `qdrant-client` (deja in requirements.txt)

**Import de start:**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
```

**Cum creezi o colectie:**
```python
client.create_collection(
    collection_name="cv_embeddings",
    vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
)
```

**Verificare ca ai terminat:** rulezi scriptul si in consola apare:
```
✓ Colectie creata: cv_embeddings
✓ Colectie creata: job_embeddings
✓ Colectie creata: course_embeddings
```

**Atentie:** daca rulezi scriptul de doua ori, va da eroare ca colectia exista deja.
Rezolvi asta cu `recreate_collection()` sau verifici mai intai cu `get_collection()`.

---

#### Pasul 3 — Creaza fisierul `rag_testing/embedding_pipeline.py`

**Ce trebuie sa faca scriptul, in ordine:**

**3.1 — Pregateste 3 CV-uri text hardcodate**
Unul junior, unul mid, unul senior. Texte simple, 5-6 randuri fiecare.

**3.2 — Genereaza embeddings cu Gemini**

Modelul de folosit: `gemini-embedding-001` (NU `gemini-2.5-flash`, acela e pentru chat)

```python
from google import genai

client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

result = client_gemini.models.embed_content(
    model="gemini-embedding-001",
    contents="textul CV-ului"
)

vector = result.embeddings[0].values  # lista de 3072 numere
```

Verifica ca `len(vector) == 3072` — daca nu e 3072, ceva e gresit.

**3.3 — Urca vectorii in Qdrant**

```python
from qdrant_client.models import PointStruct

qdrant.upsert(
    collection_name="cv_embeddings",
    points=[
        PointStruct(
            id=1,                          # un numar unic pentru fiecare CV
            vector=vector,                 # lista de 3072 numere de la Gemini
            payload={                      # metadate despre CV
                "user_id": "user_001",
                "seniority": "junior",
                "skills": ["Python", "HTML"],
                "score": 38
            }
        )
    ]
)
```

**3.4 — Testeaza cautarea**

Genereaza un vector pentru textul `"Python developer with FastAPI experience"`,
apoi cauta in Qdrant care CV e cel mai aproape:

```python
query_vector = # embed "Python developer with FastAPI experience"

results = qdrant.search(
    collection_name="cv_embeddings",
    query_vector=query_vector,
    limit=3   # top 3 rezultate
)

for r in results:
    print(r.score, r.payload)
```

**3.5 — Verifica ca rezultatele au sens**

Cautarea de "Python developer" trebuie sa returneze CV-ul mid/senior Python
inaintea celui junior cu HTML. Daca ordinea e logica, Qdrant functioneaza corect.

**Verificare ca ai terminat:**
```
✓ 3 CV-uri urcate in Qdrant
✓ Cautare "Python developer" → CV mid pe primul loc (score > 0.8)
✓ CV junior HTML pe ultimul loc
```

---

#### Greseli comune de evitat

| Greseala | Fix |
|---|---|
| Folosesti `gemini-2.5-flash` pentru embeddings | Foloseste `gemini-embedding-001` |
| `len(vector) != 3072` | Verifica modelul si cum extragi `.values` |
| Colectia exista deja → eroare | Foloseste `recreate_collection()` sau prinde exceptia |
| Qdrant nu raspunde | Verifica ca Docker ruleaza: `docker ps` |
| ID-uri duplicate la upsert | Foloseste ID-uri unice (1, 2, 3 sau UUID) |

---

### TASK 3 — CP-009: Scheletul agentului

**Ai nevoie de:** `docker-compose --profile agents up`

`src/main.py` — porneste FastAPI + consumer Redpanda in background
`src/routers/health.py` — `GET /health` returneaza `{"status": "ok"}`
`src/consumers/cv_upload_consumer.py` — asculta topic `cv.uploaded`, logheaza ce primeste

**Verificare:** agentul porneste si in loguri apare "Consumer connected to Redpanda"

---

### TASK 4 — CP-020: Implementarea completa

`src/agents/cv_analyzer.py`:
```
1. Primeste cv_text si user_id
2. Citeste promptul din prompts/cv_scoring.txt
3. Trimite la Gemini → primeste JSON cu scorul
4. Valideaza JSON cu Pydantic (retry de 3 ori daca esueaza)
5. Genereaza embedding cu Gemini gemini-embedding-001
6. Salveaza vectorul in Qdrant
7. Salveaza scorul in PostgreSQL (tabela cv_uploads)
8. Returneaza rezultatul pentru publisher
```

`src/rag/embedding_tool.py` — o functie: `generate_embedding(text) → list[float]`
`src/rag/qdrant_client.py` — doua functii: `save_cv_embedding()` si `search_similar_jobs()`

---

### TASK 5 — CP-021: Validarea cautarii

Scrie `rag_testing/search_validation.py`:
```
1. Insereaza 50 joburi mock in Qdrant job_embeddings
2. Dai 5 CV-uri diferite
3. Pentru fiecare CV, cauti top-5 joburi similare
4. Verifici manual: CV Python dev → joburi Python? ✓
                    CV junior → nu apare senior? ✓
```

---

## Cum e legat la Docker

Dockerfile-ul si intrarea in `docker-compose.yml` exista deja.
Cand dai `docker-compose --profile agents up`, Docker:
1. Construieste imaginea
2. Instaleaza tot din `requirements.txt`
3. Porneste `uvicorn src.main:app --reload`
4. Conecteaza automat la Redpanda, PostgreSQL, Qdrant din reteaua interna

Variabilele de mediu vin din `.env`. Folosesti `os.getenv("GEMINI_API_KEY")`.

---

## Ordinea de lucru

```
[✓] CP-007 — testeaza prompturile cu 5 CV-uri (DONE)
[ ] CP-008 — configureaza Qdrant si testeaza embeddings
[ ] CP-009 — scheletul FastAPI + consumer Redpanda
[ ] CP-020 — implementarea completa
[ ] CP-021 — validarea cautarii in Qdrant
```

## Unde scrii codul — rezumat rapid

| Ce faci | Unde |
|---|---|
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
