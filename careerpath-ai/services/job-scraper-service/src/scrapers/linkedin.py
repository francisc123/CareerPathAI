from playwright.sync_api import sync_playwright

def scrape_linkedin(skills, seniority, location):
    jobs = []
    search_query = f"{' '.join(skills)} {seniority}"
    url = f"https://www.linkedin.com/jobs/search?keywords={search_query}&location={location}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # Scroll pentru a încărca rezultate (LinkedIn lazy loading)
        for _ in range(3):
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(2000)

        cards = page.query_selector_all(".base-card")
        for card in cards[:50]:
            try:
                jobs.append({
                    "title": card.query_selector(".base-search-card__title").inner_text().strip(),
                    "company": card.query_selector(".base-search-card__subtitle").inner_text().strip(),
                    "location": card.query_selector(".job-search-card__location").inner_text().strip(),
                    "url": card.query_selector("a").get_attribute("href").split('?')[0],
                    "source": "linkedin"
                })
            except: continue
        browser.close()
    return jobs