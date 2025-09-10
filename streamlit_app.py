import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

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
    
    elements = soup.find_all(["p", "span", "li", "h1", "h2", "h3", "h4", "h5", "h6", "div"])
    all_text = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
    filtered_text = [t for t in all_text if topic.lower() in t.lower()]
    
    return {"url": url, "topic": topic, "paragraphs": filtered_text}

# -----------------------------
# Streamlit App Config
# -----------------------------
st.set_page_config(page_title="🌐 Smart Web Scraper", layout="wide")

# --- Session State ---
if "page_data" not in st.session_state:
    st.session_state.page_data = None

# --- Sidebar ---
st.sidebar.title("Quick Actions & API Keys")
if st.sidebar.button("🚀 Scrape New Page"):
    st.session_state.page_data = None
if st.sidebar.button("🗑️ Clear Session"):
    st.session_state.page_data = None
    st.sidebar.success("Session cleared!")

# --- Ask user for ScraperAPI Key ---
scraper_api_key = st.sidebar.text_input("ScraperAPI Key", type="password", help="Enter your personal ScraperAPI key")

if not scraper_api_key:
    st.warning("Please enter your ScraperAPI key in the sidebar to proceed.")
    st.stop()

# --- Main App ---
st.title("🌐 Smart Web Scraper")
st.markdown("Scrape a webpage (full page or topic-specific) and download the data.")

# --- Select Scraper Mode ---
scraper_mode = st.radio("Select Scraper Mode:", ["Full Page", "Topic-Driven"])

# --- Scraper Logic ---
if scraper_mode == "Full Page":
    url_full = st.text_input("Enter website URL for full page scrape:")
    if st.button("Scrape Full Page") and url_full:
        with st.spinner("Scraping full page with ScraperAPI..."):
            try:
                if not url_full.startswith("http"):
                    url_full = "https://" + url_full
                params = {"api_key": scraper_api_key, "url": url_full, "render": "true"}
                response = requests.get("https://api.scraperapi.com/", params=params, timeout=60)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")

                headings = [h.get_text(strip=True) for h in soup.find_all(["h1","h2","h3","h4","h5","h6"])]
                links = [a.get("href") for a in soup.find_all("a", href=True)]
                paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]

                st.session_state.page_data = {"url": url_full, "headings": headings, "links": links, "paragraphs": paragraphs}
                st.success("✅ Full page scraped successfully!")

            except Exception as e:
                st.error(f"Error scraping page: {e}")

elif scraper_mode == "Topic-Driven":
    url_topic = st.text_input("Enter website URL for topic-driven scrape:")
    topic = st.text_input("Enter topic/keyword to scrape:")
    if st.button("Scrape Topic") and url_topic and topic:
        with st.spinner(f"Scraping page for topic '{topic}'..."):
            try:
                page_data = scrape_topic(url_topic, topic, scraper_api_key)
                st.session_state.page_data = page_data
                st.success(f"✅ Found {len(page_data['paragraphs'])} entries for '{topic}'")
            except Exception as e:
                st.error(f"Error scraping page: {e}")

# --- Display Scraped Data Preview ---
if st.session_state.page_data:
    page_data = st.session_state.page_data
    st.subheader("📄 Scraped Data Preview")
    col1, col2 = st.columns(2)
    if scraper_mode == "Full Page":
        with col1:
            st.metric("Headings Found", len(page_data["headings"]))
            with st.expander("View Headings (first 10)"):
                for i, h in enumerate(page_data["headings"][:10], 1):
                    st.write(f"{i}. {h}")
        with col2:
            st.metric("Links Found", len(page_data["links"]))
            st.metric("Paragraphs", len(page_data["paragraphs"]))
    else:
        st.write(f"Topic: {page_data.get('topic','')}")
        st.metric("Paragraphs Found", len(page_data["paragraphs"]))
        for i, p in enumerate(page_data["paragraphs"][:10],1):
            st.write(f"{i}. {p}")

# --- Download Scraped Data ---
if st.session_state.page_data:
    st.subheader("💾 Download Scraped Data")
    save_format = st.radio("Choose format:", ["JSON", "CSV"])
    data = st.session_state.page_data

    if save_format == "JSON":
        json_str = json.dumps(data, ensure_ascii=False, indent=4)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name="scraped_page.json",
            mime="application/json"
        )
    else:
        max_len = max(len(data.get("headings",[])), len(data.get("paragraphs",[])), len(data.get("links",[])))
        df = pd.DataFrame({
            "headings": data.get("headings", []) + [""]*(max_len - len(data.get("headings", []))),
            "paragraphs": data.get("paragraphs", []) + [""]*(max_len - len(data.get("paragraphs", []))),
            "links": data.get("links", []) + [""]*(max_len - len(data.get("links", [])))
        })
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="scraped_page.csv",
            mime="text/csv"
        )
