import os
from google import genai
from google.genai import types

# 1. Inițializăm clientul Gemini
# Acesta va lua automat cheia ta din variabila de mediu GEMINI_API_KEY
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 2. Citim promptul pe care îl ai deja salvat în folderul prompts
# Folosim calea relativă pentru a ajunge în folderul părinte, apoi în 'prompts'
prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'cv_scoring.txt')
with open(prompt_path, "r", encoding="utf-8") as f:
    system_prompt = f.read()

# 3. Creăm un CV "de test" hardcodat. Aici simulăm un Junior.
cv_text_mock = """
Nume: Ion Popescu
Experienta: 6 luni internship backend la o companie locala.
Tehnologii: Python, Django, HTML, CSS, un pic de SQL.
Educatie: Facultatea de Automatica si Calculatoare, anul 3.
"""

def testeaza_promptul():
    print("Trimit cererea către Gemini... Așteaptă te rog.\n")

    # 4. Apelăm modelul Gemini
    # Pentru text/analiză, folosim flash (cum ai precizat în documentație că 001 e doar pt embeddings)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=cv_text_mock,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            # MAGIC TRICK: Forțăm modelul să răspundă DOAR cu JSON valid!
            # Fără text de genul "Iată JSON-ul cerut:" care ne-ar strica aplicația.
            response_mime_type="application/json",
        )
    )

    print("Răspunsul primit de la Gemini (trebuie să fie JSON valid):")
    print(response.text)

if __name__ == "__main__":
    # Rulăm funcția doar dacă executăm acest fișier direct
    testeaza_promptul()