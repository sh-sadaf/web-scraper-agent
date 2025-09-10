import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import google.generativeai as genai

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
st.set_page_config(page_title="🌐 Smart Web Scraper", layout="wide")

# --- Session State ---
if "page_data" not in st.session_state:
    st.session_state.page_data = None

# --- Sidebar for API Keys ---
st.sidebar.subheader("🔑 Enter Your Keys")
scraper_key = st.sidebar.text_input("ScraperAPI Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

if gemini_key:
    genai.configure(api_key=gemini_key)

st.sidebar.markdown("---")
st.sidebar.title("Quick Actions")
if st.sidebar.button("🚀 Scrape New Page"):
    st.session_state.page_data = None
if st.sidebar.button("🗑️ Clear Session"):
    st.session_state.page_data = None
    st.sidebar.success("Session cleared!")

# --- Main Tabs ---
tab1, tab2 = st.tabs(["🕸️ Scraper", "🤖 AI Assistant"])

with tab1:
    st.title("🌐 Smart Web Scraper")
    st.markdown("Scrape a webpage or a specific topic, and download the data.")

    scraper_mode = st.radio("Select Scraper Mode:", ["Full Page", "Topic-Driven"])

    if not scraper_key:
        st.warning("⚠️ Please enter your ScraperAPI Key in the sidebar to use the scraper.")
    else:
        # --- Full Page Scraper ---
        if scraper_mode == "Full Page":
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

                        st.session_state.page_data = {
                            "url": url,
                            "headings": headings,
                            "links": links,
                            "paragraphs": paragraphs
                        }
                        st.success("✅ Full page scraped successfully!")
                    except Exception as e:
                        st.error(f"Error scraping page: {e}")

        # --- Topic-Driven Scraper ---
        elif scraper_mode == "Topic-Driven":
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

    # --- Display Scraped Data Preview ---
    if st.session_state.page_data:
        page_data = st.session_state.page_data
        st.subheader("📄 Scraped Data Preview")
        col1, col2 = st.columns(2)

        if scraper_mode == "Full Page":
            with col1:
                st.metric("Headings Found", len(page_data.get("headings", [])))
                with st.expander("View Headings (first 10)"):
                    for i, h in enumerate(page_data.get("headings", [])[:10], 1):
                        st.write(f"{i}. {h}")
            with col2:
                st.metric("Links Found", len(page_data.get("links", [])))
                st.metric("Paragraphs", len(page_data.get("paragraphs", [])))
        else:
            st.write(f"Topic: {page_data.get('topic','')}")
            st.metric("Paragraphs Found", len(page_data.get("paragraphs", [])))
            for i, p in enumerate(page_data.get("paragraphs", [])[:10],1):
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
            # Handle missing keys safely
            headings = data.get("headings", [])
            paragraphs = data.get("paragraphs", [])
            links = data.get("links", [])
            max_len = max(len(headings), len(paragraphs), len(links))
            df = pd.DataFrame({
                "headings": headings + [""]*(max_len - len(headings)),
                "paragraphs": paragraphs + [""]*(max_len - len(paragraphs)),
                "links": links + [""]*(max_len - len(links))
            })
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name="scraped_page.csv",
                mime="text/csv"
            )

# --- AI Assistant Tab ---
with tab2:
    st.title("🤖 AI Assistant")

    if not gemini_key:
        st.warning("⚠️ Please enter your Gemini API Key in the sidebar to use the AI Assistant.")
    elif not st.session_state.page_data:
        st.info("ℹ️ Scrape a page first in the **Scraper** tab to use the AI Assistant.")
    else:
        page_data = st.session_state.page_data

        # Build compact context with headings, links, and paragraphs
        context_parts = []
        if page_data.get("headings"):
            context_parts.append("Headings:\n" + "\n".join(page_data["headings"][:20]))
        if page_data.get("links"):
            context_parts.append("Links:\n" + "\n".join(page_data["links"][:20]))
        if page_data.get("paragraphs"):
            context_parts.append("Paragraphs:\n" + "\n".join(page_data["paragraphs"][:20]))

        text_content = "\n\n".join(context_parts)

        if text_content.strip():
            model = genai.GenerativeModel("gemini-1.5-flash")

            # --- Summary ---
            with st.spinner("AI is summarizing the content..."):
                try:
                    summary = model.generate_content(
                        f"Summarize the following webpage data (headings, links, paragraphs):\n\n{text_content[:6000]}"
                    )
                    st.subheader("📌 AI Summary")
                    st.write(summary.text)
                except Exception as e:
                    st.error(f"Error generating summary: {e}")

            # --- Q&A ---
            st.subheader("💬 Ask the AI a Question")
            user_q = st.text_input("Type your question here:")
            if st.button("Ask"):
                with st.spinner("AI is thinking..."):
                    try:
                        answer = model.generate_content(
                            f"Based on the following webpage data, answer the question:\n\n{text_content[:6000]}\n\nQuestion: {user_q}"
                        )
                        st.write(answer.text)
                    except Exception as e:
                        st.error(f"Error generating answer: {e}")
        else:
            st.warning("⚠️ No content found in the scraped data.")
