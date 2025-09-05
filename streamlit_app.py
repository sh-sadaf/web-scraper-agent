# streamlit_app.py
import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from agent import ask_agent  # your existing Gemini agent function

st.title("Web Scraper + AI Chat")

# Initialize session state
if "page_data" not in st.session_state:
    st.session_state.page_data = None

# Input URL
url = st.text_input("Webpage URL:")

# Input Question
question = st.text_input("Your Question:")

async def scrape_page(url: str):
    """Scrape the page asynchronously using Playwright"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        
        # Get headings and links
        headings = await page.eval_on_selector_all("h1, h2, h3, h4, h5, h6", "elements => elements.map(e => e.innerText)")
        links = await page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")
        await browser.close()
        
        return {"url": url, "headings": headings, "links": links}

async def main(url, question):
    if url:
        st.session_state.page_data = await scrape_page(url)
        st.success("Page scraped successfully!")
        st.write("Headings found:", st.session_state.page_data["headings"])
        st.write("Total links found:", len(st.session_state.page_data["links"]))

    if question and st.session_state.page_data:
        # Combine page info with user question
        page_text = "\n".join(st.session_state.page_data["headings"])
        prompt = f"Here is the scraped page content:\n{page_text}\n\nUser Question: {question}"
        answer = ask_agent(prompt)
        st.subheader("AI Answer")
        st.write(answer)
    elif question:
        st.warning("Please provide a URL to scrape first.")

# Run asyncio inside Streamlit
if url or question:
    asyncio.run(main(url, question))
