import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from collections import Counter
from agent import ask_agent  # Your Gemini AI function

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
# Page Config
# -----------------------------
st.set_page_config(page_title="🌐 Smart Web Scraper + AI Assistant", layout="wide")

# -----------------------------
# Session State
# -----------------------------
if "page_data" not in st.session_state:
    st.session_state.page_data = None
if "ai_answer" not in st.session_state:
    st.session_state.ai_answer = None

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("Quick Actions")
if st.sidebar.button("🚀 Scrape New Page"):
    st.session_state.page_data = None
    st.session_state.ai_answer = None
if st.sidebar.button("🗑️ Clear Session"):
    st.session_state.page_data = None
    st.session_state.ai_answer = None
    st.sidebar.success("Session cleared!")

# -----------------------------
# Main App
# -----------------------------
st.title("🌐 Smart Web Scraper + AI Assistant")
st.markdown("Scrape a webpage, ask AI specific questions, and download the data.")

# -----------------------------
# Tabs for Scraper Modes
# -----------------------------
tab_full, tab_topic = st.tabs(["Full Page Scraper", "Topic-Driven Scraper"])

# =============================
# Full Page Scraper Tab
# =============================
with tab_full:
    url_full = st.text_input("Enter website URL for Full Page Scraper:", key="url_full")
    if st.button("Scrape Full Page", key="scrape_full") and url_full:
        with st.spinner("Scraping full page with ScraperAPI..."):
            try:
                SCRAPER_API_KEY = st.secrets["SCRAPER_API_KEY"]
                if not url_full.startswith("http"):
                    url_full = "https://" + url_full
                params = {"api_key": SCRAPER_API_KEY, "url": url_full, "render": "true"}
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

# =============================
# Topic-Driven Scraper Tab
# =============================
with tab_topic:
    url_topic = st.text_input("Enter website URL for Topic Scraper:", key="url_topic")
    topic = st.text_input("Enter topic/keyword to scrape:", key="topic")
    if st.button("Scrape Topic", key="scrape_topic") and url_topic and topic:
        with st.spinner(f"Scraping page for topic '{topic}'..."):
            try:
                SCRAPER_API_KEY = st.secrets["SCRAPER_API_KEY"]
                page_data = scrape_topic(url_topic, topic, SCRAPER_API_KEY)
                st.session_state.page_data = page_data
                st.success(f"✅ Found {len(page_data['paragraphs'])} entries for '{topic}'")
            except Exception as e:
                st.error(f"Error scraping page: {e}")

# =============================
# Display Scraped Data Preview
# =============================
if st.session_state.page_data:
    page_data = st.session_state.page_data
    st.subheader("📄 Scraped Data Preview")

    if "headings" in page_data:  # Full Page
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Headings Found", len(page_data["headings"]))
            with st.expander("View Headings (first 10)"):
                for i, h in enumerate(page_data["headings"][:10], 1):
                    st.write(f"{i}. {h}")
        with col2:
            st.metric("Links Found", len(page_data["links"]))
            st.metric("Paragraphs", len(page_data["paragraphs"]))
            with st.expander("View Paragraphs (first 10)"):
                for i, p in enumerate(page_data["paragraphs"][:10],1):
                    st.write(f"{i}. {p}")
    else:  # Topic-Driven
        st.write(f"Topic: {page_data.get('topic','')}")
        st.metric("Paragraphs Found", len(page_data["paragraphs"]))
        with st.expander("View Paragraphs"):
            for i, p in enumerate(page_data["paragraphs"][:10],1):
                st.write(f"{i}. {p}")

        # Optional: Show top keywords
        counter = Counter(" ".join(page_data["paragraphs"]).split())
        st.write("Top keywords:", counter.most_common(5))

# =============================
# AI Question Section
# =============================
if st.session_state.page_data:
    st.subheader("🤖 Ask AI About This Page")
    question = st.text_input("💬 Enter your question:", placeholder="What do you want to know?")
    get_answer_clicked = st.button("Get AI Answer", key="ai_btn")

    if get_answer_clicked and question:
        with st.spinner("AI analyzing relevant content..."):
            MAX_PARAGRAPHS = 10
            filtered_paragraphs = page_data.get("paragraphs", [])[:MAX_PARAGRAPHS]
            content_text = "\n\n".join(page_data.get("headings", []) + filtered_paragraphs)
            if len(content_text) > 2000:
                content_text = content_text[:2000] + "\n...[truncated]"

            prompt = f"""
You are a helpful AI assistant specialized in analyzing web pages.

Webpage URL: {page_data.get('url','N/A')}
Topic Filter: {page_data.get('topic','None')}

Webpage content:
{content_text}

User's question: {question}

Instructions for AI:
- Answer concisely and only using the content provided.
- If content does not contain information on the question, respond politely:
  "No information about this topic was found on the page."
- Focus only on topic if specified.
- Do not attempt to summarize unrelated sections.
"""
            try:
                st.session_state.ai_answer = ask_agent(prompt)
            except Exception as e:
                st.session_state.ai_answer = f"AI request failed: {e}"

if st.session_state.ai_answer:
    st.subheader("AI Answer")
    st.write(st.session_state.ai_answer)

# =============================
# Download Scraped Data
# =============================
if st.session_state.page_data:
    st.subheader("💾 Download Scraped Data")
    save_format = st.radio("Choose format:", ["JSON", "CSV"], key="download_format")
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
        max_len = max(len(data.get("headings",[])), len(data["paragraphs"]), len(data.get("links",[])))
        df = pd.DataFrame({
            "headings": data.get("headings", []) + [""]*(max_len - len(data.get("headings", []))),
            "paragraphs": data["paragraphs"] + [""]*(max_len - len(data["paragraphs"])),
            "links": data.get("links", []) + [""]*(max_len - len(data.get("links", [])))
        })
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="scraped_page.csv",
            mime="text/csv"
        )
