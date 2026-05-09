# Job Match Agent

**ID Task Jira:** CP-028

Acest agent este responsabil pentru a analiza joburile găsite de `Job Scraper Service` și a le potrivi cu profilul și CV-ul unui utilizator. Scopul său este să ofere o listă scurtă și relevantă de oportunități de carieră.

## Arhitectură și Tehnologii

Agentul folosește o abordare hibridă, combinând căutarea vectorială pentru eficiență cu re-ranking-ul LLM pentru acuratețe.

- **FastAPI**: Expune un server web pentru endpoint-uri REST, permițând frontend-ului să preia joburile potrivite pentru un utilizator.
- **aiokafka**: Conține un consumator care ascultă topicul `jobs.scraped`. Acest eveniment, care conține o listă de joburi, declanșează procesul de potrivire.
- **OpenAI Embeddings (`text-embedding-3-small`)**: Vom folosi acest model de la OpenAI pentru a transforma atât textul CV-ului utilizatorului, cât și descrierile joburilor în vectori numerici (embeddings).
- **Qdrant**: Baza de date vectorială unde sunt stocate embedding-urile joburilor. Agentul va interoga Qdrant pentru a găsi cele mai similare `k` joburi pentru embedding-ul CV-ului utilizatorului.
- **LLM Re-ranker (Claude 3 Haiku / Gemini 1.5 Flash)**: După obținerea unei liste brute de la Qdrant, vom folosi un model LLM rapid și eficient pentru a re-ordona această listă. LLM-ul va primi CV-ul și descrierile joburilor și va oferi un clasament final bazat pe o înțelegere mai profundă a contextului.
- **asyncpg**: Pentru a salva rezultatele finale (lista de joburi potrivite, scorul de relevanță, etc.) în baza de date PostgreSQL.

## Cum Va Fi Implementat

1.  **`config.py`**: Va stoca toate setările: cheia API OpenAI, URL-ul Qdrant, URL-ul bazei de date, etc.
2.  **`qdrant_client.py`**: Va abstractiza comunicarea cu Qdrant. Va conține funcții pentru a prelua embedding-ul CV-ului unui utilizator și pentru a efectua căutarea de similaritate pentru a găsi joburi candidate.
3.  **`prompts.py`**: Va conține promptul specific pentru re-ranking, instruind LLM-ul să compare un CV cu o listă de joburi și să le ordoneze.
4.  **`matcher.py`**: "Inima" agentului. Va conține logica principală:
    -   Funcția `get_cv_embedding` va prelua embedding-ul CV-ului din Qdrant.
    -   Funcția `find_candidate_jobs` va interoga Qdrant pentru a obține o listă inițială de joburi.
    -   Funcția `rerank_jobs_with_llm` va trimite lista de candidați către LLM pentru a obține clasamentul final.
5.  **`database.py`**: Va gestiona salvarea rezultatelor în tabela `job_matches` din PostgreSQL.
6.  **`consumer.py`**: Consumatorul Kafka care ascultă `jobs.scraped`. La primirea unui mesaj, va orchestra întregul flux de potrivire apelând funcțiile din `matcher.py` și `database.py`.
7.  **`main.py`**: Serverul FastAPI care pornește consumatorul și expune endpoint-ul `GET /jobs/{user_id}`.

## Fluxul de Execuție

1.  `Job Scraper Service` termină de colectat joburi și publică un eveniment pe `jobs.scraped`.
2.  Consumatorul din `Job Match Agent` preia mesajul.
3.  Agentul preia embedding-ul CV-ului utilizatorului din colecția `cv_embeddings` din Qdrant.
4.  Folosind acest embedding, interoghează colecția `job_embeddings` pentru a găsi cele mai similare 20-30 de joburi.
5.  Aceste joburi candidate, împreună cu textul CV-ului, sunt trimise către LLM-ul de re-ranking.
6.  LLM-ul returnează o listă ordonată a celor mai bune 5-10 joburi, împreună cu un scor și un motiv pentru fiecare.
7.  Această listă finală este salvată în baza de date PostgreSQL.
8.  Un eveniment `jobs.matched` este publicat pe Kafka.

