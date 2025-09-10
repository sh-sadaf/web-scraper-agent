import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
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
    
    # Get all relevant text
    elements = soup.find_all(["p", "span", "li", "h1", "h2", "h3", "h4", "h5", "h6", "div"])
    all_text = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
    
    # Filter by topic (case-insensitive)
    filtered_text = [t for t in all_text if topic.lower() in t.lower()]
    
    return {"url": url, "topic": topic, "paragraphs": filtered_text}

# --- Page Config ---
st.set_page_config(page_title="🌐 Smart Web Scraper + AI Assistant", layout="wide")

# --- Session State ---
if "page_data" not in st.session_state:
    st.session_state.page_data = None
if "ai_answer" not in st.session_state:
    st.session_state.ai_answer = None

# --- Sidebar ---
st.sidebar.title("Quick Actions")
if st.sidebar.button("🚀 Scrape New Page"):
    st.session_state.page_data = None
    st.session_state.ai_answer = None
if st.sidebar.button("🗑️ Clear Session"):
    st.session_state.page_data = None
    st.session_state.ai_answer = None
    st.sidebar.success("Session cleared!")

# --- Main App ---
st.title("🌐 Smart Web Scraper & AI Assistant")
st.markdown("Scrape a webpage, ask AI specific questions, and download the data.")

# --- Select Scraper Mode ---
scraper_mode = st.radio("Select Scraper Mode:", ["Full Page", "Topic-Driven"])

# --- Scraper Logic ---
if scraper_mode == "Full Page":
    url = st.text_input("Enter website URL:")
    if st.button("Scrape Full Page") and url:
        with st.spinner("Scraping full page with ScraperAPI..."):
            try:
                SCRAPER_API_KEY = st.secrets["SCRAPER_API_KEY"]
                if not url.startswith("http"):
                    url = "https://" + url
                params = {"api_key": SCRAPER_API_KEY, "url": url, "render": "true"}
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

elif scraper_mode == "Topic-Driven":
    url = st.text_input("Enter website URL:")
    topic = st.text_input("Enter topic/keyword to scrape:")

    if st.button("Scrape Topic") and url and topic:
        with st.spinner(f"Scraping page for topic '{topic}'..."):
            try:
                SCRAPER_API_KEY = st.secrets["SCRAPER_API_KEY"]
                page_data = scrape_topic(url, topic, SCRAPER_API_KEY)
                st.session_state.page_data = page_data
                st.success(f"✅ Found {len(page_data['paragraphs'])} entries for '{topic}'")
            except Exception as e:
                st.error(f"Error scraping page: {e}")

    # Here you can also add display, AI question, and download buttons for topic-driven mode

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

# --- AI Question Section ---
if st.session_state.page_data:
    st.subheader("🤖 Ask AI About This Page")
    question = st.text_input("💬 Enter your question:", placeholder="What do you want to know?")
    get_answer_clicked = st.button("Get AI Answer")

    if get_answer_clicked and question:
        with st.spinner("AI analyzing relevant content..."):
            MAX_PARAGRAPHS = 10
            if scraper_mode == "Topic-Driven":
                filtered_paragraphs = page_data["paragraphs"][:MAX_PARAGRAPHS]
            else:
                filtered_paragraphs = page_data["paragraphs"][:MAX_PARAGRAPHS]
            content_text = "\n\n".join(page_data.get("headings", []) + filtered_paragraphs)
            if len(content_text) > 2000:
                content_text = content_text[:2000] + "\n...[truncated]"

            prompt = f"""
You are a helpful AI assistant specialized in analyzing web pages.

Webpage URL: {page_data['url']}
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
