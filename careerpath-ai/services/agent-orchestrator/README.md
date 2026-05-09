# Agent Orchestrator

**ID Task Jira:** CP-022

Acest serviciu acționează ca un dirijor central pentru fluxurile de lucru ale agenților AI. Rolul său nu este să proceseze date, ci să primească rezultate de la alți agenți și să delege sarcini către următorii agenți corespunzători din flux.

## Arhitectură și Tehnologii

Agentul este construit ca un serviciu asincron Python, folosind următoarele tehnologii cheie:

- **FastAPI**: Pentru a expune un server web minimalist, necesar pentru endpoint-uri de monitorizare (ex: `/health`) și pentru a interoga starea unui flux de lucru (`/workflow/{user_id}/status`).
- **aiokafka**: Pentru comunicarea asincronă cu clusterul Redpanda (Kafka). Serviciul conține un consumator care ascultă topicul `cv.analyzed` și un producător pentru a trimite evenimente pe topicul `gaps.identified`.
- **LangGraph**: "Creierul" orchestratorului. Am folosit LangGraph pentru a modela logica de business ca un graf de stări (StateGraph). Această abordare face fluxul de decizie extrem de clar, mentenabil și ușor de extins.
- **Redis**: Folosit pentru a persista starea finală a fiecărui flux de lucru. Acest lucru permite depanarea și monitorizarea, putând verifica exact ce decizie a luat orchestratorul pentru un anumit utilizator.

## Cum a Fost Implementat

Implementarea este împărțită în module logice în folderul `src/`:

1.  **`main.py`**: Punctul de intrare al aplicației FastAPI. La pornire (`lifespan` event), lansează consumatorul Kafka într-un task de background. Expune endpoint-ul de status care citește datele din clientul Redis.
2.  **`consumer.py`**: Definește logica consumatorului Kafka. Acesta ascultă non-stop topicul `cv.analyzed`. Când un mesaj este primit, validează datele folosind un model Pydantic (`CvAnalyzedEvent`), inițializează starea și invocă graful LangGraph.
3.  **`workflow.py`**: Aici este definit graful de stări.
    - **Starea (`WorkflowState`)**: Un `TypedDict` care conține toate informațiile necesare pe parcursul fluxului (user_id, scor, etc.).
    - **Noduri**: Funcții Python asincrone care reprezintă acțiunile posibile (ex: `trigger_job_search`, `trigger_learning_path`).
    - **Muchie Condiționată (`route_flow`)**: O funcție care se uită la `cv_score` din starea curentă și returnează numele următorului nod care trebuie executat. Aceasta este piesa centrală a logicii de decizie.
4.  **`state.py`**: Centralizează definițiile modelelor de date (Pydantic) și a stării grafului (`TypedDict`).
5.  **`config.py`**: Încarcă toate variabilele de mediu și definește constantele (nume de topicuri, URL-uri) pentru a evita hardcodarea lor în logica aplicației.

## Fluxul de Execuție

1.  `CV Analyzer Agent` publică un eveniment pe topicul `cv.analyzed`.
2.  Consumatorul din `Agent Orchestrator` preia mesajul.
3.  Invocă graful LangGraph cu starea inițială extrasă din mesaj.
4.  Funcția `route_flow` este executată.
    - **Dacă `scor >= 70`**: Graful tranziționează la nodul `trigger_job_search`. Acest nod trimite un request `POST` către `job-scraper-service` pentru a porni procesul de scraping.
    - **Dacă `scor < 70`**: Graful tranziționează la nodul `trigger_learning_path`. Acest nod publică un nou eveniment pe topicul `gaps.identified`, care va fi preluat de `Learning Path Agent`.
5.  După executarea nodului final, starea completă a fluxului este salvată în Redis cu un TTL de 24 de ore.

