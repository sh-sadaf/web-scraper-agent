import streamlit as st
import requests
from bs4 import BeautifulSoup
from agent import ask_agent  # your Gemini agent function

# === Configure your Scraper API key ===
SCRAPER_API_KEY = st.secrets["SCRAPER_API_KEY"]
SCRAPER_API_URL = "http://api.scraperapi.com"

st.title("🌐 Smart Web Scraper & AI Assistant (Dynamic Pages)")

# Input URL
url = st.text_input("Enter the URL to scrape:", placeholder="https://example.com")

def scrape_page_dynamic(url: str):
    """Scrape dynamic content using ScraperAPI"""
    try:
        params = {
            "api_key": SCRAPER_API_KEY,
            "url": url,
            "render": "true"  # ensures JS rendering
        }
        response = requests.get(SCRAPER_API_URL, params=params, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")

        headings = [h.get_text(strip=True) for h in soup.find_all(["h1","h2","h3","h4","h5","h6"])]
        links = [a.get("href") for a in soup.find_all("a", href=True)]
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]

        return {"url": url, "headings": headings, "links": links, "paragraphs": paragraphs[:10]}
    except Exception as e:
        st.error(f"Failed to scrape page: {e}")
        return None

# Scrape button
if st.button("🚀 Scrape & Analyze Page") and url:
    with st.spinner("Scraping the page..."):
        page_data = scrape_page_dynamic(url)
        if page_data:
            st.success("✅ Page scraped successfully!")
            
            # Generate AI summary
            summary_prompt = f"""
            Please summarize this webpage content:
            
            Headings: {page_data['headings']}
            Paragraphs: {page_data['paragraphs']}
            URL: {page_data['url']}
            """
            summary = ask_agent(summary_prompt)
            
            st.subheader("📄 Page Summary")
            st.write(summary)
            
            st.subheader("🔹 Headings")
            st.write(page_data['headings'])
            
            st.subheader("🔹 Links")
            st.write(page_data['links'])
