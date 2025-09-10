import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from agent import ask_agent  # your Gemini AI function

st.set_page_config(page_title="🌐 Smart Web Scraper & AI Assistant", layout="wide")

# === Session State ===
if "page_data" not in st.session_state:
    st.session_state.page_data = None
if "ai_answer" not in st.session_state:
    st.session_state.ai_answer = None

# === Sidebar ===
st.sidebar.title("Quick Actions")
st.sidebar.subheader("Custom Functions")

if st.sidebar.button("🚀 Scrape New Page"):
    st.session_state.page_data = None
    st.session_state.ai_answer = None
if st.sidebar.button("💬 Ask AI"):
    st.sidebar.info("Use the main panel to enter your question about the scraped page.")
if st.sidebar.button("💾 Save Data"):
    st.sidebar.info("Choose JSON or CSV format in the main panel to save scraped data.")
if st.sidebar.button("🗑️ Clear Session"):
    st.session_state.page_data = None
    st.session_state.ai_answer = None
    st.sidebar.success("Session cleared!")

# === Main App ===
st.title("🌐 Smart Web Scraper & AI Assistant")
st.markdown("Enter a URL to scrape, ask AI questions, and save the data.")

# --- URL Input ---
url = st.text_input("🔗 Enter the website URL:")

# --- Scrape Button ---
if st.button("🚀 Scrape Page") and url:
    with st.spinner("Scraping page with ScraperAPI..."):
        try:
            SCRAPER_API_KEY = st.secrets["SCRAPER_API_KEY"]
            params = {
                "api_key": SCRAPER_API_KEY,
                "url": url,
                "render": "true"  # enables JS rendering
            }
            # Increased timeout to 30 seconds
            response = requests.get("https://api.scraperapi.com", params=params, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract content (limit to first 10 headings, 20 links, 10 paragraphs)
            headings = [h.get_text(strip=True) for h in soup.find_all(["h1","h2","h3","h4","h5","h6"])[:10]]
            links = [a.get("href") for a in soup.find_all("a", href=True)[:20]]
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20][:10]

            st.session_state.page_data = {
                "url": url,
                "headings": headings,
                "links": links,
                "paragraphs": paragraphs
            }
            st.success("✅ Page scraped successfully!")

        except Exception as e:
            st.error(f"Error scraping page: {e}")
            # Optional fallback to static scraping
            try:
                st.info("Falling back to static scraping...")
                response = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                headings = [h.get_text(strip=True) for h in soup.find_all(["h1","h2","h3","h4","h5","h6"])[:10]]
                links = [a.get("href") for a in soup.find_all("a", href=True)[:20]]
                paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20][:10]
                st.session_state.page_data = {
                    "url": url,
                    "headings": headings,
                    "links": links,
                    "paragraphs": paragraphs
                }
                st.success("✅ Page scraped successfully with fallback!")
            except Exception as e2:
                st.error(f"Static scraping also failed: {e2}")

# --- Display Scraped Data ---
if st.session_state.page_data:
    page_data = st.session_state.page_data
    st.subheader("📄 Scraped Data Preview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Headings Found", len(page_data["headings"]))
        with st.expander("View Headings"):
            for i, h in enumerate(page_data["headings"], 1):
                st.write(f"{i}. {h}")
    with col2:
        st.metric("Links Found", len(page_data["links"]))
        st.metric("Paragraphs", len(page_data["paragraphs"]))

# --- AI Question Section ---
if st.session_state.page_data:
    st.subheader("🤖 Ask AI About This Page")
    question = st.text_input("💬 Enter your question:", placeholder="What is this page about?")
    
    if st.button("Get AI Answer") and question:
        with st.spinner("AI analyzing..."):
            content_text = "\n\n".join(page_data["headings"] + page_data["paragraphs"])
            # Limit prompt size
            if len(content_text) > 3000:
                content_text = content_text[:3000] + "\n...[truncated]"
            prompt = f"Webpage content:\n{content_text}\n\nUser question: {question}"
            try:
                st.session_state.ai_answer = ask_agent(prompt)
            except Exception as e:
                st.session_state.ai_answer = f"AI request failed: {e}"
        
    if st.session_state.ai_answer:
        st.subheader("AI Answer")
        st.write(st.session_state.ai_answer)

# --- Save Scraped Data ---
if st.session_state.page_data:
    st.subheader("💾 Save Scraped Data")
    save_format = st.radio("Choose format:", ["JSON", "CSV"])
    
    if st.button("Save Data"):
        data = st.session_state.page_data
        if save_format == "JSON":
            filename = "scraped_page.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            st.success(f"Data saved as {filename}")
        else:
            df = pd.DataFrame({
                "headings": data["headings"],
                "paragraphs": data["paragraphs"],
                "links": pd.Series(data["links"])
            })
            filename = "scraped_page.csv"
            df.to_csv(filename, index=False)
            st.success(f"Data saved as {filename}")

