import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from agent import ask_agent  # your Gemini AI function

st.set_page_config(
    page_title="🌐 Smart Web Scraper & AI Assistant",
    layout="wide"
)

# === Sidebar ===
st.sidebar.title("Quick Actions")
st.sidebar.info(
    "This app scrapes webpage content, lets AI analyze it, and saves the data."
)
st.sidebar.markdown("---")
st.sidebar.subheader("Other Streamlit Projects")
st.sidebar.markdown("""
- [Weather App](https://share.streamlit.io)  
- [Stock Dashboard](https://share.streamlit.io)  
- [Text Summarizer](https://share.streamlit.io)  
*Explore other public apps on Streamlit!*
""")
st.sidebar.markdown("---")

# === Session State ===
if "page_data" not in st.session_state:
    st.session_state.page_data = None
if "ai_answer" not in st.session_state:
    st.session_state.ai_answer = None

# === Main App ===
st.title("🌐 Smart Web Scraper & AI Assistant")
st.markdown("Enter a URL to scrape, ask questions, and save the data.")

# --- URL Input ---
url = st.text_input("🔗 Enter the website URL:")

if st.button("🚀 Scrape Page") and url:
    with st.spinner("Scraping page..."):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Scrape content
            headings = [h.get_text(strip=True) for h in soup.find_all(["h1","h2","h3","h4","h5","h6"])]
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]

            st.session_state.page_data = {
                "url": url,
                "headings": headings,
                "links": links,
                "paragraphs": paragraphs[:10]
            }
            st.success("✅ Page scraped successfully!")

        except Exception as e:
            st.error(f"Error scraping page: {e}")

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
            prompt = f"Webpage content:\n{content_text}\n\nUser question: {question}"
            st.session_state.ai_answer = ask_agent(prompt)
        
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

# --- Clear Data Button ---
if st.session_state.page_data:
    if st.button("🗑️ Clear Page Data"):
        st.session_state.page_data = None
        st.session_state.ai_answer = None
        st.success("Session cleared.")
