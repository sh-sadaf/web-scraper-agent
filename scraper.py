from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_page(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("load", timeout=10000)
        except:
            print("⚠️ Page kept loading, continuing anyway...")

        content = page.content()
        browser.close()

        soup = BeautifulSoup(content, "html.parser")
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
        links = [a["href"] for a in soup.find_all("a", href=True)]

        return {
            "url": url,      # ✅ FIX HERE
            "headings": headings,
            "links": links
        }

# scraper.py (add this function)
import requests
from bs4 import BeautifulSoup

def scrape_page_requests(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])]
    links = [a.get("href") for a in soup.find_all("a") if a.get("href")]

    return {
        "headings": headings,
        "links_count": len(links),
        "url": url
    }
