# Learning Path Agent

**ID Task Jira:** CP-030, CP-050

Acest agent este responsabil pentru crearea unui plan de învățare personalizat și structurat pentru utilizatorii al căror CV a obținut un scor sub pragul de angajabilitate.

## Arhitectură și Tehnologii

Agentul este un serviciu asincron Python, proiectat să fie robust și eficient, folosind următoarele tehnologii:

- **FastAPI**: Expune un server web pentru endpoint-uri RESTful, conform task-ului `CP-050`. Acestea vor permite frontend-ului să preia planul de învățare și să trimită rezultatele quiz-urilor.
- **aiokafka**: Conține un consumator care ascultă topicul `gaps.identified`. Acesta este punctul de intrare care declanșează logica principală a agentului.
- **Google Gemini 1.5 Pro**: Am ales acest model LLM pentru capacitatea sa de a procesa contexte mari și de a genera output-uri JSON structurate și de înaltă calitate. Va fi folosit pentru a transforma o listă de "lipsuri" într-un plan de învățare complet.
- **asyncpg**: Un driver de bază de date asincron de înaltă performanță pentru PostgreSQL. Va fi folosit pentru a salva planurile de învățare generate direct în baza de date.
- **Pydantic**: Pentru validarea riguroasă a datelor, atât la intrarea din Kafka, cât și la parsarea răspunsului de la LLM.

## Cum Va Fi Implementat

Implementarea va urma o structură modulară, separând responsabilitățile:

1.  **`config.py`**: Va centraliza toate configurațiile: cheia API pentru Gemini, URL-ul bazei de date, adresele Kafka și numele topicurilor.
2.  **`prompts.py`**: Va conține textul promptului de sistem pentru Gemini. Acesta este un element critic și va fi proiectat cu atenție pentru a instrui modelul să returneze un plan de învățare în format JSON, structurat pe săptămâni, cu module, descrieri și link-uri către resurse.
3.  **`generator.py`**: Va conține logica de interacțiune cu API-ul Gemini. Va avea o funcție `generate_learning_path` care primește lista de "gaps" și rolul țintă, formatează promptul și parsează răspunsul JSON într-un model Pydantic.
4.  **`database.py`**: Va gestiona conexiunea cu baza de date PostgreSQL. Va conține funcții specifice pentru a insera un nou plan de învățare (`insert_learning_path`) și pentru a-l prelua (`get_learning_path_by_user`).
5.  **`consumer.py`**: Asemenea orchestratorului, va conține consumatorul Kafka. La primirea unui mesaj pe `gaps.identified`, va apela `generator.py` pentru a crea planul, apoi `database.py` pentru a-l salva, și în final va publica un eveniment `learning.path.created` pe Kafka.
6.  **`main.py`**: Punctul de intrare FastAPI. Va porni consumatorul în background și va expune endpoint-urile REST necesare pentru interacțiunea cu frontend-ul.

## Fluxul de Execuție

1.  `Agent Orchestrator` publică un eveniment pe topicul `gaps.identified` pentru un utilizator cu scor mic.
2.  Consumatorul din `Learning Path Agent` preia mesajul.
3.  Apelează funcția `generate_learning_path` cu datele din mesaj.
4.  Funcția trimite promptul către API-ul Gemini.
5.  Gemini returnează un obiect JSON complex, reprezentând planul de învățare.
6.  Răspunsul este validat și parsat într-un model Pydantic.
7.  Planul este salvat în tabela `learning_paths` din PostgreSQL.
8.  Un eveniment `learning.path.created` este publicat pe Kafka pentru a notifica alte servicii (ex: `Notification Service`).

