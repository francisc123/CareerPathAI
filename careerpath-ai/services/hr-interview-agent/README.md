# HR Interview Agent

**ID Task Jira:** CP-031

Acest agent simulează un interviu de HR (non-tehnic) cu utilizatorul. Este un agent conversațional, în timp real, proiectat să interacționeze natural și să ofere feedback la final.

## Arhitectură și Tehnologii

Spre deosebire de agenții anteriori bazați pe Kafka, acesta folosește o arhitectură real-time.

- **FastAPI**: Pe lângă serverul HTTP, FastAPI oferă un suport excelent pentru WebSockets, care va fi principalul canal de comunicare cu clientul (frontend).
- **WebSockets**: Tehnologia de bază pentru comunicarea bi-direcțională și real-time între browser-ul utilizatorului și agent.
- **Google Gemini 1.5 Pro**: Vom folosi Gemini pentru capacitățile sale avansate de conversație. Modelul va fi instruit printr-un prompt de sistem să acționeze ca un recruiter HR.
- **Redis**: Va fi folosit pentru a stoca istoricul conversației pentru fiecare sesiune de interviu activă. Acest lucru este esențial pentru ca agentul să aibă "memorie" și să poată purta o conversație coerentă.
- **Pydantic**: Pentru a structura și valida mesajele trimise prin WebSocket.

## Cum Va Fi Implementat

1.  **`config.py`**: Va stoca setările, cum ar fi cheia API Gemini și URL-ul Redis.
2.  **`prompts.py`**: Va conține promptul de sistem detaliat care definește personalitatea și obiectivele agentului HR. De exemplu: "Ești un recruiter prietenos, dar profesionist. Scopul tău este să evaluezi soft skill-urile, motivația și potrivirea culturală a candidatului. Pune întrebări deschise despre experiențele trecute, gestionarea conflictelor și obiectivele de carieră. Nu pune întrebări tehnice."
3.  **`connection_manager.py`**: O clasă de tip singleton care va gestiona conexiunile WebSocket active. Va avea metode pentru a conecta, deconecta și trimite mesaje către un client specific.
4.  **`conversation.py`**: "Creierul" conversațional. Va conține logica pentru:
    -   Preluarea istoricului conversației din Redis.
    -   Adăugarea noului mesaj de la utilizator la istoric.
    -   Trimiterea întregului istoric către API-ul Gemini.
    -   Primirea răspunsului de la Gemini.
    -   Actualizarea istoricului în Redis cu noul răspuns.
    -   Trimiterea răspunsului înapoi la utilizator prin WebSocket.
5.  **`main.py`**: Serverul FastAPI.
    -   Va expune un singur endpoint WebSocket: `ws://.../interview/hr/{session_id}`.
    -   Când un client se conectează, va gestiona bucla de comunicare: așteaptă un mesaj de la client, îl pasează către `conversation.py` pentru procesare și trimite răspunsul înapoi.

## Fluxul Conversațional

1.  Utilizatorul, din interfața web, inițiază un interviu HR. Frontend-ul deschide o conexiune WebSocket către `ws://.../interview/hr/{session_id}`.
2.  Serverul acceptă conexiunea. Agentul trimite un mesaj de bun venit (ex: "Salut! Sunt [Nume Agent], recruiter la CareerPath AI. Ești pregătit să începem?").
3.  Utilizatorul trimite un mesaj (răspunsul său).
4.  Serverul primește mesajul, îl adaugă la istoricul conversației din Redis și trimite totul la Gemini.
5.  Gemini generează următorul răspuns/întrebare, conform personalității definite în prompt.
6.  Serverul primește răspunsul de la Gemini, îl salvează în Redis și îl trimite utilizatorului prin WebSocket.
7.  Pașii 3-6 se repetă până când agentul (sau utilizatorul) decide să încheie conversația.
8.  La final, agentul ar putea folosi un prompt separat pentru a analiza întregul transcript din Redis și a genera un feedback structurat.

