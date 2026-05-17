import requests
from bs4 import BeautifulSoup

def scrape_ejobs(skills):
    jobs = []
    query = "-".join(skills)
    url = f"https://www.ejobs.ro/locuri-de-munca/{query}/"

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")

    # Selectori specifici eJobs
    job_list = soup.find_all("li", class_="JobCard")
    for item in job_list:
        try:
            title_elem = item.find("a", class_="JobCard-title")
            jobs.append({
                "title": title_elem.get_text().strip(),
                "url": "https://www.ejobs.ro" + title_elem["href"],
                "company": item.find("h3", class_="JobCard-company").get_text().strip(),
                "location": "Remote/Romania", # eJobs are structura complexa aici
                "source": "ejobs"
            })
        except: continue
    return jobs