from google import genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

CV_SCORING_SYSTEM_PROMPT = """
You are a senior technical recruiter with 15 years of experience. Analyze the CV and return ONLY a valid JSON object with no extra text.

Scoring rubric (total 100 points):
- Years of experience: 0-30 pts (0-1yr=5, 1-2yr=12, 2-4yr=20, 4-7yr=26, 7+yr=30)
- Skill stack relevance: 0-25 pts (modern/in-demand technologies score higher)
- Project quality: 0-20 pts (real-world impact, complexity, ownership)
- Education: 0-15 pts (CS degree=15, bootcamp=8, self-taught=5)
- Certifications: 0-10 pts (cloud/industry certs)

Return exactly this JSON structure:
{
  "score": <integer 0-100>,
  "seniority": <"junior"|"mid"|"senior">,
  "skills": [<list of identified skills>],
  "strengths": [<list of 2-4 key strengths>],
  "gaps": [<list of 2-4 missing skills or weaknesses>],
  "target_role": <"suggested job title">
}
"""

GAP_ANALYSIS_SYSTEM_PROMPT = """
You are a career development expert. Given a candidate's CV score, skills, and target role, identify skill gaps and create a learning plan.

Return ONLY a valid JSON object with no extra text:
{
  "gaps": [<list of all missing skills for the target role>],
  "priority_gaps": [<top 3 most critical gaps to address first>],
  "estimated_weeks_to_close": <integer, realistic weeks to close priority gaps>
}
"""

cv_samples = [
    {
        "label": "Junior Developer",
        "text": """
        Name: Alexandru Ionescu
        Experience: 1 year as junior Python developer at a startup
        Education: Bachelor in Computer Science, University of Bucharest, 2023
        Skills: Python, HTML, CSS, basic SQL, Git
        Projects: Built a personal blog with Flask and SQLite. Contributed to open-source project on GitHub.
        """
    },
    {
        "label": "Mid Developer",
        "text": """
        Name: Maria Constantin
        Experience: 3 years as backend developer
        Education: Bachelor in Software Engineering, Politehnica University, 2021
        Skills: Python, Django, REST APIs, PostgreSQL, Redis, Docker, AWS basics, Git, Linux
        Projects: Led backend development for an e-commerce platform with 50k users. Built internal analytics dashboard reducing reporting time by 60%.
        Certifications: AWS Cloud Practitioner
        """
    },
    {
        "label": "Senior Developer",
        "text": """
        Name: Andrei Popescu
        Experience: 8 years in software engineering, 3 years as tech lead
        Education: Master in Computer Science, Technical University Cluj, 2016
        Skills: Python, Go, Kubernetes, Terraform, AWS, GCP, PostgreSQL, Redis, Kafka, Elasticsearch, Docker, CI/CD, System Design
        Projects: Designed and built microservices platform processing 2M events/day. Led team of 6 engineers. Reduced infrastructure costs by 40% through optimization.
        Certifications: AWS Solutions Architect Professional, CKA (Kubernetes)
        """
    },
    {
        "label": "Career Changer",
        "text": """
        Name: Elena Dumitrescu
        Experience: 5 years as marketing manager, 8 months self-learning programming
        Education: Bachelor in Marketing, Academy of Economic Studies, 2018
        Skills: Python basics, HTML/CSS, Excel, SQL basics, Google Analytics, Tableau
        Projects: Built a data dashboard to analyze marketing campaigns using Python and Tableau. Completed Google Data Analytics certificate.
        Certifications: Google Data Analytics Certificate
        """
    },
    {
        "label": "Bootcamp Graduate",
        "text": """
        Name: Cristian Muresan
        Experience: No professional experience, completed 6-month bootcamp
        Education: Full-Stack Web Development Bootcamp, 2024
        Skills: JavaScript, React, Node.js, Express, MongoDB, HTML, CSS, Git
        Projects: Capstone project: full-stack task management app with authentication. 3 portfolio projects on GitHub.
        """
    }
]


def score_cv(cv_text: str) -> dict:
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"{CV_SCORING_SYSTEM_PROMPT}\n\nCV to analyze:\n{cv_text}"
    )
    raw = response.text.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


def analyze_gaps(score_result: dict) -> dict:
    prompt = f"{GAP_ANALYSIS_SYSTEM_PROMPT}\n\nCandidate data:\n{json.dumps(score_result, indent=2)}"
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    raw = response.text.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


if __name__ == "__main__":
    for sample in cv_samples:
        print(f"\n{'='*60}")
        print(f"Testing: {sample['label']}")
        print('='*60)

        score_result = score_cv(sample["text"])
        print("CV Score Result:")
        print(json.dumps(score_result, indent=2))

        gap_result = analyze_gaps(score_result)
        print("\nGap Analysis Result:")
        print(json.dumps(gap_result, indent=2))
