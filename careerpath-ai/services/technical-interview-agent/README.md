# Technical Interview Agent

**ID Task Jira:** CP-032

Acest agent simulează un interviu tehnic cu utilizatorul, axat pe algoritmică, structuri de date și system design. Este un agent conversațional, în timp real, proiectat să evalueze cunoștințele tehnice ale candidatului.

## Arhitectură și Tehnologii

Arhitectura este similară cu cea a agentului HR, fiind bazată pe comunicare în timp real.

- **FastAPI & WebSockets**: Asigură comunicarea bi-direcțională cu clientul.
- **Google Gemini 1.5 Pro**: Va fi folosit pentru a genera întrebări tehnice, a evalua răspunsurile și a oferi explicații.
- **Redis**: Va stoca istoricul conversației pentru fiecare sesiune de interviu, permițând agentului să urmărească progresul și să pună întrebări de follow-up.

## Cum Va Fi Implementat

1.  **`config.py`**: Va stoca cheia API Gemini și URL-ul Redis.
2.  **`prompts.py`**: Va conține un prompt de sistem foarte specific, care va instrui AI-ul: "Ești un inginer software senior pe nume 'Sam'. Scopul tău este să conduci un interviu tehnic. Începe cu o întrebare de algoritmică (ex: 'two-sum', 'reverse a linked list'), apoi crește dificultatea. Evaluează corectitudinea și eficiența soluției propuse de candidat. Dacă răspunsul este corect, treci la o întrebare mai grea. Dacă este greșit, oferă un indiciu. Nu oferi soluția direct."
3.  **`connection_manager.py`**: O clasă singleton pentru a gestiona conexiunile WebSocket active (identică cu cea de la agentul HR).
4.  **`conversation.py`**: Va gestiona logica de chat, preluând și salvând istoricul conversației în Redis și interacționând cu API-ul Gemini.
5.  **`main.py`**: Serverul FastAPI care expune endpoint-ul WebSocket `ws://.../interview/tech/{session_id}` și gestionează bucla de comunicare.

## Fluxul Conversațional

1.  Utilizatorul începe un interviu tehnic. Frontend-ul deschide o conexiune WebSocket.
2.  Agentul 'Sam' trimite un mesaj de salut și prima întrebare tehnică.
3.  Utilizatorul trimite soluția sau răspunsul său.
4.  Serverul primește mesajul, îl adaugă la istoric și trimite totul la Gemini pentru evaluare.
5.  Gemini, conform promptului, evaluează răspunsul și generează următoarea replică (un indiciu, o nouă întrebare, o confirmare).
6.  Serverul trimite răspunsul înapoi utilizatorului.
7.  Ciclul se repetă. La final, agentul poate oferi un sumar al performanței.

