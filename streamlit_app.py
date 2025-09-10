import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from agent import ask_agent  # Your Gemini AI function

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

# --- URL Input ---
url = st.text_input("🔗 Enter the website URL:")

# --- Scrape Button ---
if st.button("🚀 Scrape Page") and url:
    with st.spinner("Scraping full page with ScraperAPI..."):
        try:
            SCRAPER_API_KEY = st.secrets["SCRAPER_API_KEY"]
            params = {
                "api_key": SCRAPER_API_KEY,
                "url": url,
                "render": "true"  # enable JS rendering
            }
            response = requests.get("https://api.scraperapi.com/", params=params, timeout=60)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract full page content
            headings = [h.get_text(strip=True) for h in soup.find_all(
                ["h1","h2","h3","h4","h5","h6"]
            )]
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]

            st.session_state.page_data = {
                "url": url,
                "headings": headings,
                "links": links,
                "paragraphs": paragraphs
            }
            st.success("✅ Full page scraped successfully!")

        except Exception as e:
            st.error(f"Error scraping page: {e}")

# --- Display Scraped Data Preview ---
if st.session_state.page_data:
    page_data = st.session_state.page_data
    st.subheader("📄 Scraped Data Preview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Headings Found", len(page_data["headings"]))
        with st.expander("View Headings (first 10)"):
            for i, h in enumerate(page_data["headings"][:10], 1):
                st.write(f"{i}. {h}")
    with col2:
        st.metric("Links Found", len(page_data["links"]))
        st.metric("Paragraphs", len(page_data["paragraphs"]))

MAX_PARAGRAPHS = 10

if topic:
    filtered_paragraphs = [p for p in page_data["paragraphs"] if topic.lower() in p.lower()]
else:
    filtered_paragraphs = page_data["paragraphs"][:MAX_PARAGRAPHS]

if not filtered_paragraphs:
    filtered_paragraphs = page_data["paragraphs"][:MAX_PARAGRAPHS]

content_text = "\n\n".join(page_data["headings"] + filtered_paragraphs)
if len(content_text) > 2000:
    content_text = content_text[:2000] + "\n...[truncated]"

prompt = f"""
You are a helpful AI assistant specialized in analyzing web pages.

Webpage URL: {page_data['url']}
Topic Filter: {topic if topic else 'None'}

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
        # Align lengths for DataFrame
        max_len = max(len(data["headings"]), len(data["paragraphs"]), len(data["links"]))
        df = pd.DataFrame({
            "headings": data["headings"] + [""]*(max_len - len(data["headings"])),
            "paragraphs": data["paragraphs"] + [""]*(max_len - len(data["paragraphs"])),
            "links": data["links"] + [""]*(max_len - len(data["links"]))
        })
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="scraped_page.csv",
            mime="text/csv"
        )