from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def scrape_page(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # headless=False to see the browser window
        page = browser.new_page()
        page.goto(url, timeout=60000)  # open the page

        # ✅ Add extra wait to allow slow pages to finish loading
        page.wait_for_timeout(5000)  # wait 5 seconds

        # ✅ Scroll down (useful for sites that load content dynamically)
        page.mouse.wheel(0, 5000)

        # Ensure all network requests are done
        page.wait_for_load_state("networkidle")

        # Get the fully rendered HTML
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Extract title, headings, paragraphs, links
        title = soup.title.string.strip() if soup.title else "No title"
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]

        links = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True) or "NO TEXT"
            href = urljoin(url, a["href"])
            links.append({"text": text, "url": href})

        browser.close()

        return {
            "url": url,
            "title": title,
            "headings": headings,
            "paragraphs": paragraphs,
            "links": links,
        }