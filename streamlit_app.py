import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

# Optional: AI agent
try:
    from agent import ask_agent
    AI_ENABLED = True
except:
    AI_ENABLED = False

# -----------------------------
# Topic-driven scraping function
# -----------------------------
def scrape_topic(url: str, topic: str, api_key: str):
    if not url.startswith("http"):
        url = "https://" + url
    params = {"api_key": api_key, "url": url, "render": "true"}
    response = requests.get("https://api.scraperapi.com/", params=params, timeout=60)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    
    elements = soup.find_all(["p","span","li","h1","h2","h3","h4","h5","h6","div"])
    all_text = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
    
    filtered_text = [t for t in all_text if topic.lower() in t.lower()]
    
    return {"url": url, "topic": topic, "paragraphs": filtered_text}

# -----------------------------
# Streamlit App Config
# -----------------------------
st.set_page_config(page_title="🌐 Smart Web Scraper", layout="wide")

# Session State
if "page_data" not in st.session_state:
    st.session_state.page_data = None
if "filtered_paragraphs" not in st.session_state:
    st.session_state.filtered_paragraphs = None

# Sidebar for API keys
st.sidebar.subheader("🔑 Enter Your API Keys")
scraper_key = st.sidebar.text_input("ScraperAPI Key", type="password")
gemini_key = st.sidebar.text_input("Gemini AI Key (optional)", type="password")

st.sidebar.markdown("---")
st.sidebar.title("Quick Actions")
if st.sidebar.button("🚀 Scrape New Page"):
    st.session_state.page_data = None
    st.session_state.filtered_paragraphs = None
if st.sidebar.button("🗑️ Clear Session"):
    st.session_state.page_data = None
    st.session_state.filtered_paragraphs = None
    st.sidebar.success("Session cleared!")

# Main Title
st.title("🌐 Smart Web Scraper")
st.markdown("Scrape a webpage or a specific topic, and download the data.")

# Tabs: Full Page, Topic-Driven, AI Filtering
tabs = ["Full Page", "Topic-Driven"]
if AI_ENABLED:
    tabs.append("AI Filtering")

tab = st.radio("Select Mode:", tabs)

# -----------------------------
# FULL PAGE SCRAPER
# -----------------------------
if tab == "Full Page":
    if not scraper_key:
        st.warning("⚠️ Enter your ScraperAPI Key in the sidebar to use this scraper.")
    else:
        url = st.text_input("Enter website URL:")
        if st.button("Scrape Full Page") and url:
            with st.spinner("Scraping full page..."):
                try:
                    if not url.startswith("http"):
                        url = "https://" + url
                    params = {"api_key": scraper_key, "url": url, "render": "true"}
                    response = requests.get("https://api.scraperapi.com/", params=params, timeout=60)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, "html.parser")

                    headings = [h.get_text(strip=True) for h in soup.find_all(["h1","h2","h3","h4","h5","h6"])]
                    links = [a.get("href") for a in soup.find_all("a", href=True)]
                    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]

                    st.session_state.page_data = {"url": url, "headings": headings, "links": links, "paragraphs": paragraphs}
                    st.success("✅ Full page scraped successfully!")
                except Exception as e:
                    st.error(f"Error scraping page: {e}")

# -----------------------------
# TOPIC-DRIVEN SCRAPER
# -----------------------------
elif tab == "Topic-Driven":
    if not scraper_key:
        st.warning("⚠️ Enter your ScraperAPI Key in the sidebar to use this scraper.")
    else:
        url = st.text_input("Enter website URL:")
        topic = st.text_input("Enter topic/keyword to scrape:")
        if st.button("Scrape Topic") and url and topic:
            with st.spinner(f"Scraping page for topic '{topic}'..."):
                try:
                    page_data = scrape_topic(url, topic, scraper_key)
                    st.session_state.page_data = page_data
                    st.success(f"✅ Found {len(page_data.get('paragraphs', []))} entries for '{topic}'")
                except Exception as e:
                    st.error(f"Error scraping page: {e}")

# -----------------------------
# AI FILTERING (optional)
# -----------------------------
elif tab == "AI Filtering":
    if not scraper_key or not gemini_key:
        st.warning("⚠️ Both ScraperAPI Key and Gemini AI Key are required for AI filtering.")
    else:
        url = st.text_input("Enter website URL:")
        topic = st.text_input("Enter topic to filter with AI:")
        if st.button("Scrape & Filter AI") and url and topic:
            with st.spinner(f"Scraping page and filtering content about '{topic}'..."):
                try:
                    # Scrape full page first
                    if not url.startswith("http"):
                        url = "https://" + url
                    params = {"api_key": scraper_key, "url": url, "render": "true"}
                    response = requests.get("https://api.scraperapi.com/", params=params, timeout=60)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, "html.parser")

                    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]
                    content_text = "\n\n".join(paragraphs[:50])

                    # Send to AI for filtering
                    prompt = f"""
You are an AI assistant specialized in analyzing webpages.

Webpage content:
{content_text}

Task: Extract only the paragraphs that are relevant to the topic "{topic}".
Return the paragraphs in the same order as they appear.
"""
                    # Corrected call without api_key argument
		filtered_paragraphs = ask_agent(prompt)
		st.session_state.filtered_paragraphs = filtered_paragraphs
		st.session_state.page_data = {"url": url, "paragraphs": filtered_paragraphs, "topic": topic}
		st.success(f"✅ Found relevant content for '{topic}' using AI")
                except Exception as e:
                    st.error(f"Error scraping or AI filtering page: {e}")

# -----------------------------
# DISPLAY SCRAPED DATA
# -----------------------------
if st.session_state.page_data:
    page_data = st.session_state.page_data
    st.subheader("📄 Scraped Data Preview")
    col1, col2 = st.columns(2)

    if "headings" in page_data:
        with col1:
            st.metric("Headings Found", len(page_data.get("headings", [])))
            with st.expander("View Headings (first 10)"):
                for i, h in enumerate(page_data.get("headings", [])[:10], 1):
                    st.write(f"{i}. {h}")
        with col2:
            st.metric("Links Found", len(page_data.get("links", [])))
            st.metric("Paragraphs Found", len(page_data.get("paragraphs", [])))
    else:
        st.write(f"Topic: {page_data.get('topic','')}")
        st.metric("Paragraphs Found", len(page_data.get("paragraphs", [])))
        for i, p in enumerate(page_data.get("paragraphs", [])[:10],1):
            st.write(f"{i}. {p}")

# -----------------------------
# DOWNLOAD DATA
# -----------------------------
if st.session_state.page_data:
    st.subheader("💾 Download Scraped Data")
    save_format = st.radio("Choose format:", ["JSON", "CSV"])
    data = st.session_state.page_data

    if save_format == "JSON":
        json_str = json.dumps(data, ensure_ascii=False, indent=4)
        st.download_button(label="📥 Download JSON", data=json_str, file_name="scraped_page.json", mime="application/json")
    else:
        max_len = max(len(data.get("headings", [])), len(data.get("paragraphs", [])), len(data.get("links", [])))
        df = pd.DataFrame({
            "headings": data.get("headings", []) + [""]*(max_len - len(data.get("headings", []))),
            "paragraphs": data.get("paragraphs", []) + [""]*(max_len - len(data.get("paragraphs", []))),
            "links": data.get("links", []) + [""]*(max_len - len(data.get("links", [])))
        })
        csv_data = df.to_csv(index=False)
        st.download_button(label="📥 Download CSV", data=csv_data, file_name="scraped_page.csv", mime="text/csv")

